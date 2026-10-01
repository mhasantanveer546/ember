"""Ember Backend — Index Metadata Schemas (Phase 4.1)"""

from datetime import datetime

from pydantic import BaseModel


class IndexMetadataResponse(BaseModel):
    model_config = {"from_attributes": True}

    version: int
    document_count: int
    vocabulary_size: int
    last_built_at: datetime | None


class RebuildResponse(BaseModel):
    document_count: int
    vocabulary_size: int
    failed_document_count: int