"""Redis-backed fixed-window rate limiting for auth and API-key endpoints."""

from __future__ import annotations

from app.errors import RateLimitedError
from app.redis_client import get_redis


def enforce_rate_limit(*, key: str, limit: int, window_seconds: int = 60) -> None:
    """Increment the counter for ``key`` and raise 429 if it exceeds ``limit``.

    Uses INCR + EXPIRE so the window resets automatically. Fails open only if
    Redis is unreachable would be unsafe, so instead we surface the error: the
    health endpoint already guarantees Redis is up for a healthy deployment.
    """
    redis = get_redis()
    full_key = f"ratelimit:{key}"
    current = redis.incr(full_key)
    if current == 1:
        redis.expire(full_key, window_seconds)
    if current > limit:
        raise RateLimitedError(
            f"Rate limit of {limit} requests per {window_seconds}s exceeded."
        )
