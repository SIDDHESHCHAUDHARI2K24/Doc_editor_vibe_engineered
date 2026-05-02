"""SQLAlchemy 2.0 ORM models for authentication."""

import uuid as _uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import CITEXT, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.features.core.models import Base


def uuid7() -> UUID:
    """Generate a time-ordered UUID v7-like identifier.

    Constructs a UUID where the first 48 bits encode the current
    Unix timestamp in milliseconds (big-endian) and the remaining
    bits are filled from ``uuid4()`` for randomness, following the
    draft RFC 9562 UUIDv7 layout.
    """
    ts = int(datetime.now(timezone.utc).timestamp() * 1000)
    ts_bytes = ts.to_bytes(6, "big")
    rnd = _uuid.uuid4().bytes[6:]
    return _uuid.UUID(bytes=ts_bytes + rnd)


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )
    email: Mapped[str] = mapped_column(
        CITEXT,
        unique=True,
        index=True,
        nullable=False,
    )
    username: Mapped[str] = mapped_column(
        CITEXT,
        unique=True,
        index=True,
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(
        String(100),
        default="",
        server_default="",
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id!r}, email={self.email!r}, "
            f"username={self.username!r})>"
        )
