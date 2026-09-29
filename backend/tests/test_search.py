"""Tests for Phase 4 — search, autocomplete, and search history."""


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


def _search(client, token, workspace_id, query, limit=10):
    return client.post(
        f"/workspaces/{workspace_id}/search",
        json={"query": query, "limit": limit},
        headers=_auth_headers(token),
    )


# --- Basic search ---


def test_search_finds_uploaded_document(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _upload(client, token, workspace_id, "notes.txt", b"Congestion control mechanisms in TCP")

    response = _search(client, token, workspace_id, "congestion control")
    assert response.status_code == 200
    body = response.json()
    assert body["is_phrase_search"] is False
    assert len(body["results"]) == 1
    assert body["results"][0]["filename"] == "notes.txt"
    assert "congestion" in body["results"][0]["snippet"].lower()


def test_search_ranks_more_relevant_document_higher(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _upload(client, token, workspace_id, "very_relevant.txt", b"database normalization database normalization theory")
    _upload(client, token, workspace_id, "barely_relevant.txt", b"a brief mention of database somewhere")

    response = _search(client, token, workspace_id, "database normalization")
    results = response.json()["results"]
    assert results[0]["filename"] == "very_relevant.txt"


def test_search_no_matches_returns_empty_results(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _upload(client, token, workspace_id, "notes.txt", b"cooking recipes and travel guides")

    response = _search(client, token, workspace_id, "congestion control")
    assert response.status_code == 200
    assert response.json()["results"] == []


def test_search_empty_workspace_returns_empty_results(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)

    response = _search(client, token, workspace_id, "anything")
    assert response.status_code == 200
    assert response.json()["results"] == []


def test_search_respects_limit(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    for i in range(5):
        _upload(client, token, workspace_id, f"doc{i}.txt", f"shared keyword number {i}".encode())

    response = _search(client, token, workspace_id, "shared keyword", limit=2)
    assert len(response.json()["results"]) == 2


def test_search_scoped_to_workspace(client):
    token = _register_and_login(client, "user@example.com")
    workspace_a = _create_workspace(client, token, "A")
    workspace_b = _create_workspace(client, token, "B")

    _upload(client, token, workspace_a, "in_a.txt", b"congestion control notes")
    _upload(client, token, workspace_b, "in_b.txt", b"congestion control notes")

    response = _search(client, token, workspace_a, "congestion control")
    filenames = [r["filename"] for r in response.json()["results"]]
    assert filenames == ["in_a.txt"]


# --- Phrase search ---


def test_quoted_query_triggers_phrase_search(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _upload(client, token, workspace_id, "adjacent.txt", b"notes on database normalization theory")
    _upload(client, token, workspace_id, "scattered.txt", b"the database has normalization issues")

    response = _search(client, token, workspace_id, '"database normalization"')
    body = response.json()
    assert body["is_phrase_search"] is True
    filenames = [r["filename"] for r in body["results"]]
    assert filenames == ["adjacent.txt"]


def test_unquoted_query_does_not_use_phrase_mode(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _upload(client, token, workspace_id, "scattered.txt", b"the database has normalization issues")

    response = _search(client, token, workspace_id, "database normalization")
    body = response.json()
    assert body["is_phrase_search"] is False
    # unquoted query should still find the scattered (non-adjacent) match
    assert len(body["results"]) == 1


# --- Authorization ---


def test_search_requires_authentication(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)

    response = client.post(f"/workspaces/{workspace_id}/search", json={"query": "test"})
    assert response.status_code == 401


def test_search_other_users_workspace_blocked(client):
    owner_token = _register_and_login(client, "owner@example.com")
    workspace_id = _create_workspace(client, owner_token)

    attacker_token = _register_and_login(client, "attacker@example.com")
    response = _search(client, attacker_token, workspace_id, "anything")
    assert response.status_code == 404


# --- Autocomplete ---


def test_autocomplete_suggests_indexed_terms(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _upload(client, token, workspace_id, "notes.txt", b"database databases dataset")

    response = client.get(
        f"/workspaces/{workspace_id}/search/autocomplete?prefix=data",
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    suggestions = response.json()["suggestions"]
    assert "database" in suggestions
    assert "dataset" in suggestions


def test_autocomplete_no_matches_returns_empty(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _upload(client, token, workspace_id, "notes.txt", b"cooking recipes")

    response = client.get(
        f"/workspaces/{workspace_id}/search/autocomplete?prefix=xyz",
        headers=_auth_headers(token),
    )
    assert response.json()["suggestions"] == []


def test_autocomplete_requires_authentication(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)

    response = client.get(f"/workspaces/{workspace_id}/search/autocomplete?prefix=data")
    assert response.status_code == 401


# --- Search history ---


def test_search_records_history(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _search(client, token, workspace_id, "congestion control")

    response = client.get(
        f"/workspaces/{workspace_id}/search/history", headers=_auth_headers(token)
    )
    queries = [entry["query_text"] for entry in response.json()["history"]]
    assert "congestion control" in queries


def test_search_history_most_recent_first(client):
    import time

    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _search(client, token, workspace_id, "first query")
    # SQLite's CURRENT_TIMESTAMP (used by conftest.py's test database) has
    # only SECOND-level resolution, unlike real Neon Postgres's now()
    # (microsecond precision) — two inserts within the same second would
    # otherwise get identical created_at values with undefined relative
    # order. This sleep exists ONLY to make the test itself deterministic
    # under SQLite; it is not something production needs.
    time.sleep(1.1)
    _search(client, token, workspace_id, "second query")

    response = client.get(
        f"/workspaces/{workspace_id}/search/history", headers=_auth_headers(token)
    )
    queries = [entry["query_text"] for entry in response.json()["history"]]
    assert queries[0] == "second query"
    assert queries[1] == "first query"


def test_search_history_scoped_to_user(client):
    token_a = _register_and_login(client, "a@example.com")
    workspace_id = _create_workspace(client, token_a)
    _search(client, token_a, workspace_id, "a's private query")

    # user B has no access to this workspace at all, so this also proves
    # authorization holds for the history endpoint too.
    token_b = _register_and_login(client, "b@example.com")
    response = client.get(
        f"/workspaces/{workspace_id}/search/history", headers=_auth_headers(token_b)
    )
    assert response.status_code == 404


def test_search_history_scoped_to_workspace(client):
    token = _register_and_login(client, "user@example.com")
    workspace_a = _create_workspace(client, token, "A")
    workspace_b = _create_workspace(client, token, "B")

    _search(client, token, workspace_a, "query in A")
    _search(client, token, workspace_b, "query in B")

    response = client.get(
        f"/workspaces/{workspace_a}/search/history", headers=_auth_headers(token)
    )
    queries = [entry["query_text"] for entry in response.json()["history"]]
    assert queries == ["query in A"]


def test_zero_result_search_still_recorded_in_history(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    _search(client, token, workspace_id, "nothing will match this")

    response = client.get(
        f"/workspaces/{workspace_id}/search/history", headers=_auth_headers(token)
    )
    queries = [entry["query_text"] for entry in response.json()["history"]]
    assert "nothing will match this" in queries