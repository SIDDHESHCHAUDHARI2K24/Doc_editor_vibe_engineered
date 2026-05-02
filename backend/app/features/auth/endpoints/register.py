"""POST /api/v1/auth/register"""
from app.features.core.dependencies import DbDep
from app.features.auth.services import AuthService
from app.features.auth.schemas import RegisterRequest, LoginResponse


async def register(payload: RegisterRequest, db=DbDep) -> LoginResponse:
    svc = AuthService(db)
    data = await svc.register(payload.email, payload.username, payload.password)
    return LoginResponse(**data)
