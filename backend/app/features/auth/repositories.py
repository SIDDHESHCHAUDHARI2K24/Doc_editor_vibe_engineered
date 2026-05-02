"""User repository using SQLAlchemy async sessions."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email_or_username(self, identifier: str) -> User | None:
        result = await self.session.execute(
            select(User).where((User.email == identifier) | (User.username == identifier))
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def update_last_login(self, user_id: UUID) -> None:
        user = await self.get_by_id(user_id)
        if user:
            user.last_login_at = datetime.now(timezone.utc)
