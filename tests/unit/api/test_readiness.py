"""Tests for the API readiness endpoint."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from wc26 import __version__
from wc26.analytics.transfer_intelligence.catalog import (
    TransferDataCatalog,
)
from wc26.api import create_app
from wc26.api.settings import ApiSettings


def _catalog() -> TransferDataCatalog:
    """Build a minimal in-memory runtime catalog."""

    return TransferDataCatalog(
        players=pd.DataFrame(
            {
                "player_id": [978838],
                "player_name": ["Michael Olise"],
            }
        ),
        similarity=pd.DataFrame(
            {
                "source_player_id": [978838],
            }
        ),
        heatmap_similarity=pd.DataFrame(
            {
                "target_player_id": [978838],
            }
        ),
        heatmap_profiles=pd.DataFrame(
            {
                "player_id": [978838],
            }
        ),
    )


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


def test_readiness_route_is_in_openapi_schema() -> None:
    application = create_app()

    operation = application.openapi()["paths"]["/ready"]["get"]

    assert "200" in operation["responses"]
    assert "503" in operation["responses"]


def test_readiness_returns_runtime_metadata_without_catalog() -> None:
    application = create_app(
        settings=ApiSettings(
            environment="test",
            service_name="wc26-test-api",
        )
    )

    with TestClient(application) as client:
        health_response = client.get("/health")
        readiness_response = client.get("/ready")

    assert health_response.status_code == 200
    assert readiness_response.status_code == 503

    payload = readiness_response.json()

    assert payload["status"] == "not_ready"
    assert payload["service"] == "wc26-test-api"
    assert payload["version"] == __version__
    assert payload["environment"] == "test"
    assert payload["uptime_seconds"] >= 0.0
    assert payload["catalog_loaded_at"] is None
    assert _parse_datetime(payload["started_at"]).tzinfo == UTC


def test_readiness_returns_catalog_runtime_metadata() -> None:
    catalog = _catalog()

    loader_calls: list[
        tuple[
            Path,
            Path,
            Path,
            Path,
            Path,
        ]
    ] = []

    def fake_catalog_loader(
        *,
        features: Path,
        player_tournament_summary: Path,
        similarity: Path,
        heatmap_similarity: Path,
        heatmap_profiles: Path,
        heatmap_grids: Path,
    ) -> TransferDataCatalog:
        _ = player_tournament_summary
        loader_calls.append(
            (
                features,
                similarity,
                heatmap_similarity,
                heatmap_profiles,
                heatmap_grids,
            )
        )

        return catalog

    application = create_app(
        settings=ApiSettings(
            environment="test",
            service_name="wc26-ready-api",
        ),
        catalog_loader=fake_catalog_loader,
    )

    with TestClient(application) as client:
        runtime = application.state.api_runtime
        response = client.get("/ready")

        expected_started_at = runtime.started_at
        expected_catalog_loaded_at = runtime.catalog_loaded_at

        assert runtime.transfer_data_catalog is catalog

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ready"
    assert payload["service"] == "wc26-ready-api"
    assert payload["version"] == __version__
    assert payload["environment"] == "test"
    assert payload["uptime_seconds"] >= 0.0

    assert expected_started_at is not None
    assert expected_catalog_loaded_at is not None

    assert _parse_datetime(payload["started_at"]) == expected_started_at
    assert _parse_datetime(payload["catalog_loaded_at"]) == expected_catalog_loaded_at

    assert len(loader_calls) == 1
    assert loader_calls[0][-1] == (
        application.state.api_runtime.dataset_paths.heatmap_grids
    )
