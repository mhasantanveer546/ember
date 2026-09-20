"""Tests for search_engine.tokenizer"""

from search_engine.tokenizer import tokenize


def test_basic_lowercasing():
    assert tokenize("The Quick Brown Fox") == ["the", "quick", "brown", "fox"]


def test_punctuation_is_a_boundary():
    assert tokenize("Hello, world!") == ["hello", "world"]


def test_contraction_splits_on_apostrophe():
    # Known/expected behavior: no special contraction handling in MVP.
    assert tokenize("don't stop") == ["don", "t", "stop"]


def test_empty_string():
    assert tokenize("") == []


def test_whitespace_only():
    assert tokenize("   \n\t  ") == []


def test_multiple_whitespace_types_collapse():
    assert tokenize("congestion\ncontrol\ttcp") == ["congestion", "control", "tcp"]


def test_hyphenated_and_slashed_terms_split():
    assert tokenize("TCP/IP congestion-control") == ["tcp", "ip", "congestion", "control"]


def test_numbers_are_tokens():
    assert tokenize("RFC 793 defines TCP") == ["rfc", "793", "defines", "tcp"]


def test_determinism():
    text = "Database Normalization Notes - Chapter 3"
    assert tokenize(text) == tokenize(text)


def test_unicode_letters():
    assert tokenize("café résumé") == ["café", "résumé"]

def test_tokenize_with_offsets_basic():
    from search_engine.tokenizer import tokenize_with_offsets
    result = tokenize_with_offsets("The Quick Fox")
    assert result == [("the", 0, 3), ("quick", 4, 9), ("fox", 10, 13)]


def test_tokenize_with_offsets_matches_original_text_slices():
    from search_engine.tokenizer import tokenize_with_offsets
    text = "Congestion Control in TCP"
    for token, start, end in tokenize_with_offsets(text):
        assert text[start:end].lower() == token


def test_tokenize_with_offsets_empty_string():
    from search_engine.tokenizer import tokenize_with_offsets
    assert tokenize_with_offsets("") == []


def test_tokenize_with_offsets_punctuation_excluded_from_spans():
    from search_engine.tokenizer import tokenize_with_offsets
    result = tokenize_with_offsets("Hello, world!")
    assert result == [("hello", 0, 5), ("world", 7, 12)]