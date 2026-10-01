"""
Ember Backend — Search Routes (Phase 4)

    POST /workspaces/{workspace_id}/search               -> run a search
    GET  /workspaces/{workspace_id}/search/autocomplete   -> prefix suggestions
    GET  /workspaces/{workspace_id}/search/history        -> this user's recent searches in this workspace
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_workspace
from app.db.session import get_db
from app.models import SearchHistory, User, Workspace
from app.schemas.search import (
    AutocompleteResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SearchHistoryResponse,
)
from app.services.search.index_registry import get_or_create_workspace_index
from app.services.search.rebuild_service import ensure_index_fresh
from app.services.search.search_service import search_workspace
from app.services.search.trie_registry import get_or_create_workspace_trie

router = APIRouter(prefix="/workspaces/{workspace_id}/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(
    payload: SearchRequest,
    workspace: Workspace = Depends(get_owned_workspace),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchResponse:
    ensure_index_fresh(db, workspace.id)
    index = get_or_create_workspace_index(workspace.id)
    results, is_phrase = search_workspace(db, index, workspace.id, payload.query, payload.limit)

    # Record search history regardless of whether it returned results —
    # a zero-result search is still a search worth remembering (e.g. for
    # "did I already look for this?" later).
    db.add(SearchHistory(user_id=current_user.id, workspace_id=workspace.id, query_text=payload.query))
    db.commit()

    return SearchResponse(
        query=payload.query,
        is_phrase_search=is_phrase,
        results=[SearchResultItem(**result) for result in results],
    )


@router.get("/autocomplete", response_model=AutocompleteResponse)
def autocomplete(
    prefix: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=10, ge=1, le=25),
    workspace: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> AutocompleteResponse:
    ensure_index_fresh(db, workspace.id)
    trie = get_or_create_workspace_trie(workspace.id)
    suggestions = trie.suggest(prefix.lower(), limit=limit)
    return AutocompleteResponse(suggestions=suggestions)


@router.get("/history", response_model=SearchHistoryResponse)
def get_search_history(
    workspace: Workspace = Depends(get_owned_workspace),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
) -> SearchHistoryResponse:
    entries = (
        db.query(SearchHistory)
        .filter(
            SearchHistory.user_id == current_user.id,
            SearchHistory.workspace_id == workspace.id,
        )
        .order_by(SearchHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    return SearchHistoryResponse(history=entries)