"""
Ember Backend — Workspace Trie Registry (Phase 4, MINIMAL PLACEHOLDER)

Same placeholder status as index_registry.py: purely in-memory, does not
survive a process restart, would not be shared correctly across worker
processes. Exists to power autocomplete now; Phase 4.1's real
persistence design should eventually cover this too, not just the
InvertedIndex.
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