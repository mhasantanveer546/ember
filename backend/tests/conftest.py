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

Also overrides the Redis dependency with fakeredis, so the auth denylist
(logout / refresh rotation) is testable without a real Redis/Memurai
instance running.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only-not-for-production")

import fakeredis
import pytest
from fastapi.testclient import TestClient

from app.core.redis_client import get_redis_client
from app.db.session import Base, engine
from app.main import app
from app import models as _models  # noqa: F401 — registers all models on Base.metadata

_fake_redis_client = fakeredis.FakeRedis(decode_responses=True)


def _get_fake_redis_client():
    return _fake_redis_client


app.dependency_overrides[get_redis_client] = _get_fake_redis_client


@pytest.fixture(autouse=True)
def _fresh_schema_and_redis():
    Base.metadata.create_all(engine)
    _fake_redis_client.flushall()
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)