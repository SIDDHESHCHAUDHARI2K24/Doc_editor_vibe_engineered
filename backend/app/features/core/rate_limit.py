"""Token-bucket rate limiter backed by Valkey atomic Lua scripting."""

from dataclasses import dataclass

from fastapi import Request
from redis.asyncio import Redis

from app.features.core.settings import get_settings
from app.features.core.valkey import valkey_client

LUA_SCRIPT = """
local key = KEYS[1]
local max_requests = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local current = redis.call('INCR', key)
if current == 1 then
    redis.call('EXPIRE', key, window)
end
local ttl = redis.call('TTL', key)
if ttl < 0 then ttl = 0 end
if current > max_requests then
    return {0, 0, ttl}
else
    return {1, max_requests - current, 0}
end
"""


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after: float  # seconds until next allowed request


class RateLimiter:
    def __init__(self, valkey: Redis) -> None:
        self.valkey = valkey
        self._script = valkey.register_script(LUA_SCRIPT)

    async def check(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> RateLimitResult:
        allowed_raw, remaining_raw, retry_after_raw = await self._script(
            keys=[key],
            args=[max_requests, window_seconds],
        )
        return RateLimitResult(
            allowed=bool(allowed_raw),
            remaining=int(remaining_raw),
            retry_after=float(retry_after_raw),
        )


rate_limiter = RateLimiter(valkey_client)


def get_client_ip(request: Request) -> str:
    """Extract the client IP, honoring X-Forwarded-For only when trusted proxy is enabled."""
    settings = get_settings()
    if settings.trusted_proxy:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
