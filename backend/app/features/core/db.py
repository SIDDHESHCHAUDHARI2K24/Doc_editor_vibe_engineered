"""Async SQLAlchemy engine, session factory, and FastAPI dependency."""

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.features.core.settings import get_settings


@lru_cache
def _get_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        pool_size=10,
        max_overflow=20,
        echo=settings.debug,
    )


def _get_async_session() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(_get_engine(), expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields an async SQLAlchemy session."""
    async with _get_async_session()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
