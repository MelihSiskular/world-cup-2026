"""Tests for centralized WC26 API runtime settings."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from wc26.api.settings import (
    ApiSettings,
    ApiSettingsError,
    TransferDatasetPaths,
)


def test_api_settings_use_current_runtime_defaults() -> None:
    settings = ApiSettings.from_environment({})

    assert settings.environment == "development"
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000

    assert settings.title == "WC26 Transfer Intelligence API"
    assert settings.summary == ("Football recruitment intelligence powered by World Cup data.")
    assert settings.service_name == "wc26-transfer-intelligence"

    assert settings.dataset_paths == TransferDatasetPaths()
    assert settings.cors_origins == ()


def test_api_settings_read_environment_overrides() -> None:
    settings = ApiSettings.from_environment(
        {
            "WC26_ENVIRONMENT": "production",
            "WC26_API_HOST": "0.0.0.0",
            "WC26_API_PORT": "9000",
            "WC26_API_TITLE": "WC26 Production API",
            "WC26_API_SUMMARY": ("Production football analytics API."),
            "WC26_SERVICE_NAME": "wc26-api",
            "WC26_FEATURES_PATH": ("/srv/wc26/features.csv"),
            "WC26_SIMILARITY_PATH": ("/srv/wc26/similarity.csv"),
            "WC26_HEATMAP_SIMILARITY_PATH": ("/srv/wc26/heatmap-similarity.csv"),
            "WC26_HEATMAP_PROFILES_PATH": ("/srv/wc26/heatmap-profiles.csv"),
            "WC26_HEATMAP_GRIDS_PATH": ("/srv/wc26/heatmap-grids.npz"),
            "WC26_CORS_ORIGINS": ("https://zone14analyst.com,https://app.zone14analyst.com"),
        }
    )

    assert settings.environment == "production"
    assert settings.host == "0.0.0.0"
    assert settings.port == 9000

    assert settings.title == "WC26 Production API"
    assert settings.service_name == "wc26-api"

    assert settings.dataset_paths.features == Path("/srv/wc26/features.csv")
    assert settings.dataset_paths.similarity == Path("/srv/wc26/similarity.csv")
    assert settings.dataset_paths.heatmap_similarity == Path("/srv/wc26/heatmap-similarity.csv")
    assert settings.dataset_paths.heatmap_profiles == Path("/srv/wc26/heatmap-profiles.csv")
    assert settings.dataset_paths.heatmap_grids == Path("/srv/wc26/heatmap-grids.npz")

    assert settings.cors_origins == (
        "https://zone14analyst.com",
        "https://app.zone14analyst.com",
    )


def test_cors_origins_are_normalized_and_deduplicated() -> None:
    settings = ApiSettings.from_environment(
        {
            "WC26_CORS_ORIGINS": (
                " http://localhost:3000/, http://localhost:3000,https://example.com/ "
            )
        }
    )

    assert settings.cors_origins == (
        "http://localhost:3000",
        "https://example.com",
    )


def test_api_settings_read_process_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "WC26_ENVIRONMENT",
        "test",
    )
    monkeypatch.setenv(
        "WC26_API_PORT",
        "8100",
    )

    settings = ApiSettings.from_environment()

    assert settings.environment == "test"
    assert settings.port == 8100


@pytest.mark.parametrize(
    (
        "environment",
        "message",
    ),
    [
        (
            {
                "WC26_ENVIRONMENT": "staging",
            },
            "WC26_ENVIRONMENT must be one of",
        ),
        (
            {
                "WC26_API_PORT": "not-a-number",
            },
            "WC26_API_PORT must be an integer",
        ),
        (
            {
                "WC26_API_PORT": "0",
            },
            "WC26_API_PORT must be between",
        ),
        (
            {
                "WC26_API_PORT": "65536",
            },
            "WC26_API_PORT must be between",
        ),
        (
            {
                "WC26_API_HOST": "   ",
            },
            "WC26_API_HOST must not be empty",
        ),
        (
            {
                "WC26_FEATURES_PATH": "   ",
            },
            "WC26_FEATURES_PATH must not be empty",
        ),
    ],
)
def test_api_settings_reject_invalid_environment_values(
    environment: dict[str, str],
    message: str,
) -> None:
    with pytest.raises(
        ApiSettingsError,
        match=message,
    ):
        ApiSettings.from_environment(environment)


@pytest.mark.parametrize(
    "origin",
    [
        "localhost:3000",
        "ftp://example.com",
        "https://example.com/application",
        "https://example.com?source=test",
        "https://example.com#fragment",
    ],
)
def test_api_settings_reject_invalid_cors_origins(
    origin: str,
) -> None:
    with pytest.raises(ApiSettingsError):
        ApiSettings(cors_origins=(origin,))


def test_api_settings_are_immutable() -> None:
    settings = ApiSettings()

    with pytest.raises(FrozenInstanceError):
        settings.port = 9000
