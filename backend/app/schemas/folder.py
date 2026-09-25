"""
Ember Backend — Folder Schemas

FolderUpdate's fields are all optional with no default sentinel beyond
None, by design: routes read `payload.model_dump(exclude_unset=True)`
to see exactly which fields the client sent, rather than trusting that
an unset field and an explicit null mean the same thing.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    parent_folder_id: uuid.UUID | None = None


class FolderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    parent_folder_id: uuid.UUID | None = None


class FolderResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    parent_folder_id: uuid.UUID | None
    name: str
    created_at: datetime