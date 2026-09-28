"""
Pytest configuration for backend tests.

Sets required environment variables BEFORE the app is imported anywhere,
since Settings() (app/core/config.py) validates them at import time and
would otherwise fail immediately with no DATABASE_URL / JWT_SECRET set.

Uses an in-memory SQLite database for tests rather than a real Neon
connection — keeps tests fast, isolated, and runnable with no network
access or real credentials (useful for CI later, in Phase 10). Local
development still uses the real Neon DATABASE_URL from your own .env;
this only affects the test suite.

Also:
  - overrides the Redis dependency with fakeredis, so the auth denylist
    (logout / refresh rotation) is testable without a real Redis/Memurai
    instance running.
  - points LOCAL_STORAGE_PATH at a temp directory, so tests never write
    into the real backend/storage_data/ used by local dev.
  - overrides the RQ queue with a fake that runs jobs SYNCHRONOUSLY and
    IMMEDIATELY in-process, rather than needing a real `rq worker`
    process running during tests. This is a deliberate simplification:
    production uses real RQ + Redis + a separate worker process: this
    override only affects what the test suite exercises.
"""

import os
import tempfile

_storage_temp_dir = tempfile.mkdtemp(prefix="ember-test-storage-")

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only-not-for-production")
os.environ.setdefault("LOCAL_STORAGE_PATH", _storage_temp_dir)

import fakeredis
import pytest
from fastapi.testclient import TestClient

from app.core.queue import get_queue
from app.core.redis_client import get_redis_client
from app.db.session import Base, engine
from app.main import app
from app.services.search.index_registry import reset_all_indexes
from app import models as _models  # noqa: F401 — registers all models on Base.metadata

_fake_redis_client = fakeredis.FakeRedis(decode_responses=True)


def _get_fake_redis_client():
    return _fake_redis_client


class _SynchronousFakeQueue:
    """Runs enqueued jobs immediately, in-process, instead of pushing
    them to Redis for a separate worker to pick up later."""

    def enqueue(self, func, *args, **kwargs):
        return func(*args, **kwargs)


def _get_fake_queue():
    return _SynchronousFakeQueue()


app.dependency_overrides[get_redis_client] = _get_fake_redis_client
app.dependency_overrides[get_queue] = _get_fake_queue


@pytest.fixture(autouse=True)
def _fresh_schema_and_redis():
    Base.metadata.create_all(engine)
    _fake_redis_client.flushall()
    reset_all_indexes()
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)