"""
Ember Backend — Job Queue (Phase 3.5)

FastAPI dependency providing the RQ queue that document processing jobs
are enqueued onto. A separate `rq worker documents` process (not this
FastAPI process) actually executes them — see workers/document_processing.py.

Structured as a dependency (like get_db, get_redis_client) so tests can
override it with a fake that runs jobs synchronously and immediately,
rather than needing a real worker process running during tests.
"""

import redis
from rq import Queue

from app.core.config import settings

QUEUE_NAME = "documents"


def get_queue() -> Queue:
    connection = redis.Redis.from_url(settings.redis_url)
    return Queue(QUEUE_NAME, connection=connection)