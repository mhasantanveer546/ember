"""
Ember Backend — Duplicate Detection (Phase 3.4)

Checks whether a document with the same content already exists WITHIN
ONE WORKSPACE. Deliberately not a global, cross-user check — see phase
notes on why that would be a privacy leak with no real benefit for a
personal knowledge base.
"""

import uuid

from sqlalchemy.orm import Session

from app.models import Document


def find_duplicate_document(
    db: Session, workspace_id: uuid.UUID, content_hash: str
) -> Document | None:
    """
    Return an existing document in `workspace_id` with the same
    `content_hash`, if one exists — otherwise None.

    Intended use (Phase 3.5's upload flow): compute the new upload's
    hash BEFORE storing it or running extraction/indexing, so an exact
    duplicate can be short-circuited early rather than wasting storage
    and processing on content that's already indexed.
    """
    return (
        db.query(Document)
        .filter(Document.workspace_id == workspace_id, Document.content_hash == content_hash)
        .first()
    )