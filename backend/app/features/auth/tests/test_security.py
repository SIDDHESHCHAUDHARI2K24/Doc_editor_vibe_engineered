"""Tests for bcrypt password security."""
from app.features.auth.security import hash_password, verify_password


def test_verify_matching_password():
    h = hash_password("mypassword")
    assert verify_password("mypassword", h)


def test_verify_wrong_password():
    h = hash_password("mypassword")
    assert not verify_password("wrongpassword", h)


def test_different_hashes():
    h1 = hash_password("password")
    h2 = hash_password("password")
    assert h1 != h2
    assert verify_password("password", h1)
    assert verify_password("password", h2)
