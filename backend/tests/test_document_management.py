"""Phase 5.5 backend support: text preview, delete, re-index, CORS."""


def _setup(client, email="mgmt@example.com"):
    client.post("/auth/register", json={"email": email, "password": "correcthorsebattery"})
    token = client.post("/auth/login", json={"email": email, "password": "correcthorsebattery"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    workspace_id = client.post("/workspaces", json={"name": "W"}, headers=headers).json()["id"]
    doc = client.post(
        f"/workspaces/{workspace_id}/documents",
        files={"file": ("notes.txt", b"congestion control in tcp", "text/plain")},
        headers=headers,
    ).json()["document"]
    return headers, workspace_id, doc["id"]


def test_text_preview(client):
    headers, ws, doc = _setup(client)
    r = client.get(f"/workspaces/{ws}/documents/{doc}/text", headers=headers)
    assert r.status_code == 200
    assert "congestion" in r.json()["text"]


def test_delete_removes_document_and_search_results(client):
    headers, ws, doc = _setup(client)
    assert client.delete(f"/workspaces/{ws}/documents/{doc}", headers=headers).status_code == 204
    assert client.get(f"/workspaces/{ws}/documents/{doc}", headers=headers).status_code == 404
    r = client.post(f"/workspaces/{ws}/search", json={"query": "congestion"}, headers=headers)
    assert r.json()["results"] == []


def test_reindex_keeps_document_searchable_without_duplicates(client):
    headers, ws, doc = _setup(client)
    r = client.post(f"/workspaces/{ws}/documents/{doc}/reindex", headers=headers)
    assert r.status_code == 200
    r = client.post(f"/workspaces/{ws}/search", json={"query": "congestion"}, headers=headers)
    assert len(r.json()["results"]) == 1


def test_other_users_cannot_read_delete_or_reindex(client):
    _, ws, doc = _setup(client, "owner@example.com")
    client.post("/auth/register", json={"email": "intruder@example.com", "password": "correcthorsebattery"})
    token = client.post("/auth/login", json={"email": "intruder@example.com", "password": "correcthorsebattery"}).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    assert client.get(f"/workspaces/{ws}/documents/{doc}/text", headers=h).status_code in (403, 404)
    assert client.delete(f"/workspaces/{ws}/documents/{doc}", headers=h).status_code in (403, 404)
    assert client.post(f"/workspaces/{ws}/documents/{doc}/reindex", headers=h).status_code in (403, 404)


def test_cors_allows_configured_origin_only(client):
    ok = client.options("/auth/login", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"
    bad = client.options("/auth/login", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in bad.headers
