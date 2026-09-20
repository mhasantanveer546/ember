"""
Pytest wrapper around benchmark_precision_recall.py, so precision/recall
on the hand-labeled corpus is checked automatically on every test run,
not just when manually running the benchmark script.
"""

from search_engine.benchmark_precision_recall import run_benchmark


def test_benchmark_achieves_perfect_precision_and_recall_on_labeled_corpus():
    # This is a small, deliberately unambiguous corpus (see
    # benchmark_precision_recall.py) — perfect scores here are a sanity
    # check on ranking correctness, not a claim about real-world search
    # quality, which needs real usage data to evaluate properly.
    results = run_benchmark()

    for query, metrics in results.items():
        assert metrics["precision_at_k"] == 1.0, f"precision regression on {query!r}"
        assert metrics["recall"] == 1.0, f"recall regression on {query!r}"


def test_congestion_control_ranks_true_matches_above_vocabulary_near_miss():
    # doc5 ("traffic congestion in cities") legitimately shares the word
    # "congestion" with the query, so a keyword search engine correctly
    # still retrieves it with a nonzero score — that's expected, not a
    # bug. What matters for precision is that it ranks BELOW the true
    # topical matches (doc1, doc2), which both contain "congestion"
    # *and* "control". This is exactly what precision@k above already
    # measures; this test makes the ranking-order expectation explicit.
    from search_engine.benchmark_precision_recall import (
        _build_benchmark_index,
        _CORPUS,
    )
    from search_engine.tokenizer import tokenize
    from search_engine.top_k import top_k_search

    idx = _build_benchmark_index()
    all_doc_ids = [doc_id for doc_id, _ in _CORPUS]
    results = top_k_search(idx, tokenize("congestion control"), all_doc_ids, k=len(all_doc_ids))
    ranked_ids = [doc_id for doc_id, score in results if score > 0]

    doc5_rank = ranked_ids.index("doc5")
    doc1_rank = ranked_ids.index("doc1")
    doc2_rank = ranked_ids.index("doc2")

    assert doc1_rank < doc5_rank
    assert doc2_rank < doc5_rank