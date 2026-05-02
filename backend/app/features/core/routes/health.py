"""System health check endpoint with DB and Valkey pings."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.core.db import get_db
from app.features.core.settings import get_settings
from app.features.core.valkey import get_valkey, ping

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict:
    """Health check including database and Valkey connectivity."""
    settings = get_settings()
    db_status = "unreachable"
    valkey_status = "unreachable"

    try:
        async for session in get_db():
            await session.execute(text("SELECT 1"))
            db_status = "ok"
            break
    except Exception:
        pass

    try:
        client = await get_valkey()
        if await ping():
            valkey_status = "ok"
    except Exception:
        pass

    overall = "ok" if db_status == "ok" and valkey_status == "ok" else "degraded"

    return {
        "status": overall,
        "version": settings.version,
        "checks": {
            "database": db_status,
            "valkey": valkey_status,
        },
    }
