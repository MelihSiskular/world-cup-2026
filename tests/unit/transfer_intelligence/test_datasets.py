from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence.datasets import (
    load_heatmap_profiles,
    load_heatmap_similarity,
    load_similarity,
)
from wc26.analytics.transfer_intelligence.errors import (
    DatasetNotFoundError,
    InvalidDatasetError,
)


def write_csv(
    path: Path,
    rows: list[dict[str, object]],
) -> None:
    pd.DataFrame(rows).to_csv(path, index=False)


def test_load_similarity_rejects_missing_file(
    tmp_path: Path,
) -> None:
    missing_path = tmp_path / "missing.csv"

    with pytest.raises(
        DatasetNotFoundError,
        match="Similarity file not found",
    ):
        load_similarity(missing_path)


def test_load_similarity_rejects_missing_columns(
    tmp_path: Path,
) -> None:
    path = tmp_path / "similarity.csv"
    write_csv(
        path,
        [
            {
                "source_player_id": 1,
                "target_player_id": 2,
            }
        ],
    )

    with pytest.raises(
        InvalidDatasetError,
        match="Missing similarity columns",
    ):
        load_similarity(path)


def test_load_similarity_converts_numeric_values_and_drops_invalid_rows(
    tmp_path: Path,
) -> None:
    path = tmp_path / "similarity.csv"
    write_csv(
        path,
        [
            {
                "source_player_id": "1",
                "target_player_id": "2",
                "overall_similarity_pct": "87.5",
                "unused_column": "ignored",
            },
            {
                "source_player_id": "invalid",
                "target_player_id": "3",
                "overall_similarity_pct": "70",
                "unused_column": "ignored",
            },
        ],
    )

    result = load_similarity(path)

    assert result.columns.tolist() == [
        "source_player_id",
        "target_player_id",
        "overall_similarity_pct",
    ]
    assert len(result) == 1
    assert result.iloc[0].to_dict() == {
        "source_player_id": 1.0,
        "target_player_id": 2.0,
        "overall_similarity_pct": 87.5,
    }


def test_load_heatmap_similarity_rejects_missing_file(
    tmp_path: Path,
) -> None:
    missing_path = tmp_path / "missing.csv"

    with pytest.raises(
        FileNotFoundError,
        match="Heatmap similarity file not found",
    ):
        load_heatmap_similarity(missing_path)


def test_load_heatmap_similarity_rejects_missing_columns(
    tmp_path: Path,
) -> None:
    path = tmp_path / "heatmap_similarity.csv"
    write_csv(
        path,
        [
            {
                "target_player_id": 1,
                "candidate_player_id": 2,
            }
        ],
    )

    with pytest.raises(
        ValueError,
        match="Missing heatmap similarity columns",
    ):
        load_heatmap_similarity(path)


def test_load_heatmap_similarity_keeps_available_metrics(
    tmp_path: Path,
) -> None:
    path = tmp_path / "heatmap_similarity.csv"
    write_csv(
        path,
        [
            {
                "target_player_id": "1",
                "candidate_player_id": "2",
                "heatmap_similarity_score_pct": "81.5",
                "occupation_overlap_pct": "76.0",
                "unused_column": "ignored",
            }
        ],
    )

    result = load_heatmap_similarity(path)

    assert result.columns.tolist() == [
        "target_player_id",
        "candidate_player_id",
        "occupation_overlap_pct",
        "heatmap_similarity_score_pct",
    ]
    assert result.iloc[0]["target_player_id"] == 1
    assert result.iloc[0]["candidate_player_id"] == 2
    assert result.iloc[0]["heatmap_similarity_score_pct"] == pytest.approx(81.5)


def test_load_heatmap_profiles_returns_empty_when_file_is_missing(
    tmp_path: Path,
) -> None:
    result = load_heatmap_profiles(tmp_path / "missing.csv")

    assert result.empty


def test_load_heatmap_profiles_returns_empty_without_player_id(
    tmp_path: Path,
) -> None:
    path = tmp_path / "profiles.csv"
    write_csv(
        path,
        [{"central_share": 0.4}],
    )

    result = load_heatmap_profiles(path)

    assert result.empty


def test_load_heatmap_profiles_cleans_ids_and_duplicates(
    tmp_path: Path,
) -> None:
    path = tmp_path / "profiles.csv"
    write_csv(
        path,
        [
            {
                "player_id": "10",
                "central_share": 0.4,
                "weighted_mean_x": 50,
                "unused_column": "ignored",
            },
            {
                "player_id": "10",
                "central_share": 0.8,
                "weighted_mean_x": 70,
                "unused_column": "ignored",
            },
            {
                "player_id": "invalid",
                "central_share": 0.2,
                "weighted_mean_x": 20,
                "unused_column": "ignored",
            },
        ],
    )

    result = load_heatmap_profiles(path)

    assert result.columns.tolist() == [
        "player_id",
        "central_share",
        "weighted_mean_x",
    ]
    assert len(result) == 1
    assert result.iloc[0]["player_id"] == 10
    assert result.iloc[0]["central_share"] == pytest.approx(0.4)
