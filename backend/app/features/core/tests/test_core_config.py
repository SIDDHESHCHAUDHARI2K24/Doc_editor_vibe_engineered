"""Tests for core configuration."""
from app.features.core.settings import get_settings, Settings


def test_settings_singleton():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_settings_defaults():
    s = get_settings()
    assert s.app_name == "docs-editor"
    assert s.bcrypt_cost == 10
    assert s.session_cookie_name == "session_id"
    assert s.rate_limit_login_max == 5
