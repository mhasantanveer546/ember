"""
Ember Search Engine — TF-IDF

Term Frequency - Inverse Document Frequency: a per-(term, document) score
combining how often a term appears in one document (TF) with how rare
that term is across the whole indexed corpus (IDF).

    tf_idf(t, d) = tf(t, d) * idf(t)

See module docstrings below for the exact formulas and the trade-offs
between TF variants. This module has no ranking logic of its own — that's
Phase 1.7 (ranking.py), which combines tf_idf with other signals (title
boost, phrase boost, proximity).
"""

import heapq
import math
from dataclasses import dataclass

from search_engine.inverted_index import InvertedIndex
from search_engine.phrase_search import phrase_search


def term_frequency(index: InvertedIndex, term: str, document_id: str) -> int:
    """
    Raw term frequency: how many times `term` occurs in `document_id`.

    Note: raw TF is naturally biased toward longer documents (more total
    words -> more chances for any given word to repeat). See
    normalized_term_frequency / log_term_frequency for variants that
    correct for this.
    """
    postings = index.get_postings(term)
    if postings is None:
        return 0
    posting = postings.get(document_id)
    return posting.term_frequency if posting is not None else 0


def normalized_term_frequency(index: InvertedIndex, term: str, document_id: str) -> float:
    """
    Term frequency divided by total document length, correcting for
    document-length bias: tf(t,d) / |d|.

    Returns 0.0 for an empty or unknown document rather than raising, since
    a length-0 document trivially contains no term at any frequency.
    """
    doc_length = index.document_length(document_id)
    if doc_length == 0:
        return 0.0
    return term_frequency(index, term, document_id) / doc_length


def log_term_frequency(index: InvertedIndex, term: str, document_id: str) -> float:
    """
    Log-dampened term frequency: 1 + log(raw_tf) if raw_tf > 0, else 0.

    This is the most commonly used TF variant in practice: it captures
    "diminishing returns" — the jump from 1 to 2 occurrences matters far
    more than the jump from 50 to 51, which raw counts don't reflect.
    """
    raw_tf = term_frequency(index, term, document_id)
    if raw_tf == 0:
        return 0.0
    return 1.0 + math.log(raw_tf)


def inverse_document_frequency(index: InvertedIndex, term: str) -> float:
    """
    idf(t) = log(N / df(t))

    where N is the total number of indexed documents and df(t) is the
    number of documents containing `term`.

    Returns 0.0 (not an error) when:
      - the term has never been indexed (df == 0) — undefined by the
        formula, and a term that appears nowhere contributes nothing
        to any score anyway, so 0.0 is the sensible default.
      - the corpus is empty (N == 0) — same reasoning.

    Worth remembering: if a term appears in every document (df == N),
    idf == log(1) == 0. That's correct, not a bug — see module docs.
    """
    total_documents = index.document_count()
    doc_frequency = index.document_frequency(term)

    if total_documents == 0 or doc_frequency == 0:
        return 0.0

    return math.log(total_documents / doc_frequency)


def tf_idf(
    index: InvertedIndex,
    term: str,
    document_id: str,
    tf_variant: str = "log",
) -> float:
    """
    Combined TF-IDF score for one term in one document.

    Args:
        index: The InvertedIndex to score against.
        term: The term to score.
        document_id: The document to score it in.
        tf_variant: Which TF calculation to use — "raw", "normalized",
            or "log" (default). "log" is the recommended default per
            the module docs above; the others are kept available since
            the right choice can depend on real benchmark data
            (Phase 1.9 will measure this rather than assume it).

    Returns:
        The TF-IDF score. 0.0 if the term doesn't occur in the document
        or isn't indexed at all.
    """
    tf_functions = {
        "raw": term_frequency,
        "normalized": normalized_term_frequency,
        "log": log_term_frequency,
    }
    if tf_variant not in tf_functions:
        raise ValueError(
            f"Unknown tf_variant '{tf_variant}'. Must be one of: {list(tf_functions)}"
        )

    tf_value = tf_functions[tf_variant](index, term, document_id)
    idf_value = inverse_document_frequency(index, term)
    return tf_value * idf_value


