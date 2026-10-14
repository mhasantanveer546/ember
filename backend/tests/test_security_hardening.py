"""Phase 8 security hardening tests."""

import io
import time
import zipfile

import jwt
import pytest

from app.core.config import settings
from app.services.file_validation import FileValidationError, sanitize_filename, validate_upload

PW = "correcthorsebattery"


def _reg(client, email="a@example.com", pw=PW):
    return client.post("/auth/register", json={"email": email, "password": pw})


def _login(client, email="a@example.com", pw=PW):
    return client.post("/auth/login", json={"email": email, "password": pw})


def _tokens(client, email="a@example.com"):
    _reg(client, email)
    return _login(client, email).json()


# ---- headers / size guard -------------------------------------------------
def test_security_headers_present(client):
    r = client.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "default-src 'none'" in r.headers["content-security-policy"]
    assert r.headers["cache-control"] == "no-store"


def test_oversized_body_rejected_early(client):
    r = client.post("/auth/login", content=b"x", headers={"content-length": str(100 * 1024 * 1024)})
    assert r.status_code == 413


# ---- rate limiting --------------------------------------------------------
def test_login_rate_limited_per_account(client):
    _reg(client)
    codes = [_login(client, pw="wrong-password-1").status_code for _ in range(10)]
    assert codes[:8] == [401] * 8
    assert 429 in codes[8:]
    r = _login(client, pw="wrong-password-1")
    assert r.status_code == 429 and int(r.headers["retry-after"]) > 0


def test_login_limit_is_per_account_not_global(client):
    _reg(client, "a@example.com")
    _reg(client, "b@example.com")
    for _ in range(9):
        _login(client, "a@example.com", "wrong-password-1")
    assert _login(client, "b@example.com").status_code == 200


def test_register_rate_limited(client):
    codes = [_reg(client, f"u{i}@example.com").status_code for i in range(12)]
    assert codes[:10] == [201] * 10
    assert codes[10] == 429


def test_rate_limit_can_be_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_enabled", False)
    _reg(client)
    assert all(_login(client, pw="wrong-password-1").status_code == 401 for _ in range(12))


def test_rate_limiter_fails_open_without_redis(client):
    from app.core import rate_limit

    class Broken:
        def incr(self, *_):
            raise ConnectionError("down")

    assert rate_limit.hit(Broken(), "x", "y", 1, 60) == (True, 0)


# ---- auth -----------------------------------------------------------------
def test_email_is_case_insensitive(client):
    assert _reg(client, "Mixed@Example.com").status_code == 201
    assert _reg(client, "mixed@example.com").status_code == 409
    assert _login(client, "MIXED@example.COM").status_code == 200


def test_long_password_is_rejected_not_500(client):
    assert _reg(client, pw="é" * 40).status_code == 422  # 80 bytes
    assert _login(client, pw="x" * 100).status_code == 401


@pytest.mark.parametrize("pw", ["aaaaaaaaaa", "        ", "short"])
def test_weak_passwords_rejected(client, pw):
    assert _reg(client, pw=pw).status_code == 422


def test_unknown_email_and_wrong_password_look_identical(client):
    _reg(client)
    a = _login(client, "nobody@example.com")
    b = _login(client, pw="wrong-password-1")
    assert (a.status_code, a.json()) == (b.status_code, b.json())


def test_token_with_garbage_subject_is_401_not_500(client):
    bad = jwt.encode(
        {"sub": "not-a-uuid", "type": "access", "iat": int(time.time()), "exp": int(time.time()) + 60, "jti": "j"},
        settings.jwt_secret, algorithm=settings.jwt_algorithm,
    )
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {bad}"}).status_code == 401
    assert client.post("/auth/refresh", json={"refresh_token": bad}).status_code == 401


def test_token_missing_required_claims_rejected(client):
    no_jti = jwt.encode(
        {"sub": "7f8a2c9e-0000-4000-8000-000000000000", "type": "access", "exp": int(time.time()) + 60},
        settings.jwt_secret, algorithm=settings.jwt_algorithm,
    )
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {no_jti}"}).status_code == 401


