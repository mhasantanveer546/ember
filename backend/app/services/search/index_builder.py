"""
Ember Backend — Deterministic Index Rebuild (Phase 4.1)

PostgreSQL (Document rows) and each document's stored original file are
the SOURCE OF TRUTH. The InvertedIndex/Trie held in index_registry.py /
trie_registry.py are DERIVED, disposable artifacts, rebuildable at any
time from documents alone — this module performs that rebuild.

Deterministic: extraction and tokenization are both pure functions of a
document's stored bytes, so rebuilding twice from the same documents
produces an equivalent index both times.
"""

import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models import Document, DocumentStatus
from app.services.extraction.extraction_service import extract_text
from app.services.storage.local_storage import get_storage_service
from search_engine.inverted_index import InvertedIndex
from search_engine.tokenizer import tokenize
from search_engine.trie import Trie


@dataclass
class RebuildResult:
    index: InvertedIndex
    trie: Trie
    document_count: int
    vocabulary_size: int
    failed_document_ids: list[uuid.UUID] = field(default_factory=list)


def rebuild_workspace_index(db: Session, workspace_id: uuid.UUID) -> RebuildResult:
    """
    Rebuild a workspace's index FROM SCRATCH using only what's in
    PostgreSQL (READY documents) and their stored original files — never
    from any existing in-memory index state, so this is a genuine
    rebuild, not an incremental patch.

    Individual document failures (a stored file went missing, extraction
    now fails) are skipped and reported in failed_document_ids rather
    than aborting the whole rebuild — one bad document can't block every
    other document in the workspace from being searchable.
    """
    documents = (
        db.query(Document)
        .filter(Document.workspace_id == workspace_id, Document.status == DocumentStatus.READY)
        .order_by(Document.id)  # deterministic processing order
        .all()
    )

    storage = get_storage_service()
    new_index = InvertedIndex()
    new_trie = Trie()
    failed_document_ids: list[uuid.UUID] = []

    for document in documents:
        try:
            content = storage.read(document.storage_key)
            file_kind = document.filename.rsplit(".", 1)[-1].lower()
            text = extract_text(file_kind, content)
            tokens = tokenize(text)
        except Exception:
            failed_document_ids.append(document.id)
            continue

        new_index.add_document(str(document.id), tokens)
        for token in set(tokens):
            new_trie.insert(token)

    return RebuildResult(
        index=new_index,
        trie=new_trie,
        document_count=new_index.document_count(),
        vocabulary_size=new_index.vocabulary_size(),
        failed_document_ids=failed_document_ids,
    )