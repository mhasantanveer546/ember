"""Phase 4.2: search must only touch documents that match the query."""

import uuid

from app.services.search import search_service
from app.services.search.index_registry import get_or_create_workspace_index
from search_engine.tokenizer import tokenize


def test_search_scores_only_matching_documents_not_whole_collection(db_session, monkeypatch):
    workspace_id = uuid.uuid4()
    index = get_or_create_workspace_index(workspace_id)
    for i in range(500):
        index.add_document(str(uuid.uuid4()), tokenize("alpha beta gamma delta"))
    index.add_document(str(uuid.uuid4()), tokenize("alpha uniqueterm gamma"))

    scored_counts = []
    original = search_service.score_candidates

    def spy(idx, terms, candidate_ids, *args, **kwargs):
        scored_counts.append(len(candidate_ids))
        return original(idx, terms, candidate_ids, *args, **kwargs)

    monkeypatch.setattr(search_service, "score_candidates", spy)
    search_service.search_workspace(db_session, index, workspace_id, "uniqueterm", 10)

    assert scored_counts == [1]  # 1 of 501 documents scored, not all 501
