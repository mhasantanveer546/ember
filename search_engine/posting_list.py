"""
Ember Search Engine — Posting List

A "posting" records where and how often a term appears in one document.
A "posting list" is the collection of postings for a single term, across
every document that contains it — the fundamental building block of an
inverted index (see inverted_index.py).
"""

from dataclasses import dataclass, field


@dataclass
class Posting:
    """
    One term's occurrence record within a single document.

    Attributes:
        document_id: Identifier of the document this posting belongs to.
        positions: Token positions (0-indexed) where the term appears in
            the document, in the order they were recorded. Needed for
            phrase search (Phase 1.5) and proximity ranking (Phase 1.7).
    """

    document_id: str
    positions: list[int] = field(default_factory=list)

    @property
    def term_frequency(self) -> int:
        """Number of times the term appears in this document. O(1)."""
        return len(self.positions)


class PostingList:
    """
    All postings for a single term, keyed by document_id for O(1) average
    lookup/update. This is what a single entry in the inverted index's
    term -> ... map points to.
    """

    def __init__(self) -> None:
        self._postings: dict[str, Posting] = {}

    def add_occurrence(self, document_id: str, position: int) -> None:
        """
        Record one occurrence of this term at `position` within
        `document_id`. Called once per token occurrence during indexing.
        """
        posting = self._postings.get(document_id)
        if posting is None:
            posting = Posting(document_id=document_id)
            self._postings[document_id] = posting
        posting.positions.append(position)

    def get(self, document_id: str) -> Posting | None:
        """Return this term's posting for one document, or None."""
        return self._postings.get(document_id)

    def document_ids(self) -> list[str]:
        """All document IDs containing this term."""
        return list(self._postings.keys())

    def document_frequency(self) -> int:
        """Number of distinct documents containing this term. O(1)."""
        return len(self._postings)

    def remove_document(self, document_id: str) -> None:
        """Remove all record of this term occurring in `document_id`."""
        self._postings.pop(document_id, None)

    def __iter__(self):
        return iter(self._postings.values())

    def __len__(self) -> int:
        return len(self._postings)