"""
Ember Backend — Workspace Routes

Full CRUD: create, list (current user's own), get-one, update (rename),
delete (cascades to folders/documents/index_metadata per Phase 2.1).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_workspace
from app.db.session import get_db
from app.models import IndexMetadata, User, Workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    payload: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workspace:
    workspace = Workspace(owner_id=current_user.id, name=payload.name)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    # Every workspace gets an index_metadata row eagerly (1:1, Phase 2.1),
    # tracked from creation even though the index itself isn't built
    # until documents exist and Phase 4 runs.
    db.add(IndexMetadata(workspace_id=workspace.id))
    db.commit()

    return workspace


@router.get("", response_model=list[WorkspaceResponse])
def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Workspace]:
    return (
        db.query(Workspace)
        .filter(Workspace.owner_id == current_user.id)
        .order_by(Workspace.created_at.desc())
        .all()
    )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(workspace: Workspace = Depends(get_owned_workspace)) -> Workspace:
    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(
    payload: WorkspaceUpdate,
    workspace: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> Workspace:
    # exclude_unset=True: only fields the client actually sent are
    # applied — a PATCH with an empty body changes nothing, rather than
    # resetting fields to their schema defaults.
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workspace, field, value)

    db.commit()
    db.refresh(workspace)
    return workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> None:
    # Cascades to folders, documents, and index_metadata per the
    # ondelete="CASCADE" constraints defined in Phase 2.1's models.
    db.delete(workspace)
    db.commit()