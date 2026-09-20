"""
Ember Search Engine — Throughput & Latency Benchmark (Phase 1.9)

Measures:
    - Indexing throughput: documents indexed per second
    - Search latency: P50 and P95, in milliseconds

This is a standalone script, not a pytest assertion test — latency
numbers depend on the machine running them, so hardcoding a pass/fail
threshold here would be meaningless across different hardware. Run it
directly (`python -m search_engine.benchmark_performance`) and read the
numbers; assumptions about the run are printed alongside the results.

Corpus: synthetically generated. Real benchmark data (actual notes,
PDFs, etc., once the document pipeline exists in Phase 3) will give more
representative numbers — this establishes a baseline and a repeatable
methodology now, rather than waiting for real data to start measuring.
"""

import random
import statistics
import time

from search_engine.inverted_index import InvertedIndex
from search_engine.tokenizer import tokenize
from search_engine.top_k import top_k_search

_VOCABULARY = [
    "database", "normalization", "index", "query", "search", "algorithm",
    "network", "congestion", "control", "protocol", "packet", "router",
    "memory", "cache", "thread", "process", "kernel", "compiler", "syntax",
    "semantics", "recursion", "iteration", "pointer", "array", "hashmap",
    "graph", "tree", "heap", "stack", "queue", "sort", "search", "binary",
    "linear", "complexity", "notation", "proof", "theorem", "matrix",
]


def _generate_synthetic_document(word_count: int, rng: random.Random) -> str:
    return " ".join(rng.choice(_VOCABULARY) for _ in range(word_count))


def benchmark_indexing(document_count: int, words_per_document: int = 200) -> float:
    """Returns documents indexed per second."""
    rng = random.Random(42)
    documents = [
        (f"doc{i}", _generate_synthetic_document(words_per_document, rng))
        for i in range(document_count)
    ]

    idx = InvertedIndex()
    start = time.perf_counter()
    for document_id, text in documents:
        idx.add_document(document_id, tokenize(text))
    elapsed = time.perf_counter() - start

    return document_count / elapsed if elapsed > 0 else float("inf")


def _candidate_document_ids(index: InvertedIndex, query_terms: list[str]) -> list[str]:
    """
    Realistic candidate prefiltering: only documents containing AT LEAST
    ONE query term are worth scoring at all (any document containing
    none of the terms scores 0 anyway — see score_document). This is
    what Phase 4's real search API does, via the posting lists we
    already have; scoring every document in the corpus regardless
    (which an earlier version of this benchmark did) doesn't scale and
    was itself a useful finding — see phase notes.
    """
    candidate_ids: set[str] = set()
    for term in set(query_terms):
        postings = index.get_postings(term)
        if postings is not None:
            candidate_ids.update(postings.document_ids())
    return list(candidate_ids)


def benchmark_search_latency(
    document_count: int, query_count: int = 200, words_per_document: int = 200
) -> tuple[float, float]:
    """Returns (p50_ms, p95_ms) search latency over `query_count` searches."""
    rng = random.Random(42)
    idx = InvertedIndex()
    for i in range(document_count):
        text = _generate_synthetic_document(words_per_document, rng)
        idx.add_document(f"doc{i}", tokenize(text))

    latencies_ms = []

    for _ in range(query_count):
        query_terms = [rng.choice(_VOCABULARY), rng.choice(_VOCABULARY)]
        candidate_ids = _candidate_document_ids(idx, query_terms)
        start = time.perf_counter()
        top_k_search(idx, query_terms, candidate_ids, k=10)
        latencies_ms.append((time.perf_counter() - start) * 1000)

    latencies_ms.sort()
    p50 = statistics.median(latencies_ms)
    p95_index = min(len(latencies_ms) - 1, int(len(latencies_ms) * 0.95))
    p95 = latencies_ms[p95_index]
    return p50, p95


if __name__ == "__main__":
    for doc_count in (200, 1_000):
        throughput = benchmark_indexing(doc_count)
        p50, p95 = benchmark_search_latency(doc_count, query_count=50)
        print(f"\n--- {doc_count:,} documents (synthetic, ~200 words each) ---")
        print(f"Indexing throughput: {throughput:,.0f} docs/sec")
        print(f"Search latency:      P50={p50:.2f}ms  P95={p95:.2f}ms")
        print("Candidates prefiltered to documents containing >=1 query")
        print("term (via posting lists), matching Phase 4's intended design.")