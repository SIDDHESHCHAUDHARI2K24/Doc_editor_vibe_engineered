"""Application entrypoint and FastAPI factory.

This module configures the FastAPI app instance, attaches middleware
such as CORS, and wires feature routers (for example `auth`).
The `core` feature provides infrastructure only and is consumed
via dependencies, not as a public router.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.features.auth.routers import auth_router
from app.features.core.config import settings


def create_app() -> FastAPI:
    """Create and configure the main FastAPI application instance."""
    app = FastAPI(title=settings.project_name)

    allow_origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        """Simple health check endpoint used for readiness/liveness probes."""
        return {"status": "ok"}

    # Feature routers.
    app.include_router(auth_router)

    return app
