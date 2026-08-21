"""Tests for the single-player heatmap API route."""

from __future__ import annotations

from fastapi.testclient import TestClient

from wc26.analytics.transfer_intelligence.models import (
    HeatmapPlayerRequest,
    HeatmapPlayerResult,
)
from wc26.api import create_app
from wc26.api.dependencies import (
    HeatmapPlayerRunner,
    get_heatmap_player_runner,
)


def _build_heatmap() -> HeatmapPlayerResult:
    return HeatmapPlayerResult(
        player_id=978838,
        player_name="Michael Olise",
        available=True,
        grid_width=2,
        grid_height=2,
        grid=(
            (0.1, 0.4),
            (0.7, 1.0),
        ),
        matches_with_heatmap=6,
        heatmap_point_count=509,
        weighted_mean_x=61.3,
        weighted_mean_y=41.2,
        peak_cell_x=62.5,
        peak_cell_y=42.5,
        heatmap_entropy=0.81,
    )


def test_heatmap_player_route_is_in_openapi_schema() -> None:
    application = create_app()

    operation = application.openapi()["paths"][
        "/api/v1/transfer-intelligence/heatmap/{player_id}"
    ]

    assert "get" in operation


def test_heatmap_player_endpoint_delegates_to_service() -> None:
    application = create_app()

    captured: list[HeatmapPlayerRequest] = []

    def fake_runner(
        request: HeatmapPlayerRequest,
    ) -> HeatmapPlayerResult:
        captured.append(request)
        return _build_heatmap()

    def override_runner() -> HeatmapPlayerRunner:
        return fake_runner

    application.dependency_overrides[
        get_heatmap_player_runner
    ] = override_runner

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/transfer-intelligence/heatmap/978838"
        )

    assert response.status_code == 200

    assert captured == [
        HeatmapPlayerRequest(
            player_id=978838,
        )
    ]

    payload = response.json()

    assert payload["player_id"] == 978838
    assert payload["player_name"] == "Michael Olise"
    assert payload["available"] is True
    assert payload["grid_width"] == 2
    assert payload["grid_height"] == 2
    assert payload["weighted_mean_x"] == 61.3
    assert payload["weighted_mean_y"] == 41.2
    assert payload["matches_with_heatmap"] == 6
    assert payload["heatmap_point_count"] == 509
