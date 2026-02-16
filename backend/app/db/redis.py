"""Redis connection management with connection pooling."""

import asyncio
import logging
from typing import TYPE_CHECKING

import redis.asyncio as aioredis
from redis.asyncio import ConnectionPool
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff

from app.core.config import settings

if TYPE_CHECKING:
    from redis.asyncio import Redis
else:
    Redis = object  # type: ignore[misc,assignment]

logger = logging.getLogger(__name__)

redis_client: "Redis | None" = None
redis_pool: ConnectionPool | None = None
_redis_lock = asyncio.Lock()


async def get_redis() -> "Redis":
    """Get Redis client instance with connection pooling."""
    global redis_client, redis_pool

    async with _redis_lock:
        if redis_client is None:
            try:
                redis_pool = ConnectionPool.from_url(
                    str(settings.REDIS_URL),
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=100,
                    socket_timeout=10.0,
                    socket_connect_timeout=5.0,
                    socket_keepalive=True,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )

                retry = Retry(ExponentialBackoff(), retries=3)
                redis_client = aioredis.Redis(
                    connection_pool=redis_pool,
                    retry=retry,
                    retry_on_error=[
                        aioredis.ConnectionError,
                        aioredis.TimeoutError,
                    ],
                )

                await redis_client.ping()
                logger.info("Redis connection pool initialized successfully")

            except Exception:
                logger.exception("Failed to initialize Redis connection")
                raise

    return redis_client


async def close_redis() -> None:
    """Close Redis connection and connection pool."""
    global redis_client, redis_pool

    if redis_client:
        try:
            await redis_client.close()
            logger.info("Redis client closed")
        except Exception:
            logger.exception("Error closing Redis client")
        finally:
            redis_client = None

    if redis_pool:
        try:
            await redis_pool.disconnect()
            logger.info("Redis connection pool closed")
        except Exception:
            logger.exception("Error closing Redis pool")
        finally:
            redis_pool = None
