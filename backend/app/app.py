"""Application entrypoint and FastAPI factory.

This module configures the FastAPI app instance, attaches middleware
such as CORS and request-id, registers exception handlers, and wires
feature routers.
"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.features.core.errors import (
    AppException,
    UnhandledExceptionMiddleware,
    app_exception_handler,
    validation_exception_handler,
)
from app.features.core.logging import RequestIDMiddleware
from app.features.core.settings import get_settings

# Feature routers
from app.features.auth.routers import auth_router
from app.features.core.routes.demo import router as demo_router
from app.features.core.routes.health import router as health_router


def create_app() -> FastAPI:
    """Create and configure the main FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        debug=settings.debug,
    )

    # --- Exception handlers ---
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # --- Middleware (outermost -> innermost) ---
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(UnhandledExceptionMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Feature routers ---
    app.include_router(health_router)
    app.include_router(demo_router)
    app.include_router(auth_router)

    return app
