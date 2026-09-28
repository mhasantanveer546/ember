"""
Ember Backend — Workspace Index Registry (Phase 3.5, MINIMAL PLACEHOLDER)

Maps workspace_id -> search_engine.InvertedIndex, purely in-memory.

THIS IS EXPLICITLY A PLACEHOLDER, not a production design:
  - It does NOT survive a process restart — every index is rebuilt from
    nothing the moment this process exits.
  - It would NOT be shared correctly across multiple worker processes
    (each process gets its own separate dict, and thus its own separate,
    inconsistent view of each workspace's index).
  - There is no persistence, versioning, or rebuild-and-swap here at all.

This exists ONLY to prove documents flow end-to-end from upload through
extraction to a genuinely searchable index within Phase 3.5. Phase 4.1
("Index Persistence") replaces this with a real design: the database as
source of truth, a deterministic rebuild process, and an atomic swap so
a search never sees a half-built index.
"""

import uuid

from search_engine.inverted_index import InvertedIndex

_indexes: dict[str, InvertedIndex] = {}


def get_or_create_workspace_index(workspace_id: uuid.UUID) -> InvertedIndex:
    key = str(workspace_id)
    if key not in _indexes:
        _indexes[key] = InvertedIndex()
    return _indexes[key]


def reset_all_indexes() -> None:
    """Test-only utility: clear all in-memory indexes between test runs."""
    _indexes.clear()