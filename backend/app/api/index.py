"""
Ember Backend — Index Routes (Phase 4.1)

    POST /workspaces/{workspace_id}/index/rebuild -> trigger a full,
        deterministic rebuild from Postgres + stored files, with
        validate-then-atomic-swap (see rebuild_service.py)
    GET  /workspaces/{workspace_id}/index -> current index stats
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_owned_workspace
from app.db.session import get_db
from app.models import IndexMetadata, Workspace
from app.schemas.index_metadata import IndexMetadataResponse, RebuildResponse
from app.services.search.rebuild_service import rebuild_and_swap

router = APIRouter(prefix="/workspaces/{workspace_id}/index", tags=["index"])


@router.post("/rebuild", response_model=RebuildResponse)
def rebuild_index(
    workspace: Workspace = Depends(get_owned_workspace), db: Session = Depends(get_db)
) -> RebuildResponse:
    result = rebuild_and_swap(db, workspace.id)
    return RebuildResponse(
        document_count=result.document_count,
        vocabulary_size=result.vocabulary_size,
        failed_document_count=len(result.failed_document_ids),
    )


@router.get("", response_model=IndexMetadataResponse)
def get_index_metadata(
    workspace: Workspace = Depends(get_owned_workspace), db: Session = Depends(get_db)
) -> IndexMetadata:
    metadata = (
        db.query(IndexMetadata).filter(IndexMetadata.workspace_id == workspace.id).first()
    )
    if metadata is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Index metadata not found")
    return metadata