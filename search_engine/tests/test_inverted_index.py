"""Tests for search_engine.inverted_index"""

from search_engine.inverted_index import InvertedIndex
from search_engine.tokenizer import tokenize


def test_add_single_document():
    idx = InvertedIndex()
    idx.add_document("doc1", ["fox", "jumps", "fox"])

    postings = idx.get_postings("fox")
    assert postings is not None
    posting = postings.get("doc1")
    assert posting.positions == [0, 2]
    assert posting.term_frequency == 2


def test_term_not_indexed_returns_none():
    idx = InvertedIndex()
    idx.add_document("doc1", ["fox", "jumps"])
    assert idx.get_postings("sleeps") is None


def test_multiple_documents_same_term():
    idx = InvertedIndex()
    idx.add_document("doc1", ["fox", "jumps"])
    idx.add_document("doc2", ["fox", "sleeps"])

    postings = idx.get_postings("fox")
    assert postings.document_frequency() == 2
    assert set(postings.document_ids()) == {"doc1", "doc2"}


def test_document_frequency():
    idx = InvertedIndex()
    idx.add_document("doc1", ["fox", "jumps"])
    idx.add_document("doc2", ["fox", "sleeps"])
    idx.add_document("doc3", ["cat", "sleeps"])

    assert idx.document_frequency("fox") == 2
    assert idx.document_frequency("sleeps") == 2
    assert idx.document_frequency("jumps") == 1
    assert idx.document_frequency("nonexistent") == 0


def test_document_length():
    idx = InvertedIndex()
    idx.add_document("doc1", ["fox", "jumps", "over", "fence"])
    assert idx.document_length("doc1") == 4
    assert idx.document_length("unknown_doc") == 0


def test_vocabulary_and_document_count():
    idx = InvertedIndex()
    idx.add_document("doc1", ["fox", "jumps"])
    idx.add_document("doc2", ["fox", "sleeps"])

    assert idx.vocabulary_size() == 3  # fox, jumps, sleeps
    assert idx.document_count() == 2


def test_remove_document():
    idx = InvertedIndex()
    idx.add_document("doc1", ["fox", "jumps"])
    idx.add_document("doc2", ["fox", "sleeps"])

    idx.remove_document("doc1")

    assert idx.document_length("doc1") == 0
    assert idx.document_frequency("fox") == 1
    assert idx.get_postings("jumps").document_frequency() == 0
    assert idx.document_count() == 1


def test_contains():
    idx = InvertedIndex()
    idx.add_document("doc1", ["fox", "jumps"])
    assert "fox" in idx
    assert "sleeps" not in idx


def test_positions_preserved_for_phrase_search_groundwork():
    idx = InvertedIndex()
    idx.add_document("doc1", ["the", "quick", "brown", "fox"])

    assert idx.get_postings("the").get("doc1").positions == [0]
    assert idx.get_postings("quick").get("doc1").positions == [1]
    assert idx.get_postings("fox").get("doc1").positions == [3]


def test_integration_with_real_tokenizer():
    idx = InvertedIndex()
    idx.add_document("doc1", tokenize("Congestion control in TCP networking"))
    idx.add_document("doc2", tokenize("Database normalization and indexing"))

    assert idx.document_frequency("congestion") == 1
    assert idx.document_frequency("networking") == 1
    assert "database" in idx
    assert idx.get_postings("database").get("doc2") is not None