"""
Ember Backend — Document Routes (Phase 3.5)

POST /workspaces/{workspace_id}/documents does only the FAST work:
validate, hash, check duplicate, save raw bytes, create the DB row,
enqueue the background job. Everything slow (extraction, tokenization,
indexing) happens in the worker (workers/document_processing.py),
entirely outside this request/response cycle.
"""

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from rq import Queue
from sqlalchemy.orm import Session

from app.api.deps import get_owned_document, get_owned_workspace
from app.core.queue import get_queue
from app.db.session import get_db
from app.models import Document, DocumentStatus, Folder, Workspace
from app.schemas.document import (
    DocumentMove,
    DocumentResponse,
    DocumentTextResponse,
    DocumentUploadResponse,
)
from app.services.duplicate_detection import find_duplicate_document
from app.services.extraction.extraction_service import extract_text
from app.services.search.index_registry import get_or_create_workspace_index
from app.services.file_validation import FileValidationError, validate_upload
from app.services.hashing import compute_content_hash
from app.services.storage.local_storage import get_storage_service
from app.workers.document_processing import process_document

router = APIRouter(prefix="/workspaces/{workspace_id}/documents", tags=["documents"])


def _require_folder_in_workspace(db: Session, workspace: Workspace, folder_id: uuid.UUID | None) -> None:
    """A folder_id from the client is only trusted if it belongs to THIS workspace."""
    if folder_id is None:
        return
    folder = db.get(Folder, folder_id)
    if folder is None or folder.workspace_id != workspace.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    folder_id: uuid.UUID | None = Form(default=None),
    workspace: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
    queue: Queue = Depends(get_queue),
) -> DocumentUploadResponse:
    _require_folder_in_workspace(db, workspace, folder_id)
    content = await file.read()

    try:
        file_kind = validate_upload(file.filename, content)
    except FileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    content_hash = compute_content_hash(content)

    existing_document = find_duplicate_document(db, workspace.id, content_hash)
    if existing_document is not None:
        return DocumentUploadResponse(document=existing_document, is_duplicate=True)

    document = Document(
        workspace_id=workspace.id,
        folder_id=folder_id,
        owner_id=workspace.owner_id,
        filename=file.filename,
        storage_key="",  # filled in below, once the document's own ID is known
        content_hash=content_hash,
        mime_type=file.content_type or "application/octet-stream",
        file_size_bytes=len(content),
        status=DocumentStatus.UPLOADING,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    storage_key = f"workspaces/{workspace.id}/documents/{document.id}/original.{file_kind}"
    document.storage_key = storage_key
    db.commit()
    db.refresh(document)

    storage = get_storage_service()
    storage.save(storage_key, content)

    # Fast path ends here — everything else happens in the worker.
    queue.enqueue(process_document, str(document.id))

    # Refresh from the database before responding. In production, with a
    # real async worker, this is a no-op most of the time (the worker
    # hasn't started yet) — the response legitimately shows UPLOADING.
    # But with the synchronous test queue (conftest.py), the job has
    # ALREADY run by the time enqueue() returns, in a SEPARATE db
    # session — so without this refresh, the response would show the
    # stale in-memory status from before processing, even though the
    # database row itself was already updated to READY/FAILED.
    db.refresh(document)

    return DocumentUploadResponse(document=document, is_duplicate=False)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document: Document = Depends(get_owned_document)) -> Document:
    return document


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    workspace: Workspace = Depends(get_owned_workspace), db: Session = Depends(get_db)
) -> list[Document]:
    return db.query(Document).filter(Document.workspace_id == workspace.id).all()


def _read_document_text(document: Document) -> str:
    content = get_storage_service().read(document.storage_key)
    file_kind = document.filename.rsplit(".", 1)[-1].lower()
    return extract_text(file_kind, content)


@router.get("/{document_id}/text", response_model=DocumentTextResponse)
def get_document_text(document: Document = Depends(get_owned_document)) -> DocumentTextResponse:
    """Extracted text, for the document preview page (Phase 5.5)."""
    try:
        return DocumentTextResponse(text=_read_document_text(document))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract text from this document.",
        ) from exc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document: Document = Depends(get_owned_document), db: Session = Depends(get_db)
) -> None:
    storage_key = document.storage_key
    get_or_create_workspace_index(document.workspace_id).remove_document(str(document.id))
    db.delete(document)
    db.commit()
    # Autocomplete's Trie can't remove words; the next search sees the READY
    # count changed and rebuilds both index and trie (rebuild_service).
    try:
        get_storage_service().delete(storage_key)
    except Exception:
        pass  # the DB row is the source of truth; an orphaned file is harmless


@router.post("/{document_id}/reindex", response_model=DocumentResponse)
def reindex_document(
    document: Document = Depends(get_owned_document),
    db: Session = Depends(get_db),
    queue: Queue = Depends(get_queue),
) -> Document:
    """Re-run extraction + indexing for one document (Phase 5.5 "re-index")."""
    get_or_create_workspace_index(document.workspace_id).remove_document(str(document.id))
    document.status = DocumentStatus.UPLOADING
    db.commit()
    queue.enqueue(process_document, str(document.id))
    db.refresh(document)
    return document



@router.patch("/{document_id}", response_model=DocumentResponse)
def move_document(
    payload: DocumentMove,
    document: Document = Depends(get_owned_document),
    workspace: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> Document:
    """Move a document into a folder, or back to the workspace root (folder_id null)."""
    _require_folder_in_workspace(db, workspace, payload.folder_id)
    document.folder_id = payload.folder_id
    db.commit()
    db.refresh(document)
    return document
