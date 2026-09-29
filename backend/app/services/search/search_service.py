"""
Ember Backend — Search Service (Phase 4)

Connects a raw query string to Phase 1's real search engine:
InvertedIndex -> candidate gathering -> ranking (score_candidates,
top_k_by_score) -> snippet generation. No FastAPI or database concerns
belong in search_engine itself — this module is the bridge.
"""

import uuid

from sqlalchemy.orm import Session

from app.models import Document
from app.services.extraction.extraction_service import extract_text
from app.services.storage.local_storage import get_storage_service
from search_engine.inverted_index import InvertedIndex
from search_engine.phrase_search import phrase_search
from search_engine.ranking import score_candidates
from search_engine.snippets import generate_snippet
from search_engine.tokenizer import tokenize
from search_engine.top_k import top_k_by_score


def _is_phrase_query(query_text: str) -> bool:
    stripped = query_text.strip()
    return len(stripped) >= 2 and stripped.startswith('"') and stripped.endswith('"')


def _gather_or_candidates(index: InvertedIndex, query_terms: list[str]) -> list[str]:
    """
    Documents containing AT LEAST ONE query term. Ranking (summed TF-IDF
    across query terms) naturally favors documents matching MORE terms —
    there's no need for a separate strict-AND mode; a document matching
    only one of three query terms still shows up, just ranked lower,
    which matches how most people expect search to behave.
    """
    candidate_ids: set[str] = set()
    for term in set(query_terms):
        postings = index.get_postings(term)
        if postings is not None:
            candidate_ids.update(postings.document_ids())
    return list(candidate_ids)


def _generate_snippet_for_document(document: Document, query_terms: list[str]) -> str:
    """
    Re-reads and re-extracts the document's text to build a snippet.
    Deliberately NOT cached/stored anywhere — see phase notes on why
    this trade-off (small redundant work per result, zero duplicated
    storage) is the right one for now. Fails gracefully: a search should
    still return results even if one document's snippet can't be built
    (e.g. its stored file went missing).
    """
    try:
        storage = get_storage_service()
        content = storage.read(document.storage_key)
        file_kind = document.filename.rsplit(".", 1)[-1].lower()
        text = extract_text(file_kind, content)
        return generate_snippet(text, query_terms)
    except Exception:
        return ""


def search_workspace(
    db: Session,
    index: InvertedIndex,
    workspace_id: uuid.UUID,
    query_text: str,
    limit: int,
) -> tuple[list[dict], bool]:
    """
    Run a search against one workspace's index.

    Returns:
        (results, is_phrase_search) — results is a list of dicts with
        document_id, filename, score, snippet, ready to build
        SearchResultItem objects from; is_phrase_search reports which
        mode was used, so the API response can be transparent about it.
    """
    is_phrase = _is_phrase_query(query_text)
    inner_query = query_text.strip()[1:-1] if is_phrase else query_text
    query_terms = tokenize(inner_query)

    if not query_terms:
        return [], is_phrase

    if is_phrase:
        candidate_ids = phrase_search(index, query_terms)
    else:
        candidate_ids = _gather_or_candidates(index, query_terms)

    if not candidate_ids:
        return [], is_phrase

    scored = score_candidates(index, query_terms, candidate_ids)
    ranked = top_k_by_score(scored, limit)

    results = []
    for document_id_str, score in ranked:
        document = db.get(Document, uuid.UUID(document_id_str))
        # Safety net, not expected in normal operation: the index only
        # ever contains documents from this workspace (Phase 3.5 keys
        # indexes per-workspace), so this should never actually trigger.
        if document is None or document.workspace_id != workspace_id:
            continue

        results.append(
            {
                "document_id": document.id,
                "filename": document.filename,
                "score": score,
                "snippet": _generate_snippet_for_document(document, query_terms),
            }
        )

    return results, is_phrase