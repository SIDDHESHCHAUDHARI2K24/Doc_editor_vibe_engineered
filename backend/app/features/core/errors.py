"""Application exception hierarchy and error envelope formatting."""

from http import HTTPStatus

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.features.core.settings import get_settings


class AppException(Exception):
    """Base application exception with structured error metadata."""

    def __init__(
        self,
        code: str,
        message: str,
        details: dict | None = None,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
    ) -> None:
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", details: dict | None = None) -> None:
        super().__init__(
            code="NOT_FOUND",
            message=message,
            details=details,
            status_code=HTTPStatus.NOT_FOUND,
        )


class PermissionDeniedException(AppException):
    def __init__(self, message: str = "Permission denied", details: dict | None = None) -> None:
        super().__init__(
            code="PERMISSION_DENIED",
            message=message,
            details=details,
            status_code=HTTPStatus.FORBIDDEN,
        )


class ValidationException(AppException):
    def __init__(self, message: str = "Validation error", details: dict | None = None, code: str | None = None) -> None:
        super().__init__(
            code=code or "VALIDATION_ERROR",
            message=message,
            details=details,
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )


class ConflictException(AppException):
    def __init__(self, message: str = "Resource conflict", details: dict | None = None) -> None:
        super().__init__(
            code="CONFLICT",
            message=message,
            details=details,
            status_code=HTTPStatus.CONFLICT,
        )


class RateLimitedException(AppException):
    def __init__(self, message: str = "Too many requests", details: dict | None = None) -> None:
        super().__init__(
            code="RATE_LIMITED",
            message=message,
            details=details,
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
        )


class AuthenticationException(AppException):
    def __init__(self, message: str = "Authentication required", details: dict | None = None) -> None:
        super().__init__(
            code="AUTHENTICATION_REQUIRED",
            message=message,
            details=details,
            status_code=HTTPStatus.UNAUTHORIZED,
        )


class InternalException(AppException):
    def __init__(self, message: str = "Internal server error", details: dict | None = None) -> None:
        super().__init__(
            code="INTERNAL_ERROR",
            message=message,
            details=details,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


def _error_envelope(
    code: str,
    message: str,
    details: dict | None = None,
    request_id: str = "",
) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "request_id": request_id,
        }
    }


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_envelope(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=_get_request_id(request),
        ),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = {"errors": exc.errors()}
    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content=_error_envelope(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details=details,
            request_id=_get_request_id(request),
        ),
    )


class UnhandledExceptionMiddleware(BaseHTTPMiddleware):
    """Catch-all middleware that converts unhandled exceptions to the error envelope."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except AppException:
            raise
        except RequestValidationError:
            raise
        except Exception as exc:
            settings = get_settings()
            details: dict = {}
            if settings.debug:
                import traceback

                details["traceback"] = traceback.format_exc()
            return JSONResponse(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                content=_error_envelope(
                    code="INTERNAL_ERROR",
                    message="An unexpected error occurred",
                    details=details,
                    request_id=_get_request_id(request),
                ),
            )
