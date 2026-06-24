"""RQ queue wiring for enqueuing background jobs.

The worker process (``python -m app.worker``) runs this same application image so
jobs have full access to the database, object storage, and services. Enqueueing
uses a dedicated Redis connection (RQ pickles payloads, so it must not decode
responses).
"""

from __future__ import annotations

import redis
from rq import Queue

from app.config import settings

QUEUE_DEFAULT = "default"
QUEUE_VERIFICATION = "verification"
QUEUE_WEBHOOKS = "webhooks"
ALL_QUEUES = [QUEUE_DEFAULT, QUEUE_VERIFICATION, QUEUE_WEBHOOKS]

_connection: redis.Redis | None = None


def get_rq_connection() -> redis.Redis:
    global _connection
    if _connection is None:
        _connection = redis.Redis.from_url(settings.redis_url)
    return _connection


def get_queue(name: str = QUEUE_DEFAULT) -> Queue:
    return Queue(name, connection=get_rq_connection())


def enqueue(func, *args, queue: str = QUEUE_DEFAULT, **kwargs):
    """Enqueue a job. ``func`` may be a callable or an importable dotted path."""
    return get_queue(queue).enqueue(func, *args, **kwargs)
