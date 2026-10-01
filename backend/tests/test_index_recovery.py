"""Tests for Phase 4.1 recovery: a lost/stale in-memory index heals itself."""

import uuid

from app.services.search.index_registry import get_or_create_workspace_index, reset_all_indexes
from app.services.search.rebuild_service import ensure_index_fresh
from app.services.search.trie_registry import reset_all_tries


def _auth(client, email="rec@example.com", password="correcthorsebattery"):
    client.post("/auth/register", json={"email": email, "password": password})
    token = client.post("/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _setup(client, content=b"congestion control in tcp"):
    headers = _auth(client)
    workspace_id = client.post("/workspaces", json={"name": "W"}, headers=headers).json()["id"]
    client.post(
        f"/workspaces/{workspace_id}/documents",
        files={"file": ("net.txt", content, "text/plain")},
        headers=headers,
    )
    return headers, workspace_id


def test_search_recovers_after_simulated_restart(client):
    headers, workspace_id = _setup(client)

    reset_all_indexes()  # simulate process restart: memory wiped, Postgres intact
    reset_all_tries()

    response = client.post(
        f"/workspaces/{workspace_id}/search", json={"query": "congestion"}, headers=headers
    )
    assert len(response.json()["results"]) == 1


def test_autocomplete_recovers_after_simulated_restart(client):
    headers, workspace_id = _setup(client)
    reset_all_indexes()
    reset_all_tries()

    response = client.get(
        f"/workspaces/{workspace_id}/search/autocomplete?prefix=conge", headers=headers
    )
    assert "congestion" in response.json()["suggestions"]


def test_ensure_index_fresh_is_noop_when_up_to_date(client, db_session):
    _, workspace_id = _setup(client)
    wid = uuid.UUID(workspace_id)
    assert ensure_index_fresh(db_session, wid) is True   # first load
    assert ensure_index_fresh(db_session, wid) is False  # nothing changed


def test_stale_index_rebuilds_when_document_set_changes(client, db_session):
    headers, workspace_id = _setup(client)
    wid = uuid.UUID(workspace_id)
    ensure_index_fresh(db_session, wid)

    # A second document arrives (as if indexed by a different process).
    client.post(
        f"/workspaces/{workspace_id}/documents",
        files={"file": ("db.txt", b"database normalization", "text/plain")},
        headers=headers,
    )
    reset_all_indexes()  # this process never saw the new doc's incremental add
    response = client.post(
        f"/workspaces/{workspace_id}/search", json={"query": "normalization"}, headers=headers
    )
    assert len(response.json()["results"]) == 1
    assert get_or_create_workspace_index(wid).document_count() == 2
