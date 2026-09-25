"""Tests for app.services.storage.local_storage"""

import tempfile

import pytest

from app.services.storage.local_storage import LocalStorageService


@pytest.fixture
def storage():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield LocalStorageService(root=tmp_dir)


def test_save_and_read_roundtrip(storage):
    storage.save("workspace1/doc1/original.txt", b"hello world")
    assert storage.read("workspace1/doc1/original.txt") == b"hello world"


def test_save_creates_nested_directories(storage):
    storage.save("a/b/c/d/file.txt", b"nested content")
    assert storage.read("a/b/c/d/file.txt") == b"nested content"


def test_save_overwrites_existing_key(storage):
    storage.save("doc.txt", b"version 1")
    storage.save("doc.txt", b"version 2")
    assert storage.read("doc.txt") == b"version 2"


def test_read_nonexistent_key_raises(storage):
    with pytest.raises(FileNotFoundError):
        storage.read("does/not/exist.txt")


def test_exists_true_after_save(storage):
    storage.save("doc.txt", b"content")
    assert storage.exists("doc.txt") is True


def test_exists_false_for_missing_key(storage):
    assert storage.exists("nothing.txt") is False


def test_delete_removes_object(storage):
    storage.save("doc.txt", b"content")
    storage.delete("doc.txt")
    assert storage.exists("doc.txt") is False


def test_delete_nonexistent_key_does_not_raise(storage):
    storage.delete("never/existed.txt")  # should not raise


def test_binary_content_preserved_exactly(storage):
    binary_content = bytes(range(256))
    storage.save("binary.dat", binary_content)
    assert storage.read("binary.dat") == binary_content


def test_two_documents_with_same_filename_do_not_collide(storage):
    # This is the whole point of namespacing keys by document ID rather
    # than storing by original filename.
    storage.save("workspaces/w1/documents/doc-a/notes.pdf", b"user A's file")
    storage.save("workspaces/w1/documents/doc-b/notes.pdf", b"user B's file")

    assert storage.read("workspaces/w1/documents/doc-a/notes.pdf") == b"user A's file"
    assert storage.read("workspaces/w1/documents/doc-b/notes.pdf") == b"user B's file"


def test_path_traversal_attempt_rejected(storage):
    with pytest.raises(ValueError, match="path traversal"):
        storage.save("../../../etc/passwd", b"malicious content")


def test_path_traversal_with_valid_looking_prefix_rejected(storage):
    with pytest.raises(ValueError, match="path traversal"):
        storage.save("workspaces/w1/../../../etc/passwd", b"malicious content")


def test_path_traversal_on_read_rejected(storage):
    with pytest.raises(ValueError, match="path traversal"):
        storage.read("../outside_root.txt")


def test_storage_root_is_created_if_missing():
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        nonexistent_subdir = os.path.join(tmp_dir, "does", "not", "exist", "yet")
        service = LocalStorageService(root=nonexistent_subdir)
        service.save("test.txt", b"content")
        assert service.read("test.txt") == b"content"