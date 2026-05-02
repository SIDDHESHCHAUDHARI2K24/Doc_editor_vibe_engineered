"""Authentication router with prefix /api/v1/auth."""
from fastapi import APIRouter

from app.features.auth.endpoints.login import login
from app.features.auth.endpoints.logout import logout
from app.features.auth.endpoints.me import me
from app.features.auth.endpoints.register import register
from app.features.auth.endpoints.reset import reset_password

auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

auth_router.post("/login")(login)
auth_router.post("/logout")(logout)
auth_router.get("/me")(me)
auth_router.post("/register")(register)
auth_router.post("/reset")(reset_password)
