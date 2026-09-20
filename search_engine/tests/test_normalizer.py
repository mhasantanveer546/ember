"""Tests for search_engine.normalizer"""

from search_engine.normalizer import (
    DEFAULT_STOPWORDS,
    normalize,
    remove_stopwords,
    simple_stem,
    stem_tokens,
)


def test_remove_stopwords_basic():
    tokens = ["the", "quick", "brown", "fox", "is", "fast"]
    assert remove_stopwords(tokens) == ["quick", "brown", "fox", "fast"]


def test_remove_stopwords_preserves_order():
    tokens = ["a", "database", "is", "a", "structured", "store"]
    assert remove_stopwords(tokens) == ["database", "structured", "store"]


def test_remove_stopwords_no_stopwords_present():
    tokens = ["database", "normalization", "notes"]
    assert remove_stopwords(tokens) == tokens


def test_remove_stopwords_all_stopwords():
    tokens = ["the", "is", "a", "of"]
    assert remove_stopwords(tokens) == []


def test_simple_stem_plural():
    assert simple_stem("boxes") == "box"
    assert simple_stem("notes") == "note"


def test_simple_stem_ing():
    assert simple_stem("running") == "runn"  # crude stemmer, documented limitation
    assert simple_stem("indexing") == "index"


def test_simple_stem_ed():
    assert simple_stem("indexed") == "index"


def test_simple_stem_respects_min_length():
    # "as" is too short to strip anything from safely
    assert simple_stem("as") == "as"
    assert simple_stem("is") == "is"


def test_simple_stem_no_matching_suffix():
    assert simple_stem("database") == "database"


def test_stem_tokens_batch():
    tokens = ["indexes", "searching", "database"]
    assert stem_tokens(tokens) == ["index", "search", "database"]


def test_normalize_defaults_are_noop():
    tokens = ["the", "quick", "foxes", "running"]
    assert normalize(tokens) == tokens


def test_normalize_stopwords_only():
    tokens = ["the", "quick", "foxes", "is", "running"]
    result = normalize(tokens, remove_stopwords_flag=True)
    assert result == ["quick", "foxes", "running"]


def test_normalize_stem_only():
    tokens = ["the", "foxes", "running"]
    result = normalize(tokens, stem_flag=True)
    assert result == ["the", "fox", "runn"]


def test_normalize_both():
    tokens = ["the", "quick", "foxes", "is", "running"]
    result = normalize(tokens, remove_stopwords_flag=True, stem_flag=True)
    assert result == ["quick", "fox", "runn"]


def test_normalize_custom_stopwords():
    tokens = ["database", "notes", "chapter"]
    custom = frozenset({"chapter"})
    result = normalize(tokens, remove_stopwords_flag=True, stopwords=custom)
    assert result == ["database", "notes"]


def test_default_stopwords_contains_common_words():
    assert "the" in DEFAULT_STOPWORDS
    assert "is" in DEFAULT_STOPWORDS
    assert "database" not in DEFAULT_STOPWORDS