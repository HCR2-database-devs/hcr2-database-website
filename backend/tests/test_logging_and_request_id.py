import logging

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def test_unhandled_exception_is_logged_with_path_and_request_id(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = create_app()

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("secret internal detail")

    client = TestClient(app, raise_server_exceptions=False)
    with caplog.at_level(logging.ERROR, logger="hcr2"):
        response = client.get("/boom?token=do-not-log")

    assert response.status_code == 500
    assert response.json() == {"error": "Internal Server Error"}
    request_id = response.headers["X-Request-ID"]
    assert request_id
    record = next(record for record in caplog.records if record.message == "Unhandled exception")
    assert record.path == "/boom"
    assert record.request_id == request_id
    assert record.exc_info is not None
    assert "RuntimeError: secret internal detail" in caplog.text
    assert "do-not-log" not in caplog.text


def test_successful_request_has_request_id_header() -> None:
    response = TestClient(create_app()).get("/health?token=do-not-log")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_cors_allows_only_the_methods_and_headers_the_app_uses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "https://example.test")
    get_settings.cache_clear()
    try:
        app = create_app()
        client = TestClient(app)
        allowed = client.options(
            "/api/v1/maps",
            headers={
                "Origin": "https://example.test",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,x-api-key",
            },
        )
        denied = client.options(
            "/api/v1/maps",
            headers={
                "Origin": "https://example.test",
                "Access-Control-Request-Method": "DELETE",
                "Access-Control-Request-Headers": "content-type",
            },
        )
    finally:
        get_settings.cache_clear()

    assert allowed.status_code == 200
    allowed_methods = allowed.headers["Access-Control-Allow-Methods"]
    assert "GET" in allowed_methods and "POST" in allowed_methods
    assert "DELETE" not in allowed_methods
    allowed_headers = allowed.headers["Access-Control-Allow-Headers"].lower()
    assert "content-type" in allowed_headers and "x-api-key" in allowed_headers
    assert denied.status_code == 400
