"""
Ember Backend — Workspace Index Registry (Phase 3.5, finalized in Phase 4.1)

Maps workspace_id -> search_engine.InvertedIndex, purely in-memory.

In-memory cache of each workspace's InvertedIndex. This is DERIVED data:
PostgreSQL (documents + stored files) is the source of truth.
  - Restart / stale copy in another process -> rebuilt on demand by
    rebuild_service.ensure_index_fresh().
  - Explicit rebuild -> rebuild_service.rebuild_and_swap() validates the
    new index first, then swaps it in with swap_workspace_index().
"""

import uuid

from search_engine.inverted_index import InvertedIndex

_indexes: dict[str, InvertedIndex] = {}

# workspace_id -> number of READY documents in Postgres at the moment this
# process last loaded (rebuilt) that workspace's index. Used by Phase 4.1's
# recovery check: if Postgres now has a different READY count, this
# process's in-memory index is stale (restart, or a document was added by
# a separate worker process) and must be rebuilt from the source of truth.
_loaded_ready_counts: dict[str, int] = {}


def get_or_create_workspace_index(workspace_id: uuid.UUID) -> InvertedIndex:
    key = str(workspace_id)
    if key not in _indexes:
        _indexes[key] = InvertedIndex()
    return _indexes[key]


def reset_all_indexes() -> None:
    """Test-only utility: clear all in-memory indexes between test runs."""
    _indexes.clear()
    _loaded_ready_counts.clear()

def swap_workspace_index(workspace_id: uuid.UUID, new_index: InvertedIndex) -> None:
    """
    Atomically replace a workspace's live index with a fully-built new
    one (Phase 4.1's rebuild-and-swap). A plain dict item assignment is
    atomic under Python's GIL — any concurrent search reading
    get_or_create_workspace_index sees either the complete old index or
    the complete new one, never a partially-built intermediate state.
    """
    _indexes[str(workspace_id)] = new_index


def get_loaded_ready_count(workspace_id: uuid.UUID) -> int | None:
    """READY-document count at last load, or None if never loaded here."""
    return _loaded_ready_counts.get(str(workspace_id))


def mark_workspace_loaded(workspace_id: uuid.UUID, ready_document_count: int) -> None:
    _loaded_ready_counts[str(workspace_id)] = ready_document_count
