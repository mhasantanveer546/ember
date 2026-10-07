"""
Ember Backend — S3-compatible object storage (Phase 9.3 groundwork)

Production implementation of StorageService for any S3-compatible service:
Supabase Storage, Backblaze B2, Cloudflare R2, AWS S3, MinIO, Google Cloud
Storage (interoperability mode), ...

Why this exists: free app hosts (Render, Fly, Railway) give each deploy an
EPHEMERAL disk, so files saved with LocalStorageService vanish on restart.
Documents must live in durable object storage; the database stores only the
object key (see docs/DEPLOYMENT.md).

Path-style addressing is forced because it works with every provider above.
"""

from functools import lru_cache

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings
from app.services.storage.base import StorageService

_MISSING_CODES = {"404", "NoSuchKey", "NotFound"}


@lru_cache(maxsize=1)
def _default_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url or None,
        region_name=settings.s3_region or None,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


class S3StorageService(StorageService):
    def __init__(self, client=None, bucket: str | None = None) -> None:
        self._client = client or _default_client()
        self._bucket = bucket or settings.s3_bucket

    @staticmethod
    def _validate_key(key: str) -> None:
        # Keys are generated server-side, but never trust that: no traversal-looking keys.
        if not key or key.startswith("/") or ".." in key.split("/"):
            raise ValueError(f"Invalid storage key: {key!r}")

    def save(self, key: str, content: bytes) -> None:
        self._validate_key(key)
        self._client.put_object(Bucket=self._bucket, Key=key, Body=content)

    def read(self, key: str) -> bytes:
        self._validate_key(key)
        try:
            return self._client.get_object(Bucket=self._bucket, Key=key)["Body"].read()
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in _MISSING_CODES:
                raise FileNotFoundError(f"No object found at key: {key!r}") from exc
            raise

    def delete(self, key: str) -> None:
        self._validate_key(key)
        self._client.delete_object(Bucket=self._bucket, Key=key)  # S3 delete is already idempotent

    def exists(self, key: str) -> bool:
        self._validate_key(key)
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in _MISSING_CODES:
                return False
            raise
