"""Tests for the API readiness endpoint."""

from __future__ import annotations

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


def test_readiness_route_is_in_openapi_schema() -> None:
    application = create_app()

    operation = application.openapi()["paths"]["/ready"]["get"]

    assert "200" in operation["responses"]
    assert "503" in operation["responses"]


def test_readiness_returns_503_without_runtime_catalog() -> None:
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

    assert readiness_response.json() == {
        "status": "not_ready",
        "service": "wc26-test-api",
        "version": __version__,
    }


def test_readiness_returns_200_with_runtime_catalog() -> None:
    catalog = _catalog()

    loader_calls: list[
        tuple[
            Path,
            Path,
            Path,
            Path,
        ]
    ] = []

    def fake_catalog_loader(
        *,
        features: Path,
        similarity: Path,
        heatmap_similarity: Path,
        heatmap_profiles: Path,
    ) -> TransferDataCatalog:
        loader_calls.append(
            (
                features,
                similarity,
                heatmap_similarity,
                heatmap_profiles,
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
        response = client.get("/ready")

        assert application.state.transfer_data_catalog is catalog

    assert response.status_code == 200

    assert response.json() == {
        "status": "ready",
        "service": "wc26-ready-api",
        "version": __version__,
    }

    assert len(loader_calls) == 1
