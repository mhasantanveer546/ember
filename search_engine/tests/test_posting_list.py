"""Tests for search_engine.posting_list"""

from search_engine.posting_list import Posting, PostingList


def test_posting_term_frequency():
    posting = Posting(document_id="doc1", positions=[0, 5, 9])
    assert posting.term_frequency == 3


def test_posting_term_frequency_empty():
    posting = Posting(document_id="doc1")
    assert posting.term_frequency == 0


def test_add_occurrence_creates_posting():
    pl = PostingList()
    pl.add_occurrence("doc1", 0)
    posting = pl.get("doc1")
    assert posting is not None
    assert posting.document_id == "doc1"
    assert posting.positions == [0]


def test_add_occurrence_accumulates_positions():
    pl = PostingList()
    pl.add_occurrence("doc1", 0)
    pl.add_occurrence("doc1", 5)
    pl.add_occurrence("doc1", 9)
    posting = pl.get("doc1")
    assert posting.positions == [0, 5, 9]
    assert posting.term_frequency == 3


def test_multiple_documents_tracked_separately():
    pl = PostingList()
    pl.add_occurrence("doc1", 0)
    pl.add_occurrence("doc2", 3)
    pl.add_occurrence("doc2", 7)

    assert pl.get("doc1").positions == [0]
    assert pl.get("doc2").positions == [3, 7]
    assert pl.document_frequency() == 2


def test_get_missing_document_returns_none():
    pl = PostingList()
    pl.add_occurrence("doc1", 0)
    assert pl.get("doc_unknown") is None


def test_document_ids():
    pl = PostingList()
    pl.add_occurrence("doc1", 0)
    pl.add_occurrence("doc2", 0)
    assert set(pl.document_ids()) == {"doc1", "doc2"}


def test_remove_document():
    pl = PostingList()
    pl.add_occurrence("doc1", 0)
    pl.add_occurrence("doc2", 0)
    pl.remove_document("doc1")
    assert pl.get("doc1") is None
    assert pl.get("doc2") is not None
    assert pl.document_frequency() == 1


def test_remove_nonexistent_document_is_safe():
    pl = PostingList()
    pl.add_occurrence("doc1", 0)
    pl.remove_document("doc_unknown")  # should not raise
    assert pl.document_frequency() == 1


def test_len_and_iteration():
    pl = PostingList()
    pl.add_occurrence("doc1", 0)
    pl.add_occurrence("doc2", 0)
    assert len(pl) == 2
    doc_ids_seen = {posting.document_id for posting in pl}
    assert doc_ids_seen == {"doc1", "doc2"}