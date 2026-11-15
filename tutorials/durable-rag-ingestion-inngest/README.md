![](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--durable-rag-ingestion-inngest--readme)

# 🔁 Durable RAG Ingestion with Inngest

Build a document ingestion pipeline that **survives partial failures, re-runs and backfills**.

Most RAG tutorials assume your documents made it into the index. This one is about what happens
when they do not: a run over thousands of documents that dies 60 percent of the way through, and a
retry that re-parses and re-embeds everything it already paid for.

![What the naive retry costs](assets/retry-cost.svg)

This page walks through the whole tutorial, code included. The
[notebook](durable_rag_ingestion_tutorial.ipynb) is the runnable version, with the same section
numbers. Sections 1 to 5 run with no API key and no account, and every number on this page comes
from them.

## 📑 Contents

- [What You'll Learn](#-what-youll-learn)
- [Run It](#-run-it)
- [The Tutorial](#-the-tutorial)
  - [1. A corpus and five stages](#1-a-corpus-and-five-stages)
  - [2. The index, in its naive form](#2-the-index-in-its-naive-form)
  - [3. Run it. It works.](#3-run-it-it-works)
  - [4. Now kill it, and count what the retry costs](#4-now-kill-it-and-count-what-the-retry-costs)
  - [5. Fix one: make the upsert idempotent](#5-fix-one-make-the-upsert-idempotent)
  - [6. Where the record of completed work should live](#6-where-the-record-of-completed-work-should-live)
  - [7. The same pipeline, as durable steps](#7-the-same-pipeline-as-durable-steps)
  - [8. Run it for real](#8-run-it-for-real)
  - [9. Fan-out, and why one bad file stops mattering](#9-fan-out-and-why-one-bad-file-stops-mattering)
  - [10. A human gate for the documents that should not be guessed](#10-a-human-gate-for-the-documents-that-should-not-be-guessed)
  - [11. Replay: fix the parser, re-run only what broke](#11-replay-fix-the-parser-re-run-only-what-broke)
  - [12. Query the finished index](#12-query-the-finished-index)
  - [13. When you do not need any of this](#13-when-you-do-not-need-any-of-this)
  - [What to take away](#what-to-take-away)
- [FAQ](#-faq)
- [Files](#-files)
- [Sponsor](#-sponsor)

## 🎯 What You'll Learn

- **What Inngest actually is**, from the events-functions-steps model up, in section 6. No prior
  knowledge of it assumed
- **What a failed run actually costs.** You run the naive pipeline, kill it at document 3,000 of
  5,000, retry it, and count the wasted embedding calls and the duplicate chunks yourself
- **Durable steps**: wrapping each stage in `step.run()` so a retry resumes at the document that
  failed instead of at document one
- **Idempotent upserts** keyed on document ID and chunk number, so re-ingesting a file updates in
  place rather than adding a second copy, and a corrected file leaves no stale chunks behind
- **Fan-out per document**, so one unparseable file fails on its own instead of taking the run down,
  and when `step.invoke` is the better tool than an event
- **Flow control**: throttling and per-tenant concurrency, so a historical backfill does not starve
  live ingestion
- **A human review gate** with `step.wait_for_event()` for documents that parse to nothing
- **When you do not need any of this**, which is a real answer for a lot of pipelines

## 🚀 Run It

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NirDiamant/agents-towards-production/blob/main/tutorials/durable-rag-ingestion-inngest/durable_rag_ingestion_tutorial.ipynb)

📓 Notebook: [durable_rag_ingestion_tutorial.ipynb](durable_rag_ingestion_tutorial.ipynb)

- **Python 3.10+**, then `pip install -r requirements.txt`
- **No API key.** Embeddings are a deterministic local stand-in so the numbers are reproducible and
  nobody has to pay to read a tutorial. Swapping in a real embedding model is one function.
- **Node.js**, only for sections 7 onward, to run `npx inngest-cli@latest dev`

Sections 1 to 5 run anywhere, Colab included. They are the part that shows the cost. Sections 7
onward run the real pipeline against the local Inngest dev server, which is a single command and
also free. Section 8 has the commands.

**Total Tutorial Time**: ~45 minutes
**Difficulty**: Intermediate (Python, basic RAG concepts, no prior Inngest knowledge assumed)

## 📖 The Tutorial

### 1. A corpus and five stages

Ingestion is always the same five stages: fetch, parse, chunk, embed, upsert.

We need a corpus big enough that a partial failure hurts. 5,000 documents is small for production
and more than enough to make the point.

Two notes on the fake parts. `embed()` is a deterministic stand-in for a paid embedding call, so
this tutorial is reproducible and costs nothing to read. Swapping in a real model is one function
body. The counters are the interesting part: they record how much billable work each run does.

```python
import hashlib, random

def make_corpus(n=5000, seed=7):
    rnd = random.Random(seed)
    topics = ["retrieval", "embeddings", "chunking", "reranking", "evaluation"]
    docs = []
    for i in range(n):
        t = rnd.choice(topics)
        body = " ".join(rnd.choice(
            ["latency","recall","index","vector","token","corpus","query","chunk"]
        ) for _ in range(60))
        docs.append({"id": f"doc-{i:05d}", "topic": t, "text": f"{t}. {body}"})
    return docs

docs = make_corpus()
print(f"{len(docs)} documents")
print(docs[0])
```

```python
class Counters:
    """Every unit of billable work this pipeline does."""
    def __init__(self): self.parsed = self.embedded = self.upserted = 0
    def __repr__(self):
        return f"parsed={self.parsed} embedded={self.embedded} upserted={self.upserted}"

def parse(doc, c):
    c.parsed += 1
    return doc["text"]

def chunk(text, size=200):
    return [text[i:i+size] for i in range(0, len(text), size)]

def embed(chunk_text, c):
    """Stand-in for a paid embedding call. Deterministic, so results are reproducible."""
    c.embedded += 1
    h = hashlib.sha256(chunk_text.encode()).digest()
    return [b / 255.0 for b in h[:16]]

def content_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]
```

### 2. The index, in its naive form

The default vector store setup appends. You hand it a chunk and a vector, it stores a row. It has
no opinion about whether it has seen that chunk before, because you never gave it a key that would
let it tell.

`append_only=True` is that behaviour. We turn it off in section 5 and watch what changes.

```python
class Index:
    def __init__(self, append_only=True):
        self.rows = []       # naive: every upsert appends
        self.by_key = {}     # idempotent: keyed on (doc_id, chunk_no)
        self.append_only = append_only

    def upsert(self, doc_id, chunk_no, text, vec, c):
        c.upserted += 1
        if self.append_only:
            self.rows.append((doc_id, chunk_no, text, vec))
        else:
            # No content hash in the key: a corrected chunk must overwrite the bad one, not sit beside it.
            self.by_key[(doc_id, chunk_no)] = (text, vec)

    def prune(self, doc_id, n_chunks):
        """Drop a document's chunks past its new end, so a shorter re-ingest leaves nothing stale."""
        if self.append_only: return 0
        stale = [k for k in self.by_key if k[0] == doc_id and k[1] >= n_chunks]
        for k in stale: del self.by_key[k]
        return len(stale)

    def size(self):
        return len(self.rows) if self.append_only else len(self.by_key)

    def duplicates(self):
        """Rows whose (doc, chunk, content) triple already appeared earlier in the index."""
        if not self.append_only: return 0
        seen, dupes = set(), 0
        for doc_id, chunk_no, text, _ in self.rows:
            k = (doc_id, chunk_no, content_hash(text))
            if k in seen: dupes += 1
            else: seen.add(k)
        return dupes
```

The naive pipeline is the loop almost everyone ships:

```python
class Boom(Exception):
    """Stands in for the embedding provider returning 429, or a PDF that parses to garbage."""

def ingest_naive(docs, index, c, fail_at=None):
    for n, doc in enumerate(docs):
        if fail_at is not None and n == fail_at:
            raise Boom(f"embedding provider returned 429 at document {n}")
        text = parse(doc, c)
        chunks = chunk(text)
        for i, ch in enumerate(chunks):
            index.upsert(doc["id"], i, ch, embed(ch, c), c)
        index.prune(doc["id"], len(chunks))
    return n + 1
```

### 3. Run it. It works.

On the happy path there is nothing wrong with this pipeline. That is exactly why it survives code
review and ends up in production.

```python
index, c0 = Index(), Counters()
done = ingest_naive(docs, index, c0)
print(f"ingested {done} documents")
print(f"work done: {c0}")
print(f"index rows: {index.size()}, duplicates: {index.duplicates()}")
```

All 5,000 documents go in as 14,571 index rows, with no duplicates.

### 4. Now kill it, and count what the retry costs

This is the section the whole tutorial exists for.

A real ingestion run dies partway. Rate limit, OOM, a deploy, a malformed file. The naive recovery
is to run the script again, because the script has no memory of what it finished.

Run one dies at document 3,000. Run two starts at document 0.

```python
index, c1 = Index(), Counters()
try:
    ingest_naive(docs, index, c1, fail_at=3000)
except Boom as e:
    print(f"run 1 died: {e}")

print(f"  run 1 completed work : {c1}")
print(f"  index rows so far    : {index.size()}")
```

```python
# The naive retry: same script, from the top, into the same index.
c2 = Counters()
ingest_naive(docs, index, c2)

print(f"run 2 completed work : {c2}")
print(f"index rows           : {index.size()}")
print(f"duplicate rows       : {index.duplicates()}")
print()
billed = c1.embedded + c2.embedded
print(f"embeddings billed across both runs : {billed}")
print(f"embeddings actually needed         : {c2.embedded}")
print(f"wasted                             : {c1.embedded}  ({billed/c2.embedded - 1:.0%} overspend)")
```

| | Count |
|---|---|
| Embeddings run one completed before dying | 8,735 |
| Embeddings run two did from scratch | 14,571 |
| Embeddings billed across both runs | 23,306 |
| **Embedding calls paid for twice** | **8,735 (60% overspend)** |
| **Duplicate rows now in the index** | **8,735** |

#### What just happened

Two numbers matter here, and neither of them is the failure itself.

**8,735 embedding calls were paid for twice.** Run one embedded 8,735 chunks before it died. Run
two embedded all 14,571 from scratch, because nothing recorded that the first 8,735 were already
done. On a real embedding provider that is a 60 percent overspend on this ingest, and it scales
with how late the failure lands. A run that dies at 95 percent wastes almost a full corpus.

**8,735 duplicate rows are now in your index**, competing in retrieval. This is the one that hurts
later, because it does not raise an error anywhere. Retrieval just gets quietly worse: the same
chunk comes back twice in the top-k, crowding out a different chunk that should have made it.

The failure was never the expensive part. The redo was.

### 5. Fix one: make the upsert idempotent

The duplicate problem is not really about failures. It is about the index having no way to
recognise a chunk it has already stored.

Key each entry on document ID and chunk number. Re-ingesting an unchanged document now overwrites
in place. Re-ingesting a corrected document overwrites its chunks, and `prune` drops any past its
new end, so nothing stale stays behind.

Keep the content hash out of the key. With the hash in it, a corrected chunk gets a new key and the
bad one stays in the index next to it, which is exactly the state you are trying to repair after a
parser bug.

This one is worth doing whether or not you adopt anything else in this tutorial.

```python
index2, d1 = Index(append_only=False), Counters()
try:
    ingest_naive(docs, index2, d1, fail_at=3000)
except Boom:
    pass

d2 = Counters()
ingest_naive(docs, index2, d2)

print(f"index entries  : {index2.size()}")
print(f"duplicate rows : {index2.duplicates()}")
print()
print(f"embeddings still billed twice: {d1.embedded}")
```

The index ends with 14,571 entries and zero duplicate rows. Duplicates are gone. The wasted
embedding calls are not: all 8,735 are still billed twice.

That is the limit of fixing this at the storage layer: the index can deduplicate what it is
handed, but by then you have already paid to parse and embed the document. To stop paying twice,
something has to remember which work finished, and it has to remember it across a process that
died.

### 6. Where the record of completed work should live

Three options, in the order most teams reach for them.

**Rerun the script.** No memory. Cheapest to write, and section 4 measured what it costs.

**A state table you maintain.** Write a row per document, check it before processing. This works,
and most production pipelines end up here. The gap is the window between writing the row and doing
the work: if the process dies in there, the row lies to you. Closing that honestly means two-phase
writes and a reconciliation job, which is a distributed systems problem you now own.

**Put the record in the execution runtime.** Each stage of the pipeline is a recorded step. The
runtime journals what completed, and a retry replays the journal rather than re-running the work.
Resumption stops being state you maintain and becomes a property of how the function executes.

[Inngest](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--durable-rag-ingestion-inngest--readme&click=inngest-home&target=https%3A%2F%2Fwww.inngest.com%2F%3Futm_source%3Ddiamantai%26utm_medium%3Dgithub%26utm_campaign%3Ddurable-rag-ingestion&text=Inngest) is the third option, and the rest of this tutorial builds on it.

#### What Inngest is, if you have not used it

Enough of the model to read the rest of this tutorial. Skip to section 7 if you already use it.

Inngest is a durable execution platform. The part that matters here is where the durability lives:
in your own codebase, as ordinary Python functions, rather than in a queue and a worker fleet you
operate. There is no broker to run and no idempotency layer of your own to keep in sync.

Three pieces, and that is the whole model.

**Events.** A named JSON payload, like `rag/document.received`. Your application sends them, or one
function sends them to trigger others.

**Functions.** An ordinary Python function, decorated so the platform knows what starts it and how
it should behave when things go wrong:

```python
@client.create_function(
    fn_id="ingest-document",
    trigger=inngest.TriggerEvent(event="rag/document.received"),
    retries=3,
)
def ingest_document(ctx: inngest.ContextSync) -> dict:
    ...
```

Your own app serves these over HTTP. With FastAPI that is one line,
`inngest.fast_api.serve(app, client, [ingest_document])`, which mounts `/api/inngest`.

**Steps.** Inside a function, `ctx.step.run(step_id, handler)` marks a unit of work worth
remembering. Each step is executed as a separate request into your app, and its return value is
persisted in Inngest's state store. On a later attempt the step's code does not run again: the SDK
looks the result up by step ID and injects it into the return value of `step.run`.

That last sentence is the entire tutorial. A completed `embed` step returns its vector from the
state store on a retry, so the embedding call inside it is billed once rather than once per
attempt. Section 4 measured what the alternative costs.

![What a retry replays and what it re-executes](assets/step-replay.svg)

Two consequences worth knowing before you write any of it. Anything non-deterministic or billable,
an API call, a database query, a paid embedding, belongs *inside* a step rather than between
steps, because only what is inside a step gets recorded. And step IDs are how results are matched
across attempts, which makes a step ID part of your compatibility surface: rename one and it
replays as new work. Section 13 comes back to that as a real cost rather than a footnote.

Retries, `throttle` and `concurrency` are arguments on the decorator, not infrastructure you stand
up. Section 7 uses all three.

None of this needs an account or an API key to try. `npx inngest-cli@latest dev` runs a local dev
server with a UI at `http://127.0.0.1:8288`, and `is_production=False` points the SDK at it.
Section 8 is the two commands.

### 7. The same pipeline, as durable steps

Below is the real thing. Two changes to notice.

Every stage is wrapped in `ctx.step.run(step_id, handler)`. When a function run is retried, Inngest
replays each completed step from its journal instead of executing it again. The embedding calls
inside a completed step are not re-billed.

Each document gets its own function run, triggered by its own event. A document that fails is one
failed run out of 5,000, not a dead pipeline.

This is the core of [`app.py`](app.py), which runs as is:

```python
import datetime
import inngest

client = inngest.Inngest(app_id="rag-ingestion", is_production=False)

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
    doc_id = ctx.event.data["doc_id"]
    doc = CORPUS[doc_id]

    text   = ctx.step.run("parse", lambda: parse(doc, COUNTERS))
    chunks = ctx.step.run("chunk", lambda: chunk(text))

    for i, ch in enumerate(chunks):
        # Each embed is its own step, so a failure at chunk 40
        # does not re-bill chunks 0 through 39.
        vec = ctx.step.run(f"embed-{i}", lambda ch=ch: embed(ch, COUNTERS))
        ctx.step.run(f"upsert-{i}",
                     lambda i=i, ch=ch, vec=vec: INDEX.upsert(doc_id, i, ch, vec, COUNTERS))

    # A corrected document can come back with fewer chunks. Drop the ones past its new end.
    ctx.step.run("prune", lambda: INDEX.prune(doc_id, len(chunks)))

    return {"doc_id": doc_id, "chunks": len(chunks), "index_size": INDEX.size()}
```

#### The two flow-control arguments

`throttle` caps how fast the function runs, across every document. That is what keeps a 5,000
document backfill inside your embedding provider's rate limit instead of collecting 429s.

`concurrency` with a `key` partitions that limit. Keyed on tenant, a customer re-indexing their
whole history gets 5 concurrent runs and everyone else still gets theirs. Without the key, one
backfill starves live ingestion.

Both are configuration on the function. Neither is a queue you operate.

### 8. Run it for real

No account, no keys. `is_production=False` points the SDK at the local dev server. From this
folder:

```bash
pip install -r requirements.txt

# terminal 1
uvicorn app:app --reload --port 8000

# terminal 2
npx inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest
```

Open http://127.0.0.1:8288 for the dev UI, then kick off the whole corpus:

```bash
curl -X POST http://127.0.0.1:8288/e/dev_key \
  -H "Content-Type: application/json" \
  -d '{"name": "rag/corpus.ingest", "data": {}}'
```

Watch the runs appear, and open one to see each step recorded individually. Progress comes
straight from the running app:

```bash
curl http://127.0.0.1:8000/stats
```

### 9. Fan-out, and why one bad file stops mattering

`ingest_corpus` does one thing: it lists the documents and sends one event per document. Each of
those events starts an independent run of `ingest_document`.

```python
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
```

The failure story changes completely. A PDF that makes the parser throw fails its own run and
retries on its own schedule. One that parses to nothing waits in the review queue from section 10.
The other 4,999 documents never notice.
Compare that to the naive loop, where the same file ends the run.

![One bad document, two failure stories](assets/fan-out.svg)

The `send_event` calls go out 500 at a time. Sending 5,000 events in one step makes one very large
payload, so batching keeps each step small.

**Why events here, and not `step.invoke`.** Inngest can also call one function from another and
hand back its return value, with
[`step.invoke`](https://www.inngest.com/docs/guides/invoking-functions-directly?guide=python):

```python
result = ctx.step.invoke(
    "ingest-one",
    function=ingest_document,
    data={"doc_id": doc_id, "tenant_id": tenant},
)
```

That is the better tool in two cases: the caller actually needs the child's result, or the work
wants its own retry and concurrency settings instead of the caller's. Neither applies to a 5,000
document backfill. `invoke` waits for the child to finish, and if the child fails the step fails
and raises a `NonRetriableError` in the calling run. Waiting and shared fate are exactly the two
couplings this section exists to remove: one unparseable PDF would be back to taking the corpus
down with it. Events buy 5,000 runs that succeed, fail and retry on their own.

### 10. A human gate for the documents that should not be guessed

Some documents should not go into the index on a best guess. A scanned contract that OCR'd badly,
a file whose parser returned three characters. In `ingest_document`, right after chunking:

```python
if not chunks:
    ctx.step.send_event(
        "flag-for-review",
        inngest.Event(name="rag/document.needs_review", data={"doc_id": doc_id}),
    )
    approval = ctx.step.wait_for_event(
        "await-approval",
        event="rag/document.approved",
        if_exp=f"async.data.doc_id == '{doc_id}'",
        timeout=datetime.timedelta(days=7),
    )
    if approval is None:
        return {"doc_id": doc_id, "status": "rejected-or-timed-out"}
```

`ctx.step.wait_for_event()` suspends the run, for up to seven days here, without holding a worker
open. The run is durable while it waits. When a reviewer approves the document, the run picks up
exactly where it stopped.

`if_exp` is what routes the approval to the one run waiting for that document.

`step.invoke` does not replace this one either, and it is worth being clear about why. It does
save you a send-and-wait pair when a run is waiting on *another Inngest function* and wants what
that function returns. Here the run is waiting on a person. The decision arrives as an event from
outside the system, on a timescale of days, and there is no child function whose return value
would carry it.

### 11. Replay: fix the parser, re-run only what broke

This is the payoff of running each document as its own function run.

A parser bug breaks 40 documents. In the naive pipeline you re-run the corpus. Here, the dev UI
shows you which runs failed and which step failed inside them. You fix the parser, deploy, and
[replay](https://www.inngest.com/docs/platform/replay) those runs. Only those 40 documents run
again. The other 4,960 are not touched.

Be precise about what a replay saves. A replay, like a
[rerun](https://www.inngest.com/docs/platform/manage/rerun-function-runs), starts a new run from the
original event, and completed steps from the old run are not reused. Here that is what you want:
`parse` is the first step, so the 40 documents are parsed, chunked and embedded again, and they have
to be, because their text changed. The saved step results pay off in two other places. Within a
run, a retry skips the steps that already completed, so a failure at chunk 40 does not re-bill
chunks 0 to 39. And for one run that failed late, Rerun from step keeps the results of every
earlier step, so a vector store write that timed out does not repeat the embeddings.

One case a replay will not catch: a bug that produces wrong text without raising. Those runs finish
as completed, so a replay of failed runs skips them, and the gate in section 10 only stops documents
that parse to nothing. Find them by their output, then send their events again. The index from
section 5 overwrites their chunks and prunes the rest.

Open any run in the dev UI at http://127.0.0.1:8288 to see the per-step timeline this is built on.

### 12. Query the finished index

The pipeline exists to serve retrieval, so here is the other end of it. Nothing exotic: cosine
similarity over the vectors the durable pipeline wrote.

```python
import math

def cosine(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x*x for x in a)), math.sqrt(sum(y*y for y in b))
    return dot / (na * nb + 1e-12)

def search(index, query, k=3):
    c = Counters()
    qv = embed(query, c)
    scored = [(cosine(qv, vec), doc_key, text)
              for doc_key, (text, vec) in index.by_key.items()]
    return sorted(scored, key=lambda r: -r[0])[:k]

for score, key, text in search(index2, "how do I measure recall"):
    print(f"{score:.3f}  {key[0]} chunk {key[1]}  {text[:60]}...")
```

### 13. When you do not need any of this

Worth saying plainly, because a tutorial that only sells you the tool is not much use.

If your corpus is a few hundred documents that reindex nightly, and a full rerun costs you a few
cents and four minutes, use the script. The idempotent upserts from section 5 are still worth it,
because duplicate chunks degrade retrieval quietly and the fix is ten lines. The durable runtime
is not.

Durable execution starts paying when at least one of these is true:

- A full re-run is expensive, in tokens or in hours
- Partial failure is the normal case rather than an incident, which is what large corpora and
  flaky third-party parsers produce
- You have multiple tenants and one of them re-indexing must not degrade the others
- Some documents genuinely need a human in the loop before they enter the index

It also is not free. You adopt a runtime, your functions get shaped around steps, and step IDs
become part of your compatibility surface: renaming a step changes what replays. That is a real
cost and you should weigh it against the state table in section 6.

The honest summary is that the second option and the third are both defensible. The first one, the
one almost everybody is actually running, is the one this tutorial is arguing against.

### What to take away

The retry is where an ingestion pipeline's design shows. Everyone builds the happy path carefully
and then leaves recovery to a rerun, and that rerun quietly costs a share of your embedding bill
and fills your index with duplicates that make retrieval worse without ever raising an error.

You measured both in section 4. 8,735 wasted embedding calls and 8,735 duplicate rows, from a
single failure at 60 percent through the corpus.

Fixing it has two halves. Key your upserts on document ID and chunk number so the index can recognise what it already
has. Then put the record of completed work somewhere that survives the process dying, so a retry
resumes instead of restarting.

## ❓ FAQ

**How do I resume a failed embedding job without re-embedding documents that already finished?**
Something has to record which work completed, in a place that survives the process dying. Either a
state table you maintain (and reconcile), or a durable execution runtime where each stage is a
recorded step. With Inngest, wrapping each embed call in `ctx.step.run()` means a retry of the run
returns the stored vector instead of calling the embedding provider again. See sections 6 and 7.

**How do I stop a RAG re-ingest from creating duplicate chunks?**
Make the upsert idempotent: key every chunk on document ID and chunk number, and keep the content
hash out of the key. Re-ingesting an unchanged document then overwrites in place, a corrected one
overwrites its old chunks, and a prune step drops any past its new end. This is independent of any
runtime. See section 5.

**What is durable execution, in one sentence?**
A runtime that journals each completed step of a function, so a retry replays finished steps from
the journal and only re-executes the step that failed.

**Does replaying a failed run reuse the steps that already succeeded?**
No. A replay, like a rerun, starts a new run from the original event and runs every step again.
After a parser fix that is what you want, because the text changed. Completed steps are reused in
two other places: a retry inside the same run, and Rerun from step, which keeps the result of every
step before the one you pick. See section 11.

**Should I fan out with events or `step.invoke`?**
Events, when each unit of work should succeed, fail and retry on its own, as in a corpus backfill.
`step.invoke`, when the caller needs the child's return value. See section 9.

**How do I keep a backfill from starving live ingestion?**
`throttle` to stay under your provider's rate limit, plus `concurrency` keyed on tenant so one
tenant's backfill cannot take every slot. See section 7.

## 📁 Files

| File | What it is |
|---|---|
| [durable_rag_ingestion_tutorial.ipynb](durable_rag_ingestion_tutorial.ipynb) | The full runnable tutorial |
| [pipeline.py](pipeline.py) | Corpus, instrumented stages, naive and idempotent index |
| [app.py](app.py) | The durable pipeline, served to the Inngest dev server |
| [test_reingest.py](test_reingest.py) | Checks that re-ingesting a corrected document leaves no stale chunks |
| [requirements.txt](requirements.txt) | `inngest`, `fastapi`, `uvicorn` |

## 🙏 Sponsor

This tutorial was sponsored by **[Inngest](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--durable-rag-ingestion-inngest--readme&click=inngest-home&target=https%3A%2F%2Fwww.inngest.com%2F%3Futm_source%3Ddiamantai%26utm_medium%3Dgithub%26utm_campaign%3Ddurable-rag-ingestion&text=Inngest)**, the
durable execution platform used throughout. The architecture, the tradeoffs and the section on when
not to use it are the author's own. All code runs, so you can check every claim in it.

[Inngest docs](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--durable-rag-ingestion-inngest--readme&click=inngest-docs&target=https%3A%2F%2Fwww.inngest.com%2Fdocs%3Futm_source%3Ddiamantai%26utm_medium%3Dgithub%26utm_campaign%3Ddurable-rag-ingestion&text=Inngest%20docs)
