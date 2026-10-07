"""Deployment-readiness tests: S3 storage backend, production config checks, closing registration."""

import io

import pytest
from botocore.exceptions import ClientError
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.services.storage.s3_storage import S3StorageService


class FakeS3:
    """Minimal in-memory S3 client that raises the same ClientErrors boto3 does."""

    def __init__(self):
        self.objects = {}

    def put_object(self, Bucket, Key, Body):
        self.objects[(Bucket, Key)] = Body

    def get_object(self, Bucket, Key):
        if (Bucket, Key) not in self.objects:
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)])}

    def head_object(self, Bucket, Key):
        if (Bucket, Key) not in self.objects:
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")

    def delete_object(self, Bucket, Key):
        self.objects.pop((Bucket, Key), None)


def test_s3_roundtrip_exists_and_idempotent_delete():
    s = S3StorageService(client=FakeS3(), bucket="b")
    key = "workspaces/w/documents/d/original.txt"
    assert not s.exists(key)
    s.save(key, b"hello")
    assert s.exists(key) and s.read(key) == b"hello"
    s.delete(key)
    s.delete(key)  # already gone: must not raise
    assert not s.exists(key)


def test_s3_missing_key_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        S3StorageService(client=FakeS3(), bucket="b").read("nope")


@pytest.mark.parametrize("bad", ["", "/abs", "a/../b", ".."])
def test_s3_rejects_suspicious_keys(bad):
    with pytest.raises(ValueError):
        S3StorageService(client=FakeS3(), bucket="b").save(bad, b"x")


BASE = dict(database_url="postgresql://u:p@h/db", jwt_secret="x" * 40)


def test_production_requires_strong_secret_and_real_cors():
    with pytest.raises(ValidationError):
        Settings(**{**BASE, "jwt_secret": "short"}, environment="production", cors_origins="https://a.app")
    with pytest.raises(ValidationError):
        Settings(**BASE, environment="production", cors_origins="http://localhost:3000")
    Settings(**BASE, environment="production", cors_origins="https://a.app")  # valid


def test_s3_backend_requires_credentials():
    with pytest.raises(ValidationError):
        Settings(**BASE, storage_backend="s3")
    Settings(**BASE, storage_backend="s3", s3_bucket="b", s3_access_key_id="k", s3_secret_access_key="s")


def test_registration_can_be_closed(client, monkeypatch):
    monkeypatch.setattr(settings, "allow_registration", False)
    r = client.post("/auth/register", json={"email": "late@example.com", "password": "correcthorsebattery"})
    assert r.status_code == 403
    assert "closed" in r.json()["detail"].lower()
