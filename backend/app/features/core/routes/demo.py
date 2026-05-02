"""Demo endpoints for showcasing the error envelope."""

from fastapi import APIRouter

from app.features.core.errors import NotFoundException

router = APIRouter(prefix="/api/v1", tags=["demo"])


@router.get("/_demo/error")
async def demo_error() -> None:
    """Raise a NotFoundException to demonstrate the error envelope shape."""
    raise NotFoundException(message="This is a demo error", details={"hint": "Check the error envelope shape"})
