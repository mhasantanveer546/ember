"""
Ember Backend — Workspace Routes (minimal, Phase 2.3)

Only create + get-one for now, deliberately minimal — just enough
surface area to prove the ownership pattern (get_owned_workspace) works
end-to-end via real HTTP requests. Full CRUD, folders, and browsing
arrive in Phase 2.4.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_workspace
from app.db.session import get_db
from app.models import IndexMetadata, User, Workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse

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


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(workspace: Workspace = Depends(get_owned_workspace)) -> Workspace:
    return workspace