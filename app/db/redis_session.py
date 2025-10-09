from typing import Any, AsyncGenerator

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=10,  # Adjust based on expected load
    decode_responses=True  # Automatically decode responses from bytes to UTF-8 strings
)


async def get_redis_client() -> AsyncGenerator[Redis, Any]:
    client = redis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.close()