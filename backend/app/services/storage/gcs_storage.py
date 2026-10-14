"""
Ember Backend — Google Cloud Storage (Phase 9.3)

StorageService on a GCS bucket. Authentication is Application Default
Credentials: on Cloud Run that is the service's own service account, so no
key file or HMAC secret exists anywhere to leak. Grant that account
`roles/storage.objectAdmin` on the ONE bucket (not the project).

Buckets are flat: "folders" are just "/" characters inside object keys, which
is why keys like workspaces/<id>/documents/<id>/original.pdf work unchanged.
Files are only ever served through the API after an ownership check; if direct
downloads are ever added, use short-lived V4 signed URLs (blob.generate_signed_url)
rather than making the bucket public.
"""

from functools import lru_cache

from app.core.config import settings
from app.services.storage.base import StorageService


@lru_cache(maxsize=1)
def _default_bucket():
    from google.cloud import storage  # imported lazily: only needed when STORAGE_BACKEND=gcs

    return storage.Client().bucket(settings.gcs_bucket)


class GCSStorageService(StorageService):
    def __init__(self, bucket=None) -> None:
        self._bucket = bucket if bucket is not None else _default_bucket()

    @staticmethod
    def _validate_key(key: str) -> None:
        if not key or key.startswith("/") or ".." in key.split("/"):
            raise ValueError(f"Invalid storage key: {key!r}")

    def save(self, key: str, content: bytes) -> None:
        self._validate_key(key)
        self._bucket.blob(key).upload_from_string(content, content_type="application/octet-stream")

    def read(self, key: str) -> bytes:
        self._validate_key(key)
        from google.api_core.exceptions import NotFound

        try:
            return self._bucket.blob(key).download_as_bytes()
        except NotFound as exc:
            raise FileNotFoundError(f"No object found at key: {key!r}") from exc

    def delete(self, key: str) -> None:
        self._validate_key(key)
        from google.api_core.exceptions import NotFound

        try:
            self._bucket.blob(key).delete()
        except NotFound:
            pass  # idempotent

    def exists(self, key: str) -> bool:
        self._validate_key(key)
        return bool(self._bucket.blob(key).exists())
