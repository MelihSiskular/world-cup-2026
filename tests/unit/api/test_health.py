"""Tests for the API health endpoint."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from wc26 import __version__
from wc26.api import create_app
from wc26.api.settings import ApiSettings


def _parse_datetime(
    value: object,
) -> datetime:
    """Parse one timestamp returned by the API."""

    assert isinstance(value, str)

    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )


def test_health_endpoint_returns_runtime_metadata() -> None:
    application = create_app()

    with TestClient(application) as client:
        runtime = application.state.api_runtime
        response = client.get("/health")

        expected_started_at = runtime.started_at

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["service"] == "wc26-transfer-intelligence"
    assert payload["version"] == __version__
    assert payload["environment"] == "development"
    assert payload["uptime_seconds"] >= 0.0

    assert expected_started_at is not None

    returned_started_at = _parse_datetime(payload["started_at"])

    assert returned_started_at == expected_started_at
    assert returned_started_at.tzinfo == UTC


def test_health_endpoint_uses_configured_runtime_settings() -> None:
    application = create_app(
        settings=ApiSettings(
            environment="test",
            service_name="wc26-test-api",
        )
    )

    with TestClient(application) as client:
        response = client.get("/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["service"] == "wc26-test-api"
    assert payload["version"] == __version__
    assert payload["environment"] == "test"
    assert payload["uptime_seconds"] >= 0.0
    assert _parse_datetime(payload["started_at"]).tzinfo == UTC


def test_health_endpoint_declares_json_content_type() -> None:
    application = create_app()

    with TestClient(application) as client:
        response = client.get("/health")

    assert response.headers["content-type"].startswith("application/json")
