"""Tests for the FastAPI application factory."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from wc26 import __version__
from wc26.api import create_app
from wc26.api.settings import (
    ApiSettings,
    TransferDatasetPaths,
)


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


def test_create_app_uses_explicit_runtime_settings() -> None:
    dataset_paths = TransferDatasetPaths(
        features=Path("configured/features.csv"),
        similarity=Path("configured/similarity.csv"),
        heatmap_similarity=Path("configured/heatmap-similarity.csv"),
        heatmap_profiles=Path("configured/heatmap-profiles.csv"),
    )

    settings = ApiSettings(
        environment="test",
        title="Configured WC26 API",
        summary="Configured API summary.",
        service_name="configured-wc26-api",
        dataset_paths=dataset_paths,
    )

    application = create_app(
        settings=settings,
    )

    assert application.title == "Configured WC26 API"
    assert application.summary == "Configured API summary."
    assert application.state.api_settings is settings
    assert application.state.transfer_dataset_paths == dataset_paths


def test_explicit_dataset_paths_override_settings_paths() -> None:
    settings = ApiSettings(
        dataset_paths=TransferDatasetPaths(
            features=Path("settings/features.csv"),
            similarity=Path("settings/similarity.csv"),
            heatmap_similarity=Path("settings/heatmap-similarity.csv"),
            heatmap_profiles=Path("settings/heatmap-profiles.csv"),
        )
    )

    override_paths = TransferDatasetPaths(
        features=Path("override/features.csv"),
        similarity=Path("override/similarity.csv"),
        heatmap_similarity=Path("override/heatmap-similarity.csv"),
        heatmap_profiles=Path("override/heatmap-profiles.csv"),
    )

    application = create_app(
        settings=settings,
        dataset_paths=override_paths,
    )

    assert application.state.api_settings.dataset_paths == override_paths
    assert application.state.transfer_dataset_paths == override_paths
