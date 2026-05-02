"""Tests for application exception hierarchy and error envelope format."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.features.core.errors import (
    AppException,
    AuthenticationException,
    ConflictException,
    InternalException,
    NotFoundException,
    PermissionDeniedException,
    RateLimitedException,
    ValidationException,
)


def _create_test_app() -> FastAPI:
    """Minimal FastAPI app that registers error handlers for testing."""
    from fastapi.exceptions import RequestValidationError

    from app.features.core.errors import (
        AppException,
        UnhandledExceptionMiddleware,
        app_exception_handler,
        validation_exception_handler,
    )

    app = FastAPI(debug=True)

    app.add_middleware(UnhandledExceptionMiddleware)
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    return app


class TestNotFoundException:
    def test_has_correct_status_and_code(self) -> None:
        exc = NotFoundException(message="Document not found")
        assert exc.status_code == 404
        assert exc.code == "NOT_FOUND"
        assert exc.message == "Document not found"

    def test_has_error_envelope_shape(self) -> None:
        app = _create_test_app()

        @app.get("/test-404")
        async def raise_404() -> None:
            raise NotFoundException(message="Document not found", details={"doc_id": "abc"})

        client = TestClient(app)
        resp = client.get("/test-404")
        assert resp.status_code == 404
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] == "NOT_FOUND"
        assert body["error"]["message"] == "Document not found"
        assert body["error"]["details"] == {"doc_id": "abc"}
        assert "request_id" in body["error"]


class TestPermissionDeniedException:
    def test_has_correct_status_and_code(self) -> None:
        exc = PermissionDeniedException()
        assert exc.status_code == 403
        assert exc.code == "PERMISSION_DENIED"

    def test_envelope_in_response(self) -> None:
        app = _create_test_app()

        @app.get("/test-403")
        async def raise_403() -> None:
            raise PermissionDeniedException(message="Access denied")

        client = TestClient(app)
        resp = client.get("/test-403")
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"


class TestValidationException:
    def test_has_correct_status_and_code(self) -> None:
        exc = ValidationException()
        assert exc.status_code == 422
        assert exc.code == "VALIDATION_ERROR"

    def test_envelope_in_response(self) -> None:
        app = _create_test_app()

        @app.get("/test-422")
        async def raise_422() -> None:
            raise ValidationException(message="Invalid input", details={"field": "email"})

        client = TestClient(app)
        resp = client.get("/test-422")
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


class TestConflictException:
    def test_has_correct_status_and_code(self) -> None:
        exc = ConflictException()
        assert exc.status_code == 409
        assert exc.code == "CONFLICT"

    def test_envelope_in_response(self) -> None:
        app = _create_test_app()

        @app.get("/test-409")
        async def raise_409() -> None:
            raise ConflictException(message="Email already taken")

        client = TestClient(app)
        resp = client.get("/test-409")
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "CONFLICT"


class TestRateLimitedException:
    def test_has_correct_status_and_code(self) -> None:
        exc = RateLimitedException()
        assert exc.status_code == 429
        assert exc.code == "RATE_LIMITED"

    def test_envelope_in_response(self) -> None:
        app = _create_test_app()

        @app.get("/test-429")
        async def raise_429() -> None:
            raise RateLimitedException()

        client = TestClient(app)
        resp = client.get("/test-429")
        assert resp.status_code == 429
        assert resp.json()["error"]["code"] == "RATE_LIMITED"


class TestAuthenticationException:
    def test_has_correct_status_and_code(self) -> None:
        exc = AuthenticationException()
        assert exc.status_code == 401
        assert exc.code == "AUTHENTICATION_REQUIRED"

    def test_envelope_in_response(self) -> None:
        app = _create_test_app()

        @app.get("/test-401")
        async def raise_401() -> None:
            raise AuthenticationException(message="Invalid credentials")

        client = TestClient(app)
        resp = client.get("/test-401")
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


class TestInternalException:
    def test_has_correct_status_and_code(self) -> None:
        exc = InternalException()
        assert exc.status_code == 500
        assert exc.code == "INTERNAL_ERROR"

    def test_envelope_in_response(self) -> None:
        app = _create_test_app()

        @app.get("/test-500-app")
        async def raise_500() -> None:
            raise InternalException(message="Database failure")

        client = TestClient(app)
        resp = client.get("/test-500-app")
        assert resp.status_code == 500
        assert resp.json()["error"]["code"] == "INTERNAL_ERROR"


class TestUnhandledException:
    def test_envelope_in_response_with_traceback_in_debug(self) -> None:
        app = _create_test_app()

        @app.get("/crash")
        async def crash() -> None:
            raise ValueError("something went wrong")

        client = TestClient(app)
        resp = client.get("/crash")
        assert resp.status_code == 500
        body = resp.json()
        assert body["error"]["code"] == "INTERNAL_ERROR"
        assert body["error"]["message"] == "An unexpected error occurred"
        assert "traceback" in body["error"]["details"]
        assert "request_id" in body["error"]


class TestRequestValidationError:
    def test_pydantic_validation_error_envelope(self) -> None:
        from pydantic import BaseModel

        app = _create_test_app()

        class Item(BaseModel):
            name: str

        @app.post("/items")
        async def create_item(item: Item) -> dict:
            return {"name": item.name}

        client = TestClient(app)
        resp = client.post("/items", json={})
        assert resp.status_code == 422
        body = resp.json()
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert "errors" in body["error"]["details"]
