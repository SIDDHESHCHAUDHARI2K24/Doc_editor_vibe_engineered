"""Alembic environment configuration for the backend.

This file configures how Alembic connects to the database and runs
migrations. It reads the database URL from the application Settings
and uses the SQLAlchemy Base metadata for autogeneration.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import application models and settings
from app.features.core.models import Base  # noqa: E402
from app.features.core.settings import get_settings  # noqa: E402

# Ensure all feature models are registered on Base.metadata
import app.features.auth.models  # noqa: E402, F401
import app.features.core.audit  # noqa: E402, F401
import app.features.documents.models  # noqa: E402, F401

settings = get_settings()
target_metadata = Base.metadata

# Set the database URL from application settings (use sync driver for migrations)
sync_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
config.set_main_option("sqlalchemy.url", sync_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode using a URL only."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an Engine connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
