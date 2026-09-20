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