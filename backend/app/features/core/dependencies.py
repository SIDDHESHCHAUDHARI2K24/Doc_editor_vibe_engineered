"""FastAPI dependency helpers for the `core` feature.

Re-exports reusable dependency callables for injecting configuration,
database sessions, and Valkey connections into route handlers.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_db
from .settings import Settings, get_settings
from .valkey import get_valkey


def get_settings_dep() -> Settings:
    """Return the global `Settings` instance as a dependency."""
    return get_settings()


async def get_db_dep() -> AsyncSession:
    """Yield an async SQLAlchemy session."""
    async for session in get_db():
        yield session


SettingsDep = Depends(get_settings_dep)
DbDep = Depends(get_db_dep)
ValkeyDep = Depends(get_valkey)

from app.features.auth.session_store import session_store as _session_store

SessionStoreDep = Depends(lambda: _session_store)
