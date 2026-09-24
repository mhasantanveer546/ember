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

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, oauth2_scheme
from app.core import security
from app.core.denylist import add_to_denylist, is_denylisted
from app.core.redis_client import get_redis_client
from app.db.session import get_db
from app.models import Profile, User
from app.schemas.auth import RefreshRequest, TokenResponse, UserLogin, UserPublic, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)) -> User:
    existing_user = db.query(User).filter(User.email == payload.email).first()
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
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()

    # Deliberately identical error for "no such user" and "wrong password"
    # — distinguishing them would let an attacker enumerate which emails
    # are registered.
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
    )
    if user is None or not security.verify_password(payload.password, user.hashed_password):
        raise invalid_credentials

    return TokenResponse(
        access_token=security.create_access_token(user.id),
        refresh_token=security.create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
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

    jti = token_payload.get("jti")
    if jti and is_denylisted(redis_client, jti):
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
    if jti:
        add_to_denylist(redis_client, jti, security.seconds_until_expiry(token_payload))

    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    token: str = Depends(oauth2_scheme),
    redis_client=Depends(get_redis_client),
) -> None:
    try:
        payload = security.decode_token(token, expected_type="access")
    except security.TokenError:
        return  # already invalid/expired — nothing meaningful to revoke

    jti = payload.get("jti")
    if jti:
        add_to_denylist(redis_client, jti, security.seconds_until_expiry(payload))


@router.get("/me", response_model=UserPublic)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user