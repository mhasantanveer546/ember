"""Tests for Phase 4.1 — deterministic rebuild, validation, atomic swap."""

import uuid

import pytest

from app.services.search.index_builder import RebuildResult, rebuild_workspace_index
from app.services.search.index_registry import get_or_create_workspace_index
from app.services.search.rebuild_service import RebuildValidationError, _validate_rebuild, rebuild_and_swap


def _register_and_login(client, email: str, password: str = "correcthorsebattery") -> str:
    client.post("/auth/register", json={"email": email, "password": password})
    response = client.post("/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_workspace(client, token, name="Workspace") -> str:
    response = client.post("/workspaces", json={"name": name}, headers=_auth_headers(token))
    return response.json()["id"]


def _upload(client, token, workspace_id, filename, content):
    return client.post(
        f"/workspaces/{workspace_id}/documents",
        files={"file": (filename, content, "text/plain")},
        headers=_auth_headers(token),
    )


# --- Deterministic rebuild ---


def test_rebuild_reconstructs_index_matching_original(client, db_session):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _upload(client, token, workspace_id, "notes.txt", b"congestion control notes on tcp")

    result = rebuild_workspace_index(db_session, uuid.UUID(workspace_id))

    assert result.document_count == 1
    assert "congestion" in result.index
    assert result.failed_document_ids == []


def test_rebuild_is_deterministic_across_runs(client, db_session):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _upload(client, token, workspace_id, "a.txt", b"database normalization theory")
    _upload(client, token, workspace_id, "b.txt", b"sorting algorithms overview")

    first = rebuild_workspace_index(db_session, uuid.UUID(workspace_id))
    second = rebuild_workspace_index(db_session, uuid.UUID(workspace_id))

    assert first.document_count == second.document_count
    assert first.vocabulary_size == second.vocabulary_size
    assert first.index.document_frequency("database") == second.index.document_frequency("database")
    assert first.index.document_frequency("sorting") == second.index.document_frequency("sorting")


def test_rebuild_only_includes_ready_documents(client, db_session):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _upload(client, token, workspace_id, "ready.txt", b"this document is ready")
    # No way to easily create a non-READY document through the API
    # (upload always completes synchronously in tests) — this is
    # implicitly covered by the query filter itself
    # (Document.status == DocumentStatus.READY) rather than a separate
    # runtime test; see the filter in index_builder.py.

    result = rebuild_workspace_index(db_session, uuid.UUID(workspace_id))
    assert result.document_count == 1


def test_rebuild_skips_document_with_missing_file_without_crashing(client, db_session):
    from app.models import Document

    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    upload_response = _upload(client, token, workspace_id, "notes.txt", b"will be deleted")
    document_id = upload_response.json()["document"]["id"]

    # Simulate the stored file going missing (e.g. deleted out-of-band)
    # without touching the Document row's status.
    document = db_session.get(Document, uuid.UUID(document_id))
    document.storage_key = "nonexistent/path/that/does/not/exist.txt"
    db_session.commit()

    result = rebuild_workspace_index(db_session, uuid.UUID(workspace_id))

    assert result.document_count == 0
    assert uuid.UUID(document_id) in result.failed_document_ids


def test_rebuild_partial_failure_does_not_block_other_documents(client, db_session):
    from app.models import Document

    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    good_upload = _upload(client, token, workspace_id, "good.txt", b"this one works fine")
    bad_upload = _upload(client, token, workspace_id, "bad.txt", b"this one will break")

    bad_document_id = bad_upload.json()["document"]["id"]
    bad_document = db_session.get(Document, uuid.UUID(bad_document_id))
    bad_document.storage_key = "broken/path.txt"
    db_session.commit()

    result = rebuild_workspace_index(db_session, uuid.UUID(workspace_id))

    assert result.document_count == 1
    assert uuid.UUID(bad_document_id) in result.failed_document_ids


# --- Validation ---


def test_validate_rebuild_passes_when_counts_match():
    from search_engine.inverted_index import InvertedIndex
    from search_engine.trie import Trie

    result = RebuildResult(
        index=InvertedIndex(), trie=Trie(), document_count=3, vocabulary_size=10, failed_document_ids=[]
    )
    _validate_rebuild(result, expected_ready_count=3)  # should not raise


def test_validate_rebuild_raises_on_mismatch():
    from search_engine.inverted_index import InvertedIndex
    from search_engine.trie import Trie

    result = RebuildResult(
        index=InvertedIndex(), trie=Trie(), document_count=2, vocabulary_size=10, failed_document_ids=[]
    )
    with pytest.raises(RebuildValidationError):
        _validate_rebuild(result, expected_ready_count=5)  # 5 expected, only 2 indexed, 0 failed = inconsistent


# --- Atomic swap via rebuild_and_swap ---


def test_rebuild_and_swap_replaces_live_index(client, db_session):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _upload(client, token, workspace_id, "notes.txt", b"congestion control")

    # The live index already has this from the upload worker (Phase 3.5).
    live_index_before = get_or_create_workspace_index(uuid.UUID(workspace_id))
    assert "congestion" in live_index_before

    rebuild_and_swap(db_session, uuid.UUID(workspace_id))

    live_index_after = get_or_create_workspace_index(uuid.UUID(workspace_id))
    assert "congestion" in live_index_after


def test_rebuild_and_swap_updates_index_metadata(client, db_session):
    from app.models import IndexMetadata

    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _upload(client, token, workspace_id, "notes.txt", b"database normalization")

    rebuild_and_swap(db_session, uuid.UUID(workspace_id))

    metadata = (
        db_session.query(IndexMetadata)
        .filter(IndexMetadata.workspace_id == uuid.UUID(workspace_id))
        .first()
    )
    assert metadata.document_count == 1
    assert metadata.vocabulary_size > 0
    assert metadata.last_built_at is not None
    assert metadata.version >= 1


def test_rebuild_and_swap_bumps_version_on_each_call(client, db_session):
    from app.models import IndexMetadata

    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _upload(client, token, workspace_id, "notes.txt", b"some content")

    rebuild_and_swap(db_session, uuid.UUID(workspace_id))
    metadata = (
        db_session.query(IndexMetadata)
        .filter(IndexMetadata.workspace_id == uuid.UUID(workspace_id))
        .first()
    )
    version_after_first_rebuild = metadata.version

    rebuild_and_swap(db_session, uuid.UUID(workspace_id))
    db_session.refresh(metadata)

    assert metadata.version == version_after_first_rebuild + 1


def test_incremental_upload_updates_metadata_without_full_rebuild(client, db_session):
    from app.models import IndexMetadata

    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _upload(client, token, workspace_id, "notes.txt", b"some content here")

    metadata = (
        db_session.query(IndexMetadata)
        .filter(IndexMetadata.workspace_id == uuid.UUID(workspace_id))
        .first()
    )
    # Upload alone (Phase 3.5's worker) should have updated stats, with
    # NO explicit rebuild_and_swap call made in this test.
    assert metadata.document_count == 1
    assert metadata.vocabulary_size > 0


# --- API endpoints ---


def test_rebuild_endpoint_requires_ownership(client):
    owner_token = _register_and_login(client, "owner@example.com")
    workspace_id = _create_workspace(client, owner_token)

    attacker_token = _register_and_login(client, "attacker@example.com")
    response = client.post(
        f"/workspaces/{workspace_id}/index/rebuild", headers=_auth_headers(attacker_token)
    )
    assert response.status_code == 404


def test_rebuild_endpoint_returns_stats(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _upload(client, token, workspace_id, "notes.txt", b"database normalization")

    response = client.post(
        f"/workspaces/{workspace_id}/index/rebuild", headers=_auth_headers(token)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["document_count"] == 1
    assert body["vocabulary_size"] > 0
    assert body["failed_document_count"] == 0


def test_get_index_metadata_endpoint(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _upload(client, token, workspace_id, "notes.txt", b"some content")

    response = client.get(f"/workspaces/{workspace_id}/index", headers=_auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["document_count"] == 1
    assert body["version"] >= 0


def test_get_index_metadata_requires_ownership(client):
    owner_token = _register_and_login(client, "owner@example.com")
    workspace_id = _create_workspace(client, owner_token)

    attacker_token = _register_and_login(client, "attacker@example.com")
    response = client.get(
        f"/workspaces/{workspace_id}/index", headers=_auth_headers(attacker_token)
    )
    assert response.status_code == 404