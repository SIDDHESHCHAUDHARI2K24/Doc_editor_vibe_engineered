"""Integration tests for document CRUD endpoints (Stage 2)."""
import uuid

import httpx
import pytest

from app.app import create_app


@pytest.fixture
def app():
    return create_app()


async def _register_and_login(
    client: httpx.AsyncClient, email: str, username: str, password: str
) -> str:
    register_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert register_resp.status_code in (200, 409), register_resp.text
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"identifier": email, "password": password},
    )
    assert login_resp.status_code == 200, (
        f"Login failed ({login_resp.status_code}): {login_resp.text}. "
        f"Email={email}, username={username}"
    )
    client.cookies = login_resp.cookies
    csrf_token = login_resp.cookies.get("csrf_token")
    assert csrf_token, "csrf_token cookie missing from login response"
    return csrf_token


async def _login_as_alice(client: httpx.AsyncClient) -> str:
    uid = uuid.uuid4().hex[:8]
    return await _register_and_login(client, f"alice-{uid}@example.com", f"alice_{uid}", "Password123!")


async def _login_as_bob(client: httpx.AsyncClient) -> str:
    uid = uuid.uuid4().hex[:8]
    return await _register_and_login(client, f"bob-{uid}@example.com", f"bob_{uid}", "Password123!")


async def _create_doc(
    client: httpx.AsyncClient, csrf_token: str, title: str = "Test Doc"
):
    return await client.post(
        "/api/v1/documents",
        json={"title": title},
        headers={"X-CSRF-Token": csrf_token},
    )


def _new_client(app) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_document(app):
    async with _new_client(app) as client:
        csrf = await _login_as_alice(client)
        resp = await _create_doc(client, csrf, "My Doc")
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["title"] == "My Doc"
        assert "id" in data
        assert "owner_id" in data


@pytest.mark.asyncio
async def test_create_document_unauthenticated(app):
    async with _new_client(app) as client:
        resp = await client.post("/api/v1/documents", json={"title": "My Doc"})
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_document_empty_title(app):
    async with _new_client(app) as client:
        csrf = await _login_as_alice(client)
        resp = await client.post(
            "/api/v1/documents",
            json={"title": ""},
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# LIST
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_owned_documents(app):
    async with _new_client(app) as client:
        csrf = await _login_as_alice(client)
        await _create_doc(client, csrf, "Doc 1")
        resp = await client.get("/api/v1/documents?scope=owned")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "next_cursor" in data
        assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_list_shared_empty(app):
    async with _new_client(app) as client:
        csrf = await _login_as_alice(client)
        resp = await client.get("/api/v1/documents?scope=shared")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["next_cursor"] is None


@pytest.mark.asyncio
async def test_list_unauthenticated(app):
    async with _new_client(app) as client:
        resp = await client.get("/api/v1/documents")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_document_owner(app):
    async with _new_client(app) as client:
        csrf = await _login_as_alice(client)
        create_resp = await _create_doc(client, csrf, "Test Doc")
        doc_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/documents/{doc_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Test Doc"


@pytest.mark.asyncio
async def test_get_document_non_owner(app):
    async with _new_client(app) as alice:
        csrf = await _login_as_alice(alice)
        create_resp = await _create_doc(alice, csrf, "Alice's Doc")
        doc_id = create_resp.json()["id"]
    async with _new_client(app) as bob:
        await _login_as_bob(bob)
        resp = await bob.get(f"/api/v1/documents/{doc_id}")
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"


# ---------------------------------------------------------------------------
# RENAME (PATCH)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rename_document(app):
    async with _new_client(app) as client:
        csrf = await _login_as_alice(client)
        create_resp = await _create_doc(client, csrf, "Old Title")
        doc_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/documents/{doc_id}",
            json={"title": "New Title"},
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["title"] == "New Title"


@pytest.mark.asyncio
async def test_rename_document_non_owner(app):
    async with _new_client(app) as alice:
        csrf = await _login_as_alice(alice)
        create_resp = await _create_doc(alice, csrf, "Alice's Doc")
        doc_id = create_resp.json()["id"]
    async with _new_client(app) as bob:
        bob_csrf = await _login_as_bob(bob)
        resp = await bob.patch(
            f"/api/v1/documents/{doc_id}",
            json={"title": "Hacked!"},
            headers={"X-CSRF-Token": bob_csrf},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_document(app):
    async with _new_client(app) as client:
        csrf = await _login_as_alice(client)
        create_resp = await _create_doc(client, csrf, "To Delete")
        doc_id = create_resp.json()["id"]
        resp = await client.delete(
            f"/api/v1/documents/{doc_id}",
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 204
        get_resp = await client.get(f"/api/v1/documents/{doc_id}")
        assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_non_owner(app):
    async with _new_client(app) as alice:
        csrf = await _login_as_alice(alice)
        create_resp = await _create_doc(alice, csrf, "Alice's Doc")
        doc_id = create_resp.json()["id"]
    async with _new_client(app) as bob:
        bob_csrf = await _login_as_bob(bob)
        resp = await bob.delete(
            f"/api/v1/documents/{doc_id}",
            headers={"X-CSRF-Token": bob_csrf},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mutation_without_csrf_fails(app):
    async with _new_client(app) as client:
        csrf = await _login_as_alice(client)
        resp = await client.post(
            "/api/v1/documents",
            json={"title": "No CSRF header"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "CSRF_MISMATCH"


@pytest.mark.asyncio
async def test_mutation_with_csrf_works(app):
    async with _new_client(app) as client:
        csrf = await _login_as_alice(client)
        resp = await _create_doc(client, csrf, "CSRF Works")
        assert resp.status_code == 201
