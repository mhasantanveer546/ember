"""Ember Backend — Search Schemas (Phase 4)"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=100)


class SearchResultItem(BaseModel):
    document_id: uuid.UUID
    filename: str
    score: float
    snippet: str


class SearchResponse(BaseModel):
    query: str
    is_phrase_search: bool
    results: list[SearchResultItem]


class AutocompleteResponse(BaseModel):
    suggestions: list[str]


class SearchHistoryItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    query_text: str
    created_at: datetime


class SearchHistoryResponse(BaseModel):
    history: list[SearchHistoryItem]
    