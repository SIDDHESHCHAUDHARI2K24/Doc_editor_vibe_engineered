"""Unit tests for Valkey session store."""
import pytest
import redis.asyncio as aioredis
from uuid import uuid4
from app.features.auth.session_store import SessionStore, SessionData
from app.features.core.settings import get_settings


@pytest.fixture
async def store():
    """Create a fresh SessionStore per test to avoid event loop conflicts."""
    settings = get_settings()
    client = aioredis.from_url(
        settings.valkey_url,
        encoding="utf-8",
        decode_responses=False,
    )
    s = SessionStore(client, settings.session_ttl_seconds)
    yield s
    await client.aclose()


@pytest.mark.asyncio
async def test_create_and_get_session(store):
    """Session can be created and retrieved."""
    user_id = uuid4()
    token, data = await store.create(user_id)
    assert isinstance(data, SessionData)
    assert data.user_id == user_id
    assert data.csrf_token
    assert token


@pytest.mark.asyncio
async def test_get_nonexistent_session(store):
    """Getting a non-existent token returns None."""
    result = await store.get("nonexistent-token")
    assert result is None


@pytest.mark.asyncio
async def test_destroy_session(store):
    """Destroying a session removes it."""
    user_id = uuid4()
    token, _ = await store.create(user_id)
    await store.destroy(token)
    result = await store.get(token)
    assert result is None
