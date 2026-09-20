"""
Ember Search Engine — Top-K Selection

Selects the top K highest-scoring items from a candidate list using a
min-heap of size K, rather than sorting the entire candidate list.

    Full sort:        O(n log n)
    Min-heap top-K:   O(n log k)

Since k is typically a small constant (10, 20, 50 results per page) while
n (total matching documents) can be large and grows with the corpus, this
difference matters at real scale — most of a full sort's work would be
spent ordering results nobody asked for.
"""

import heapq
from typing import TypeVar

from search_engine.inverted_index import InvertedIndex
from search_engine.ranking import RankingWeights, score_candidates

T = TypeVar("T")


def top_k_by_score(items: list[tuple[T, float]], k: int) -> list[tuple[T, float]]:
    """
    Return the top `k` (item, score) pairs by score, descending, using a
    min-heap of size k. General-purpose — not specific to documents or
    search, so it's independently testable and reusable.

    Args:
        items: (item, score) pairs. Order not assumed.
        k: How many top-scoring items to return.

    Returns:
        Up to k (item, score) pairs, sorted by score descending. Fewer
        than k if there are fewer than k items. Empty list if k <= 0.
    """
    if k <= 0:
        return []

    # Heap entries are (score, insertion_order, item). insertion_order is
    # a tiebreaker so heapq never has to compare two `item` values directly
    # when scores are equal (avoids relying on items being orderable, and
    # keeps behavior deterministic regardless of item type).
    heap: list[tuple[float, int, T]] = []

    for insertion_order, (item, score) in enumerate(items):
        if len(heap) < k:
            heapq.heappush(heap, (score, insertion_order, item))
        elif score > heap[0][0]:
            heapq.heapreplace(heap, (score, insertion_order, item))
        # else: score isn't good enough to make the current top k — O(1)
        # discard, no heap operation needed at all.

    ranked = sorted(heap, key=lambda entry: entry[0], reverse=True)
    return [(item, score) for score, _, item in ranked]


def top_k_search(
    index: InvertedIndex,
    query_terms: list[str],
    candidate_document_ids: list[str],
    k: int = 10,
    weights: RankingWeights | None = None,
    title_tokens_map: dict[str, list[str]] | None = None,
    filename_tokens_map: dict[str, list[str]] | None = None,
) -> list[tuple[str, float]]:
    """
    Score every candidate document against the query (Phase 1.7's
    score_document) and return the top k, using top_k_by_score above.

    Args:
        index: The InvertedIndex to score against.
        query_terms: Tokenized query terms.
        candidate_document_ids: Documents to consider (e.g. from
            intersect_postings — only documents containing at least one
            query term need to be scored at all).
        k: Number of top results to return.
        weights: Ranking weights; defaults to RankingWeights() if omitted.
        title_tokens_map: Optional {document_id: tokenized title}.
        filename_tokens_map: Optional {document_id: tokenized filename}.

    Returns:
        Up to k (document_id, score) pairs, sorted by score descending.
    """
    if weights is None:
        weights = RankingWeights()

    scored_documents = score_candidates(
        index,
        query_terms,
        candidate_document_ids,
        weights=weights,
        title_tokens_map=title_tokens_map,
        filename_tokens_map=filename_tokens_map,
    )

    return top_k_by_score(scored_documents, k)