# ---------------------------------------------------------------------------
# Phase 1.7 — Full ranking: combines TF-IDF (above) with title/filename
# boosts, phrase matching, and positional proximity into one final score
# per document. Weights are deliberately configurable, not hardcoded
# constants — the right values are a tuning question for real benchmark
# data (Phase 1.9), not something to assume up front.
# ---------------------------------------------------------------------------


@dataclass
class RankingWeights:
    """
    Configurable weights for combining ranking signals. Defaults are
    reasonable starting points, not tuned values — revisit once Phase 1.9
    benchmarks are in place.
    """

    body: float = 1.0
    title: float = 2.0
    filename: float = 1.5
    phrase: float = 3.0
    proximity: float = 1.0


def _body_score(index: InvertedIndex, query_terms: list[str], document_id: str) -> float:
    """Sum of TF-IDF scores across all unique query terms for one document."""
    return sum(tf_idf(index, term, document_id) for term in set(query_terms))


def _field_boost_score(
    index: InvertedIndex, query_terms: list[str], field_tokens: list[str] | None, weight: float
) -> float:
    """
    Boost for query terms that also appear in a secondary field (title or
    filename). Weighted by each matching term's IDF, so a rare matching
    term in the title boosts more than a common one — consistent with how
    body scoring already treats term rarity.
    """
    if not field_tokens or weight == 0.0:
        return 0.0
    field_token_set = set(field_tokens)
    matching_terms = set(query_terms) & field_token_set
    return weight * sum(inverse_document_frequency(index, term) for term in matching_terms)


def _phrase_boost_score(
    document_id: str, phrase_matching_doc_ids: frozenset[str], weight: float
) -> float:
    """
    Flat boost if `document_id` is among the documents where the full
    query matches as an exact consecutive phrase.

    Takes a PRECOMPUTED set of matching document IDs rather than calling
    phrase_search() itself. Phase 1.9 benchmarking caught a real O(n^2)
    performance bug here: phrase_search() does a full corpus-wide
    intersection on every call, and the original version of this function
    called it once per candidate document being scored — meaning scoring
    N candidates redundantly repeated that full-corpus work N times.
    Computing it once per QUERY (in score_candidates, below) and passing
    the result down fixes this.
    """
    if weight == 0.0:
        return 0.0
    return weight if document_id in phrase_matching_doc_ids else 0.0


def _smallest_window_covering_all_terms(position_lists: list[list[int]]) -> int | None:
    """
    Given one sorted position list per query term (all within the same
    document), find the size of the smallest window containing at least
    one position from every list. Returns None if any term has no
    positions in this document (i.e. can't cover all terms at all).

    Classic "smallest range covering elements from k lists" algorithm,
    using a min-heap: O(total_positions * log k).
    """
    if len(position_lists) < 2 or any(not positions for positions in position_lists):
        return None

    k = len(position_lists)
    pointers = [0] * k
    heap = [(position_lists[i][0], i) for i in range(k)]
    heapq.heapify(heap)
    current_max = max(positions[0] for positions in position_lists)
    best_window: int | None = None

    while True:
        current_min, list_index = heapq.heappop(heap)
        window_size = current_max - current_min + 1
        if best_window is None or window_size < best_window:
            best_window = window_size

        pointers[list_index] += 1
        if pointers[list_index] == len(position_lists[list_index]):
            # This term's positions are exhausted — no smaller window
            # covering all terms is possible from here on.
            break

        next_position = position_lists[list_index][pointers[list_index]]
        current_max = max(current_max, next_position)
        heapq.heappush(heap, (next_position, list_index))

    return best_window


