"""
Ember Backend — Rebuild Orchestration (Phase 4.1)

Full flow: rebuild from Postgres (source of truth) -> validate ->
atomic swap into the live registries -> update IndexMetadata.

Validation happens BEFORE the swap, so a failed validation leaves the
CURRENT live index completely untouched — a bad rebuild never takes
search down for documents that were working a moment ago.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Document, DocumentStatus, IndexMetadata
from app.services.search.index_builder import RebuildResult, rebuild_workspace_index
from app.services.search.index_registry import swap_workspace_index
from app.services.search.trie_registry import swap_workspace_trie


class RebuildValidationError(Exception):
    """Raised when a rebuild's result doesn't match expectations. The
    live index is NOT touched when this is raised."""


def _validate_rebuild(result: RebuildResult, expected_ready_count: int) -> None:
    expected_indexed_count = expected_ready_count - len(result.failed_document_ids)
    if result.document_count != expected_indexed_count:
        raise RebuildValidationError(
            f"Rebuild produced {result.document_count} indexed documents, "
            f"expected {expected_indexed_count} "
            f"({expected_ready_count} READY documents, {len(result.failed_document_ids)} failed)."
        )


def rebuild_and_swap(db: Session, workspace_id: uuid.UUID) -> RebuildResult:
    """
    Run the full Phase 4.1 flow for one workspace.

    Returns:
        The RebuildResult that was validated and swapped in.

    Raises:
        RebuildValidationError: if the rebuilt index fails validation.
            The previously-live index remains in place, unchanged.
    """
    ready_document_count = (
        db.query(Document)
        .filter(Document.workspace_id == workspace_id, Document.status == DocumentStatus.READY)
        .count()
    )

    result = rebuild_workspace_index(db, workspace_id)
    _validate_rebuild(result, ready_document_count)

    swap_workspace_index(workspace_id, result.index)
    swap_workspace_trie(workspace_id, result.trie)

    _update_index_metadata(db, workspace_id, result, bump_version=True)

    return result


def record_incremental_index_update(
    db: Session, workspace_id: uuid.UUID, document_count: int, vocabulary_size: int
) -> None:
    """
    Update IndexMetadata's live stats after a SINGLE document is added
    incrementally (Phase 3.5's worker, on every upload) — NOT a full
    rebuild, so version is deliberately not bumped here. version only
    increments on an explicit rebuild_and_swap(); document_count and
    vocabulary_size stay fresh either way, so the stats shown to a user
    don't go stale between rebuilds.
    """
    metadata = (
        db.query(IndexMetadata).filter(IndexMetadata.workspace_id == workspace_id).first()
    )
    if metadata is None:
        metadata = IndexMetadata(workspace_id=workspace_id, version=0)
        db.add(metadata)

    metadata.document_count = document_count
    metadata.vocabulary_size = vocabulary_size
    metadata.last_built_at = datetime.now(timezone.utc)
    db.commit()


def _update_index_metadata(
    db: Session, workspace_id: uuid.UUID, result: RebuildResult, bump_version: bool
) -> None:
    metadata = (
        db.query(IndexMetadata).filter(IndexMetadata.workspace_id == workspace_id).first()
    )
    if metadata is None:
        # Shouldn't normally happen (every workspace gets one at
        # creation, Phase 2.4), but create it rather than fail outright
        # if it's somehow missing.
        metadata = IndexMetadata(workspace_id=workspace_id, version=0)
        db.add(metadata)

    if bump_version:
        metadata.version += 1
    metadata.document_count = result.document_count
    metadata.vocabulary_size = result.vocabulary_size
    metadata.last_built_at = datetime.now(timezone.utc)
    db.commit()