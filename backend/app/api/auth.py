"""
Ember Backend — Auth Routes

    POST /auth/register  -> create a user (+ empty profile), no login yet
    POST /auth/login      -> verify credentials, issue access + refresh tokens
    POST /auth/refresh    -> exchange a valid refresh token for a new pair
                             (rotates the refresh token: the old one is
                             denylisted so it can't be reused)
    POST /auth/logout     -> denylist the current access token
    GET  /auth/me         -> the authenticated user's own info
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, oauth2_scheme
from app.core import security
from app.core.config import settings
from app.core.denylist import add_to_denylist, is_denylisted
from app.core.rate_limit import enforce, rate_limit
from app.core.redis_client import get_redis_client
from app.db.session import get_db
from app.models import Profile, User
from app.schemas.auth import LogoutRequest, RefreshRequest, TokenResponse, UserLogin, UserPublic, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("register", 10, 3600))],
)
def register(payload: UserRegister, db: Session = Depends(get_db)) -> User:
    if not settings.allow_registration:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Registration is closed on this server.")
    existing_user = db.query(User).filter(func.lower(User.email) == payload.email).first()
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    user = User(email=payload.email, hashed_password=security.hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    # Every user gets an (initially empty) profile — see Phase 2.1's
    # separation of auth identity (User) from extended info (Profile).
    profile = Profile(user_id=user.id)
    db.add(profile)
    db.commit()

    return user


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    payload: UserLogin,
    db: Session = Depends(get_db),
    redis_client=Depends(get_redis_client),
) -> TokenResponse:
    # Two limits: per (IP, email) stops guessing one account; per IP alone
    # stops one client spraying many accounts.
    enforce(request, redis_client, "login-acct", payload.email, 8, 300)
    enforce(request, redis_client, "login-ip", "all", 40, 300)
    user = db.query(User).filter(func.lower(User.email) == payload.email).first()

    # Deliberately identical error for "no such user" and "wrong password"
    # — distinguishing them would let an attacker enumerate which emails
    # are registered.
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
    )
    if user is None:
        security.burn_password_check(payload.password)  # equalise timing with the wrong-password path
        raise invalid_credentials
    if not security.verify_password(payload.password, user.hashed_password):
        raise invalid_credentials

    return TokenResponse(
        access_token=security.create_access_token(user.id),
        refresh_token=security.create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse, dependencies=[Depends(rate_limit("refresh", 60, 60))])
def refresh(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
    redis_client=Depends(get_redis_client),
) -> TokenResponse:
    invalid_token = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
    )

    try:
        token_payload = security.decode_token(payload.refresh_token, expected_type="refresh")
    except security.TokenError as exc:
        raise invalid_token from exc

    jti = token_payload["jti"]  # required claim, guaranteed by decode_token
    if is_denylisted(redis_client, jti):
        raise invalid_token

    user = db.get(User, uuid.UUID(token_payload["sub"]))
    if user is None:
        raise invalid_token

    new_access_token = security.create_access_token(user.id)
    new_refresh_token = security.create_refresh_token(user.id)

    # Refresh token rotation: the old refresh token is denylisted so it
    # can't be used again, even though it hasn't expired yet. Without
    # this, a leaked refresh token would remain valid for its full 7-day
    # lifetime even after being used once legitimately.
    add_to_denylist(redis_client, jti, security.seconds_until_expiry(token_payload))

    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: LogoutRequest | None = None,
    token: str = Depends(oauth2_scheme),
    redis_client=Depends(get_redis_client),
) -> None:
    # Revoke the refresh token too (if the client sent it), otherwise a
    # stolen refresh token would keep minting access tokens after logout.
    if payload and payload.refresh_token:
        try:
            refresh_payload = security.decode_token(payload.refresh_token, expected_type="refresh")
            add_to_denylist(redis_client, refresh_payload["jti"], security.seconds_until_expiry(refresh_payload))
        except security.TokenError:
            pass
    try:
        payload = security.decode_token(token, expected_type="access")
    except security.TokenError:
        return  # already invalid/expired — nothing meaningful to revoke

    add_to_denylist(redis_client, payload["jti"], security.seconds_until_expiry(payload))


@router.get("/me", response_model=UserPublic)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user