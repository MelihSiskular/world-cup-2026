"""Tests for the deployable ASGI application entrypoint."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI

from wc26 import __version__
from wc26.api.main import app, create_production_app


def test_asgi_entrypoint_exposes_fastapi_application() -> None:
    assert isinstance(app, FastAPI)
    assert app.title == "WC26 Transfer Intelligence API"
    assert app.version == __version__


def test_asgi_entrypoint_includes_health_endpoint() -> None:
    openapi_schema = app.openapi()

    assert "/health" in openapi_schema["paths"]
    assert "get" in openapi_schema["paths"]["/health"]


def test_create_production_app_reads_process_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "WC26_ENVIRONMENT",
        "production",
    )
    monkeypatch.setenv(
        "WC26_API_TITLE",
        "WC26 Deployment API",
    )
    monkeypatch.setenv(
        "WC26_FEATURES_PATH",
        "/srv/wc26/features.csv",
    )
    monkeypatch.setenv(
        "WC26_SIMILARITY_PATH",
        "/srv/wc26/similarity.csv",
    )
    monkeypatch.setenv(
        "WC26_HEATMAP_SIMILARITY_PATH",
        "/srv/wc26/heatmap-similarity.csv",
    )
    monkeypatch.setenv(
        "WC26_HEATMAP_PROFILES_PATH",
        "/srv/wc26/heatmap-profiles.csv",
    )

    application = create_production_app()

    runtime = application.state.api_runtime
    settings = runtime.settings

    assert settings.environment == "production"
    assert application.title == "WC26 Deployment API"

    assert settings.dataset_paths.features == Path("/srv/wc26/features.csv")
    assert settings.dataset_paths.similarity == Path("/srv/wc26/similarity.csv")
    assert settings.dataset_paths.heatmap_similarity == Path("/srv/wc26/heatmap-similarity.csv")
    assert settings.dataset_paths.heatmap_profiles == Path("/srv/wc26/heatmap-profiles.csv")
    assert runtime.dataset_paths == settings.dataset_paths
