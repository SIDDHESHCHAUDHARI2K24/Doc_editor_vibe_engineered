"""FastAPI dependency helpers for the `core` feature.

Re-exports reusable dependency callables for injecting configuration
and database connections into route handlers.
"""

from collections.abc import AsyncIterator

from fastapi import Depends

from .database import get_db
from .settings import Settings, get_settings


def get_settings_dep() -> Settings:
    """Return the global `Settings` instance as a dependency."""
    return get_settings()


async def get_db_dep() -> AsyncIterator:
    """Yield a database connection as a dependency using `get_db()`."""
    async with get_db() as conn:
        yield conn


SettingsDep = Depends(get_settings_dep)
DbDep = Depends(get_db_dep)
