"""
Tests for authorization — the core requirement of Phase 2.3:
User A must NEVER be able to access User B's workspaces or documents.

Uses the real HTTP layer (register -> login -> create -> cross-access)
rather than calling dependency functions directly, so these tests prove
the whole chain works together, not just the ownership-check function
in isolation.
"""

import uuid

from app.db.session import SessionLocal
from app.models import Document, DocumentStatus, Folder, Workspace


def _register_and_login(client, email: str, password: str = "correcthorsebattery") -> str:
    client.post("/auth/register", json={"email": email, "password": password})
    response = client.post("/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_create_workspace_requires_authentication(client):
    response = client.post("/workspaces", json={"name": "My Notes"})
    assert response.status_code == 401


def test_create_workspace_succeeds_when_authenticated(client):
    token = _register_and_login(client, "owner@example.com")
    response = client.post(
        "/workspaces", json={"name": "My Notes"}, headers=_auth_headers(token)
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "My Notes"
    assert "id" in body


def test_owner_can_get_own_workspace(client):
    token = _register_and_login(client, "owner@example.com")
    create_response = client.post(
        "/workspaces", json={"name": "My Notes"}, headers=_auth_headers(token)
    )
    workspace_id = create_response.json()["id"]

    get_response = client.get(f"/workspaces/{workspace_id}", headers=_auth_headers(token))
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "My Notes"


def test_other_user_cannot_get_workspace_they_dont_own(client):
    owner_token = _register_and_login(client, "owner@example.com")
    create_response = client.post(
        "/workspaces", json={"name": "Owner's Private Notes"}, headers=_auth_headers(owner_token)
    )
    workspace_id = create_response.json()["id"]

    attacker_token = _register_and_login(client, "attacker@example.com")
    attack_response = client.get(
        f"/workspaces/{workspace_id}", headers=_auth_headers(attacker_token)
    )

    # THE core assertion of this phase.
    assert attack_response.status_code == 404


def test_cross_user_denial_is_404_not_403(client):
    # Specifically confirms we don't leak existence via a 403 — see
    # phase notes on why 404 is required here, not 403.
    owner_token = _register_and_login(client, "owner@example.com")
    create_response = client.post(
        "/workspaces", json={"name": "Secret"}, headers=_auth_headers(owner_token)
    )
    workspace_id = create_response.json()["id"]

    attacker_token = _register_and_login(client, "attacker@example.com")
    response = client.get(f"/workspaces/{workspace_id}", headers=_auth_headers(attacker_token))

    assert response.status_code == 404
    assert response.status_code != 403


def test_nonexistent_workspace_also_returns_404(client):
    # Same status code as "exists but not yours" — an attacker can't
    # distinguish "never existed" from "exists, belongs to someone else"
    # by comparing responses.
    token = _register_and_login(client, "user@example.com")
    fake_id = uuid.uuid4()

    response = client.get(f"/workspaces/{fake_id}", headers=_auth_headers(token))
    assert response.status_code == 404


def test_nonexistent_and_not_owned_return_identical_error_body(client):
    owner_token = _register_and_login(client, "owner@example.com")
    create_response = client.post(
        "/workspaces", json={"name": "Secret"}, headers=_auth_headers(owner_token)
    )
    real_workspace_id = create_response.json()["id"]

    attacker_token = _register_and_login(client, "attacker@example.com")
    response_for_real_but_not_owned = client.get(
        f"/workspaces/{real_workspace_id}", headers=_auth_headers(attacker_token)
    )
    response_for_fake_id = client.get(
        f"/workspaces/{uuid.uuid4()}", headers=_auth_headers(attacker_token)
    )

    assert response_for_real_but_not_owned.status_code == response_for_fake_id.status_code
    assert response_for_real_but_not_owned.json() == response_for_fake_id.json()


def test_get_workspace_requires_authentication(client):
    owner_token = _register_and_login(client, "owner@example.com")
    create_response = client.post(
        "/workspaces", json={"name": "My Notes"}, headers=_auth_headers(owner_token)
    )
    workspace_id = create_response.json()["id"]

    response = client.get(f"/workspaces/{workspace_id}")  # no auth header at all
    assert response.status_code == 401


# --- Document-level authorization (get_owned_document) ---
# No document upload route exists yet (Phase 3), so these test the
# dependency's logic directly against database fixtures, proving the
# access-control rule is correct BEFORE any route relies on it.

def _make_workspace_with_document(owner_id) -> tuple:
    db = SessionLocal()
    workspace = Workspace(owner_id=owner_id, name="Workspace")
    db.add(workspace)
    db.commit()

    document = Document(
        workspace_id=workspace.id,
        owner_id=owner_id,
        filename="secret_notes.txt",
        storage_key="key",
        content_hash="f" * 64,
        mime_type="text/plain",
        file_size_bytes=10,
        status=DocumentStatus.READY,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Capture IDs BEFORE closing the session — SQLAlchemy expires object
    # attributes after commit() by default, so accessing .id after
    # db.close() would try (and fail) to reload from a session that no
    # longer exists (DetachedInstanceError). This is the same class of
    # mistake as the earlier ORM-cascade bugs: an attribute access that
    # looks free actually depends on session state.
    workspace_id = workspace.id
    document_id = document.id
    db.close()
    return workspace_id, document_id


def test_get_owned_document_allows_workspace_owner(client):
    from app.api.deps import get_owned_document

    token = _register_and_login(client, "owner@example.com")
    me_response = client.get("/auth/me", headers=_auth_headers(token))
    owner_id = uuid.UUID(me_response.json()["id"])

    _workspace_id, document_id = _make_workspace_with_document(owner_id)

    db = SessionLocal()
    from app.models import User

    owner_user = db.get(User, owner_id)
    result = get_owned_document(document_id=document_id, current_user=owner_user, db=db)
    db.close()

    assert result.id == document_id


def test_get_owned_document_denies_non_owner(client):
    from fastapi import HTTPException

    from app.api.deps import get_owned_document
    from app.models import User

    owner_token = _register_and_login(client, "owner@example.com")
    owner_me = client.get("/auth/me", headers=_auth_headers(owner_token))
    owner_id = uuid.UUID(owner_me.json()["id"])
    _workspace_id, document_id = _make_workspace_with_document(owner_id)

    attacker_token = _register_and_login(client, "attacker@example.com")
    attacker_me = client.get("/auth/me", headers=_auth_headers(attacker_token))
    attacker_id = uuid.UUID(attacker_me.json()["id"])

    db = SessionLocal()
    attacker_user = db.get(User, attacker_id)

    try:
        get_owned_document(document_id=document_id, current_user=attacker_user, db=db)
        assert False, "expected HTTPException(404)"
    except HTTPException as exc:
        assert exc.status_code == 404
    finally:
        db.close()