def test_alg_none_token_rejected(client):
    forged = jwt.encode({"sub": "x", "type": "access"}, key=None, algorithm="none")
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_logout_revokes_access_and_refresh(client):
    t = _tokens(client)
    h = {"Authorization": f"Bearer {t['access_token']}"}
    assert client.post("/auth/logout", json={"refresh_token": t["refresh_token"]}, headers=h).status_code == 204
    assert client.get("/auth/me", headers=h).status_code == 401
    assert client.post("/auth/refresh", json={"refresh_token": t["refresh_token"]}).status_code == 401


def test_logout_without_body_still_works(client):
    t = _tokens(client)
    h = {"Authorization": f"Bearer {t['access_token']}"}
    assert client.post("/auth/logout", headers=h).status_code == 204
    assert client.get("/auth/me", headers=h).status_code == 401


def test_refresh_token_cannot_be_reused(client):
    t = _tokens(client)
    assert client.post("/auth/refresh", json={"refresh_token": t["refresh_token"]}).status_code == 200
    assert client.post("/auth/refresh", json={"refresh_token": t["refresh_token"]}).status_code == 401


def test_access_token_cannot_be_used_as_refresh(client):
    t = _tokens(client)
    assert client.post("/auth/refresh", json={"refresh_token": t["access_token"]}).status_code == 401


# ---- docs exposure --------------------------------------------------------
def test_docs_disabled_in_production(monkeypatch):
    import importlib

    import app.main as main

    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "enable_docs", None)
    reloaded = importlib.reload(main)
    try:
        assert reloaded.app.docs_url is None and reloaded.app.openapi_url is None
    finally:
        monkeypatch.undo()
        importlib.reload(main)


# ---- uploads --------------------------------------------------------------
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("../../etc/passwd", "passwd"),
        ("C:\\Users\\x\\notes.txt", "notes.txt"),
        ("a\x00b\nc.txt", "abc.txt"),
        ("report\u202egnp.exe", "reportgnp.exe"),
        ("   ...  ", "untitled"),
        (None, "untitled"),
        ("", "untitled"),
    ],
)
def test_sanitize_filename(raw, expected):
    assert sanitize_filename(raw) == expected


def test_sanitize_filename_bounds_length_and_keeps_extension():
    out = sanitize_filename("a" * 500 + ".pdf")
    assert len(out) <= 200 and out.endswith(".pdf")


def _zip(entries: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in entries.items():
            z.writestr(name, data)
    return buf.getvalue()


def test_docx_zip_bomb_rejected():
    bomb = _zip({"word/document.xml": b"0" * (60 * 1024 * 1024)})
    assert len(bomb) < 1024 * 1024
    with pytest.raises(FileValidationError, match="unsafe size"):
        validate_upload("x.docx", bomb)


def test_docx_path_traversal_entry_rejected():
    evil = _zip({"word/document.xml": b"<x/>", "../../evil.txt": b"hi"})
    with pytest.raises(FileValidationError, match="unsafe"):
        validate_upload("x.docx", evil)


def test_upload_filename_is_sanitized_end_to_end(client):
    t = _tokens(client)
    h = {"Authorization": f"Bearer {t['access_token']}"}
    ws = client.post("/workspaces", json={"name": "w"}, headers=h).json()["id"]
    r = client.post(
        f"/workspaces/{ws}/documents",
        files={"file": ("../../evil/notes.txt", b"hello hardening world", "text/plain")},
        headers=h,
    )
    assert r.status_code == 201
    assert r.json()["document"]["filename"] == "notes.txt"


def test_upload_over_limit_without_content_length_rejected(client, monkeypatch):
    from app.services import file_validation

    monkeypatch.setattr(file_validation, "MAX_FILE_SIZE_BYTES", 1000)
    import app.api.documents as docs

    monkeypatch.setattr(docs, "MAX_FILE_SIZE_BYTES", 1000)
    t = _tokens(client)
    h = {"Authorization": f"Bearer {t['access_token']}"}
    ws = client.post("/workspaces", json={"name": "w"}, headers=h).json()["id"]
    r = client.post(
        f"/workspaces/{ws}/documents", files={"file": ("big.txt", b"a b " * 1000, "text/plain")}, headers=h
    )
    assert r.status_code == 400 and "maximum" in r.json()["detail"]
