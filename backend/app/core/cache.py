"""Redis caching utilities and decorators."""

import hashlib
import json
import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from app.db.redis import get_redis

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def _generate_cache_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    """Generate a unique cache key from function arguments."""
    key_data = {
        "args": [str(arg) for arg in args if not callable(arg)],
        "kwargs": {k: str(v) for k, v in kwargs.items() if not callable(v)},
    }
    key_string = json.dumps(key_data, sort_keys=True)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()  # noqa: S324
    return f"{prefix}:{key_hash}"


async def cache_get(key: str) -> Any | None:
    """Get value from cache."""
    try:
        redis = await get_redis()
        value = await redis.get(key)
        if value is not None:
            return json.loads(value)
        return None
    except Exception:
        logger.exception("Error getting from cache key '%s'", key)
        return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    """Set value in cache with TTL."""
    try:
        redis = await get_redis()
        serialized = json.dumps(value, default=str)
        await redis.setex(key, ttl, serialized)
        return True
    except Exception:
        logger.exception("Error setting cache key '%s'", key)
        return False


async def cache_delete(key: str) -> bool:
    """Delete value from cache."""
    try:
        redis = await get_redis()
        await redis.delete(key)
        return True
    except Exception:
        logger.exception("Error deleting cache key '%s'", key)
        return False


async def cache_invalidate(pattern: str) -> int:
    """Invalidate all cache keys matching a pattern."""
    try:
        redis = await get_redis()
        keys = []
        async for key in redis.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            deleted: int = await redis.delete(*keys)
            return deleted
        return 0
    except Exception:
        logger.exception("Error invalidating cache pattern '%s'", pattern)
        return 0


def cached(
    prefix: str,
    ttl: int = 300,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Decorator to cache async function results."""

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            cache_key = _generate_cache_key(prefix, *args, **kwargs)
            cached_value = await cache_get(cache_key)
            if cached_value is not None:
                return cached_value  # type: ignore[no-any-return]
            result = await func(*args, **kwargs)
            await cache_set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator
