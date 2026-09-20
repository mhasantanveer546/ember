"""
Ember Search Engine — Phrase Search

Finds documents where a sequence of terms appears consecutively, in order
(e.g. "database normalization" as an exact phrase), using the positional
data already stored in each term's PostingList (Phase 1.3). No raw text
re-scanning at query time.

Algorithm:
    1. Intersect the document-ID lists of every term in the phrase
       (two-pointer merge on sorted lists, smallest list first) to get
       candidate documents that contain ALL terms.
    2. For each candidate, check whether the terms' positions form a
       consecutive run: term[0] at position p, term[1] at p+1, etc.
"""

from search_engine.inverted_index import InvertedIndex


def two_pointer_intersect(a: list[str], b: list[str]) -> list[str]:
    """
    Intersect two SORTED lists using the two-pointer technique.
    O(len(a) + len(b)) — each pointer only ever moves forward, so total
    work is linear in the combined size, with no nested scanning.
    """
    result: list[str] = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            result.append(a[i])
            i += 1
            j += 1
        elif a[i] < b[j]:
            i += 1
        else:
            j += 1
    return result


def intersect_postings(index: InvertedIndex, terms: list[str]) -> list[str]:
    """
    Return a sorted list of document IDs containing ALL given terms.

    Any term absent from the index at all means zero possible matches,
    so we short-circuit immediately. Otherwise, posting lists are sorted
    by document frequency (smallest first) before intersecting, so the
    candidate set shrinks as early and as fast as possible.
    """
    posting_lists = []
    for term in terms:
        posting_list = index.get_postings(term)
        if posting_list is None:
            return []
        posting_lists.append(posting_list)

    posting_lists.sort(key=lambda pl: pl.document_frequency())

    result_ids = sorted(posting_lists[0].document_ids())
    for posting_list in posting_lists[1:]:
        if not result_ids:
            break
        result_ids = two_pointer_intersect(result_ids, sorted(posting_list.document_ids()))

    return result_ids


def phrase_search(index: InvertedIndex, phrase_terms: list[str]) -> list[str]:
    """
    Return document IDs where `phrase_terms` appear consecutively, in
    order, as an exact phrase.

    Args:
        index: The InvertedIndex to search.
        phrase_terms: Ordered list of terms making up the phrase, e.g.
            tokenize("database normalization").

    Returns:
        Sorted list of matching document IDs. Empty if the phrase is
        empty, any term is unindexed, or no document contains the exact
        consecutive sequence.
    """
    if not phrase_terms:
        return []

    candidate_doc_ids = intersect_postings(index, phrase_terms)
    if not candidate_doc_ids:
        return []

    # Re-fetch postings in original phrase order (intersect_postings
    # reordered its own copy for efficiency, but we need original order
    # here to check consecutive positions correctly).
    posting_lists = [index.get_postings(term) for term in phrase_terms]

    matches: list[str] = []
    for doc_id in candidate_doc_ids:
        first_term_positions = posting_lists[0].get(doc_id).positions
        later_position_sets = [
            set(posting_lists[i].get(doc_id).positions) for i in range(1, len(phrase_terms))
        ]

        for start_position in first_term_positions:
            if all(
                (start_position + offset) in later_position_sets[offset - 1]
                for offset in range(1, len(phrase_terms))
            ):
                matches.append(doc_id)
                break  # one match is enough to confirm this document

    return matches