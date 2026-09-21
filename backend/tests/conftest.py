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
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only-not-for-production")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)