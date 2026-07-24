"""Tests for the FastAPI runtime data-catalog lifespan."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from wc26.analytics.transfer_intelligence.catalog import (
    TransferDataCatalog,
)
from wc26.analytics.transfer_intelligence.errors import (
    InvalidDatasetError,
)
from wc26.analytics.transfer_intelligence.models import (
    PlayerSearchItem,
    PlayerSearchRequest,
    PlayerSearchResult,
)
from wc26.api import create_app, dependencies
from wc26.api.dependencies import TransferDatasetPaths


def _catalog() -> TransferDataCatalog:
    """Build a small in-memory runtime catalog."""

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


def _dataset_paths() -> TransferDatasetPaths:
    """Return deterministic application dataset paths."""

    return TransferDatasetPaths(
        features=Path("runtime/features.csv"),
        similarity=Path("runtime/similarity.csv"),
        heatmap_similarity=Path("runtime/heatmap-similarity.csv"),
        heatmap_profiles=Path("runtime/heatmap-profiles.csv"),
    )


def test_application_lifespan_loads_catalog_once() -> None:
    catalog = _catalog()
    dataset_paths = _dataset_paths()

    calls: list[
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
        calls.append(
            (
                features,
                similarity,
                heatmap_similarity,
                heatmap_profiles,
            )
        )

        return catalog

    application = create_app(
        dataset_paths=dataset_paths,
        catalog_loader=fake_catalog_loader,
    )

    assert not hasattr(
        application.state,
        "transfer_data_catalog",
    )

    with TestClient(application) as client:
        first_response = client.get("/health")
        second_response = client.get("/health")

        assert first_response.status_code == 200
        assert second_response.status_code == 200

        assert application.state.transfer_data_catalog is catalog

    assert calls == [
        (
            dataset_paths.features,
            dataset_paths.similarity,
            dataset_paths.heatmap_similarity,
            dataset_paths.heatmap_profiles,
        )
    ]

    assert not hasattr(
        application.state,
        "transfer_data_catalog",
    )


def test_player_search_uses_startup_loaded_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _catalog()
    dataset_paths = _dataset_paths()

    captured_calls: list[
        tuple[
            PlayerSearchRequest,
            pd.DataFrame,
        ]
    ] = []

    def fake_search_players_from_dataframe(
        request: PlayerSearchRequest,
        dataframe: pd.DataFrame,
    ) -> PlayerSearchResult:
        captured_calls.append(
            (
                request,
                dataframe,
            )
        )

        return PlayerSearchResult(
            query=request.query,
            players=(
                PlayerSearchItem(
                    player_id=978838,
                    player_name="Michael Olise",
                    national_team_name="France",
                    position="M",
                    final_role=("Advanced Central Playmaker"),
                    archetype="Wide Creator",
                    age=24.6,
                    market_value=144_000_000.0,
                    market_value_currency="EUR",
                ),
            ),
        )

    def fail_path_based_search(
        request: PlayerSearchRequest,
    ) -> PlayerSearchResult:
        del request

        raise AssertionError("Path-based player search was called.")

    monkeypatch.setattr(
        dependencies,
        "search_players_from_dataframe",
        fake_search_players_from_dataframe,
    )
    monkeypatch.setattr(
        dependencies,
        "search_players",
        fail_path_based_search,
    )

    def fake_catalog_loader(
        *,
        features: Path,
        similarity: Path,
        heatmap_similarity: Path,
        heatmap_profiles: Path,
    ) -> TransferDataCatalog:
        del (
            features,
            similarity,
            heatmap_similarity,
            heatmap_profiles,
        )

        return catalog

    application = create_app(
        dataset_paths=dataset_paths,
        catalog_loader=fake_catalog_loader,
    )

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/players/search",
            params={
                "q": "olise",
                "limit": 5,
            },
        )

    assert response.status_code == 200

    assert captured_calls == [
        (
            PlayerSearchRequest(
                query="olise",
                features=dataset_paths.features,
                limit=5,
            ),
            catalog.players,
        )
    ]

    assert response.json()["players"][0]["player_id"] == 978838


def test_application_without_catalog_uses_path_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = PlayerSearchResult(
        query="olise",
        players=(),
    )

    calls: list[PlayerSearchRequest] = []

    def fake_path_based_search(
        request: PlayerSearchRequest,
    ) -> PlayerSearchResult:
        calls.append(request)

        return expected

    def fail_catalog_search(
        request: PlayerSearchRequest,
        dataframe: pd.DataFrame,
    ) -> PlayerSearchResult:
        del request
        del dataframe

        raise AssertionError("Catalog player search was called.")

    monkeypatch.setattr(
        dependencies,
        "search_players",
        fake_path_based_search,
    )
    monkeypatch.setattr(
        dependencies,
        "search_players_from_dataframe",
        fail_catalog_search,
    )

    application = create_app()

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/players/search",
            params={
                "q": "olise",
            },
        )

    assert response.status_code == 200
    assert len(calls) == 1
    assert calls[0].query == "olise"


def test_catalog_loading_failure_stops_application_startup() -> None:
    def failing_catalog_loader(
        *,
        features: Path,
        similarity: Path,
        heatmap_similarity: Path,
        heatmap_profiles: Path,
    ) -> TransferDataCatalog:
        del (
            features,
            similarity,
            heatmap_similarity,
            heatmap_profiles,
        )

        raise InvalidDatasetError("Runtime catalog could not be loaded.")

    application = create_app(
        catalog_loader=failing_catalog_loader,
    )

    with pytest.raises(
        InvalidDatasetError,
        match="Runtime catalog could not be loaded",
    ):
        with TestClient(application):
            pass
