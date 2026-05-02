"""Pydantic schemas for auth requests and responses."""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    identifier: str
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    display_name: str
    created_at: str


class LoginResponse(BaseModel):
    user: UserResponse


class MeResponse(BaseModel):
    user: UserResponse
    csrf_token: str


class StatusResponse(BaseModel):
    status: str
