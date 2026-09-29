"""
Ember Backend — Document Processing Worker (Phase 3.5)

The RQ job that does everything the upload endpoint deliberately does
NOT do inline: read the stored file, extract text, tokenize it, and add
it to the workspace's search index — updating Document.status at each
step so the frontend can show real progress (Phase 6.2 will poll this).

Run by a real worker process locally with:
    rq worker documents

(assuming Redis/Memurai is running and REDIS_URL in .env points to it)
"""

import uuid

from app.db.session import SessionLocal
from app.models import Document, DocumentStatus
from app.services.extraction.extraction_service import extract_text
from app.services.search.index_registry import get_or_create_workspace_index
from app.services.storage.local_storage import get_storage_service
from search_engine.tokenizer import tokenize
from app.services.search.trie_registry import get_or_create_workspace_trie


def process_document(document_id: str) -> None:
    """
    Process one uploaded document: PROCESSING -> extract -> INDEXING ->
    tokenize + index -> READY. Sets status to FAILED and re-raises on
    any error, so RQ's own failure tracking/retry behavior still applies.

    Args:
        document_id: str, not uuid.UUID — RQ serializes job arguments,
            and a plain string round-trips more predictably than a UUID
            object across that boundary.
    """
    db = SessionLocal()
    try:
        document = db.get(Document, uuid.UUID(document_id))
        if document is None:
            # Document was deleted between being enqueued and the worker
            # picking up the job — nothing to do, not an error.
            return

        try:
            document.status = DocumentStatus.PROCESSING
            db.commit()

            storage = get_storage_service()
            content = storage.read(document.storage_key)

            file_kind = document.filename.rsplit(".", 1)[-1].lower()
            text = extract_text(file_kind, content)

            document.status = DocumentStatus.INDEXING
            db.commit()

            tokens = tokenize(text)
            workspace_index = get_or_create_workspace_index(document.workspace_id)
            workspace_index.add_document(str(document.id), tokens)

            # Populate autocomplete's Trie with this document's distinct
            # vocabulary. set() since inserting the same word twice is a
            # safe no-op anyway (Trie.insert), but no reason to repeat it.
            workspace_trie = get_or_create_workspace_trie(document.workspace_id)
            for token in set(tokens):
                workspace_trie.insert(token)

            document.status = DocumentStatus.READY
            db.commit()

        except Exception:
            # Deliberately broad: ANY failure at any step (storage read,
            # extraction, tokenization, indexing) should mark the
            # document FAILED rather than leave it stuck in PROCESSING
            # or INDEXING forever. re-raised so RQ's own failure
            # tracking/retry behavior still sees the job failed.
            document.status = DocumentStatus.FAILED
            db.commit()
            raise
    finally:
        db.close()