"""Tests for player-discovery filter metadata API."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from wc26.analytics.transfer_intelligence.catalog import (
    TransferDataCatalog,
)
from wc26.analytics.transfer_intelligence.models import (
    PlayerSearchFilterOption,
    PlayerSearchFilterRange,
    PlayerSearchFiltersRequest,
    PlayerSearchFiltersResult,
)
from wc26.api import create_app, dependencies
from wc26.api.dependencies import (
    PlayerSearchFiltersRunner,
    TransferDatasetPaths,
    get_player_search_filters_runner,
    get_transfer_dataset_paths,
)


def _filter_result() -> PlayerSearchFiltersResult:
    return PlayerSearchFiltersResult(
        player_count=3,
        positions=(
            PlayerSearchFilterOption(
                value="D",
                label="Defender",
                count=2,
            ),
            PlayerSearchFilterOption(
                value="F",
                label="Forward",
                count=1,
            ),
        ),
        final_roles=(
            PlayerSearchFilterOption(
                value="Poacher",
                label="Poacher",
                count=1,
            ),
        ),
        archetypes=(
            PlayerSearchFilterOption(
                value="Ball-Carrying Defender",
                label="Ball-Carrying Defender",
                count=2,
            ),
        ),
        countries=(
            PlayerSearchFilterOption(
                value="France",
                label="France",
                count=2,
                country_alpha3="FRA",
            ),
        ),
        age=PlayerSearchFilterRange(
            minimum=21.0,
            maximum=29.0,
        ),
        market_value=PlayerSearchFilterRange(
            minimum=10_000_000.0,
            maximum=50_000_000.0,
        ),
        minutes=PlayerSearchFilterRange(
            minimum=300.0,
            maximum=700.0,
        ),
        role_confidence=PlayerSearchFilterRange(
            minimum=70.0,
            maximum=90.0,
        ),
        data_reliability=PlayerSearchFilterRange(
            minimum=60.0,
            maximum=88.0,
        ),
        market_value_currency="EUR",
    )


def test_player_search_filters_route_is_in_openapi_schema() -> None:
    application = create_app()

    operation = application.openapi()["paths"]["/api/v1/players/search/filters"]

    assert "get" in operation


def test_player_search_filters_endpoint_delegates_to_service() -> None:
    application = create_app()

    dataset_paths = TransferDatasetPaths(
        features=Path("test-data/features.csv"),
        player_tournament_summary=Path("test-data/summary.csv"),
        similarity=Path("test-data/similarity.csv"),
        heatmap_similarity=Path("test-data/heatmap-similarity.csv"),
        heatmap_profiles=Path("test-data/heatmap-profiles.csv"),
    )

    captured_requests: list[PlayerSearchFiltersRequest] = []

    def override_dataset_paths() -> TransferDatasetPaths:
        return dataset_paths

    def fake_filter_runner(
        request: PlayerSearchFiltersRequest,
    ) -> PlayerSearchFiltersResult:
        captured_requests.append(request)

        return _filter_result()

    def override_filter_runner() -> PlayerSearchFiltersRunner:
        return fake_filter_runner

    application.dependency_overrides[get_transfer_dataset_paths] = override_dataset_paths

    application.dependency_overrides[get_player_search_filters_runner] = override_filter_runner

    with TestClient(application) as client:
        response = client.get("/api/v1/players/search/filters")

    assert response.status_code == 200

    assert captured_requests == [
        PlayerSearchFiltersRequest(
            features=dataset_paths.features,
            player_tournament_summary=(dataset_paths.player_tournament_summary),
        )
    ]

    assert response.json() == {
        "player_count": 3,
        "positions": [
            {
                "value": "D",
                "label": "Defender",
                "count": 2,
                "country_alpha3": None,
            },
            {
                "value": "F",
                "label": "Forward",
                "count": 1,
                "country_alpha3": None,
            },
        ],
        "final_roles": [
            {
                "value": "Poacher",
                "label": "Poacher",
                "count": 1,
                "country_alpha3": None,
            }
        ],
        "archetypes": [
            {
                "value": "Ball-Carrying Defender",
                "label": "Ball-Carrying Defender",
                "count": 2,
                "country_alpha3": None,
            }
        ],
        "countries": [
            {
                "value": "France",
                "label": "France",
                "count": 2,
                "country_alpha3": "FRA",
            }
        ],
        "age": {
            "minimum": 21.0,
            "maximum": 29.0,
        },
        "market_value": {
            "minimum": 10_000_000.0,
            "maximum": 50_000_000.0,
        },
        "minutes": {
            "minimum": 300.0,
            "maximum": 700.0,
        },
        "role_confidence": {
            "minimum": 70.0,
            "maximum": 90.0,
        },
        "data_reliability": {
            "minimum": 60.0,
            "maximum": 88.0,
        },
        "market_value_currency": "EUR",
    }


def test_catalog_filter_runner_uses_preloaded_datasets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    players = pd.DataFrame(
        {
            "player_id": [1],
        }
    )
    summary = pd.DataFrame(
        {
            "player_id": [1],
            "country_alpha3": ["FRA"],
        }
    )

    catalog = TransferDataCatalog(
        players=players,
        player_tournament_summary=summary,
        similarity=pd.DataFrame(),
        heatmap_similarity=pd.DataFrame(),
        heatmap_profiles=pd.DataFrame(),
    )

    request = PlayerSearchFiltersRequest(
        features=Path("unused-features.csv"),
        player_tournament_summary=Path("unused-summary.csv"),
    )

    expected = _filter_result()

    calls: list[
        tuple[
            pd.DataFrame,
            pd.DataFrame,
        ]
    ] = []

    def fake_get_filters_from_dataframe(
        dataframe: pd.DataFrame,
        tournament_summary: pd.DataFrame | None = None,
    ) -> PlayerSearchFiltersResult:
        assert tournament_summary is not None

        calls.append(
            (
                dataframe,
                tournament_summary,
            )
        )

        return expected

    monkeypatch.setattr(
        dependencies,
        "get_player_search_filters_from_dataframe",
        fake_get_filters_from_dataframe,
    )

    runner = dependencies.create_catalog_player_search_filters_runner(catalog)

    result = runner(request)

    assert result is expected
    assert calls == [
        (
            catalog.players,
            catalog.player_tournament_summary,
        )
    ]


def test_player_search_filters_endpoint_hides_unexpected_errors() -> None:
    application = create_app()

    def failing_filter_runner(
        request: PlayerSearchFiltersRequest,
    ) -> PlayerSearchFiltersResult:
        del request

        raise RuntimeError("sensitive filter metadata detail")

    def override_filter_runner() -> PlayerSearchFiltersRunner:
        return failing_filter_runner

    application.dependency_overrides[get_player_search_filters_runner] = override_filter_runner

    with TestClient(application) as client:
        response = client.get("/api/v1/players/search/filters")

    assert response.status_code == 500

    assert response.json() == {
        "error": {
            "code": "player_search_failed",
            "message": ("Player search could not be completed."),
        }
    }

    assert "sensitive filter metadata detail" not in response.text
