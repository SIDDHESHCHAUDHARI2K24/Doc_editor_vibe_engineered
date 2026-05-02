"""Auth service layer."""
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Response

from app.features.auth.repositories import UserRepository
from app.features.auth.security import hash_password, verify_password
from app.features.auth.session_store import session_store
from app.features.core.errors import AuthenticationException, ConflictException
from app.features.core.settings import get_settings

settings = get_settings()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def login(self, identifier: str, password: str, response: Response) -> dict:
        user = await self.repo.get_by_email_or_username(identifier)
        if user is None:
            try:
                verify_password(password, "$2b$10$invalidhashplaceholder0000000000000000000000000000")
            except ValueError:
                pass
            raise AuthenticationException(message="Invalid credentials")
        if not verify_password(password, user.password_hash):
            raise AuthenticationException(message="Invalid credentials")
        token, session_data = await session_store.create(user.id)
        await self.repo.update_last_login(user.id)
        response.set_cookie(
            key=settings.session_cookie_name,
            value=token,
            httponly=True,
            samesite=settings.session_cookie_samesite,
            secure=settings.session_cookie_secure,
            path="/",
        )
        response.set_cookie(
            key="csrf_token",
            value=session_data.csrf_token,
            samesite=settings.session_cookie_samesite,
            secure=settings.session_cookie_secure,
            path="/",
        )
        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "display_name": user.display_name,
                "created_at": user.created_at.isoformat(),
            }
        }

    async def logout(self, token: str | None, response: Response) -> dict:
        if token:
            await session_store.destroy(token)
        response.delete_cookie(settings.session_cookie_name, path="/")
        response.delete_cookie("csrf_token", path="/")
        return {"status": "ok"}

    async def get_me(self, user_model) -> dict:
        return {
            "user": {
                "id": str(user_model.id),
                "email": user_model.email,
                "username": user_model.username,
                "display_name": user_model.display_name,
                "created_at": user_model.created_at.isoformat(),
            },
            "csrf_token": "",
        }

    async def register(self, email: str, username: str, password: str) -> dict:
        from datetime import datetime, timezone

        existing = await self.repo.get_by_email(email)
        if existing:
            raise ConflictException(message="Email already registered")
        existing = await self.repo.get_by_email_or_username(username)
        if existing:
            raise ConflictException(message="Username already taken")
        from app.features.auth.models import User

        now = datetime.now(timezone.utc)
        user = User(
            email=email,
            username=username,
            display_name=username,
            password_hash=hash_password(password),
            created_at=now,
            updated_at=now,
        )
        self.repo.session.add(user)
        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "display_name": user.display_name,
                "created_at": user.created_at.isoformat(),
            }
        }

    async def reset_password(self, email: str, new_password: str) -> dict:
        user = await self.repo.get_by_email(email)
        if user:
            new_hash = hash_password(new_password)
            user.password_hash = new_hash
        return {"detail": "If the account exists, the password was reset"}