def _proximity_score(
    index: InvertedIndex, query_terms: list[str], document_id: str, weight: float
) -> float:
    """
    Boost inversely proportional to how close together the query terms
    appear in the document — even when they don't form an exact phrase.
    0.0 if any query term is absent from the document, or fewer than 2
    distinct query terms (proximity is meaningless for a single term).
    """
    unique_terms = list(set(query_terms))
    if weight == 0.0 or len(unique_terms) < 2:
        return 0.0

    position_lists = []
    for term in unique_terms:
        postings = index.get_postings(term)
        posting = postings.get(document_id) if postings else None
        if posting is None:
            return 0.0  # term entirely absent from this document
        position_lists.append(posting.positions)

    window_size = _smallest_window_covering_all_terms(position_lists)
    if window_size is None or window_size == 0:
        return 0.0
    return weight / window_size


def score_document(
    index: InvertedIndex,
    query_terms: list[str],
    document_id: str,
    weights: RankingWeights = RankingWeights(),
    title_tokens: list[str] | None = None,
    filename_tokens: list[str] | None = None,
    phrase_matching_doc_ids: frozenset[str] | None = None,
) -> float:
    """
    Full ranking score for one document against a query, combining body
    relevance (TF-IDF), title/filename boosts, phrase matching, and
    positional proximity.

    Args:
        index: The InvertedIndex holding the document body content.
        query_terms: Tokenized query terms, e.g. tokenize("congestion control").
        document_id: The document being scored.
        weights: Configurable per-signal weights. See RankingWeights.
        title_tokens: Optional tokenized document title, for title boost.
        filename_tokens: Optional tokenized filename, for filename boost.
        phrase_matching_doc_ids: Precomputed phrase_search() result for
            this query, shared across all documents being scored for the
            same query. If None, it's computed here for this call alone —
            correct for scoring a single document in isolation, but
            scoring many documents this way repeats the full-corpus
            phrase search unnecessarily. Use score_candidates() (below)
            for batches, which computes this once per query.
    """
    if phrase_matching_doc_ids is None:
        phrase_matching_doc_ids = (
            frozenset(phrase_search(index, query_terms)) if len(query_terms) >= 2 else frozenset()
        )

    return (
        weights.body * _body_score(index, query_terms, document_id)
        + _field_boost_score(index, query_terms, title_tokens, weights.title)
        + _field_boost_score(index, query_terms, filename_tokens, weights.filename)
        + _phrase_boost_score(document_id, phrase_matching_doc_ids, weights.phrase)
        + _proximity_score(index, query_terms, document_id, weights.proximity)
    )


def score_candidates(
    index: InvertedIndex,
    query_terms: list[str],
    candidate_document_ids: list[str],
    weights: RankingWeights = RankingWeights(),
    title_tokens_map: dict[str, list[str]] | None = None,
    filename_tokens_map: dict[str, list[str]] | None = None,
) -> list[tuple[str, float]]:
    """
    Score many candidate documents against one query efficiently.

    Precomputes the phrase_search() result ONCE for the whole query,
    rather than once per candidate (see _phrase_boost_score docstring for
    why that matters) — this is the function top_k_search should use
    internally instead of calling score_document in a loop.

    Returns:
        List of (document_id, score) pairs, in the same order as
        candidate_document_ids (not sorted — top_k.py handles ranking).
    """
    phrase_matching_doc_ids = (
        frozenset(phrase_search(index, query_terms)) if len(query_terms) >= 2 else frozenset()
    )

    results = []
    for document_id in candidate_document_ids:
        title_tokens = title_tokens_map.get(document_id) if title_tokens_map else None
        filename_tokens = filename_tokens_map.get(document_id) if filename_tokens_map else None
        score = score_document(
            index,
            query_terms,
            document_id,
            weights=weights,
            title_tokens=title_tokens,
            filename_tokens=filename_tokens,
            phrase_matching_doc_ids=phrase_matching_doc_ids,
        )
        results.append((document_id, score))
    return results