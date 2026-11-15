"""Core logic for the durable RAG ingestion tutorial. Tested standalone first."""
import hashlib, random

# ---------- corpus ----------
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

# ---------- instrumented stages ----------
class Counters:
    def __init__(self): self.parsed = self.embedded = self.upserted = 0
    def __repr__(self):
        return f"parsed={self.parsed} embedded={self.embedded} upserted={self.upserted}"

def parse(doc, c):
    c.parsed += 1
    return doc["text"]

def chunk(text, size=200):
    return [text[i:i+size] for i in range(0, len(text), size)]

def embed(chunk_text, c):
    """Stand-in for a paid embedding call. Deterministic, so the tutorial is reproducible."""
    c.embedded += 1
    h = hashlib.sha256(chunk_text.encode()).digest()
    return [b / 255.0 for b in h[:16]]

def content_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]

# ---------- the index ----------
class Index:
    """append_only=True is the naive version: every upsert adds a row."""
    def __init__(self, append_only=True):
        self.rows = []          # naive
        self.by_key = {}        # idempotent: keyed on (doc_id, chunk_no)
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
        if not self.append_only: return 0
        seen, dupes = set(), 0
        for doc_id, chunk_no, text, _ in self.rows:
            k = (doc_id, chunk_no, content_hash(text))
            if k in seen: dupes += 1
            else: seen.add(k)
        return dupes

# ---------- the naive pipeline ----------
class Boom(Exception): pass

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

if __name__ == "__main__":
    docs = make_corpus(5000)
    print(f"corpus: {len(docs)} documents")

    # --- run 1: dies at 3000 ---
    idx, c1 = Index(), Counters()
    try:
        ingest_naive(docs, idx, c1, fail_at=3000)
    except Boom as e:
        print(f"\nrun 1 failed: {e}")
    print(f"  run 1 work done : {c1}")
    print(f"  index rows      : {idx.size()}")

    # --- run 2: the naive retry, from the top ---
    c2 = Counters()
    ingest_naive(docs, idx, c2, fail_at=None)
    print(f"\nrun 2 (naive retry from doc 0):")
    print(f"  run 2 work done : {c2}")
    print(f"  index rows      : {idx.size()}")
    print(f"  duplicate rows  : {idx.duplicates()}")
    print(f"\n  WASTED re-embeds (work run 1 already paid for): {c1.embedded}")
    total = c1.embedded + c2.embedded
    print(f"  embeddings billed across both runs: {total}")
    print(f"  embeddings actually needed        : {c2.embedded}")
    print(f"  overspend: {total/c2.embedded - 1:.0%}")

    # --- the idempotent index, same two runs ---
    idx2, d1 = Index(append_only=False), Counters()
    try: ingest_naive(docs, idx2, d1, fail_at=3000)
    except Boom: pass
    d2 = Counters(); ingest_naive(docs, idx2, d2)
    print(f"\nwith idempotent upserts, same two runs:")
    print(f"  index entries   : {idx2.size()}")
    print(f"  duplicate rows  : 0 by construction")
