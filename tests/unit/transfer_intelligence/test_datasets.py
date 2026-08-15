from __future__ import annotations

import operator
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence.datasets import (
    load_heatmap_grids,
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



def test_load_heatmap_grids_loads_immutable_grids(
    tmp_path: Path,
) -> None:
    path = tmp_path / "heatmap_grids.npz"

    olise_grid = np.array(
        [
            [0.1, 0.2],
            [0.3, 0.4],
        ],
        dtype=np.float64,
    )
    olmo_grid = np.full(
        (2, 2),
        0.25,
        dtype=np.float64,
    )

    np.savez(
        path,
        **{
            "978838": olise_grid,
            "789071": olmo_grid,
        },
    )

    result = load_heatmap_grids(path)

    assert set(result) == {
        978838,
        789071,
    }

    assert result[978838].shape == (2, 2)
    assert result[978838].dtype == np.float32

    np.testing.assert_allclose(
        result[978838],
        olise_grid,
    )

    assert not result[978838].flags.writeable
    assert not result[789071].flags.writeable

    with pytest.raises(ValueError):
        result[978838][0, 0] = 0.0

    with pytest.raises(TypeError):
        operator.setitem(
            result,
            123,
            result[978838],
        )


def test_load_heatmap_grids_rejects_missing_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "missing.npz"

    with pytest.raises(
        DatasetNotFoundError,
        match="Heatmap grid archive not found",
    ):
        load_heatmap_grids(path)


def test_load_heatmap_grids_rejects_malformed_archive(
    tmp_path: Path,
) -> None:
    path = tmp_path / "heatmap_grids.npz"

    path.write_text(
        "not an npz archive",
        encoding="utf-8",
    )

    with pytest.raises(
        InvalidDatasetError,
        match="Heatmap grid archive could not be read",
    ):
        load_heatmap_grids(path)


def test_load_heatmap_grids_rejects_empty_archive(
    tmp_path: Path,
) -> None:
    path = tmp_path / "heatmap_grids.npz"

    np.savez(path)

    with pytest.raises(
        InvalidDatasetError,
        match="contains no player grids",
    ):
        load_heatmap_grids(path)


def test_load_heatmap_grids_rejects_invalid_player_key(
    tmp_path: Path,
) -> None:
    path = tmp_path / "heatmap_grids.npz"

    grid = np.full(
        (2, 2),
        0.25,
        dtype=np.float32,
    )

    np.savez(
        path,
        **{
            "player-x": grid,
        },
    )

    with pytest.raises(
        InvalidDatasetError,
        match="invalid player key",
    ):
        load_heatmap_grids(path)


@pytest.mark.parametrize(
    "player_key",
    [
        "0",
        "-1",
    ],
)
def test_load_heatmap_grids_rejects_non_positive_player_id(
    tmp_path: Path,
    player_key: str,
) -> None:
    path = tmp_path / "heatmap_grids.npz"

    grid = np.full(
        (2, 2),
        0.25,
        dtype=np.float32,
    )

    np.savez(
        path,
        **{
            player_key: grid,
        },
    )

    with pytest.raises(
        InvalidDatasetError,
        match="non-positive player ID",
    ):
        load_heatmap_grids(path)


def test_load_heatmap_grids_rejects_duplicate_canonical_player_id(
    tmp_path: Path,
) -> None:
    path = tmp_path / "heatmap_grids.npz"

    grid = np.full(
        (2, 2),
        0.25,
        dtype=np.float32,
    )

    np.savez(
        path,
        **{
            "1": grid,
            "01": grid,
        },
    )

    with pytest.raises(
        InvalidDatasetError,
        match="duplicate player ID",
    ):
        load_heatmap_grids(path)


@pytest.mark.parametrize(
    "grid",
    [
        np.array(
            [0.25, 0.25, 0.25, 0.25],
            dtype=np.float32,
        ),
        np.full(
            (2, 2, 2),
            0.125,
            dtype=np.float32,
        ),
    ],
)
def test_load_heatmap_grids_rejects_non_2d_grid(
    tmp_path: Path,
    grid: np.ndarray,
) -> None:
    path = tmp_path / "heatmap_grids.npz"

    np.savez(
        path,
        **{
            "1": grid,
        },
    )

    with pytest.raises(
        InvalidDatasetError,
        match="must be two-dimensional",
    ):
        load_heatmap_grids(path)


def test_load_heatmap_grids_rejects_too_small_dimensions(
    tmp_path: Path,
) -> None:
    path = tmp_path / "heatmap_grids.npz"

    grid = np.array(
        [
            [0.5, 0.5],
        ],
        dtype=np.float32,
    )

    np.savez(
        path,
        **{
            "1": grid,
        },
    )

    with pytest.raises(
        InvalidDatasetError,
        match="must both be at least 2",
    ):
        load_heatmap_grids(path)


def test_load_heatmap_grids_rejects_inconsistent_shapes(
    tmp_path: Path,
) -> None:
    path = tmp_path / "heatmap_grids.npz"

    first_grid = np.full(
        (2, 2),
        0.25,
        dtype=np.float32,
    )
    second_grid = np.full(
        (2, 3),
        1.0 / 6.0,
        dtype=np.float32,
    )

    np.savez(
        path,
        **{
            "1": first_grid,
            "2": second_grid,
        },
    )

    with pytest.raises(
        InvalidDatasetError,
        match="inconsistent grid dimensions",
    ):
        load_heatmap_grids(path)


@pytest.mark.parametrize(
    "invalid_value",
    [
        np.nan,
        np.inf,
    ],
)
def test_load_heatmap_grids_rejects_non_finite_values(
    tmp_path: Path,
    invalid_value: float,
) -> None:
    path = tmp_path / "heatmap_grids.npz"

    grid = np.array(
        [
            [invalid_value, 0.2],
            [0.3, 0.5],
        ],
        dtype=np.float32,
    )

    np.savez(
        path,
        **{
            "1": grid,
        },
    )

    with pytest.raises(
        InvalidDatasetError,
        match="contains non-finite values",
    ):
        load_heatmap_grids(path)


def test_load_heatmap_grids_rejects_negative_density(
    tmp_path: Path,
) -> None:
    path = tmp_path / "heatmap_grids.npz"

    grid = np.array(
        [
            [-0.1, 0.4],
            [0.3, 0.4],
        ],
        dtype=np.float32,
    )

    np.savez(
        path,
        **{
            "1": grid,
        },
    )

    with pytest.raises(
        InvalidDatasetError,
        match="contains negative density",
    ):
        load_heatmap_grids(path)


def test_load_heatmap_grids_rejects_non_normalized_grid(
    tmp_path: Path,
) -> None:
    path = tmp_path / "heatmap_grids.npz"

    grid = np.full(
        (2, 2),
        0.2,
        dtype=np.float32,
    )

    np.savez(
        path,
        **{
            "1": grid,
        },
    )

    with pytest.raises(
        InvalidDatasetError,
        match="is not normalized",
    ):
        load_heatmap_grids(path)


def test_load_heatmap_profiles_keeps_sample_evidence(
    tmp_path: Path,
) -> None:
    path = tmp_path / "profiles.csv"

    write_csv(
        path,
        [
            {
                "player_id": "978838",
                "matches_with_heatmap": "7",
                "heatmap_point_count": "312",
                "weighted_mean_x": "58.4",
                "weighted_mean_y": "41.2",
            }
        ],
    )

    result = load_heatmap_profiles(path)

    assert len(result) == 1
    assert result.iloc[0]["player_id"] == 978838
    assert result.iloc[0]["matches_with_heatmap"] == 7
    assert result.iloc[0]["heatmap_point_count"] == 312
