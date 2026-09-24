"""
Tests for app.models — relationships, cascade deletes, and constraints.

Uses the app's own engine, which conftest.py has already pointed at an
in-memory SQLite database via DATABASE_URL. Tables are created fresh
before each test and dropped after, so tests don't leak state into
each other.
"""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.session import Base, SessionLocal, engine
from app.models import (
    Document,
    DocumentStatus,
    Folder,
    IndexMetadata,
    Profile,
    SearchHistory,
    User,
    Workspace,
)


@pytest.fixture(autouse=True)
def _fresh_schema():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _make_user(db, email="test@example.com") -> User:
    user = User(email=email, hashed_password="not_a_real_hash")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_create_user_and_profile(db):
    user = _make_user(db)
    profile = Profile(user_id=user.id, display_name="Hasan")
    db.add(profile)
    db.commit()
    db.refresh(user)

    assert user.profile.display_name == "Hasan"
    assert profile.user.email == "test@example.com"


def test_email_uniqueness_enforced(db):
    _make_user(db, email="dupe@example.com")
    duplicate = User(email="dupe@example.com", hashed_password="x")
    db.add(duplicate)
    with pytest.raises(IntegrityError):
        db.commit()


def test_workspace_belongs_to_owner(db):
    user = _make_user(db)
    workspace = Workspace(owner_id=user.id, name="My Notes")
    db.add(workspace)
    db.commit()
    db.refresh(user)

    assert workspace.owner.email == user.email
    assert workspace in user.workspaces


def test_folder_nesting(db):
    user = _make_user(db)
    workspace = Workspace(owner_id=user.id, name="Workspace")
    db.add(workspace)
    db.commit()

    parent = Folder(workspace_id=workspace.id, name="Parent")
    db.add(parent)
    db.commit()

    child = Folder(workspace_id=workspace.id, name="Child", parent_folder_id=parent.id)
    db.add(child)
    db.commit()
    db.refresh(parent)

    assert child.parent.name == "Parent"
    assert parent.children[0].name == "Child"


def test_document_belongs_to_workspace_and_optional_folder(db):
    user = _make_user(db)
    workspace = Workspace(owner_id=user.id, name="Workspace")
    db.add(workspace)
    db.commit()

    folder = Folder(workspace_id=workspace.id, name="Notes")
    db.add(folder)
    db.commit()

    document = Document(
        workspace_id=workspace.id,
        folder_id=folder.id,
        owner_id=user.id,
        filename="networking.pdf",
        storage_key="workspaces/x/networking.pdf",
        content_hash="a" * 64,
        mime_type="application/pdf",
        file_size_bytes=1024,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    assert document.status == DocumentStatus.UPLOADING  # default
    assert document.folder.name == "Notes"
    assert document.workspace.name == "Workspace"


def test_document_root_level(db):
    user = _make_user(db)
    workspace = Workspace(owner_id=user.id, name="Workspace")
    db.add(workspace)
    db.commit()

    document = Document(
        workspace_id=workspace.id,
        folder_id=None,
        owner_id=user.id,
        filename="root_doc.txt",
        storage_key="workspaces/x/root_doc.txt",
        content_hash="b" * 64,
        mime_type="text/plain",
        file_size_bytes=100,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    assert document.folder is None
    assert document.folder_id is None


def test_deleting_workspace_cascades_to_folders_and_documents(db):
    user = _make_user(db)
    workspace = Workspace(owner_id=user.id, name="Workspace")
    db.add(workspace)
    db.commit()

    folder = Folder(workspace_id=workspace.id, name="Notes")
    db.add(folder)
    db.commit()

    document = Document(
        workspace_id=workspace.id,
        folder_id=folder.id,
        owner_id=user.id,
        filename="doc.txt",
        storage_key="key",
        content_hash="c" * 64,
        mime_type="text/plain",
        file_size_bytes=10,
    )
    db.add(document)
    db.commit()

    workspace_id = workspace.id
    db.delete(workspace)
    db.commit()

    assert db.get(Folder, folder.id) is None
    assert db.get(Document, document.id) is None
    assert db.get(Workspace, workspace_id) is None


def test_deleting_folder_sets_document_folder_id_null(db):
    user = _make_user(db)
    workspace = Workspace(owner_id=user.id, name="Workspace")
    db.add(workspace)
    db.commit()

    folder = Folder(workspace_id=workspace.id, name="Notes")
    db.add(folder)
    db.commit()

    document = Document(
        workspace_id=workspace.id,
        folder_id=folder.id,
        owner_id=user.id,
        filename="doc.txt",
        storage_key="key",
        content_hash="d" * 64,
        mime_type="text/plain",
        file_size_bytes=10,
    )
    db.add(document)
    db.commit()
    document_id = document.id

    db.delete(folder)
    db.commit()

    refreshed_document = db.get(Document, document_id)
    assert refreshed_document is not None  # document survives folder deletion
    assert refreshed_document.folder_id is None


def test_deleting_user_cascades_to_workspaces_and_profile(db):
    user = _make_user(db)
    profile = Profile(user_id=user.id, display_name="Hasan")
    workspace = Workspace(owner_id=user.id, name="Workspace")
    db.add_all([profile, workspace])
    db.commit()

    user_id = user.id
    profile_id = profile.id
    workspace_id = workspace.id

    db.delete(user)
    db.commit()

    assert db.get(User, user_id) is None
    assert db.get(Profile, profile_id) is None
    assert db.get(Workspace, workspace_id) is None


def test_search_history_records_query(db):
    user = _make_user(db)
    workspace = Workspace(owner_id=user.id, name="Workspace")
    db.add(workspace)
    db.commit()

    entry = SearchHistory(user_id=user.id, workspace_id=workspace.id, query_text="congestion control")
    db.add(entry)
    db.commit()
    db.refresh(entry)

    assert entry.query_text == "congestion control"
    assert entry.user.email == user.email


def test_search_history_workspace_optional(db):
    user = _make_user(db)
    entry = SearchHistory(user_id=user.id, workspace_id=None, query_text="global search")
    db.add(entry)
    db.commit()
    db.refresh(entry)

    assert entry.workspace_id is None


def test_index_metadata_one_per_workspace(db):
    user = _make_user(db)
    workspace = Workspace(owner_id=user.id, name="Workspace")
    db.add(workspace)
    db.commit()

    metadata = IndexMetadata(workspace_id=workspace.id, version=1, document_count=0, vocabulary_size=0)
    db.add(metadata)
    db.commit()

    duplicate_metadata = IndexMetadata(workspace_id=workspace.id, version=2)
    db.add(duplicate_metadata)
    with pytest.raises(IntegrityError):
        db.commit()


def test_document_status_defaults_to_uploading(db):
    user = _make_user(db)
    workspace = Workspace(owner_id=user.id, name="Workspace")
    db.add(workspace)
    db.commit()

    document = Document(
        workspace_id=workspace.id,
        owner_id=user.id,
        filename="f.txt",
        storage_key="k",
        content_hash="e" * 64,
        mime_type="text/plain",
        file_size_bytes=1,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    assert document.status == DocumentStatus.UPLOADING