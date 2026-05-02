"""Bcrypt password hashing and verification.

Replaces the PBKDF2-SHA256 implementation previously in ``auth/utils.py``.

Timing guidelines (typical hardware):
    - bcrypt_cost=10  → ~50 ms
    - bcrypt_cost=12  → ~250 ms
"""

from passlib.context import CryptContext

from app.features.core.settings import get_settings

_settings = get_settings()

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=_settings.bcrypt_cost,
)


def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*."""
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Return ``True`` if *password* matches *hashed*."""
    return pwd_context.verify(password, hashed)
