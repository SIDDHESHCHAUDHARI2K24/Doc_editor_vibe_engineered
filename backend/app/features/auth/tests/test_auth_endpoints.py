"""Integration tests for auth endpoints (Stage 2)."""
import pytest
from fastapi.testclient import TestClient
from app.app import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.mark.asyncio
async def test_login_success(client):
    """Login with valid demo credentials returns 200 + sets session cookie."""
    resp = client.post("/api/v1/auth/login", json={
        "identifier": "alice@example.com",
        "password": "Password123!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "user" in data
    assert data["user"]["email"] == "alice@example.com"
    assert "session_id" in resp.cookies


@pytest.mark.asyncio
async def test_login_invalid_password(client):
    """Login with wrong password returns 401 with envelope."""
    resp = client.post("/api/v1/auth/login", json={
        "identifier": "alice@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    """Login with non-existent user returns 401."""
    resp = client.post("/api/v1/auth/login", json={
        "identifier": "nonexistent@example.com",
        "password": "somepassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_authenticated(client):
    """Logout when authenticated returns 200 and clears cookie."""
    login_resp = client.post("/api/v1/auth/login", json={
        "identifier": "alice@example.com",
        "password": "Password123!",
    })
    cookies = login_resp.cookies
    resp = client.post("/api/v1/auth/logout", cookies=cookies)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_logout_unauthenticated(client):
    """Logout without session returns 401."""
    resp = client.post("/api/v1/auth/logout")
    assert resp.status_code == 401
    data = resp.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_me_authenticated(client):
    """GET /me with valid session returns user data."""
    login_resp = client.post("/api/v1/auth/login", json={
        "identifier": "alice@example.com",
        "password": "Password123!",
    })
    cookies = login_resp.cookies
    resp = client.get("/api/v1/auth/me", cookies=cookies)
    assert resp.status_code == 200
    data = resp.json()
    assert "user" in data
    assert data["user"]["email"] == "alice@example.com"
    assert "csrf_token" in data


@pytest.mark.asyncio
async def test_me_unauthenticated(client):
    """GET /me without session returns 401."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    data = resp.json()
    assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.asyncio
async def test_register_new_user(client):
    """Register a new user returns 200."""
    import uuid
    resp = client.post("/api/v1/auth/register", json={
        "email": f"newuser-{uuid.uuid4().hex}@example.com",
        "username": f"user_{uuid.uuid4().hex[:8]}",
        "password": "Password123!",
    })
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """Register with existing email returns 409."""
    resp = client.post("/api/v1/auth/register", json={
        "email": "alice@example.com",
        "username": "someotheruser",
        "password": "Password123!",
    })
    assert resp.status_code == 409
    data = resp.json()
    assert data["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
@pytest.mark.skip(reason="Rate limiting requires working Valkey in test event loop")
async def test_rate_limit_login(client):
    """Exceeding rate limit returns 429 (requires Valkey)."""
    for _ in range(5):
        resp = client.post("/api/v1/auth/login", json={
            "identifier": "alice@example.com",
            "password": "wrongpassword",
        })
    resp = client.post("/api/v1/auth/login", json={
        "identifier": "alice@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 429
    data = resp.json()
    assert data["error"]["code"] == "RATE_LIMITED"
