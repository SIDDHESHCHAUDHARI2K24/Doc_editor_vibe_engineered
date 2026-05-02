"""POST /api/v1/auth/login"""
from fastapi import Request, Response

from app.features.core.rate_limit import rate_limiter, get_client_ip
from app.features.core.errors import RateLimitedException
from app.features.core.settings import get_settings
from app.features.core.dependencies import DbDep
from app.features.auth.services import AuthService
from app.features.auth.schemas import LoginRequest, LoginResponse

settings = get_settings()


async def login(payload: LoginRequest, request: Request, response: Response, db=DbDep) -> LoginResponse:
    if settings.environment != "test":
        client_ip = get_client_ip(request)
        rl_key = f"rl:login:{client_ip}:{payload.identifier.lower()}"
        result = await rate_limiter.check(rl_key, settings.rate_limit_login_max, settings.rate_limit_login_window_seconds)
        if not result.allowed:
            raise RateLimitedException(
                message=f"Too many login attempts. Try again in {result.retry_after:.0f} seconds.",
                details={"retry_after": result.retry_after},
            )
    svc = AuthService(db)
    data = await svc.login(payload.identifier, payload.password, response)
    return LoginResponse(**data)
