"""Tests for the runtime Transfer Intelligence data catalog."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence import catalog as catalog_module
from wc26.analytics.transfer_intelligence.datasets import (
    load_player_features,
)
from wc26.analytics.transfer_intelligence.errors import (
    DatasetNotFoundError,
    InvalidDatasetError,
)


def test_load_player_features_returns_full_table(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "players.csv"

    expected = pd.DataFrame(
        {
            "player_id": [978838, 12994],
            "player_name": [
                "Michael Olise",
                "Lionel Messi",
            ],
            "minutes": [520.0, 610.0],
        }
    )

    expected.to_csv(
        dataset_path,
        index=False,
    )

    result = load_player_features(dataset_path)

    pd.testing.assert_frame_equal(
        result,
        expected,
    )


def test_load_player_features_rejects_missing_file(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "missing.csv"

    with pytest.raises(
        DatasetNotFoundError,
        match="Player feature table not found",
    ):
        load_player_features(dataset_path)


def test_load_player_features_maps_csv_read_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "players.csv"
    dataset_path.touch()

    def raise_empty_data_error(
        path: Path,
        *,
        low_memory: bool,
    ) -> pd.DataFrame:
        del path
        del low_memory

        raise pd.errors.EmptyDataError("No columns to parse from file")

    monkeypatch.setattr(
        pd,
        "read_csv",
        raise_empty_data_error,
    )

    with pytest.raises(
        InvalidDatasetError,
        match="Player feature table could not be read",
    ):
        load_player_features(dataset_path)


def test_load_transfer_data_catalog_loads_each_dataset_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    features_path = Path("players.csv")
    similarity_path = Path("similarity.csv")
    heatmap_similarity_path = Path("heatmap_similarity.csv")
    heatmap_profiles_path = Path("heatmap_profiles.csv")
    heatmap_grids_path = Path("heatmap_grids.npz")
    player_tournament_summary_path = Path("player_tournament_summary.csv")

    players = pd.DataFrame(
        {
            "player_id": [978838],
        }
    )
    similarity = pd.DataFrame(
        {
            "source_player_id": [978838],
        }
    )
    heatmap_similarity = pd.DataFrame(
        {
            "target_player_id": [978838],
        }
    )
    heatmap_profiles = pd.DataFrame(
        {
            "player_id": [978838],
        }
    )
    heatmap_grids: Mapping[int, np.ndarray] = {
        978838: np.full(
            (2, 2),
            0.25,
            dtype=np.float32,
        )
    }
    player_tournament_summary = pd.DataFrame(
        {
            "player_id": [978838],
            "player_primary_position": ["M"],
            "matches_played": [8],
            "starts": [8],
            "substitute_appearances": [0],
            "captain_appearances": [0],
            "total_minutes": [650],
            "formations_used": [1],
            "primary_formation": ["4-2-3-1"],
            "primary_lineup_position": ["M"],
        }
    )

    calls: list[tuple[str, Path]] = []

    def load_players(
        path: Path,
    ) -> pd.DataFrame:
        calls.append(
            (
                "players",
                path,
            )
        )
        return players

    def load_similarity(
        path: Path,
    ) -> pd.DataFrame:
        calls.append(
            (
                "similarity",
                path,
            )
        )
        return similarity

    def load_heatmap_similarity(
        path: Path,
    ) -> pd.DataFrame:
        calls.append(
            (
                "heatmap_similarity",
                path,
            )
        )
        return heatmap_similarity

    def load_heatmap_profiles(
        path: Path,
    ) -> pd.DataFrame:
        calls.append(
            (
                "heatmap_profiles",
                path,
            )
        )
        return heatmap_profiles

    def load_heatmap_grids(
        path: Path,
    ) -> Mapping[int, np.ndarray]:
        calls.append(
            (
                "heatmap_grids",
                path,
            )
        )
        return heatmap_grids

    def load_player_tournament_summary(
        path: Path,
    ) -> pd.DataFrame:
        calls.append(
            (
                "player_tournament_summary",
                path,
            )
        )
        return player_tournament_summary

    monkeypatch.setattr(
        catalog_module,
        "load_player_features",
        load_players,
    )
    monkeypatch.setattr(
        catalog_module,
        "load_player_tournament_summary",
        load_player_tournament_summary,
    )
    monkeypatch.setattr(
        catalog_module,
        "load_similarity",
        load_similarity,
    )
    monkeypatch.setattr(
        catalog_module,
        "load_heatmap_similarity",
        load_heatmap_similarity,
    )
    monkeypatch.setattr(
        catalog_module,
        "load_heatmap_profiles",
        load_heatmap_profiles,
    )
    monkeypatch.setattr(
        catalog_module,
        "load_heatmap_grids",
        load_heatmap_grids,
    )

    result = catalog_module.load_transfer_data_catalog(
        features=features_path,
        similarity=similarity_path,
        heatmap_similarity=heatmap_similarity_path,
        heatmap_profiles=heatmap_profiles_path,
        player_tournament_summary=(player_tournament_summary_path),
        heatmap_grids=heatmap_grids_path,
    )

    assert result.players is players
    assert result.similarity is similarity
    assert result.heatmap_similarity is heatmap_similarity
    assert result.heatmap_profiles is heatmap_profiles
    assert result.heatmap_grids is heatmap_grids
    assert result.player_tournament_summary is player_tournament_summary

    assert len(calls) == 6
    assert set(calls) == {
        (
            "players",
            features_path,
        ),
        (
            "player_tournament_summary",
            player_tournament_summary_path,
        ),
        (
            "similarity",
            similarity_path,
        ),
        (
            "heatmap_similarity",
            heatmap_similarity_path,
        ),
        (
            "heatmap_profiles",
            heatmap_profiles_path,
        ),
        (
            "heatmap_grids",
            heatmap_grids_path,
        ),
    }
