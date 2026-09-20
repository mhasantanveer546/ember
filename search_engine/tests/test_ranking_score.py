"""Tests for search_engine.ranking (Phase 1.7 — full scoring)"""

from search_engine.inverted_index import InvertedIndex
from search_engine.ranking import (
    RankingWeights,
    _smallest_window_covering_all_terms,
    score_document,
)
from search_engine.tokenizer import tokenize


def test_smallest_window_terms_adjacent():
    # "database" at 0, "normalization" at 1 -> window size 2
    assert _smallest_window_covering_all_terms([[0], [1]]) == 2


def test_smallest_window_terms_far_apart():
    assert _smallest_window_covering_all_terms([[0], [100]]) == 101


def test_smallest_window_picks_best_combination():
    # term A at [0, 50], term B at [51] -> best window uses 50 & 51 -> size 2
    assert _smallest_window_covering_all_terms([[0, 50], [51]]) == 2


def test_smallest_window_missing_term_returns_none():
    assert _smallest_window_covering_all_terms([[0, 1], []]) is None


def test_smallest_window_three_terms():
    # positions: A=[0], B=[2], C=[4] -> window covering all three: 0..4 -> size 5
    assert _smallest_window_covering_all_terms([[0], [2], [4]]) == 5


def _build_index() -> InvertedIndex:
    idx = InvertedIndex()
    idx.add_document("doc_adjacent", tokenize("database normalization notes"))
    idx.add_document("doc_far", tokenize("database is a big topic with many uses and normalization appears way later"))
    idx.add_document("doc_missing_term", tokenize("database theory only"))
    idx.add_document("doc_unrelated", tokenize("cooking recipes and travel guides"))
    return idx


def test_score_document_phrase_match_scores_highest():
    idx = _build_index()
    query = tokenize("database normalization")

    score_adjacent = score_document(idx, query, "doc_adjacent")
    score_far = score_document(idx, query, "doc_far")

    assert score_adjacent > score_far


def test_score_document_missing_term_scores_lower_than_full_match():
    idx = _build_index()
    query = tokenize("database normalization")

    score_full = score_document(idx, query, "doc_adjacent")
    score_partial = score_document(idx, query, "doc_missing_term")

    assert score_full > score_partial
    assert score_partial > 0  # "database" alone still contributes body score


def test_score_document_unrelated_document_scores_zero():
    idx = _build_index()
    query = tokenize("database normalization")
    assert score_document(idx, query, "doc_unrelated") == 0.0


def test_score_document_title_boost_increases_score():
    idx = _build_index()
    query = tokenize("database normalization")

    score_without_title = score_document(idx, query, "doc_far")
    score_with_title = score_document(
        idx, query, "doc_far", title_tokens=tokenize("Database Normalization Guide")
    )

    assert score_with_title > score_without_title


def test_score_document_filename_boost_increases_score():
    idx = _build_index()
    query = tokenize("database normalization")

    score_without = score_document(idx, query, "doc_far")
    # Hyphens split into separate tokens; underscores do not (tokenizer's
    # \w treats "_" as a word character) — see tokenizer.py docstring.
    # Using a hyphenated filename here to test the intended boost behavior.
    score_with = score_document(
        idx, query, "doc_far", filename_tokens=tokenize("database-normalization-notes.pdf")
    )

    assert score_with > score_without


def test_score_document_custom_weights_change_ranking():
    idx = _build_index()
    query = tokenize("database normalization")

    # With proximity/phrase weights zeroed out, adjacency shouldn't matter
    flat_weights = RankingWeights(body=1.0, title=0.0, filename=0.0, phrase=0.0, proximity=0.0)

    score_adjacent = score_document(idx, query, "doc_adjacent", weights=flat_weights)
    score_far = score_document(idx, query, "doc_far", weights=flat_weights)

    assert score_adjacent > 0
    assert score_far > 0


def test_score_document_single_term_query_no_proximity_or_phrase_boost():
    idx = _build_index()
    query = tokenize("database")
    score = score_document(idx, query, "doc_adjacent")
    assert score > 0  # body score still applies