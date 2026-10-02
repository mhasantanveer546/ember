"""
Ember Backend — document-processing worker (cross-platform).

Run from the REPO ROOT (same folder as the API, so both read the same .env
and the same storage folder):

    python backend/scripts/run_worker.py

Why this exists: RQ's default `rq worker` forks a child process for every
job, and Windows has no fork(). This uses RQ's SimpleWorker (runs each job
in the worker process itself) with a thread-based timeout instead of
Unix signals, so it works on Windows, macOS and Linux.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))              # search_engine package
sys.path.insert(0, str(ROOT / "backend"))  # app package

import redis  # noqa: E402
from rq import Queue, SimpleWorker  # noqa: E402
from rq.timeouts import TimerDeathPenalty  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.queue import QUEUE_NAME  # noqa: E402


class PortableWorker(SimpleWorker):
    death_penalty_class = TimerDeathPenalty


if __name__ == "__main__":
    connection = redis.Redis.from_url(settings.redis_url)
    connection.ping()  # fail fast with a clear error if Redis/Memurai isn't running
    print(f"Ember worker listening on queue '{QUEUE_NAME}' ({settings.redis_url}) ...")
    PortableWorker([Queue(QUEUE_NAME, connection=connection)], connection=connection).work()
