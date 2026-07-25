"""Tests for WC26 API CORS configuration."""

from __future__ import annotations

from fastapi.testclient import TestClient

from wc26.api import create_app
from wc26.api.settings import ApiSettings


def test_api_without_cors_origins_does_not_return_cors_headers() -> None:
    application = create_app(
        settings=ApiSettings(
            environment="test",
        )
    )

    with TestClient(application) as client:
        response = client.get(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
            },
        )

    assert response.status_code == 200

    assert "access-control-allow-origin" not in response.headers


def test_api_allows_configured_cors_origin() -> None:
    application = create_app(
        settings=ApiSettings(
            environment="test",
            cors_origins=("http://localhost:3000",),
        )
    )

    with TestClient(application) as client:
        response = client.get(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
            },
        )

    assert response.status_code == 200

    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "Origin" in response.headers["vary"]


def test_api_does_not_allow_unconfigured_cors_origin() -> None:
    application = create_app(
        settings=ApiSettings(
            environment="test",
            cors_origins=("https://app.zone14analyst.com",),
        )
    )

    with TestClient(application) as client:
        response = client.get(
            "/health",
            headers={
                "Origin": "https://untrusted.example.com",
            },
        )

    assert response.status_code == 200

    assert "access-control-allow-origin" not in response.headers


def test_api_handles_cors_preflight_request() -> None:
    application = create_app(
        settings=ApiSettings(
            environment="test",
            cors_origins=("https://app.zone14analyst.com",),
        )
    )

    with TestClient(application) as client:
        response = client.options(
            "/api/v1/transfer-intelligence/analyze",
            headers={
                "Origin": ("https://app.zone14analyst.com"),
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": ("Content-Type, Authorization"),
            },
        )

    assert response.status_code == 200

    assert response.headers["access-control-allow-origin"] == "https://app.zone14analyst.com"

    assert "POST" in response.headers["access-control-allow-methods"]

    allowed_headers = response.headers["access-control-allow-headers"].casefold()

    assert "content-type" in allowed_headers
    assert "authorization" in allowed_headers
