"""
Ember Backend — API Dependencies

get_current_user is the dependency every protected route will use:

    @router.get("/something")
    def something(current_user: User = Depends(get_current_user)):
        ...

FastAPI's dependency injection resolves the whole chain automatically:
extract the bearer token -> decode/verify it -> check it's not
denylisted -> load the user from the database -> hand it to the route.
Any failure along the way raises 401 before the route body ever runs.
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core import security
from app.core.denylist import is_denylisted
from app.core.redis_client import get_redis_client
from app.db.session import get_db
from app.models import User

# tokenUrl is only used to populate the /docs "Authorize" button correctly;
# it doesn't affect how tokens are actually validated here.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    redis_client=Depends(get_redis_client),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = security.decode_token(token, expected_type="access")
    except security.TokenError as exc:
        raise credentials_exception from exc

    jti = payload.get("jti")
    if jti and is_denylisted(redis_client, jti):
        raise credentials_exception

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    user = db.get(User, uuid.UUID(user_id_str))
    if user is None:
        raise credentials_exception

    return user