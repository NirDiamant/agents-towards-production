"""The durable version of the ingestion pipeline, served to the Inngest dev server.

Run it with two terminals:

    uvicorn app:app --reload --port 8000
    npx inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest

Then open http://127.0.0.1:8288 and send the trigger event from the notebook.
"""
import datetime
import inngest
import inngest.fast_api
from fastapi import FastAPI

from pipeline import Counters, Index, chunk, content_hash, embed, make_corpus, parse

app = FastAPI()

# is_production=False points the SDK at the local dev server. No account, no keys.
client = inngest.Inngest(app_id="rag-ingestion", is_production=False)

CORPUS = {d["id"]: d for d in make_corpus(5000)}
INDEX = Index(append_only=False)   # idempotent: keyed on doc id + chunk no
COUNTERS = Counters()


@client.create_function(
    fn_id="ingest-corpus",
    trigger=inngest.TriggerEvent(event="rag/corpus.ingest"),
    retries=3,
)
def ingest_corpus(ctx: inngest.ContextSync) -> dict:
    """Fan out one event per document.

    One unparseable file fails its own function run. It does not take the corpus with it.
    """
    doc_ids = ctx.step.run("list-documents", lambda: sorted(CORPUS))

    # Fan out by event rather than step.invoke. invoke waits for the child and, if the
    # child fails, raises a NonRetriableError in this run. Waiting and shared fate are
    # both things per-document isolation exists to avoid. See notebook section 9, and
    # https://www.inngest.com/docs/guides/invoking-functions-directly?guide=python
    #
    # Chunked sends keep a single step payload small.
    for i in range(0, len(doc_ids), 500):
        batch = doc_ids[i : i + 500]
        ctx.step.send_event(
            f"fan-out-{i}",
            [
                inngest.Event(
                    name="rag/document.received",
                    data={"doc_id": d, "tenant_id": CORPUS[d]["topic"]},
                )
                for d in batch
            ],
        )
    return {"documents": len(doc_ids)}


@client.create_function(
    fn_id="ingest-document",
    trigger=inngest.TriggerEvent(event="rag/document.received"),
    retries=3,
    # Stay under the embedding provider's rate limit.
    throttle=inngest.Throttle(limit=100, period=datetime.timedelta(minutes=1)),
    # A backfill for one tenant cannot starve live ingestion for the others.
    concurrency=[inngest.Concurrency(key="event.data.tenant_id", limit=5)],
)
def ingest_document(ctx: inngest.ContextSync) -> dict:
    """One document, one function run, every stage its own recorded step.

    A retry replays completed steps from the journal instead of re-running them, so the
    embedding calls below are paid for once even if the run is retried.
    """
    doc_id = ctx.event.data["doc_id"]
    doc = CORPUS[doc_id]

    text = ctx.step.run("parse", lambda: parse(doc, COUNTERS))
    chunks = ctx.step.run("chunk", lambda: chunk(text))

    # A document that parses to nothing goes to a human instead of into the index.
    if not chunks:
        ctx.step.send_event(
            "flag-for-review",
            inngest.Event(name="rag/document.needs_review", data={"doc_id": doc_id}),
        )
        # Waiting on a person, not on another function, so wait_for_event rather than
        # step.invoke: no child function's return value would carry a human decision.
        approval = ctx.step.wait_for_event(
            "await-approval",
            event="rag/document.approved",
            if_exp=f"async.data.doc_id == '{doc_id}'",
            timeout=datetime.timedelta(days=7),
        )
        if approval is None:
            return {"doc_id": doc_id, "status": "rejected-or-timed-out"}

    for i, ch in enumerate(chunks):
        # Each embed is its own step, so a failure at chunk 40 does not re-bill chunks 0 to 39.
        vec = ctx.step.run(f"embed-{i}", lambda ch=ch: embed(ch, COUNTERS))
        ctx.step.run(
            f"upsert-{i}",
            lambda i=i, ch=ch, vec=vec: INDEX.upsert(doc_id, i, ch, vec, COUNTERS),
        )

    # A corrected document can come back with fewer chunks. Drop the ones past its new end.
    ctx.step.run("prune", lambda: INDEX.prune(doc_id, len(chunks)))

    return {"doc_id": doc_id, "chunks": len(chunks), "index_size": INDEX.size()}


@client.create_function(
    fn_id="approve-document",
    trigger=inngest.TriggerEvent(event="rag/document.review_decision"),
)
def approve_document(ctx: inngest.ContextSync) -> dict:
    """A reviewer's decision, forwarded to whichever run is waiting on it."""
    doc_id = ctx.event.data["doc_id"]
    ctx.step.send_event(
        "forward-approval",
        inngest.Event(name="rag/document.approved", data={"doc_id": doc_id}),
    )
    return {"doc_id": doc_id, "approved": True}


@app.get("/stats")
def stats() -> dict:
    return {
        "index_entries": INDEX.size(),
        "duplicates": INDEX.duplicates(),
        "work": {
            "parsed": COUNTERS.parsed,
            "embedded": COUNTERS.embedded,
            "upserted": COUNTERS.upserted,
        },
    }


inngest.fast_api.serve(app, client, [ingest_corpus, ingest_document, approve_document])
