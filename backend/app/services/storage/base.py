"""
Ember Backend — Storage Service Interface (Phase 3.2)

Defines the contract every storage backend must implement. Route and
service code depends ONLY on this interface, never on a concrete
backend directly — so swapping local disk for Google Cloud Storage
(Phase 9.3) later means changing which class gets instantiated in one
place (get_storage_service, at the bottom of local_storage.py), not
hunting down file-handling code scattered across the app.
"""

from abc import ABC, abstractmethod


class StorageService(ABC):
    @abstractmethod
    def save(self, key: str, content: bytes) -> None:
        """Store `content` under `key`, creating it or overwriting it."""

    @abstractmethod
    def read(self, key: str) -> bytes:
        """
        Retrieve the content stored under `key`.

        Raises:
            FileNotFoundError: if no object exists under this key.
        """

    @abstractmethod
    def delete(self, key: str) -> None:
        """
        Remove the object stored under `key`. Safe to call even if the
        key doesn't exist (idempotent) — deleting something already
        gone should not be an error.
        """

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Whether an object currently exists under `key`."""