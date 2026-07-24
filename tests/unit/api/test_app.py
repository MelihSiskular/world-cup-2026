"""Tests for the FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from wc26 import __version__
from wc26.api import create_app


def test_create_app_configures_application_metadata() -> None:
    application = create_app()

    assert isinstance(application, FastAPI)
    assert application.title == "WC26 Transfer Intelligence API"
    assert application.version == __version__


def test_create_app_registers_health_route() -> None:
    application = create_app()

    openapi_schema = application.openapi()

    assert "/health" in openapi_schema["paths"]
    assert application.docs_url == "/docs"
    assert application.openapi_url == "/openapi.json"
