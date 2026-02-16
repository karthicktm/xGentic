"""Rate limiting configuration."""

import logging

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

logger = logging.getLogger(__name__)

# Legacy decorator-based rate limiter
limiter = Limiter(key_func=get_remote_address)


class RateLimit:
    """Dependency-based rate limiter using Redis."""

    def __init__(self, max_requests: int = 0, window_seconds: int = 60) -> None:
        self.max_requests = max_requests or settings.RATE_LIMIT_PER_MINUTE
        self.window_seconds = window_seconds

    async def check(self, key: str) -> bool:
        """Check if request is within rate limit."""
        from app.db.redis import get_redis

        try:
            redis = await get_redis()
            cache_key = f"ratelimit:{key}"
            current = await redis.incr(cache_key)

            if current == 1:
                await redis.expire(cache_key, self.window_seconds)

            return current <= self.max_requests
        except Exception:
            logger.exception("Rate limit check failed")
            return True  # Fail open
