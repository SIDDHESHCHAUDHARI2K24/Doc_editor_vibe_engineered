"""Low-level SQL helpers for auth-related tables.

This module defines the SQL schema and helper functions for the
`users` and `sessions` tables using asyncpg connections.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import asyncpg


USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

SESSIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);
"""


async def ensure_auth_schema(conn: asyncpg.Connection) -> None:
    """Create the `users` and `sessions` tables if they do not exist."""
    await conn.execute(USERS_TABLE_SQL)
    await conn.execute(SESSIONS_TABLE_SQL)


async def create_user(
    conn: asyncpg.Connection, *, email: str, password_hash: str
) -> asyncpg.Record:
    """Insert a new user row and return it."""
    return await conn.fetchrow(
        "INSERT INTO users (email, password_hash) VALUES ($1, $2) "
        "RETURNING id, email, created_at",
        email,
        password_hash,
    )


async def get_user_by_email(
    conn: asyncpg.Connection, *, email: str
) -> Optional[asyncpg.Record]:
    """Return a user row for the given email, or None."""
    return await conn.fetchrow(
        "SELECT id, email, password_hash, created_at FROM users WHERE email = $1",
        email,
    )


async def update_user_password(
    conn: asyncpg.Connection, *, email: str, new_password_hash: str
) -> int:
    """Update a user's password hash, returning the number of affected rows."""
    result = await conn.execute(
        "UPDATE users SET password_hash = $1 WHERE email = $2",
        new_password_hash,
        email,
    )
    # asyncpg returns strings like 'UPDATE 1'
    return int(result.split()[-1])


async def create_session(
    conn: asyncpg.Connection,
    *,
    user_id: int,
    session_token: str,
    ttl_minutes: int = 60 * 24,
) -> asyncpg.Record:
    """Create a new session row for the user and return it."""
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
    return await conn.fetchrow(
        "INSERT INTO sessions (user_id, session_token, expires_at) "
        "VALUES ($1, $2, $3) "
        "RETURNING id, user_id, session_token, created_at, expires_at",
        user_id,
        session_token,
        expires_at,
    )


async def get_session(
    conn: asyncpg.Connection, *, session_token: str
) -> Optional[asyncpg.Record]:
    """Return a session row by token, or None."""
    return await conn.fetchrow(
        "SELECT id, user_id, session_token, created_at, expires_at "
        "FROM sessions WHERE session_token = $1",
        session_token,
    )


async def delete_session(
    conn: asyncpg.Connection, *, session_token: str
) -> int:
    """Delete a session by token, returning the number of affected rows."""
    result = await conn.execute(
        "DELETE FROM sessions WHERE session_token = $1", session_token
    )
    return int(result.split()[-1])

