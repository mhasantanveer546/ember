"""
Ember Backend — Workspace Schemas (minimal, Phase 2.3)

Just enough to test the authorization pattern end-to-end via real HTTP
requests. Full CRUD (list, update, delete, folders) is Phase 2.4.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class WorkspaceResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    created_at: datetime