"""
Ember Search Engine — Inverted Index

Maps term -> PostingList (term -> documents containing it -> positions).
This is the core data structure that makes search fast: instead of
scanning every document for every query (work proportional to total
corpus size, every time), we look up each query term directly (average
O(1), via a Python dict/hash map) and get back exactly the documents
that contain it, with no other documents even touched.
"""

from search_engine.posting_list import PostingList


class InvertedIndex:
    """
    term -> PostingList

    Backed by a Python dict (hash map): average O(1) insert and lookup
    per term, regardless of how many documents are indexed. This is what
    lets Ember search a growing document collection without search time
    scaling linearly with total content size.
    """

    def __init__(self) -> None:
        self._index: dict[str, PostingList] = {}
        self._document_lengths: dict[str, int] = {}  # doc_id -> token count

    def add_document(self, document_id: str, tokens: list[str]) -> None:
        """
        Index one document's tokens (already tokenized/normalized upstream
        by tokenizer.py / normalizer.py — this class doesn't know or care
        about that; it only deals with a flat, ordered list of terms).

        Args:
            document_id: Unique identifier for the document.
            tokens: Ordered list of terms, e.g. from tokenize(text).
        """
        for position, term in enumerate(tokens):
            if term not in self._index:
                self._index[term] = PostingList()
            self._index[term].add_occurrence(document_id, position)
        self._document_lengths[document_id] = len(tokens)

    def remove_document(self, document_id: str) -> None:
        """
        Remove a document from every term's posting list it appears in.
        Needed when a document is deleted or re-indexed. (Phase 4.1 also
        supports a full rebuild-and-atomic-swap; this is for incremental
        removal without rebuilding the whole index.)
        """
        for posting_list in self._index.values():
            posting_list.remove_document(document_id)
        self._document_lengths.pop(document_id, None)

    def get_postings(self, term: str) -> PostingList | None:
        """
        Average O(1) lookup: all documents containing `term`, with
        positions. Returns None if the term has never been indexed.
        """
        return self._index.get(term)

    def document_frequency(self, term: str) -> int:
        """Number of documents containing `term`. Average O(1)."""
        posting_list = self._index.get(term)
        return posting_list.document_frequency() if posting_list else 0

    def document_length(self, document_id: str) -> int:
        """Total token count for a document (used later for ranking)."""
        return self._document_lengths.get(document_id, 0)

    def vocabulary_size(self) -> int:
        """Number of distinct terms in the index."""
        return len(self._index)

    def document_count(self) -> int:
        """Number of distinct documents indexed."""
        return len(self._document_lengths)

    def __contains__(self, term: str) -> bool:
        return term in self._index