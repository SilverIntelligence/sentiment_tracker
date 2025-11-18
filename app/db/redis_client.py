"""Redis client setup."""

from functools import lru_cache
from typing import Optional

import redis

from app.core.config import get_settings


@lru_cache()
def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    settings = get_settings()
    return redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_keepalive=True,
    )


def get_redis_bytes() -> redis.Redis:
    """Get Redis client for binary data."""
    settings = get_settings()
    return redis.from_url(
        settings.redis_url,
        decode_responses=False,
        socket_connect_timeout=5,
        socket_keepalive=True,
    )


def cache_get(key: str) -> Optional[str]:
    """Get value from cache."""
    r = get_redis()
    return r.get(key)


def cache_set(key: str, value: str, ttl: Optional[int] = None) -> None:
    """Set value in cache with optional TTL."""
    r = get_redis()
    if ttl:
        r.setex(key, ttl, value)
    else:
        r.set(key, value)


def cache_delete(key: str) -> None:
    """Delete key from cache."""
    r = get_redis()
    r.delete(key)
