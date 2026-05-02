"""Structured logging configuration and request-id middleware."""

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


def configure_logging(log_level: str = "DEBUG") -> None:
    """Configure structlog with JSON output to stdout."""
    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.EventRenamer("message"),
            structlog.dev.ConsoleRenderer() if log_level == "DEBUG" else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns a unique request_id to every request.

    Generates a UUID4, binds it to structlog context, sets it on
    request.state, and includes it in the X-Request-ID response header.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        structlog.contextvars.bind_contextvars(request_id=request_id)

        logger = get_logger("app.middleware.request_id")
        logger.info("request_started", method=request.method, path=request.url.path)

        start_time = time.monotonic()
        try:
            response = await call_next(request)
            elapsed = time.monotonic() - start_time
            logger.info("request_finished", status_code=response.status_code, elapsed_ms=round(elapsed * 1000, 3))
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception:
            elapsed = time.monotonic() - start_time
            logger.exception("request_failed", elapsed_ms=round(elapsed * 1000, 3))
            raise
        finally:
            structlog.contextvars.clear_contextvars()
