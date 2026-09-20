"""Tests for search_engine.phrase_search"""

from search_engine.inverted_index import InvertedIndex
from search_engine.phrase_search import (
    intersect_postings,
    phrase_search,
    two_pointer_intersect,
)
from search_engine.tokenizer import tokenize


def test_two_pointer_intersect_basic():
    assert two_pointer_intersect(["doc1", "doc2", "doc3"], ["doc2", "doc3", "doc4"]) == [
        "doc2",
        "doc3",
    ]


def test_two_pointer_intersect_no_overlap():
    assert two_pointer_intersect(["doc1"], ["doc2"]) == []


def test_two_pointer_intersect_empty_input():
    assert two_pointer_intersect([], ["doc1"]) == []
    assert two_pointer_intersect(["doc1"], []) == []


def test_two_pointer_intersect_identical_lists():
    assert two_pointer_intersect(["doc1", "doc2"], ["doc1", "doc2"]) == ["doc1", "doc2"]


def _build_index() -> InvertedIndex:
    idx = InvertedIndex()
    idx.add_document("doc1", tokenize("notes on database normalization theory"))
    idx.add_document("doc2", tokenize("the database has normalization issues"))
    idx.add_document("doc3", tokenize("database normalization is a core sql concept"))
    idx.add_document("doc4", tokenize("no relevant terms here at all"))
    return idx


def test_intersect_postings_all_terms_present():
    idx = _build_index()
    result = intersect_postings(idx, ["database", "normalization"])
    assert set(result) == {"doc1", "doc2", "doc3"}


def test_intersect_postings_missing_term_returns_empty():
    idx = _build_index()
    assert intersect_postings(idx, ["database", "nonexistentword"]) == []


def test_phrase_search_finds_consecutive_match():
    idx = _build_index()
    matches = phrase_search(idx, ["database", "normalization"])
    assert set(matches) == {"doc1", "doc3"}  # doc2 has them non-adjacent


def test_phrase_search_excludes_non_adjacent():
    idx = _build_index()
    matches = phrase_search(idx, ["database", "normalization"])
    assert "doc2" not in matches


def test_phrase_search_three_word_phrase():
    idx = InvertedIndex()
    idx.add_document("doc1", tokenize("the quick brown fox jumps"))
    idx.add_document("doc2", tokenize("the quick red fox jumps"))

    matches = phrase_search(idx, tokenize("quick brown fox"))
    assert matches == ["doc1"]


def test_phrase_search_single_term_is_just_document_frequency():
    idx = _build_index()
    matches = phrase_search(idx, ["database"])
    assert set(matches) == {"doc1", "doc2", "doc3"}


def test_phrase_search_empty_phrase_returns_empty():
    idx = _build_index()
    assert phrase_search(idx, []) == []


def test_phrase_search_term_not_in_index_returns_empty():
    idx = _build_index()
    assert phrase_search(idx, ["database", "nonexistentword"]) == []


def test_phrase_search_repeated_phrase_in_same_document():
    idx = InvertedIndex()
    idx.add_document(
        "doc1", tokenize("database normalization matters. database normalization is key.")
    )
    matches = phrase_search(idx, ["database", "normalization"])
    assert matches == ["doc1"]


def test_phrase_search_reversed_order_does_not_match():
    idx = InvertedIndex()
    idx.add_document("doc1", tokenize("normalization database theory"))
    matches = phrase_search(idx, ["database", "normalization"])
    assert matches == []