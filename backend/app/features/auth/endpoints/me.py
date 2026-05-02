"""GET /api/v1/auth/me"""
from fastapi import Depends
from app.features.core.security import require_session, AuthenticatedSession
from app.features.core.dependencies import DbDep
from app.features.auth.services import AuthService
from app.features.auth.schemas import MeResponse


async def me(db=DbDep, auth_session: AuthenticatedSession = Depends(require_session)) -> MeResponse:
    svc = AuthService(db)
    data = await svc.get_me(auth_session.user)
    data["csrf_token"] = auth_session.session.csrf_token
    return MeResponse(**data)
