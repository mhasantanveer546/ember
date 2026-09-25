"""
Ember Backend — Folder Routes

Nested under a workspace: /workspaces/{workspace_id}/folders/...
get_owned_folder (api/deps.py) ensures a folder_id in the URL actually
belongs to the workspace_id also in the URL — not just that the folder
exists somewhere the user owns.

Two validations beyond plain ownership, both explained inline:
  - a folder's parent_folder_id (on create or move) must belong to the
    SAME workspace — otherwise folders could nest across workspaces
  - moving a folder must not create a cycle (a folder becoming its own
    ancestor) — checked by walking up the proposed new parent's chain
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_owned_folder, get_owned_workspace
from app.db.session import get_db
from app.models import Folder, Workspace
from app.schemas.folder import FolderCreate, FolderResponse, FolderUpdate

router = APIRouter(prefix="/workspaces/{workspace_id}/folders", tags=["folders"])


def _validate_parent_in_same_workspace(
    db: Session, workspace_id: uuid.UUID, parent_folder_id: uuid.UUID | None
) -> None:
    if parent_folder_id is None:
        return
    parent = db.get(Folder, parent_folder_id)
    if parent is None or parent.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="parent_folder_id must reference a folder in the same workspace",
        )


def _would_create_cycle(db: Session, folder_id: uuid.UUID, proposed_parent_id: uuid.UUID) -> bool:
    """
    Walk up from `proposed_parent_id` through its ancestor chain. If
    `folder_id` appears anywhere in that chain (including being the
    proposed parent itself), moving folder_id there would make it its
    own ancestor — a cycle.
    """
    current_id: uuid.UUID | None = proposed_parent_id
    while current_id is not None:
        if current_id == folder_id:
            return True
        current = db.get(Folder, current_id)
        current_id = current.parent_folder_id if current is not None else None
    return False


@router.post("", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
def create_folder(
    payload: FolderCreate,
    workspace: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> Folder:
    _validate_parent_in_same_workspace(db, workspace.id, payload.parent_folder_id)

    folder = Folder(
        workspace_id=workspace.id, name=payload.name, parent_folder_id=payload.parent_folder_id
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@router.get("", response_model=list[FolderResponse])
def list_folders(
    workspace: Workspace = Depends(get_owned_workspace), db: Session = Depends(get_db)
) -> list[Folder]:
    # Flat list — the client reconstructs the tree from parent_folder_id.
    # Returning an already-nested structure would need recursive
    # serialization for no real benefit at this scale.
    return db.query(Folder).filter(Folder.workspace_id == workspace.id).all()


@router.get("/{folder_id}", response_model=FolderResponse)
def get_folder(folder: Folder = Depends(get_owned_folder)) -> Folder:
    return folder


@router.patch("/{folder_id}", response_model=FolderResponse)
def update_folder(
    payload: FolderUpdate,
    workspace: Workspace = Depends(get_owned_workspace),
    folder: Folder = Depends(get_owned_folder),
    db: Session = Depends(get_db),
) -> Folder:
    update_data = payload.model_dump(exclude_unset=True)

    if "parent_folder_id" in update_data:
        new_parent_id = update_data["parent_folder_id"]
        if new_parent_id is not None:
            _validate_parent_in_same_workspace(db, workspace.id, new_parent_id)
            if new_parent_id == folder.id or _would_create_cycle(db, folder.id, new_parent_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot move a folder into itself or one of its own descendants",
                )

    for field, value in update_data.items():
        setattr(folder, field, value)

    db.commit()
    db.refresh(folder)
    return folder


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(folder: Folder = Depends(get_owned_folder), db: Session = Depends(get_db)) -> None:
    # Children folders cascade-delete; documents directly in this folder
    # have their folder_id set to NULL (survive at workspace root) — both
    # per the ondelete behavior defined on the model relationships in
    # Phase 2.1.
    db.delete(folder)
    db.commit()