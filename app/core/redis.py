import redis.asyncio as redis
from redis.asyncio.client import Redis

from app.core.config import settings

# Without an explicit timeout, a Redis that's down or unreachable (wrong
# port, firewall, container not started) doesn't fail fast — confirmed
# directly on this stack: a single connection attempt to a closed port took
# ~4 seconds end to end, not the near-instant OS-level "connection refused"
# you'd expect, because redis-py has no default connect timeout at all.
# Every caller that already catches connection errors and falls back
# (RateLimitMiddleware's try/except, CacheBackend's fail-open get/set/delete)
# would otherwise eat that multi-second stall on every single call while
# Redis is unavailable, in production exactly as much as in tests.
_CONNECT_TIMEOUT_SECONDS = 2.0

# None when Redis is globally disabled (settings.redis.enabled: false) — the
# client is never constructed in that case, so nothing can accidentally open
# a connection a deployment deliberately chose not to have.
redis_client: Redis | None = (
    redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=_CONNECT_TIMEOUT_SECONDS,
        socket_timeout=_CONNECT_TIMEOUT_SECONDS,
    )
    if settings.redis.enabled and settings.REDIS_URL
    else None
)


async def get_redis() -> Redis | None:
    return redis_client
