"""Redis client used for rate limiting, token revocation, and (later) queues."""

from __future__ import annotations

import redis

from app.config import settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def check_redis() -> None:
    """Raise if Redis is not reachable. Used by the health endpoint."""
    get_redis().ping()
