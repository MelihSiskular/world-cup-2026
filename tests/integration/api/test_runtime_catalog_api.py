"""Real-data integration tests for the runtime data catalog."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from wc26.analytics.transfer_intelligence import (
    catalog as catalog_module,
)
from wc26.api import create_app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("WC26_RUN_INTEGRATION") != "1",
        reason=("Set WC26_RUN_INTEGRATION=1 to run real-data integration tests."),
    ),
]


def test_runtime_catalog_loads_once_and_serves_complete_api_flow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify startup loading and request-time cache reuse."""

    project_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(project_root)

    calls: list[tuple[str, Path]] = []

    original_load_player_features = catalog_module.load_player_features
    original_load_similarity = catalog_module.load_similarity
    original_load_heatmap_similarity = catalog_module.load_heatmap_similarity
    original_load_heatmap_profiles = catalog_module.load_heatmap_profiles

    def counted_load_player_features(
        path: Path,
    ) -> pd.DataFrame:
        calls.append(
            (
                "players",
                path,
            )
        )

        return original_load_player_features(path)

    def counted_load_similarity(
        path: Path,
    ) -> pd.DataFrame:
        calls.append(
            (
                "similarity",
                path,
            )
        )

        return original_load_similarity(path)

    def counted_load_heatmap_similarity(
        path: Path,
    ) -> pd.DataFrame:
        calls.append(
            (
                "heatmap_similarity",
                path,
            )
        )

        return original_load_heatmap_similarity(path)

    def counted_load_heatmap_profiles(
        path: Path,
    ) -> pd.DataFrame:
        calls.append(
            (
                "heatmap_profiles",
                path,
            )
        )

        return original_load_heatmap_profiles(path)

    monkeypatch.setattr(
        catalog_module,
        "load_player_features",
        counted_load_player_features,
    )
    monkeypatch.setattr(
        catalog_module,
        "load_similarity",
        counted_load_similarity,
    )
    monkeypatch.setattr(
        catalog_module,
        "load_heatmap_similarity",
        counted_load_heatmap_similarity,
    )
    monkeypatch.setattr(
        catalog_module,
        "load_heatmap_profiles",
        counted_load_heatmap_profiles,
    )

    application = create_app(catalog_loader=(catalog_module.load_transfer_data_catalog))

    assert not hasattr(
        application.state,
        "transfer_data_catalog",
    )

    with TestClient(application) as client:
        runtime_catalog = application.state.transfer_data_catalog

        startup_calls = tuple(calls)

        assert [dataset_name for dataset_name, _ in startup_calls] == [
            "players",
            "similarity",
            "heatmap_similarity",
            "heatmap_profiles",
        ]

        assert not runtime_catalog.players.empty
        assert not runtime_catalog.similarity.empty
        assert not runtime_catalog.heatmap_similarity.empty

        search_response = client.get(
            "/api/v1/players/search",
            params={
                "q": "olise",
                "limit": 10,
            },
        )

        assert search_response.status_code == 200, search_response.text

        search_payload = search_response.json()

        michael_olise = next(
            player
            for player in search_payload["players"]
            if player["player_name"] == "Michael Olise"
        )

        player_id = michael_olise["player_id"]

        profile_response = client.get(f"/api/v1/players/{player_id}")

        assert profile_response.status_code == 200, profile_response.text

        analysis_response = client.post(
            "/api/v1/transfer-intelligence/analyze",
            json={
                "player_id": player_id,
            },
        )

        assert analysis_response.status_code == 200, analysis_response.text

        repeated_search_response = client.get(
            "/api/v1/players/search",
            params={
                "q": "michael",
                "limit": 10,
            },
        )

        assert repeated_search_response.status_code == 200, repeated_search_response.text

        assert application.state.transfer_data_catalog is runtime_catalog

        assert tuple(calls) == startup_calls

        profile_payload = profile_response.json()
        analysis_payload = analysis_response.json()

        assert player_id == 978838

        assert profile_payload["player_id"] == player_id
        assert profile_payload["player_name"] == "Michael Olise"

        assert analysis_payload["target"]["player_id"] == player_id
        assert analysis_payload["target"]["player_name"] == "Michael Olise"

    assert not hasattr(
        application.state,
        "transfer_data_catalog",
    )
