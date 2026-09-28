"""
Tests for Phase 3.5 — the full upload pipeline, end to end: upload ->
validate -> hash -> store -> (synchronous, in test) extract -> tokenize
-> index -> status READY.

The fake queue in conftest.py runs the background job immediately and
synchronously, so by the time upload_document() returns in these tests,
processing has ALREADY completed — letting us assert on the final
status directly, without polling or sleeping.
"""

import io

import docx
import pytest
from reportlab.pdfgen import canvas

from app.services.search.index_registry import get_or_create_workspace_index


def _register_and_login(client, email: str, password: str = "correcthorsebattery") -> str:
    client.post("/auth/register", json={"email": email, "password": password})
    response = client.post("/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_workspace(client, token, name="Workspace") -> str:
    response = client.post("/workspaces", json={"name": name}, headers=_auth_headers(token))
    return response.json()["id"]


def _make_pdf_with_text(text: str) -> bytes:
    buffer = io.BytesIO()
    pdf_canvas = canvas.Canvas(buffer)
    pdf_canvas.drawString(100, 750, text)
    pdf_canvas.save()
    return buffer.getvalue()


def _make_docx_with_text(text: str) -> bytes:
    document = docx.Document()
    document.add_paragraph(text)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _upload(client, token, workspace_id, filename, content, content_type="text/plain"):
    return client.post(
        f"/workspaces/{workspace_id}/documents",
        files={"file": (filename, content, content_type)},
        headers=_auth_headers(token),
    )


# --- End-to-end pipeline ---


def test_upload_txt_processes_to_ready(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)

    response = _upload(client, token, workspace_id, "notes.txt", b"Congestion control notes")
    assert response.status_code == 201
    body = response.json()
    assert body["is_duplicate"] is False
    assert body["document"]["status"] == "READY"
    assert body["document"]["filename"] == "notes.txt"


def test_upload_pdf_processes_to_ready(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    pdf_bytes = _make_pdf_with_text("Database normalization notes")

    response = _upload(client, token, workspace_id, "notes.pdf", pdf_bytes, "application/pdf")
    assert response.status_code == 201
    assert response.json()["document"]["status"] == "READY"


def test_upload_docx_processes_to_ready(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    docx_bytes = _make_docx_with_text("Sorting algorithms overview")

    response = _upload(
        client,
        token,
        workspace_id,
        "notes.docx",
        docx_bytes,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    assert response.status_code == 201
    assert response.json()["document"]["status"] == "READY"


def test_uploaded_document_actually_becomes_searchable(client):
    # The real end-to-end proof: after upload, the workspace's index
    # (Phase 1's real InvertedIndex, via the Phase 3.5 registry) actually
    # contains the uploaded content's terms.
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)

    upload_response = _upload(
        client, token, workspace_id, "notes.txt", b"Congestion control mechanisms in TCP"
    )
    document_id = upload_response.json()["document"]["id"]

    index = get_or_create_workspace_index(workspace_id)
    assert "congestion" in index
    postings = index.get_postings("congestion")
    assert postings.get(document_id) is not None


# --- Duplicate detection integration ---


def test_uploading_same_content_twice_returns_duplicate(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    content = b"identical content for duplicate check"

    first = _upload(client, token, workspace_id, "a.txt", content)
    second = _upload(client, token, workspace_id, "b.txt", content)  # different filename, same bytes

    assert first.json()["is_duplicate"] is False
    assert second.json()["is_duplicate"] is True
    assert second.json()["document"]["id"] == first.json()["document"]["id"]


def test_duplicate_upload_does_not_create_second_document(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    content = b"content to check duplicate counting"

    _upload(client, token, workspace_id, "a.txt", content)
    _upload(client, token, workspace_id, "b.txt", content)

    list_response = client.get(
        f"/workspaces/{workspace_id}/documents", headers=_auth_headers(token)
    )
    assert len(list_response.json()) == 1


# --- Validation integration ---


def test_upload_rejects_invalid_file_type(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)

    response = _upload(client, token, workspace_id, "malware.exe", b"anything")
    assert response.status_code == 400


def test_upload_rejects_spoofed_pdf(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)

    response = _upload(
        client, token, workspace_id, "fake.pdf", b"not really a pdf", "application/pdf"
    )
    assert response.status_code == 400


# --- Authorization integration ---


def test_upload_requires_authentication(client):
    workspace_id = _create_workspace(client, _register_and_login(client, "user@example.com"))
    response = client.post(
        f"/workspaces/{workspace_id}/documents", files={"file": ("a.txt", b"content", "text/plain")}
    )
    assert response.status_code == 401


def test_upload_to_other_users_workspace_blocked(client):
    owner_token = _register_and_login(client, "owner@example.com")
    workspace_id = _create_workspace(client, owner_token)

    attacker_token = _register_and_login(client, "attacker@example.com")
    response = _upload(client, attacker_token, workspace_id, "a.txt", b"content")
    assert response.status_code == 404


def test_get_document_from_wrong_workspace_in_url_returns_404(client):
    token = _register_and_login(client, "user@example.com")
    workspace_a = _create_workspace(client, token, "A")
    workspace_b = _create_workspace(client, token, "B")

    upload_response = _upload(client, token, workspace_a, "notes.txt", b"content in workspace A")
    document_id = upload_response.json()["document"]["id"]

    response = client.get(
        f"/workspaces/{workspace_b}/documents/{document_id}", headers=_auth_headers(token)
    )
    assert response.status_code == 404


def test_get_document_correct_workspace_succeeds(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)

    upload_response = _upload(client, token, workspace_id, "notes.txt", b"some content")
    document_id = upload_response.json()["document"]["id"]

    response = client.get(
        f"/workspaces/{workspace_id}/documents/{document_id}", headers=_auth_headers(token)
    )
    assert response.status_code == 200
    assert response.json()["filename"] == "notes.txt"


def test_list_documents_scoped_to_workspace(client):
    token = _register_and_login(client, "user@example.com")
    workspace_a = _create_workspace(client, token, "A")
    workspace_b = _create_workspace(client, token, "B")

    _upload(client, token, workspace_a, "in_a.txt", b"content a")
    _upload(client, token, workspace_b, "in_b.txt", b"content b")

    response = client.get(f"/workspaces/{workspace_a}/documents", headers=_auth_headers(token))
    filenames = [d["filename"] for d in response.json()]
    assert filenames == ["in_a.txt"]