"""Tests for app.api.auth — register, login, refresh, logout, me."""

from app.core import security


def _register(client, email="hasan@example.com", password="correcthorsebattery"):
    return client.post("/auth/register", json={"email": email, "password": password})


def _login(client, email="hasan@example.com", password="correcthorsebattery"):
    return client.post("/auth/login", json={"email": email, "password": password})


def test_register_creates_user(client):
    response = _register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "hasan@example.com"
    assert "id" in body
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_email_rejected(client):
    _register(client)
    response = _register(client)
    assert response.status_code == 409


def test_register_password_too_short_rejected(client):
    response = client.post(
        "/auth/register", json={"email": "short@example.com", "password": "short"}
    )
    assert response.status_code == 422


def test_register_invalid_email_rejected(client):
    response = client.post(
        "/auth/register", json={"email": "not-an-email", "password": "correcthorsebattery"}
    )
    assert response.status_code == 422


def test_password_is_hashed_not_stored_plaintext(client):
    _register(client)
    from app.db.session import SessionLocal
    from app.models import User

    db = SessionLocal()
    user = db.query(User).filter(User.email == "hasan@example.com").first()
    db.close()

    assert user.hashed_password != "correcthorsebattery"
    assert security.verify_password("correcthorsebattery", user.hashed_password)


def test_login_succeeds_with_correct_credentials(client):
    _register(client)
    response = _login(client)
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_fails_with_wrong_password(client):
    _register(client)
    response = _login(client, password="wrongpassword")
    assert response.status_code == 401


def test_login_fails_for_nonexistent_user(client):
    response = _login(client, email="ghost@example.com")
    assert response.status_code == 401


def test_login_error_identical_for_wrong_password_and_missing_user(client):
    # Prevents email enumeration: both failure modes must look the same.
    _register(client)
    wrong_password_response = _login(client, password="wrongpassword")
    missing_user_response = _login(client, email="ghost@example.com")

    assert wrong_password_response.status_code == missing_user_response.status_code
    assert wrong_password_response.json() == missing_user_response.json()


def test_me_requires_authentication(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user_with_valid_token(client):
    _register(client)
    tokens = _login(client).json()

    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "hasan@example.com"


def test_me_rejects_invalid_token(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_me_rejects_refresh_token_used_as_access_token(client):
    # A refresh token has a different `type` claim — using it where an
    # access token is expected must be rejected, not silently accepted.
    _register(client)
    tokens = _login(client).json()

    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
    )
    assert response.status_code == 401


def test_refresh_issues_new_token_pair(client):
    _register(client)
    tokens = _login(client).json()

    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]


def test_refresh_old_token_cannot_be_reused_after_rotation(client):
    _register(client)
    tokens = _login(client).json()

    first_refresh = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert first_refresh.status_code == 200

    # Reusing the SAME (now-rotated) refresh token must fail.
    second_attempt = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert second_attempt.status_code == 401


def test_refresh_rejects_access_token_used_as_refresh_token(client):
    _register(client)
    tokens = _login(client).json()

    response = client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert response.status_code == 401


def test_logout_denylists_access_token(client):
    _register(client)
    tokens = _login(client).json()
    access_token = tokens["access_token"]

    logout_response = client.post(
        "/auth/logout", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert logout_response.status_code == 204

    # The same access token must no longer work after logout.
    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_response.status_code == 401


def test_logout_without_token_does_not_error(client):
    response = client.post("/auth/logout")
    # No Authorization header at all -> OAuth2PasswordBearer itself
    # rejects with 401 before the route body runs.
    assert response.status_code == 401