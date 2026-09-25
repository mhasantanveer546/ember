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
from app.models import Document, Folder, User, Workspace

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


def get_owned_workspace(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workspace:
    """
    Load a workspace AND verify the current user owns it, in one place,
    so every route touching a specific workspace uses this instead of
    hand-rolling the check (and risking forgetting it on some route).

    Returns an IDENTICAL 404 whether the workspace doesn't exist at all,
    or exists but belongs to someone else — see phase notes on why a 403
    here would leak information about other users' resources.
    """
    not_found = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    workspace = db.get(Workspace, workspace_id)
    if workspace is None:
        raise not_found
    if workspace.owner_id != current_user.id:
        raise not_found

    return workspace


def get_owned_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Document:
    """
    Load a document AND verify the current user has access to it.

    Deliberately checks WORKSPACE ownership (document.workspace.owner_id),
    not document.owner_id (who uploaded it). document.owner_id is
    attribution — useful for "uploaded by" display — while access control
    belongs at the workspace level, since a future shared-workspace
    feature would give multiple users legitimate access to documents
    none of them personally uploaded. Checking owner_id here would need
    to be revisited the moment sharing exists; checking workspace
    ownership doesn't.
    """
    not_found = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    document = db.get(Document, document_id)
    if document is None:
        raise not_found
    if document.workspace.owner_id != current_user.id:
        raise not_found

    return document

def get_owned_folder(
    folder_id: uuid.UUID,
    workspace: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> Folder:
    """
    Load a folder AND verify it belongs to the workspace already
    authorized by get_owned_workspace (which itself verified the current
    user owns that workspace).

    Checking folder.workspace_id == workspace.id here — not just "does
    this folder exist" — matters: without it, a URL like
    /workspaces/{MY_workspace}/folders/{SOMEONE_ELSES_folder_id} could
    return a folder from a workspace the user doesn't own, as long as
    the folder ID itself was guessable/known, even though the workspace
    in the URL is legitimately theirs.
    """
    not_found = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")

    folder = db.get(Folder, folder_id)
    if folder is None or folder.workspace_id != workspace.id:
        raise not_found

    return folder