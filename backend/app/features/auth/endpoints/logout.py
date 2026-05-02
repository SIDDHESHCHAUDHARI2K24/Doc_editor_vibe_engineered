"""POST /api/v1/auth/logout"""
from fastapi import Depends, Request, Response
from app.features.core.dependencies import DbDep
from app.features.core.security import require_session, AuthenticatedSession
from app.features.core.settings import get_settings
from app.features.auth.services import AuthService

settings = get_settings()


async def logout(
    request: Request,
    response: Response,
    db=DbDep,
    auth_session: AuthenticatedSession = Depends(require_session),
) -> dict:
    svc = AuthService(db)
    token = request.cookies.get(settings.session_cookie_name)
    return await svc.logout(token, response)
