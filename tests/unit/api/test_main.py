"""Tests for the deployable ASGI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from wc26 import __version__
from wc26.api.main import app


def test_asgi_entrypoint_exposes_fastapi_application() -> None:
    assert isinstance(app, FastAPI)
    assert app.title == "WC26 Transfer Intelligence API"
    assert app.version == __version__


def test_asgi_entrypoint_includes_health_endpoint() -> None:
    openapi_schema = app.openapi()

    assert "/health" in openapi_schema["paths"]
    assert "get" in openapi_schema["paths"]["/health"]
