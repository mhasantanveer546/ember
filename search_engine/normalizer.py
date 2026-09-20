"""
Ember Search Engine — Normalizer

Optional post-processing of tokens produced by tokenizer.py:
  - stopword removal
  - stemming (crude, rule-based suffix stripping)

Both are OFF by default. See docs/ARCHITECTURE.md / phase notes for why:
exact-phrase search and precision both depend on NOT silently discarding
or mutating tokens unless explicitly requested.

No external dependencies — stopword list and stemmer are both hand-rolled,
on purpose, to keep the search engine package dependency-free and to make
the mechanics visible/learnable rather than hidden inside a library.
"""

# A small, standard English stopword list. Not exhaustive — deliberately
# conservative (only very high-frequency function words) so we don't
# accidentally strip words that might be meaningful in technical notes
# (e.g. "will" as in a legal document, though here we still include it;
# tune this list based on real usage/benchmarks later, per Phase 1.9).
DEFAULT_STOPWORDS: frozenset[str] = frozenset(
    {
        "a", "an", "the",
        "is", "are", "was", "were", "be", "been", "being",
        "am",
        "and", "or", "but", "if", "then", "than",
        "of", "to", "in", "on", "at", "by", "for", "with", "about",
        "as", "from", "into", "through", "during", "before", "after",
        "i", "you", "he", "she", "it", "we", "they",
        "this", "that", "these", "those",
        "do", "does", "did", "doing",
        "have", "has", "had", "having",
        "not", "no",
        "will", "would", "shall", "should", "can", "could", "may", "might",
    }
)

# Suffixes checked longest-first. Plurals ("-es" / "-s") are handled
# separately below with a bit more care, since blindly stripping "es"
# from any word ending in those two letters over-stems words like "notes"
# (which is "note" + "s", not a genuine "-es" plural like "boxes").
# This is a deliberately simple, crude stemmer (NOT a full Porter/Snowball
# algorithm) — good enough to demonstrate the concept and get real recall
# gains, with known limitations documented below.
_SUFFIXES: tuple[str, ...] = ("ational", "ing", "edly", "ies", "ied", "ed", "ly")

# Letters that, immediately before a trailing "es", typically indicate a
# genuine "-es" plural (box-es, watch-es, glass-es, buzz-es) rather than a
# word that just happens to end in "e" + "s" (not-es -> note-s).
_ES_PLURAL_PRECEDING_LETTERS = frozenset({"s", "x", "z", "h"})

_MIN_STEM_LENGTH = 3  # never stem a word down to fewer than this many chars


def remove_stopwords(
    tokens: list[str], stopwords: frozenset[str] = DEFAULT_STOPWORDS
) -> list[str]:
    """
    Remove stopwords from a token list. O(n) — one pass, O(1) set lookups.

    Args:
        tokens: Tokens as produced by tokenizer.tokenize().
        stopwords: Set of words to remove. Defaults to DEFAULT_STOPWORDS.

    Returns:
        A new list with stopwords removed, order preserved.
    """
    return [t for t in tokens if t not in stopwords]


def simple_stem(token: str) -> str:
    """
    Crude suffix-stripping stemmer.

    Known limitations (documented, not hidden):
      - This is not linguistically accurate; it will occasionally under-stem
        (miss a real suffix) or over-stem (strip too much), e.g.
        "running" -> "runn" rather than the linguistically correct "run".
        A real Porter/Snowball stemmer handles many more cases correctly.
        We're using this simplified version to keep the package
        dependency-free and the mechanics transparent for learning.

    Args:
        token: A single lowercase token.

    Returns:
        The stemmed token, or the original token if no safe suffix strip
        applies.
    """
    for suffix in _SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= _MIN_STEM_LENGTH:
            return token[: -len(suffix)]

    # Plural handling: "-es" only counts as a plural suffix when preceded
    # by a letter that commonly forms "-es" plurals (box+es, watch+es).
    # Otherwise fall back to stripping a bare trailing "s" (note+s, cat+s),
    # but never strip "-ss" (e.g. "glass" should not become "glas").
    if (
        token.endswith("es")
        and len(token) - 2 >= _MIN_STEM_LENGTH
        and token[-3] in _ES_PLURAL_PRECEDING_LETTERS
    ):
        return token[:-2]

    if token.endswith("s") and not token.endswith("ss") and len(token) - 1 >= _MIN_STEM_LENGTH:
        return token[:-1]

    return token


def stem_tokens(tokens: list[str]) -> list[str]:
    """Apply simple_stem() to every token. O(n) overall."""
    return [simple_stem(t) for t in tokens]


def normalize(
    tokens: list[str],
    remove_stopwords_flag: bool = False,
    stem_flag: bool = False,
    stopwords: frozenset[str] = DEFAULT_STOPWORDS,
) -> list[str]:
    """
    Apply optional normalization steps, in order: stopword removal, then
    stemming. Both default to False — normalization is opt-in.

    Args:
        tokens: Tokens as produced by tokenizer.tokenize().
        remove_stopwords_flag: If True, strip stopwords first.
        stem_flag: If True, stem the (possibly stopword-filtered) tokens.
        stopwords: Custom stopword set, if remove_stopwords_flag is True.

    Returns:
        The normalized token list.
    """
    result = tokens
    if remove_stopwords_flag:
        result = remove_stopwords(result, stopwords)
    if stem_flag:
        result = stem_tokens(result)
    return result