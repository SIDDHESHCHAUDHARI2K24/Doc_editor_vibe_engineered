"""Tests for Valkey-backed rate limiter."""
import uuid

import pytest
import redis.asyncio as aioredis

from app.features.core.rate_limit import RateLimiter


@pytest.fixture
async def rl():
    client = aioredis.from_url("redis://localhost:6379/0", decode_responses=False)
    limiter = RateLimiter(client)
    yield limiter
    await client.aclose()


@pytest.mark.asyncio
async def test_bucket_allows_requests(rl: RateLimiter):
    """Within the window, up to max requests are allowed."""
    key = f"test:rate:{uuid.uuid4().hex}"
    for i in range(5):
        result = await rl.check(key, 5, 60)
        assert result.allowed
        assert result.remaining == 4 - i


@pytest.mark.asyncio
async def test_bucket_blocks_excess(rl: RateLimiter):
    """Exceeding max requests blocks."""
    key = f"test:rate:{uuid.uuid4().hex}"
    for _ in range(5):
        await rl.check(key, 5, 60)
    result = await rl.check(key, 5, 60)
    assert not result.allowed
    assert result.remaining == 0
    assert result.retry_after > 0


@pytest.mark.asyncio
async def test_different_keys_independent(rl: RateLimiter):
    """Separate keys have separate rate limits."""
    key_a = f"test:rate:{uuid.uuid4().hex}"
    key_b = f"test:rate:{uuid.uuid4().hex}"

    await rl.check(key_a, 5, 60)
    await rl.check(key_a, 5, 60)

    result_b = await rl.check(key_b, 5, 60)
    assert result_b.allowed
    assert result_b.remaining == 4


@pytest.mark.asyncio
async def test_result_dataclass():
    """RateLimitResult is correctly constructed."""
    from app.features.core.rate_limit import RateLimitResult

    r = RateLimitResult(allowed=True, remaining=3, retry_after=0.0)
    assert r.allowed is True
    assert r.remaining == 3
    assert r.retry_after == 0.0
