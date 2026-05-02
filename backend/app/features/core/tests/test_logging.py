"""Tests for structured logging and RequestIDMiddleware."""

import io
import json
import logging
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.features.core.logging import RequestIDMiddleware, configure_logging


def test_request_id_header_present() -> None:
    """Every response should include an X-Request-ID header."""
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/ping")
    async def ping() -> dict:
        return {"ok": True}

    client = TestClient(app)
    resp = client.get("/ping")
    assert "x-request-id" in resp.headers
    request_id = resp.headers["x-request-id"]
    assert len(request_id) == 36  # UUID4 format


def test_request_id_is_unique() -> None:
    """Consecutive requests should get different request IDs."""
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/")
    async def root() -> dict:
        return {}

    client = TestClient(app)
    ids = {client.get("/").headers["x-request-id"] for _ in range(5)}
    assert len(ids) == 5


def test_middleware_logs_request_started_and_finished() -> None:
    """Middleware should emit 'request_started' and 'request_finished' log events to stdout."""
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/healthy")
    async def healthy() -> dict:
        return {"status": "ok"}

    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured

    try:
        client = TestClient(app)
        resp = client.get("/healthy")
        assert resp.status_code == 200
    finally:
        sys.stdout = old_stdout

    output = captured.getvalue()
    assert "request_started" in output, f"Expected 'request_started' in output: {output}"
    assert "request_finished" in output, f"Expected 'request_finished' in output: {output}"


def test_configure_logging_does_not_raise() -> None:
    """configure_logging() should run without error."""
    configure_logging(log_level="INFO")
    assert True


def test_request_id_on_error() -> None:
    """Error responses should also include X-Request-ID header."""
    from app.features.core.errors import (
        AppException,
        app_exception_handler,
    )

    app = FastAPI(debug=True)
    app.add_middleware(RequestIDMiddleware)
    app.add_exception_handler(AppException, app_exception_handler)

    @app.get("/error")
    async def error() -> None:
        raise AppException(code="TEST_ERROR", message="test error", status_code=400)

    client = TestClient(app)
    resp = client.get("/error")
    assert resp.status_code == 400
    assert "x-request-id" in resp.headers
    body = resp.json()
    assert body["error"]["request_id"] == resp.headers["x-request-id"]
