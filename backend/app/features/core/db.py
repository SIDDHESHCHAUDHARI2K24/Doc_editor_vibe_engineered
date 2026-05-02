"""Async SQLAlchemy engine, session factory, and FastAPI dependency."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.features.core.settings import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,
)

async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields an async SQLAlchemy session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
