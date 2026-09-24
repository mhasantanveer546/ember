"""
Ember Backend — Models Package

Importing every model here ensures they're all registered on
Base.metadata (app/db/session.py) by the time Alembic (or anything else)
inspects it. Without this, a model file that's never imported anywhere
would be invisible to Alembic's autogenerate, silently missing from
migrations.
"""

from app.models.document import Document, DocumentStatus
from app.models.folder import Folder
from app.models.index_metadata import IndexMetadata
from app.models.profile import Profile
from app.models.search_history import SearchHistory
from app.models.user import User
from app.models.workspace import Workspace

__all__ = [
    "Document",
    "DocumentStatus",
    "Folder",
    "IndexMetadata",
    "Profile",
    "SearchHistory",
    "User",
    "Workspace",
]