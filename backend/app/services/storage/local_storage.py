"""
Ember Backend — Local Disk Storage (Phase 3.2)

The development-time implementation of StorageService. Stores files
under settings.local_storage_path, using the object key as a relative
path — so a key like "workspaces/abc/documents/def/original.pdf" becomes
a real nested directory structure on disk.

Path traversal is explicitly guarded against: a key containing ".." or
resolving outside the storage root is rejected, rather than trusted.
Object keys in this app are always generated server-side (Phase 3.3+
constructs them from workspace/document IDs), never taken directly from
user input — but validating here costs nothing and removes an entire
class of bug if that assumption is ever violated by a future change.
"""

from pathlib import Path

from app.core.config import settings
from app.services.storage.base import StorageService


class LocalStorageService(StorageService):
    def __init__(self, root: str | None = None) -> None:
        self._root = Path(root or settings.local_storage_path).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        candidate = (self._root / key).resolve()
        if not candidate.is_relative_to(self._root):
            raise ValueError(f"Invalid storage key (path traversal attempt): {key!r}")
        return candidate

    def save(self, key: str, content: bytes) -> None:
        path = self._resolve_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def read(self, key: str) -> bytes:
        path = self._resolve_path(key)
        if not path.is_file():
            raise FileNotFoundError(f"No object found at key: {key!r}")
        return path.read_bytes()

    def delete(self, key: str) -> None:
        path = self._resolve_path(key)
        path.unlink(missing_ok=True)

    def exists(self, key: str) -> bool:
        return self._resolve_path(key).is_file()


def get_storage_service() -> StorageService:
    """
    FastAPI dependency (and general factory) for the active storage
    backend. Currently always local disk — Phase 9.3 will branch on
    settings.storage_backend to return a GCS-backed implementation
    instead, with every caller unchanged.
    """
    return LocalStorageService()