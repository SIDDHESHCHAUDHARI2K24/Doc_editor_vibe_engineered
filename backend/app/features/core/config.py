"""Application configuration and environment settings for the backend.

This module centralizes configuration using `pydantic-settings`. It
reads values from the process environment and the local `.env` file
in the backend directory. Use the `settings` singleton or the
`get_settings()` helper in dependencies instead of instantiating
`Settings` directly.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed configuration model for the application.

    Attributes:
        project_name: Human-friendly name for the service.
        environment: Deployment environment identifier (e.g. local, dev, prod).
        database_url: PostgreSQL connection URL used by the async driver.
        log_level: Application log level (e.g. INFO, DEBUG).
    """

    project_name: str = "FastAPI Backend Boilerplate"
    environment: str = "local"
    database_url: str
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of `Settings` loaded from the environment."""
    return Settings()


settings = get_settings()

