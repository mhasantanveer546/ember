"""Tests for search_engine.top_k"""

import random

from search_engine.inverted_index import InvertedIndex
from search_engine.top_k import top_k_by_score, top_k_search
from search_engine.tokenizer import tokenize


def test_top_k_basic_selection():
    items = [("a", 5.0), ("b", 9.0), ("c", 1.0), ("d", 7.0), ("e", 3.0)]
    result = top_k_by_score(items, k=3)
    assert result == [("b", 9.0), ("d", 7.0), ("a", 5.0)]


def test_top_k_returns_descending_order():
    items = [("a", 1.0), ("b", 5.0), ("c", 3.0)]
    result = top_k_by_score(items, k=3)
    scores = [score for _, score in result]
    assert scores == sorted(scores, reverse=True)


def test_top_k_k_larger_than_items_returns_all():
    items = [("a", 1.0), ("b", 2.0)]
    result = top_k_by_score(items, k=10)
    assert len(result) == 2
    assert result[0] == ("b", 2.0)


def test_top_k_zero_returns_empty():
    items = [("a", 1.0), ("b", 2.0)]
    assert top_k_by_score(items, k=0) == []


def test_top_k_negative_returns_empty():
    items = [("a", 1.0)]
    assert top_k_by_score(items, k=-5) == []


def test_top_k_empty_items_returns_empty():
    assert top_k_by_score([], k=5) == []


def test_top_k_handles_tied_scores_without_crashing():
    items = [("a", 5.0), ("b", 5.0), ("c", 5.0), ("d", 5.0)]
    result = top_k_by_score(items, k=2)
    assert len(result) == 2
    assert all(score == 5.0 for _, score in result)


def test_top_k_matches_naive_full_sort_on_random_data():
    # Correctness check: the heap-based approach must select exactly the
    # same top-k set (by score) as a naive full sort, on non-trivial data.
    random.seed(42)
    items = [(f"doc{i}", random.uniform(0, 100)) for i in range(500)]

    naive_top_k = sorted(items, key=lambda pair: pair[1], reverse=True)[:15]
    heap_top_k = top_k_by_score(items, k=15)

    naive_scores = sorted(score for _, score in naive_top_k)
    heap_scores = sorted(score for _, score in heap_top_k)
    assert naive_scores == heap_scores


def test_top_k_single_item():
    assert top_k_by_score([("only", 42.0)], k=1) == [("only", 42.0)]


def _build_index() -> InvertedIndex:
    idx = InvertedIndex()
    idx.add_document("doc1", tokenize("database normalization notes"))
    idx.add_document("doc2", tokenize("database theory and normalization basics"))
    idx.add_document("doc3", tokenize("database only, no other term"))
    idx.add_document("doc4", tokenize("completely unrelated cooking content"))
    return idx


def test_top_k_search_integration():
    idx = _build_index()
    query = tokenize("database normalization")
    candidates = ["doc1", "doc2", "doc3", "doc4"]

    results = top_k_search(idx, query, candidates, k=2)

    assert len(results) == 2
    result_ids = [doc_id for doc_id, _ in results]
    # doc1 (exact adjacent phrase) and doc2 (both terms present) should
    # outrank doc3 (only one term) and doc4 (no terms at all).
    assert "doc1" in result_ids
    assert "doc4" not in result_ids


def test_top_k_search_respects_k():
    idx = _build_index()
    query = tokenize("database")
    candidates = ["doc1", "doc2", "doc3", "doc4"]

    results = top_k_search(idx, query, candidates, k=1)
    assert len(results) == 1


def test_top_k_search_with_title_boost():
    idx = _build_index()
    query = tokenize("database normalization")

    results = top_k_search(
        idx,
        query,
        ["doc2", "doc3"],
        k=2,
        title_tokens_map={"doc3": tokenize("Database Normalization Guide")},
    )
    # doc3's title boost should let it outrank doc2 despite doc2 having
    # both terms in the body and doc3 only having "database".
    assert results[0][0] == "doc3"