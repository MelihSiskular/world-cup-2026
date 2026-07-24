"""Tests for catalog-backed API application-service runners."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence.catalog import (
    TransferDataCatalog,
)
from wc26.analytics.transfer_intelligence.models import (
    PlayerProfileRequest,
    PlayerProfileResult,
    PlayerSearchRequest,
    PlayerSearchResult,
    TransferAnalysisRequest,
    TransferAnalysisResult,
)
from wc26.api import dependencies


def _catalog() -> TransferDataCatalog:
    """Build a small in-memory dataset catalog."""

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


def test_catalog_player_search_runner_uses_catalog_players(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _catalog()

    request = PlayerSearchRequest(
        query="olise",
        limit=10,
        features=Path("unused-features.csv"),
    )

    expected = PlayerSearchResult(
        query="olise",
        players=(),
    )

    calls: list[
        tuple[
            PlayerSearchRequest,
            pd.DataFrame,
        ]
    ] = []

    def fake_search_players_from_dataframe(
        delegated_request: PlayerSearchRequest,
        dataframe: pd.DataFrame,
    ) -> PlayerSearchResult:
        calls.append(
            (
                delegated_request,
                dataframe,
            )
        )

        return expected

    monkeypatch.setattr(
        dependencies,
        "search_players_from_dataframe",
        fake_search_players_from_dataframe,
    )

    runner = dependencies.create_catalog_player_search_runner(catalog)

    result = runner(request)

    assert result is expected
    assert calls == [
        (
            request,
            catalog.players,
        )
    ]


def test_catalog_player_profile_runner_uses_catalog_players(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _catalog()

    request = PlayerProfileRequest(
        player_id=978838,
        features=Path("unused-features.csv"),
    )

    expected = cast(
        PlayerProfileResult,
        object(),
    )

    calls: list[
        tuple[
            PlayerProfileRequest,
            pd.DataFrame,
        ]
    ] = []

    def fake_get_player_profile_from_dataframe(
        delegated_request: PlayerProfileRequest,
        dataframe: pd.DataFrame,
    ) -> PlayerProfileResult:
        calls.append(
            (
                delegated_request,
                dataframe,
            )
        )

        return expected

    monkeypatch.setattr(
        dependencies,
        "get_player_profile_from_dataframe",
        fake_get_player_profile_from_dataframe,
    )

    runner = dependencies.create_catalog_player_profile_runner(catalog)

    result = runner(request)

    assert result is expected
    assert calls == [
        (
            request,
            catalog.players,
        )
    ]


def test_catalog_transfer_analysis_runner_uses_entire_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _catalog()

    request = TransferAnalysisRequest(
        player=None,
        player_id=978838,
        features=Path("unused-features.csv"),
        similarity=Path("unused-similarity.csv"),
        heatmap_similarity=Path("unused-heatmap-similarity.csv"),
        heatmap_profiles=Path("unused-heatmap-profiles.csv"),
        minimum_minutes=150.0,
        minimum_role_confidence=50.0,
        maximum_market_value=None,
        neutral_heatmap_score=70.0,
    )

    expected = TransferAnalysisResult(
        target={
            "player_id": 978838,
            "player_name": "Michael Olise",
        },
        modes=(),
    )

    calls: list[
        tuple[
            TransferAnalysisRequest,
            TransferDataCatalog,
        ]
    ] = []

    def fake_run_transfer_analysis_from_catalog(
        delegated_request: TransferAnalysisRequest,
        delegated_catalog: TransferDataCatalog,
    ) -> TransferAnalysisResult:
        calls.append(
            (
                delegated_request,
                delegated_catalog,
            )
        )

        return expected

    monkeypatch.setattr(
        dependencies,
        "run_transfer_analysis_from_catalog",
        fake_run_transfer_analysis_from_catalog,
    )

    runner = dependencies.create_catalog_transfer_analysis_runner(catalog)

    result = runner(request)

    assert result is expected
    assert calls == [
        (
            request,
            catalog,
        )
    ]
