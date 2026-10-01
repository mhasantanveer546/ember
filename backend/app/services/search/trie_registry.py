"""
Ember Backend — Workspace Trie Registry

In-memory cache of each workspace's autocomplete Trie. DERIVED data: it
is rebuilt from Postgres alongside the InvertedIndex (Phase 4.1,
rebuild_service.rebuild_and_swap / ensure_index_fresh), so losing it on a
restart or having a stale copy in another process is recoverable.
"""

import uuid

from search_engine.trie import Trie

_tries: dict[str, Trie] = {}


def get_or_create_workspace_trie(workspace_id: uuid.UUID) -> Trie:
    key = str(workspace_id)
    if key not in _tries:
        _tries[key] = Trie()
    return _tries[key]


def reset_all_tries() -> None:
    """Test-only utility: clear all in-memory tries between test runs."""
    _tries.clear()

def swap_workspace_trie(workspace_id: uuid.UUID, new_trie: Trie) -> None:
    """Atomic swap — same reasoning as swap_workspace_index."""
    _tries[str(workspace_id)] = new_trie