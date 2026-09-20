"""Tests for search_engine.ranking (TF-IDF portion, Phase 1.6)"""

import math

from search_engine.inverted_index import InvertedIndex
from search_engine.ranking import (
    inverse_document_frequency,
    log_term_frequency,
    normalized_term_frequency,
    term_frequency,
    tf_idf,
)


def _build_index() -> InvertedIndex:
    idx = InvertedIndex()
    idx.add_document("doc1", ["database", "database", "database", "notes"])
    idx.add_document("doc2", ["database", "theory"])
    idx.add_document("doc3", ["cooking", "recipes", "notes"])
    return idx


def test_term_frequency_raw_count():
    idx = _build_index()
    assert term_frequency(idx, "database", "doc1") == 3
    assert term_frequency(idx, "database", "doc2") == 1


def test_term_frequency_absent_term():
    idx = _build_index()
    assert term_frequency(idx, "nonexistent", "doc1") == 0


def test_term_frequency_absent_document():
    idx = _build_index()
    assert term_frequency(idx, "database", "unknown_doc") == 0


def test_normalized_term_frequency():
    idx = _build_index()
    # doc1 has 4 tokens total, "database" occurs 3 times
    assert normalized_term_frequency(idx, "database", "doc1") == 3 / 4


def test_normalized_term_frequency_zero_length_document():
    idx = InvertedIndex()  # no documents added at all
    assert normalized_term_frequency(idx, "database", "doc1") == 0.0


def test_log_term_frequency_matches_formula():
    idx = _build_index()
    expected = 1.0 + math.log(3)
    assert log_term_frequency(idx, "database", "doc1") == expected


def test_log_term_frequency_zero_when_absent():
    idx = _build_index()
    assert log_term_frequency(idx, "nonexistent", "doc1") == 0.0


def test_idf_rarer_term_has_higher_idf():
    idx = _build_index()
    # "database" appears in 2/3 docs, "cooking" in 1/3 docs -> cooking rarer
    idf_database = inverse_document_frequency(idx, "database")
    idf_cooking = inverse_document_frequency(idx, "cooking")
    assert idf_cooking > idf_database


def test_idf_term_in_every_document_is_zero():
    idx = InvertedIndex()
    idx.add_document("doc1", ["shared"])
    idx.add_document("doc2", ["shared"])
    assert inverse_document_frequency(idx, "shared") == 0.0


def test_idf_matches_formula():
    idx = _build_index()
    # "database": df=2, N=3 -> log(3/2)
    expected = math.log(3 / 2)
    assert inverse_document_frequency(idx, "database") == expected


def test_idf_unindexed_term_returns_zero():
    idx = _build_index()
    assert inverse_document_frequency(idx, "nonexistent") == 0.0


def test_idf_empty_corpus_returns_zero():
    idx = InvertedIndex()
    assert inverse_document_frequency(idx, "anything") == 0.0


def test_tf_idf_zero_when_term_absent_from_document():
    idx = _build_index()
    assert tf_idf(idx, "cooking", "doc1") == 0.0


def test_tf_idf_default_uses_log_variant():
    idx = _build_index()
    expected_tf = log_term_frequency(idx, "database", "doc1")
    expected_idf = inverse_document_frequency(idx, "database")
    assert tf_idf(idx, "database", "doc1") == expected_tf * expected_idf


def test_tf_idf_raw_variant():
    idx = _build_index()
    expected = term_frequency(idx, "database", "doc1") * inverse_document_frequency(
        idx, "database"
    )
    assert tf_idf(idx, "database", "doc1", tf_variant="raw") == expected


def test_tf_idf_normalized_variant():
    idx = _build_index()
    expected = normalized_term_frequency(
        idx, "database", "doc1"
    ) * inverse_document_frequency(idx, "database")
    assert tf_idf(idx, "database", "doc1", tf_variant="normalized") == expected


def test_tf_idf_invalid_variant_raises():
    idx = _build_index()
    try:
        tf_idf(idx, "database", "doc1", tf_variant="bogus")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_tf_idf_higher_for_more_distinctive_term_in_same_document():
    idx = InvertedIndex()
    idx.add_document("doc1", ["database", "database", "unique_term"])
    idx.add_document("doc2", ["database", "other"])
    idx.add_document("doc3", ["database", "other"])

    # "database" is common (df=3/3, idf=0); "unique_term" appears only in doc1
    score_database = tf_idf(idx, "database", "doc1")
    score_unique = tf_idf(idx, "unique_term", "doc1")
    assert score_unique > score_database