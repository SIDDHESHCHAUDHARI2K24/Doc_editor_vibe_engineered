"""Async PostgreSQL database access helpers.

This module exposes a single `get_db()` async context manager that
wraps an `asyncpg` connection. It is intended to be used with
FastAPI dependencies so that each request can borrow a connection
and return it cleanly after use.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg

from .config import settings


@asynccontextmanager
async def get_db() -> AsyncIterator[asyncpg.Connection]:
    """Yield an `asyncpg.Connection` bound to the configured database URL.

    The connection is opened when entering the context and is always
    closed on exit, even if an error occurs in the calling code.
    """
    conn = await asyncpg.connect(settings.database_url)
    try:
        yield conn
    finally:
        await conn.close()

