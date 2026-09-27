"""Tests for app.services.hashing and app.services.duplicate_detection"""

import hashlib

import pytest

from app.db.session import SessionLocal
from app.models import Document, DocumentStatus, User, Workspace
from app.services.hashing import compute_content_hash
from app.services.duplicate_detection import find_duplicate_document


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# --- Hashing ---


def test_known_sha256_vector_empty_string():
    # Standard reference vector: SHA-256 of empty bytes is well-known and
    # documented — confirms we're really computing SHA-256, not some
    # other algorithm or a mis-encoded variant.
    assert compute_content_hash(b"") == hashlib.sha256(b"").hexdigest()


def test_known_sha256_vector_abc():
    assert compute_content_hash(b"abc") == hashlib.sha256(b"abc").hexdigest()


def test_hash_is_deterministic():
    content = b"Congestion control notes"
    assert compute_content_hash(content) == compute_content_hash(content)


def test_different_content_produces_different_hash():
    hash_a = compute_content_hash(b"Content A")
    hash_b = compute_content_hash(b"Content B")
    assert hash_a != hash_b


def test_single_byte_change_produces_completely_different_hash():
    # Avalanche effect: a one-character difference shouldn't produce a
    # visually similar hash.
    hash_a = compute_content_hash(b"Congestion control notes")
    hash_b = compute_content_hash(b"Congestion control notex")
    assert hash_a != hash_b
    # Not a rigorous statistical test, but confirms the hashes don't
    # share an unexpectedly long common prefix (which would suggest
    # something other than a real cryptographic hash was used).
    common_prefix_length = len(
        [c1 for c1, c2 in zip(hash_a, hash_b) if c1 == c2]
    )
    assert common_prefix_length < 8


def test_hash_output_length_is_64_hex_characters():
    result = compute_content_hash(b"any content")
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


def test_empty_and_nonempty_content_hash_differently():
    assert compute_content_hash(b"") != compute_content_hash(b"a")


# --- Duplicate detection ---


def _make_user_and_workspace(db, email="user@example.com") -> tuple:
    user = User(email=email, hashed_password="x")
    db.add(user)
    db.commit()
    workspace = Workspace(owner_id=user.id, name="Workspace")
    db.add(workspace)
    db.commit()
    return user.id, workspace.id


def _make_document(db, workspace_id, owner_id, content_hash, filename="doc.txt") -> Document:
    document = Document(
        workspace_id=workspace_id,
        owner_id=owner_id,
        filename=filename,
        storage_key=f"key/{filename}",
        content_hash=content_hash,
        mime_type="text/plain",
        file_size_bytes=10,
        status=DocumentStatus.READY,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def test_find_duplicate_returns_match_when_hash_exists(db):
    owner_id, workspace_id = _make_user_and_workspace(db)
    existing = _make_document(db, workspace_id, owner_id, content_hash="a" * 64)

    result = find_duplicate_document(db, workspace_id, "a" * 64)
    assert result is not None
    assert result.id == existing.id


def test_find_duplicate_returns_none_when_no_match(db):
    _owner_id, workspace_id = _make_user_and_workspace(db)
    _make_document(db, workspace_id, _owner_id, content_hash="a" * 64)

    result = find_duplicate_document(db, workspace_id, "b" * 64)
    assert result is None


def test_find_duplicate_scoped_to_workspace_not_global(db):
    # Two DIFFERENT workspaces (could be different users) both happen to
    # contain a document with the identical content hash. A lookup
    # scoped to workspace A must not "leak" workspace B's document.
    owner_id, workspace_a = _make_user_and_workspace(db, "a@example.com")
    _, workspace_b = _make_user_and_workspace(db, "b@example.com")

    _make_document(db, workspace_a, owner_id, content_hash="c" * 64, filename="a_doc.txt")
    doc_in_b = _make_document(db, workspace_b, owner_id, content_hash="c" * 64, filename="b_doc.txt")

    result_for_a = find_duplicate_document(db, workspace_a, "c" * 64)
    result_for_b = find_duplicate_document(db, workspace_b, "c" * 64)

    assert result_for_a.filename == "a_doc.txt"
    assert result_for_b.id == doc_in_b.id
    assert result_for_a.id != result_for_b.id


def test_find_duplicate_empty_workspace_returns_none(db):
    _owner_id, workspace_id = _make_user_and_workspace(db)

    result = find_duplicate_document(db, workspace_id, "a" * 64)
    assert result is None