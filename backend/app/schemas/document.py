"""Ember Backend — Document Schemas (Phase 3.5)"""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models import DocumentStatus


class DocumentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    folder_id: uuid.UUID | None
    owner_id: uuid.UUID
    filename: str
    mime_type: str
    file_size_bytes: int
    status: DocumentStatus
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    is_duplicate: bool


class DocumentTextResponse(BaseModel):
    text: str



class DocumentMove(BaseModel):
    folder_id: uuid.UUID | None = None
