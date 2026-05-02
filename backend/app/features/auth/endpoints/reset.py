"""POST /api/v1/auth/reset"""
from app.features.core.dependencies import DbDep
from app.features.auth.services import AuthService
from app.features.auth.schemas import RegisterRequest


class ResetRequest(RegisterRequest):
    pass


async def reset_password(payload: ResetRequest, db=DbDep) -> dict:
    svc = AuthService(db)
    return await svc.reset_password(payload.email, payload.password)
