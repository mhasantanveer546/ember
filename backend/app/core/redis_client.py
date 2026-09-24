"""
Ember Backend — Redis Client

A minimal FastAPI dependency providing a Redis client, used for the JWT
denylist (logout / refresh-token rotation — see security.py and
api/auth.py). Redis is already part of the stack for RQ (Phase 3.5), so
reusing it here avoids introducing a second piece of infrastructure just
for token revocation.

Structured as a dependency (like get_db) rather than a module-level
global specifically so tests can override it with a fake client
(fakeredis) instead of needing a real Redis/Memurai instance running.
"""

import redis

from app.core.config import settings


def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)