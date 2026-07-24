"""Tests for the API health endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from wc26 import __version__
from wc26.api import create_app


def test_health_endpoint_returns_service_status() -> None:
    application = create_app()

    with TestClient(application) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "wc26-transfer-intelligence",
        "version": __version__,
    }


def test_health_endpoint_declares_json_content_type() -> None:
    application = create_app()

    with TestClient(application) as client:
        response = client.get("/health")

    assert response.headers["content-type"].startswith("application/json")
