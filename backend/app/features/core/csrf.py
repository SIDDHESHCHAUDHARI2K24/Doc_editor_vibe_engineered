"""CSRF protection using double-submit cookie pattern."""
import secrets

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.features.core.errors import _error_envelope, _get_request_id

CSRF_EXEMPT_PATHS = {"/api/v1/auth/login", "/api/v1/auth/logout", "/api/v1/auth/register", "/api/v1/auth/reset"}
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class CsrfMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method in SAFE_METHODS:
            return await call_next(request)
        if request.url.path in CSRF_EXEMPT_PATHS:
            return await call_next(request)
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        cookie_token = request.cookies.get("csrf_token")
        header_token = request.headers.get("X-CSRF-Token")

        if not cookie_token or not header_token or not secrets.compare_digest(cookie_token, header_token):
            return JSONResponse(
                status_code=403,
                content=_error_envelope(
                    code="CSRF_MISMATCH",
                    message="CSRF validation failed — ensure X-CSRF-Token header matches csrf_token cookie",
                    request_id=_get_request_id(request),
                ),
            )
        return await call_next(request)
