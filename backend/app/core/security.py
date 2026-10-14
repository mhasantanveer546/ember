"""
Ember Backend — Security Primitives

Password hashing (bcrypt) and JWT creation/verification (PyJWT).

Library choices, since both had valid alternatives:
  - bcrypt (this file) vs passlib[bcrypt]: passlib wraps bcrypt with a
    nicer API but has been effectively unmaintained for years; the
    `bcrypt` package itself is actively maintained and simple enough
    (hash + verify, two functions) that the wrapper isn't worth the risk
    of depending on a stalled project.
  - PyJWT (this file) vs python-jose: python-jose supports more
    algorithms and the broader JOSE spec (JWE encryption, not just JWS
    signing), but Ember only needs HS256 signing — PyJWT covers that
    with a smaller, simpler API and is the more widely used choice for
    this exact use case.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings


MAX_PASSWORD_BYTES = 72  # bcrypt ignores (or, in bcrypt>=5, rejects) anything longer


def password_too_long(password: str) -> bool:
    return len(password.encode("utf-8")) > MAX_PASSWORD_BYTES


def hash_password(password: str) -> str:
    """
    One-way bcrypt hash. Includes a random salt automatically (bcrypt.gensalt()),
    so two users with the same password get different hashes. Cannot be
    reversed to recover the original password, even by us — only checked
    via verify_password().
    """
    hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    if password_too_long(plain_password):
        return False  # can never match a hash we created; avoids a bcrypt ValueError (500)
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


# A real bcrypt hash of a random value, computed once. Login verifies against it
# when the email is unknown so "no such user" costs the same ~100ms as "wrong
# password" — otherwise response time reveals which emails are registered.
_DUMMY_HASH = bcrypt.hashpw(uuid.uuid4().hex.encode(), bcrypt.gensalt()).decode()


def burn_password_check(plain_password: str) -> None:
    verify_password(plain_password, _DUMMY_HASH)


class TokenError(Exception):
    """Raised for any invalid, expired, or wrong-type token."""


def _create_token(subject: uuid.UUID, expires_delta: timedelta, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        # jti (JWT ID): a unique identifier for THIS token, not the user.
        # Needed so logout/refresh-rotation can denylist one specific
        # token without needing to invalidate every token a user holds.
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: uuid.UUID) -> str:
    return _create_token(
        user_id, timedelta(minutes=settings.jwt_access_token_expire_minutes), "access"
    )


def create_refresh_token(user_id: uuid.UUID) -> str:
    return _create_token(
        user_id, timedelta(days=settings.jwt_refresh_token_expire_days), "refresh"
    )


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """
    Verify a token's signature and expiry, and confirm it's the expected
    type (an access token can't be used where a refresh token is
    required, and vice versa — without this check, a short-lived access
    token payload shape being accepted at the refresh endpoint would be
    a real privilege confusion bug).

    Raises TokenError for any failure — invalid signature, expired,
    wrong type — the caller shouldn't need to know which.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "iat", "sub", "jti", "type"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Invalid token") from exc

    try:
        uuid.UUID(str(payload["sub"]))
    except ValueError as exc:
        raise TokenError("Invalid token subject") from exc

    if payload.get("type") != expected_type:
        raise TokenError(f"Expected a {expected_type} token, got {payload.get('type')!r}")

    return payload


def seconds_until_expiry(payload: dict[str, Any]) -> int:
    """
    How many seconds remain until a decoded token's `exp` claim. Used to
    set a denylist entry's TTL to exactly match — no point keeping a
    denylist entry around after the token itself would have expired
    anyway (Redis will evict it automatically once the TTL passes).
    """
    now_ts = datetime.now(timezone.utc).timestamp()
    remaining = int(payload["exp"] - now_ts)
    return max(remaining, 1)  # at least 1 second, avoid a zero/negative TTL