"""Tests for search_engine.snippets"""

from search_engine.snippets import generate_snippet
from search_engine.tokenizer import tokenize


def test_snippet_highlights_matched_term():
    text = "Notes on database normalization theory and practice."
    snippet = generate_snippet(text, ["database"])
    assert "**database**" in snippet


def test_snippet_highlights_multiple_query_terms():
    text = "Notes on database normalization theory."
    snippet = generate_snippet(text, tokenize("database normalization"))
    assert "**database**" in snippet
    assert "**normalization**" in snippet


def test_snippet_preserves_original_casing():
    text = "Notes on Database Normalization theory."
    snippet = generate_snippet(text, ["database"])
    assert "**Database**" in snippet  # original case preserved, not lowercased


def test_snippet_no_match_falls_back_to_leading_excerpt():
    text = "This document is about cooking and recipes only."
    snippet = generate_snippet(text, ["database"])
    assert snippet != ""
    assert "database" not in snippet.lower() or "**" not in snippet


def test_snippet_empty_text_returns_empty():
    assert generate_snippet("", ["database"]) == ""


def test_snippet_empty_query_returns_empty():
    assert generate_snippet("some text here", []) == ""


def test_snippet_prefix_ellipsis_when_not_at_document_start():
    # Many tokens before the match -> window should start mid-document
    text = " ".join(f"filler{i}" for i in range(30)) + " database normalization"
    snippet = generate_snippet(text, ["database"], context_tokens=3)
    assert snippet.startswith("...")


def test_snippet_no_prefix_ellipsis_when_match_near_start():
    text = "database normalization is discussed here in great detail across many lines"
    snippet = generate_snippet(text, ["database"], context_tokens=3)
    assert not snippet.startswith("...")


def test_snippet_suffix_ellipsis_when_not_at_document_end():
    text = "database normalization " + " ".join(f"filler{i}" for i in range(30))
    snippet = generate_snippet(text, ["database"], context_tokens=3)
    assert snippet.endswith("...")


def test_snippet_custom_highlight_markers():
    text = "Notes on database theory."
    snippet = generate_snippet(text, ["database"], highlight=("<mark>", "</mark>"))
    assert "<mark>database</mark>" in snippet


def test_snippet_respects_context_window_size():
    text = " ".join(f"word{i}" for i in range(50))
    # "word25" is the match target; small context window
    snippet = generate_snippet(text, ["word25"], context_tokens=2)
    # Should not contain tokens far outside the window
    assert "word0" not in snippet
    assert "word49" not in snippet