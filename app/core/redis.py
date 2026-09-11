import redis.asyncio as redis
from redis.asyncio.client import Redis

from app.core.config import settings

# None when Redis is globally disabled (settings.redis.enabled: false) — the
# client is never constructed in that case, so nothing can accidentally open
# a connection a deployment deliberately chose not to have.
redis_client: Redis | None = (
    redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    if settings.redis.enabled and settings.REDIS_URL
    else None
)


async def get_redis() -> Redis | None:
    return redis_client
