"""
Ember Backend — Index Metadata Model

Tracks the state of each workspace's search index: what version it's on,
how many documents/terms it covers, and when it was last rebuilt. This
is metadata ABOUT the index (Phase 4.1's rebuild-and-atomic-swap design),
not the index itself — the actual inverted index lives in memory / a
serialized form, built from search_engine.InvertedIndex.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class IndexMetadata(Base):
    __tablename__ = "index_metadata"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    document_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vocabulary_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_built_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="index_metadata")