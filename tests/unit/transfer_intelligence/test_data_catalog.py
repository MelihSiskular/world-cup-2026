"""Tests for the runtime Transfer Intelligence data catalog."""

from __future__ import annotations

from pathlib import Path

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

    monkeypatch.setattr(
        catalog_module,
        "load_player_features",
        load_players,
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

    result = catalog_module.load_transfer_data_catalog(
        features=features_path,
        similarity=similarity_path,
        heatmap_similarity=heatmap_similarity_path,
        heatmap_profiles=heatmap_profiles_path,
    )

    assert result.players is players
    assert result.similarity is similarity
    assert result.heatmap_similarity is heatmap_similarity
    assert result.heatmap_profiles is heatmap_profiles

    assert calls == [
        (
            "players",
            features_path,
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
    ]
