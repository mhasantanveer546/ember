"""GCS backend against an in-memory fake bucket (no network, no credentials)."""

import pytest
from google.api_core.exceptions import NotFound

from app.core.config import Settings
from app.services.storage.gcs_storage import GCSStorageService


class FakeBlob:
    def __init__(self, store, key):
        self.store, self.key = store, key

    def upload_from_string(self, content, content_type=None):
        self.store[self.key] = content

    def download_as_bytes(self):
        if self.key not in self.store:
            raise NotFound("nope")
        return self.store[self.key]

    def delete(self):
        if self.key not in self.store:
            raise NotFound("nope")
        del self.store[self.key]

    def exists(self):
        return self.key in self.store


class FakeBucket:
    def __init__(self):
        self.store = {}

    def blob(self, key):
        return FakeBlob(self.store, key)


def test_roundtrip_exists_and_idempotent_delete():
    s = GCSStorageService(FakeBucket())
    s.save("workspaces/a/documents/b/original.txt", b"hello")
    assert s.exists("workspaces/a/documents/b/original.txt")
    assert s.read("workspaces/a/documents/b/original.txt") == b"hello"
    s.delete("workspaces/a/documents/b/original.txt")
    s.delete("workspaces/a/documents/b/original.txt")
    assert not s.exists("workspaces/a/documents/b/original.txt")


def test_missing_key_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        GCSStorageService(FakeBucket()).read("nope/x.txt")


@pytest.mark.parametrize("bad", ["../etc/passwd", "/abs", "a/../../b", ""])
def test_rejects_suspicious_keys(bad):
    with pytest.raises(ValueError):
        GCSStorageService(FakeBucket()).save(bad, b"x")


def test_gcs_backend_requires_bucket():
    base = dict(database_url="postgresql://u:p@h/db", jwt_secret="x" * 40)
    with pytest.raises(ValueError):
        Settings(**base, storage_backend="gcs")
    assert Settings(**base, storage_backend="gcs", gcs_bucket="b").storage_backend == "gcs"
