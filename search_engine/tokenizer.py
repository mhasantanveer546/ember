"""
Ember Search Engine — Tokenizer

Converts raw text into a deterministic list of lowercase word tokens.

Design decisions (see docs/ARCHITECTURE.md for the full rationale):
- Case folding: all tokens are lowercased.
- Tokens are maximal runs of alphanumeric characters. Everything else
  (punctuation, whitespace, symbols) is treated as a separator.
- No stemming, no stopword removal here — that belongs to normalizer.py
  (Phase 1.2), kept as a separate, optional step.

This module has zero dependencies outside the standard library, and no
dependency on FastAPI, the database, or anything else in Ember. It must
be usable and testable completely on its own.
"""

import re

# Matches one or more "word characters" in the Unicode sense: letters and
# digits from any language, plus underscore. Using \w with re.UNICODE
# (the default in Python 3) means this handles non-ASCII text (e.g. accented
# characters) correctly, not just plain ASCII a-z.
#
# We explicitly exclude underscore-only tokens from being meaningful by not
# special-casing it further for now — "_" behaving as a word character is
# a known quirk of \w; it rarely matters for prose/documents but is worth
# knowing about.
_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """
    Split raw text into a deterministic list of lowercase tokens.

    Args:
        text: Raw input text (document content or a search query).

    Returns:
        A list of lowercase token strings, in the order they appeared.
        Empty input returns an empty list.

    Examples:
        >>> tokenize("The Quick Brown Fox!")
        ['the', 'quick', 'brown', 'fox']

        >>> tokenize("don't stop")
        ['don', 't', 'stop']

        >>> tokenize("")
        []

        >>> tokenize("TCP/IP congestion-control")
        ['tcp', 'ip', 'congestion', 'control']
    """
    if not text:
        return []

    # Lowercase first, then extract tokens. Order doesn't affect correctness
    # here since \w+ matching is case-insensitive to what counts as a word
    # character, but lowercasing first means we only ever produce lowercase
    # tokens with a single, simple pass.
    lowered = text.lower()
    return _TOKEN_PATTERN.findall(lowered)


def tokenize_with_offsets(text: str) -> list[tuple[str, int, int]]:
    """
    Like tokenize(), but also returns each token's character offsets in
    the ORIGINAL (non-lowercased) text: (lowercase_token, start, end).

    This exists specifically for snippet generation (snippets.py), which
    needs to slice out and highlight exact substrings of the original
    document text — something the plain token list alone can't do, since
    it discards position information.

    Examples:
        >>> tokenize_with_offsets("The Quick Fox")
        [('the', 0, 3), ('quick', 4, 9), ('fox', 10, 13)]
    """
    if not text:
        return []

    # Match against the original text's lowercase form so offsets line up
    # with `text` itself (lowercasing doesn't change string length for the
    # ASCII/most-Unicode case, and re.finditer positions refer to whatever
    # string we call it on — so we match on `text.lower()` but the offsets
    # are equally valid on `text` since case-folding preserves length here).
    lowered = text.lower()
    return [(m.group(), m.start(), m.end()) for m in _TOKEN_PATTERN.finditer(lowered)]