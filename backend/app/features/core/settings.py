"""Application configuration and environment settings.

Uses pydantic-settings to load values from environment variables and
the local .env file. Exposes a cached singleton via get_settings().
"""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed configuration for the collaborative document editor."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    app_name: str = "docs-editor"
    environment: Literal["development", "production", "test"] = "development"
    log_level: str = "DEBUG"
    debug: bool = True
    version: str = "0.1.0"

    # --- HTTP ---
    cors_origins: list[str] = ["http://localhost:5173"]
    csrf_secret_key: SecretStr = SecretStr("dev-csrf-secret-change-in-prod")

    # --- Postgres ---
    database_url: str = "postgresql+asyncpg://postgres:xyzzyspoon2k01@localhost:5432/ajaia_project"

    # --- Valkey ---
    valkey_url: str = "redis://localhost:6379/0"
    session_ttl_seconds: int = 604800

    # --- Object storage ---
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: SecretStr = SecretStr("minioadmin")
    s3_addressing_style: Literal["path", "virtual"] = "path"
    s3_bucket_documents: str = "docs"
    s3_bucket_snapshots: str = "snapshots"
    s3_bucket_attachments: str = "attachments"
    s3_region: str = "us-east-1"

    # --- Auth ---
    bcrypt_cost: int = 10
    session_cookie_name: str = "session_id"
    session_cookie_secure: bool = False
    session_cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    # --- Rate limiting ---
    rate_limit_login_max: int = 5
    rate_limit_login_window_seconds: int = 300
    rate_limit_sharing_max: int = 20
    rate_limit_sharing_window_seconds: int = 60
    rate_limit_upload_max: int = 10
    rate_limit_upload_window_seconds: int = 60

    # --- WebSocket ---
    ws_max_message_bytes: int = 1048576

    # --- Uploads ---
    upload_max_txt_md_bytes: int = 1048576
    upload_max_docx_bytes: int = 10485760
    upload_max_attachment_bytes: int = 26214400


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
