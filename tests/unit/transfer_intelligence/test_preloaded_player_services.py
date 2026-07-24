"""Tests for services using preloaded player datasets."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence import (
    player_profile as player_profile_module,
)
from wc26.analytics.transfer_intelligence import (
    player_search as player_search_module,
)
from wc26.analytics.transfer_intelligence.models import (
    PlayerProfileRequest,
    PlayerSearchRequest,
)
from wc26.analytics.transfer_intelligence.player_profile import (
    get_player_profile,
    get_player_profile_from_dataframe,
)
from wc26.analytics.transfer_intelligence.player_search import (
    search_players,
    search_players_from_dataframe,
)


def _player_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "player_id": 978838,
                "player_name": "Michael Olise",
                "national_team_name": "France",
                "country_name": "France",
                "position": "M",
                "age": 24.6,
                "height_cm": 184.0,
                "appearances": 7,
                "starts": 6,
                "minutes": 520.0,
                "weighted_rating": 7.44,
                "market_value": 144_000_000.0,
                "market_value_currency": "EUR",
                "archetype": "Wide Creator",
                "spatial_role": "Central Creator",
                "final_role": ("Advanced Central Playmaker"),
                "lateral_profile": "Right",
                "vertical_profile": "Advanced",
                "mobility_profile": "Mobile",
                "role_confidence_pct": 88.0,
                "spatial_reliability": 90.0,
                "data_reliability_score": 92.0,
                "player_quality_score": 89.0,
                "role_reason": "Creative attacking profile.",
            }
        ]
    )


def test_search_players_from_dataframe_ignores_dataset_path(
    tmp_path: Path,
) -> None:
    dataframe = _player_dataframe()
    original = dataframe.copy(deep=True)

    request = PlayerSearchRequest(
        query="olise",
        limit=10,
        features=tmp_path / "missing.csv",
    )

    result = search_players_from_dataframe(
        request,
        dataframe,
    )

    assert len(result.players) == 1
    assert result.players[0].player_id == 978838
    assert result.players[0].player_name == "Michael Olise"

    pd.testing.assert_frame_equal(
        dataframe,
        original,
    )


def test_get_player_profile_from_dataframe_ignores_dataset_path(
    tmp_path: Path,
) -> None:
    dataframe = _player_dataframe()
    original = dataframe.copy(deep=True)

    request = PlayerProfileRequest(
        player_id=978838,
        features=tmp_path / "missing.csv",
    )

    result = get_player_profile_from_dataframe(
        request,
        dataframe,
    )

    assert result.player_id == 978838
    assert result.player_name == "Michael Olise"

    pd.testing.assert_frame_equal(
        dataframe,
        original,
    )


def test_search_players_uses_shared_feature_loader(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    dataframe = _player_dataframe()
    dataset_path = tmp_path / "players.csv"
    calls: list[Path] = []

    def fake_loader(
        path: Path,
    ) -> pd.DataFrame:
        calls.append(path)
        return dataframe

    monkeypatch.setattr(
        player_search_module,
        "load_player_features",
        fake_loader,
    )

    result = search_players(
        PlayerSearchRequest(
            query="michael",
            limit=10,
            features=dataset_path,
        )
    )

    assert calls == [dataset_path]
    assert result.players[0].player_id == 978838


def test_get_player_profile_uses_shared_feature_loader(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    dataframe = _player_dataframe()
    dataset_path = tmp_path / "players.csv"
    calls: list[Path] = []

    def fake_loader(
        path: Path,
    ) -> pd.DataFrame:
        calls.append(path)
        return dataframe

    monkeypatch.setattr(
        player_profile_module,
        "load_player_features",
        fake_loader,
    )

    result = get_player_profile(
        PlayerProfileRequest(
            player_id=978838,
            features=dataset_path,
        )
    )

    assert calls == [dataset_path]
    assert result.player_id == 978838
