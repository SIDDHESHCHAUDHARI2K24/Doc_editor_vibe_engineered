"""Valkey (Redis-compatible) client and connection management."""

import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.features.core.settings import get_settings

settings = get_settings()

valkey_client: Redis = aioredis.from_url(
    settings.valkey_url,
    encoding="utf-8",
    decode_responses=False,
)


async def ping() -> bool:
    """Ping the Valkey server to verify connectivity."""
    return await valkey_client.ping()


async def get_valkey() -> Redis:
    """FastAPI dependency that returns the Valkey client."""
    return valkey_client
