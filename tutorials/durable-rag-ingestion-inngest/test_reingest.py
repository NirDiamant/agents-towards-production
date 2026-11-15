"""Re-ingestion tests for the idempotent index.

Run with `python -m pytest test_reingest.py` or plain `python test_reingest.py`.

The case that matters: a parser bug wrote bad text for a document, the parser is fixed, and the
document is ingested again. The index must end up holding only the corrected chunks.
"""
from pipeline import Counters, Index, chunk, ingest_naive

BAD = {"id": "doc-00001", "topic": "retrieval", "text": "garbled " * 200}   # what the buggy parser produced
GOOD = {"id": "doc-00001", "topic": "retrieval", "text": "retrieval. recall index vector " * 30}
OTHER = {"id": "doc-00002", "topic": "chunking", "text": "chunking. token chunk corpus " * 30}


def chunks_for(index, doc_id):
    return sorted((k[1], text) for k, (text, _) in index.by_key.items() if k[0] == doc_id)


def test_corrected_document_leaves_no_stale_chunks():
    idx, c = Index(append_only=False), Counters()
    ingest_naive([BAD, OTHER], idx, c)
    ingest_naive([GOOD], idx, c)                       # re-ingest after the parser fix
    expected = list(enumerate(chunk(GOOD["text"])))
    assert chunks_for(idx, GOOD["id"]) == expected      # only the corrected chunks remain
    assert chunks_for(idx, OTHER["id"]) == list(enumerate(chunk(OTHER["text"])))


def test_shorter_corrected_document_drops_its_old_tail():
    idx, c = Index(append_only=False), Counters()
    ingest_naive([BAD], idx, c)
    assert len(chunks_for(idx, BAD["id"])) > len(chunk(GOOD["text"]))   # the bad text had more chunks
    ingest_naive([GOOD], idx, c)
    assert len(chunks_for(idx, GOOD["id"])) == len(chunk(GOOD["text"]))


def test_document_that_now_parses_to_nothing_is_removed():
    idx, c = Index(append_only=False), Counters()
    ingest_naive([BAD, OTHER], idx, c)
    ingest_naive([{"id": BAD["id"], "topic": "retrieval", "text": ""}], idx, c)
    assert chunks_for(idx, BAD["id"]) == []
    assert chunks_for(idx, OTHER["id"])                 # other documents are untouched


def test_unchanged_reingest_is_still_idempotent():
    idx, c = Index(append_only=False), Counters()
    ingest_naive([GOOD, OTHER], idx, c)
    size = idx.size()
    ingest_naive([GOOD, OTHER], idx, c)
    assert idx.size() == size


def test_naive_index_still_counts_duplicates():
    idx, c = Index(append_only=True), Counters()
    ingest_naive([GOOD], idx, c)
    ingest_naive([GOOD], idx, c)
    assert idx.duplicates() == len(chunk(GOOD["text"]))


if __name__ == "__main__":
    import sys
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError:
                failed += 1
                print(f"FAIL {name}")
    sys.exit(1 if failed else 0)
