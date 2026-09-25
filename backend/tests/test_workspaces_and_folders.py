"""Tests for Phase 2.4 — workspace CRUD and folder CRUD with nesting."""


def _register_and_login(client, email: str, password: str = "correcthorsebattery") -> str:
    client.post("/auth/register", json={"email": email, "password": password})
    response = client.post("/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_workspace(client, token, name="Workspace") -> str:
    response = client.post("/workspaces", json={"name": name}, headers=_auth_headers(token))
    return response.json()["id"]


# --- Workspace CRUD ---


def test_list_workspaces_returns_only_own(client):
    token_a = _register_and_login(client, "a@example.com")
    token_b = _register_and_login(client, "b@example.com")

    _create_workspace(client, token_a, "A's workspace")
    _create_workspace(client, token_b, "B's workspace")

    response = client.get("/workspaces", headers=_auth_headers(token_a))
    assert response.status_code == 200
    names = [w["name"] for w in response.json()]
    assert names == ["A's workspace"]


def test_update_workspace_renames(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token, "Old Name")

    response = client.patch(
        f"/workspaces/{workspace_id}", json={"name": "New Name"}, headers=_auth_headers(token)
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_update_workspace_empty_body_changes_nothing(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token, "Unchanged")

    response = client.patch(f"/workspaces/{workspace_id}", json={}, headers=_auth_headers(token))
    assert response.status_code == 200
    assert response.json()["name"] == "Unchanged"


def test_update_workspace_other_user_blocked(client):
    owner_token = _register_and_login(client, "owner@example.com")
    workspace_id = _create_workspace(client, owner_token, "Owner's")

    attacker_token = _register_and_login(client, "attacker@example.com")
    response = client.patch(
        f"/workspaces/{workspace_id}", json={"name": "Hacked"}, headers=_auth_headers(attacker_token)
    )
    assert response.status_code == 404


def test_delete_workspace(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)

    delete_response = client.delete(f"/workspaces/{workspace_id}", headers=_auth_headers(token))
    assert delete_response.status_code == 204

    get_response = client.get(f"/workspaces/{workspace_id}", headers=_auth_headers(token))
    assert get_response.status_code == 404


def test_delete_workspace_other_user_blocked(client):
    owner_token = _register_and_login(client, "owner@example.com")
    workspace_id = _create_workspace(client, owner_token)

    attacker_token = _register_and_login(client, "attacker@example.com")
    response = client.delete(f"/workspaces/{workspace_id}", headers=_auth_headers(attacker_token))
    assert response.status_code == 404


# --- Folder CRUD ---


def test_create_root_folder(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)

    response = client.post(
        f"/workspaces/{workspace_id}/folders", json={"name": "Notes"}, headers=_auth_headers(token)
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Notes"
    assert body["parent_folder_id"] is None


def test_create_nested_folder(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)

    parent_response = client.post(
        f"/workspaces/{workspace_id}/folders", json={"name": "Parent"}, headers=_auth_headers(token)
    )
    parent_id = parent_response.json()["id"]

    child_response = client.post(
        f"/workspaces/{workspace_id}/folders",
        json={"name": "Child", "parent_folder_id": parent_id},
        headers=_auth_headers(token),
    )
    assert child_response.status_code == 201
    assert child_response.json()["parent_folder_id"] == parent_id


def test_create_folder_other_user_workspace_blocked(client):
    owner_token = _register_and_login(client, "owner@example.com")
    workspace_id = _create_workspace(client, owner_token)

    attacker_token = _register_and_login(client, "attacker@example.com")
    response = client.post(
        f"/workspaces/{workspace_id}/folders",
        json={"name": "Intrusion"},
        headers=_auth_headers(attacker_token),
    )
    assert response.status_code == 404


def test_create_folder_with_parent_from_different_workspace_rejected(client):
    token = _register_and_login(client, "user@example.com")
    workspace_a = _create_workspace(client, token, "Workspace A")
    workspace_b = _create_workspace(client, token, "Workspace B")

    folder_in_a = client.post(
        f"/workspaces/{workspace_a}/folders", json={"name": "Folder A"}, headers=_auth_headers(token)
    ).json()

    response = client.post(
        f"/workspaces/{workspace_b}/folders",
        json={"name": "Cross-workspace child", "parent_folder_id": folder_in_a["id"]},
        headers=_auth_headers(token),
    )
    assert response.status_code == 400


def test_list_folders_scoped_to_workspace(client):
    token = _register_and_login(client, "user@example.com")
    workspace_a = _create_workspace(client, token, "A")
    workspace_b = _create_workspace(client, token, "B")

    client.post(f"/workspaces/{workspace_a}/folders", json={"name": "In A"}, headers=_auth_headers(token))
    client.post(f"/workspaces/{workspace_b}/folders", json={"name": "In B"}, headers=_auth_headers(token))

    response = client.get(f"/workspaces/{workspace_a}/folders", headers=_auth_headers(token))
    names = [f["name"] for f in response.json()]
    assert names == ["In A"]


def test_get_folder_from_wrong_workspace_in_url_returns_404(client):
    token = _register_and_login(client, "user@example.com")
    workspace_a = _create_workspace(client, token, "A")
    workspace_b = _create_workspace(client, token, "B")

    folder_in_a = client.post(
        f"/workspaces/{workspace_a}/folders", json={"name": "Folder A"}, headers=_auth_headers(token)
    ).json()

    # Folder genuinely exists and belongs to this user — just not to
    # workspace_b, which is also this URL's workspace_id.
    response = client.get(
        f"/workspaces/{workspace_b}/folders/{folder_in_a['id']}", headers=_auth_headers(token)
    )
    assert response.status_code == 404


def test_rename_folder(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    folder = client.post(
        f"/workspaces/{workspace_id}/folders", json={"name": "Old"}, headers=_auth_headers(token)
    ).json()

    response = client.patch(
        f"/workspaces/{workspace_id}/folders/{folder['id']}",
        json={"name": "New"},
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New"


def test_move_folder_to_new_parent(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    folder_a = client.post(
        f"/workspaces/{workspace_id}/folders", json={"name": "A"}, headers=_auth_headers(token)
    ).json()
    folder_b = client.post(
        f"/workspaces/{workspace_id}/folders", json={"name": "B"}, headers=_auth_headers(token)
    ).json()

    response = client.patch(
        f"/workspaces/{workspace_id}/folders/{folder_b['id']}",
        json={"parent_folder_id": folder_a["id"]},
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    assert response.json()["parent_folder_id"] == folder_a["id"]


def test_move_folder_into_itself_rejected(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    folder = client.post(
        f"/workspaces/{workspace_id}/folders", json={"name": "A"}, headers=_auth_headers(token)
    ).json()

    response = client.patch(
        f"/workspaces/{workspace_id}/folders/{folder['id']}",
        json={"parent_folder_id": folder["id"]},
        headers=_auth_headers(token),
    )
    assert response.status_code == 400


def test_move_folder_into_own_descendant_rejected(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)

    grandparent = client.post(
        f"/workspaces/{workspace_id}/folders", json={"name": "Grandparent"}, headers=_auth_headers(token)
    ).json()
    parent = client.post(
        f"/workspaces/{workspace_id}/folders",
        json={"name": "Parent", "parent_folder_id": grandparent["id"]},
        headers=_auth_headers(token),
    ).json()
    child = client.post(
        f"/workspaces/{workspace_id}/folders",
        json={"name": "Child", "parent_folder_id": parent["id"]},
        headers=_auth_headers(token),
    ).json()

    # Attempt to move "Grandparent" to become a child of "Child" — its
    # own great-grandchild. Must be rejected as a cycle.
    response = client.patch(
        f"/workspaces/{workspace_id}/folders/{grandparent['id']}",
        json={"parent_folder_id": child["id"]},
        headers=_auth_headers(token),
    )
    assert response.status_code == 400


def test_delete_folder_other_user_blocked(client):
    owner_token = _register_and_login(client, "owner@example.com")
    workspace_id = _create_workspace(client, owner_token)
    folder = client.post(
        f"/workspaces/{workspace_id}/folders", json={"name": "Notes"}, headers=_auth_headers(owner_token)
    ).json()

    attacker_token = _register_and_login(client, "attacker@example.com")
    response = client.delete(
        f"/workspaces/{workspace_id}/folders/{folder['id']}", headers=_auth_headers(attacker_token)
    )
    assert response.status_code == 404


def test_delete_folder_children_cascade(client):
    token = _register_and_login(client, "user@example.com")
    workspace_id = _create_workspace(client, token)
    parent = client.post(
        f"/workspaces/{workspace_id}/folders", json={"name": "Parent"}, headers=_auth_headers(token)
    ).json()
    child = client.post(
        f"/workspaces/{workspace_id}/folders",
        json={"name": "Child", "parent_folder_id": parent["id"]},
        headers=_auth_headers(token),
    ).json()

    client.delete(f"/workspaces/{workspace_id}/folders/{parent['id']}", headers=_auth_headers(token))

    child_check = client.get(
        f"/workspaces/{workspace_id}/folders/{child['id']}", headers=_auth_headers(token)
    )
    assert child_check.status_code == 404