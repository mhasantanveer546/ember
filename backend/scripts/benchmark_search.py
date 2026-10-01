"""
Ember Backend — End-to-end search benchmark (Phase 4.2)

Measures the REAL backend search path (search_service.search_workspace:
index lookup -> candidate gathering -> ranking -> Top-K -> DB fetch ->
snippet generation from stored files) at 1,000 and 10,000 documents, plus
the cost of a full index rebuild from Postgres + storage (Phase 4.1).

Run from the repo root:

    cd backend
    PYTHONPATH=..:. python scripts/benchmark_search.py [--sizes 1000 10000]

Uses an in-memory SQLite DB and a temp storage dir, so it needs no Neon
credentials and never touches real data.

ASSUMPTIONS (printed with the results too — numbers are only meaningful
alongside them):
  - Synthetic corpus: Zipf-distributed vocabulary (VOCAB_SIZE words), so
    a few terms are very common and most are rare, like real text.
  - WORDS_PER_DOC words per document, stored as .txt.
  - Single process, single thread, warm cache, local disk, SQLite (not
    Neon: a real Postgres round trip per result adds network latency,
    which this benchmark does NOT include).
  - Top-K limit = 10 (the API default).
"""

import argparse
import os
import platform
import random
import statistics
import sys
import tempfile
import time
import uuid

_tmp_storage = tempfile.mkdtemp(prefix="ember-bench-storage-")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "benchmark-only-secret-not-for-production-use")
os.environ["LOCAL_STORAGE_PATH"] = _tmp_storage

from app.db.session import Base, SessionLocal, engine  # noqa: E402
from app import models as _models  # noqa: E402,F401
from app.models import Document, DocumentStatus, User, Workspace  # noqa: E402
from app.services.search.index_registry import get_or_create_workspace_index  # noqa: E402
from app.services.search.rebuild_service import rebuild_and_swap  # noqa: E402
from app.services.search.search_service import search_workspace  # noqa: E402
from app.services.storage.local_storage import get_storage_service  # noqa: E402

VOCAB_SIZE = 5000
WORDS_PER_DOC = 300
QUERIES_PER_SHAPE = 60
TARGET_P95_MS = 500.0


def _build_vocab() -> list[str]:
    return [f"w{i:04d}x" for i in range(VOCAB_SIZE)]


def _zipf_weights() -> list[float]:
    return [1.0 / (rank + 1) for rank in range(VOCAB_SIZE)]


def _populate(db, doc_count: int, rng: random.Random) -> uuid.UUID:
    vocab, weights = _build_vocab(), _zipf_weights()
    user = User(email=f"bench{doc_count}@example.com", hashed_password="x")
    db.add(user)
    db.flush()
    workspace = Workspace(owner_id=user.id, name=f"bench-{doc_count}")
    db.add(workspace)
    db.flush()

    storage = get_storage_service()
    for i in range(doc_count):
        doc_id = uuid.uuid4()
        text = " ".join(rng.choices(vocab, weights=weights, k=WORDS_PER_DOC))
        key = f"workspaces/{workspace.id}/documents/{doc_id}/original.txt"
        storage.save(key, text.encode())
        db.add(
            Document(
                id=doc_id, workspace_id=workspace.id, owner_id=user.id,
                filename=f"doc{i}.txt", storage_key=key,
                content_hash=f"{doc_id.hex}{'0' * 32}", mime_type="text/plain",
                file_size_bytes=len(text), status=DocumentStatus.READY,
            )
        )
    db.commit()
    return workspace.id


def _make_queries(rng: random.Random) -> dict[str, list[str]]:
    vocab = _build_vocab()
    common, mid, rare = vocab[:20], vocab[200:1000], vocab[2500:]
    pick = lambda pool, n: " ".join(rng.sample(pool, n))
    return {
        "1 rare term": [pick(rare, 1) for _ in range(QUERIES_PER_SHAPE)],
        "1 common term (worst case: huge posting list)": [pick(common, 1) for _ in range(QUERIES_PER_SHAPE)],
        "2 terms (mid)": [pick(mid, 2) for _ in range(QUERIES_PER_SHAPE)],
        "3 terms (common+mid)": [f"{pick(common, 1)} {pick(mid, 2)}" for _ in range(QUERIES_PER_SHAPE)],
        "exact phrase (2 words)": [f'"{pick(common, 2)}"' for _ in range(QUERIES_PER_SHAPE)],
    }


def _percentile(sorted_ms: list[float], pct: float) -> float:
    return sorted_ms[min(len(sorted_ms) - 1, int(len(sorted_ms) * pct))]


def run(sizes: list[int]) -> bool:
    Base.metadata.create_all(engine)
    all_ok = True
    print(f"Python {platform.python_version()} | {platform.platform()} | "
          f"{os.cpu_count()} CPUs | vocab={VOCAB_SIZE} words/doc={WORDS_PER_DOC} top-k=10\n")

    for size in sizes:
        rng = random.Random(42)
        db = SessionLocal()
        try:
            t0 = time.perf_counter()
            workspace_id = _populate(db, size, rng)
            print(f"=== {size:,} documents (corpus generated in {time.perf_counter() - t0:.1f}s) ===")

            t0 = time.perf_counter()
            result = rebuild_and_swap(db, workspace_id)
            rebuild_s = time.perf_counter() - t0
            print(f"Full rebuild: {rebuild_s:.2f}s  ({size / rebuild_s:,.0f} docs/s)  "
                  f"vocab={result.vocabulary_size:,}")

            index = get_or_create_workspace_index(workspace_id)
            for shape, queries in _make_queries(rng).items():
                search_workspace(db, index, workspace_id, queries[0], 10)  # warm-up
                timings = []
                for q in queries:
                    t = time.perf_counter()
                    search_workspace(db, index, workspace_id, q, 10)
                    timings.append((time.perf_counter() - t) * 1000)
                timings.sort()
                p50, p95 = statistics.median(timings), _percentile(timings, 0.95)
                ok = p95 < TARGET_P95_MS
                all_ok &= ok
                print(f"  {shape:<48} P50 {p50:7.1f} ms   P95 {p95:7.1f} ms   {'OK' if ok else 'OVER TARGET'}")
            print()
        finally:
            db.close()
    print(f"Target: P95 < {TARGET_P95_MS:.0f} ms  ->  {'ALL WITHIN TARGET' if all_ok else 'SOME SHAPES OVER TARGET'}")
    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=int, nargs="+", default=[1000, 10000])
    sys.exit(0 if run(parser.parse_args().sizes) else 1)
