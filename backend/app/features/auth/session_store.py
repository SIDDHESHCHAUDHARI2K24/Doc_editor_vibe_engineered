import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from pydantic import BaseModel
from redis.asyncio import Redis

from app.features.core.settings import get_settings
from app.features.core.valkey import valkey_client


class SessionData(BaseModel):
    user_id: UUID
    created_at: datetime
    expires_at: datetime
    csrf_token: str


class SessionStore:
    def __init__(self, valkey: Redis, ttl_seconds: int):
        self.valkey = valkey
        self.ttl_seconds = ttl_seconds

    def _key(self, token: str) -> str:
        return f"session:{token}"

    async def create(self, user_id: UUID) -> tuple[str, SessionData]:
        token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self.ttl_seconds)
        data = SessionData(
            user_id=user_id,
            created_at=now,
            expires_at=expires_at,
            csrf_token=csrf_token,
        )
        await self.valkey.set(
            self._key(token),
            data.model_dump_json(),
            ex=self.ttl_seconds,
        )
        return token, data

    async def get(self, token: str) -> SessionData | None:
        raw = await self.valkey.get(self._key(token))
        if raw is None:
            return None
        return SessionData.model_validate_json(raw.decode("utf-8"))

    async def destroy(self, token: str) -> None:
        await self.valkey.delete(self._key(token))

    async def touch(self, token: str) -> None:
        await self.valkey.expire(self._key(token), self.ttl_seconds)


class InMemorySessionStore:
    """Session store backed by a plain dict — for tests and development."""

    def __init__(self, ttl_seconds: int):
        self._store: dict[str, SessionData] = {}
        self.ttl_seconds = ttl_seconds

    async def create(self, user_id: UUID) -> tuple[str, SessionData]:
        token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self.ttl_seconds)
        data = SessionData(
            user_id=user_id,
            created_at=now,
            expires_at=expires_at,
            csrf_token=csrf_token,
        )
        self._store[token] = data
        return token, data

    async def get(self, token: str) -> SessionData | None:
        data = self._store.get(token)
        if data is None:
            return None
        if data.expires_at < datetime.now(timezone.utc):
            del self._store[token]
            return None
        return data

    async def destroy(self, token: str) -> None:
        self._store.pop(token, None)

    async def touch(self, token: str) -> None:
        pass


settings = get_settings()
if settings.environment == "test":
    session_store = InMemorySessionStore(settings.session_ttl_seconds)
else:
    session_store = SessionStore(valkey_client, settings.session_ttl_seconds)
