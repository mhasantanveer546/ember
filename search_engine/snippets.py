"""
Ember Search Engine — Snippet Generation

Produces a short excerpt from a document's raw text, centered on a query
term match, with matched terms highlighted — the "...notes on **database**
**normalization** theory..." text shown under a search result.

Built on tokenize_with_offsets() (Phase 1.9 addition to tokenizer.py),
which maps each token back to its exact character span in the original
text — needed here because tokenize() alone discards position information.
"""

from search_engine.tokenizer import tokenize_with_offsets


def generate_snippet(
    text: str,
    query_terms: list[str],
    context_tokens: int = 8,
    highlight: tuple[str, str] = ("**", "**"),
) -> str:
    """
    Build a snippet centered on the first query term match in `text`,
    with matched terms wrapped in `highlight` markers.

    Args:
        text: The document's raw (original-case) text.
        query_terms: Tokenized query terms to look for and highlight.
        context_tokens: How many tokens of context to include on each
            side of the first match.
        highlight: (start_marker, end_marker) wrapped around each matched
            term in the output, e.g. ("**", "**") for Markdown bold, or
            ("<mark>", "</mark>") for HTML.

    Returns:
        A snippet string, with "..." prepended/appended if the snippet
        doesn't start/end at the document boundary. Empty string if the
        text or query is empty.
    """
    if not text or not query_terms:
        return ""

    query_term_set = set(query_terms)
    tokens = tokenize_with_offsets(text)
    if not tokens:
        return ""

    match_index = next(
        (i for i, (token, _, _) in enumerate(tokens) if token in query_term_set), None
    )
    if match_index is None:
        match_index = 0  # no match: fall back to a leading excerpt

    window_start_index = max(0, match_index - context_tokens)
    window_end_index = min(len(tokens) - 1, match_index + context_tokens)

    window_start_char = tokens[window_start_index][1]
    window_end_char = tokens[window_end_index][2]

    pieces: list[str] = []
    cursor = window_start_char
    for i in range(window_start_index, window_end_index + 1):
        token, token_start, token_end = tokens[i]
        pieces.append(text[cursor:token_start])  # separator text before this token
        original_token_text = text[token_start:token_end]
        if token in query_term_set:
            pieces.append(f"{highlight[0]}{original_token_text}{highlight[1]}")
        else:
            pieces.append(original_token_text)
        cursor = token_end

    snippet_body = "".join(pieces)
    prefix = "..." if window_start_char > 0 else ""
    suffix = "..." if window_end_char < len(text) else ""

    return f"{prefix}{snippet_body}{suffix}"