"""Idempotent seed script for 5 demo users.

Usage:
    uv run python scripts/seed_demo_users.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path so we can import app
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.features.auth.security import hash_password
from app.features.auth.models import User
from app.features.core.db import _get_async_session

DEMO_USERS = [
    ("alice@example.com", "alice", "Alice", "Password123!"),
    ("bob@example.com", "bob", "Bob", "Password123!"),
    ("carol@example.com", "carol", "Carol", "Password123!"),
    ("dan@example.com", "dan", "Dan", "Password123!"),
    ("erin@example.com", "erin", "Erin", "Password123!"),
]


async def seed() -> None:
    session_factory = _get_async_session()
    async with session_factory() as session:
        inserted = 0
        for email, username, display_name, password in DEMO_USERS:
            # Check if user already exists
            from sqlalchemy import select
            existing = await session.execute(
                select(User).where(User.email == email)
            )
            if existing.scalar_one_or_none() is None:
                user = User(
                    email=email,
                    username=username,
                    display_name=display_name,
                    password_hash=hash_password(password),
                )
                session.add(user)
                inserted += 1
                print(f"  Created: {email} / {username}")

        if inserted:
            await session.commit()
            print(f"\nSeeded {inserted} demo user(s).")
        else:
            print("All demo users already exist — nothing to do.")


if __name__ == "__main__":
    asyncio.run(seed())
