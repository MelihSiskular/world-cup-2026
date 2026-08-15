from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest

from wc26.deployment.dataset_manifest import (
    DatasetDefinition,
    DatasetManifestError,
    generate_manifest,
    render_manifest,
)


def write_csv(
    path: Path,
    rows: list[list[str]],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerows(rows)


def test_generate_manifest_contains_dataset_metadata(
    tmp_path: Path,
) -> None:
    write_csv(
        tmp_path / "data/players.csv",
        [
            ["player_id", "player_name"],
            ["1", "Michael Olise"],
            ["2", "Lamine Yamal"],
        ],
    )

    definitions = (
        DatasetDefinition(
            key="players",
            relative_path=Path("data/players.csv"),
        ),
    )

    manifest = generate_manifest(
        repository_root=tmp_path,
        definitions=definitions,
    )

    assert manifest["manifest_version"] == 2
    assert len(manifest["bundle_sha256"]) == 64

    dataset = manifest["datasets"][0]

    assert dataset["key"] == "players"
    assert dataset["path"] == "data/players.csv"
    assert dataset["artifact_type"] == "csv"
    assert dataset["row_count"] == 2
    assert dataset["column_count"] == 2
    assert dataset["columns"] == (
        "player_id",
        "player_name",
    )
    assert dataset["size_bytes"] > 0
    assert len(dataset["sha256"]) == 64


def test_manifest_generation_is_deterministic(
    tmp_path: Path,
) -> None:
    write_csv(
        tmp_path / "data/runtime.csv",
        [
            ["id", "value"],
            ["1", "alpha"],
        ],
    )

    definitions = (
        DatasetDefinition(
            key="runtime",
            relative_path=Path("data/runtime.csv"),
        ),
    )

    first = generate_manifest(
        repository_root=tmp_path,
        definitions=definitions,
    )
    second = generate_manifest(
        repository_root=tmp_path,
        definitions=definitions,
    )

    assert first == second
    assert render_manifest(first) == render_manifest(second)


def test_manifest_rejects_duplicate_columns(
    tmp_path: Path,
) -> None:
    write_csv(
        tmp_path / "data/invalid.csv",
        [
            ["player_id", "player_id"],
            ["1", "1"],
        ],
    )

    definitions = (
        DatasetDefinition(
            key="invalid",
            relative_path=Path("data/invalid.csv"),
        ),
    )

    with pytest.raises(
        DatasetManifestError,
        match="duplicate column",
    ):
        generate_manifest(
            repository_root=tmp_path,
            definitions=definitions,
        )


def test_manifest_rejects_inconsistent_rows(
    tmp_path: Path,
) -> None:
    write_csv(
        tmp_path / "data/invalid.csv",
        [
            ["id", "name"],
            ["1", "Michael Olise", "extra"],
        ],
    )

    definitions = (
        DatasetDefinition(
            key="invalid",
            relative_path=Path("data/invalid.csv"),
        ),
    )

    with pytest.raises(
        DatasetManifestError,
        match="unexpected column count",
    ):
        generate_manifest(
            repository_root=tmp_path,
            definitions=definitions,
        )



def test_generate_manifest_contains_heatmap_grid_metadata(
    tmp_path: Path,
) -> None:
    dataset_path = (
        tmp_path
        / "data/player_heatmap_grids.npz"
    )
    dataset_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    first_grid = np.full(
        (2, 3),
        1.0 / 6.0,
        dtype=np.float32,
    )
    second_grid = np.full(
        (2, 3),
        1.0 / 6.0,
        dtype=np.float32,
    )

    np.savez(
        dataset_path,
        **{
            "978838": first_grid,
            "789071": second_grid,
        },
    )

    manifest = generate_manifest(
        repository_root=tmp_path,
        definitions=(
            DatasetDefinition(
                key="heatmap_grids",
                relative_path=Path(
                    "data/player_heatmap_grids.npz"
                ),
                artifact_type="heatmap_grid_npz",
            ),
        ),
    )

    dataset = manifest["datasets"][0]

    assert dataset["key"] == "heatmap_grids"
    assert dataset["artifact_type"] == "heatmap_grid_npz"
    assert dataset["grid_count"] == 2
    assert dataset["grid_height"] == 2
    assert dataset["grid_width"] == 3
    assert dataset["dtype"] == "float32"

    assert "row_count" not in dataset
    assert "column_count" not in dataset
    assert "columns" not in dataset

    assert dataset["size_bytes"] > 0
    assert len(dataset["sha256"]) == 64


def test_manifest_rejects_inconsistent_heatmap_grid_shapes(
    tmp_path: Path,
) -> None:
    dataset_path = (
        tmp_path
        / "data/player_heatmap_grids.npz"
    )
    dataset_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    np.savez(
        dataset_path,
        **{
            "1": np.full(
                (2, 2),
                0.25,
                dtype=np.float32,
            ),
            "2": np.full(
                (2, 3),
                1.0 / 6.0,
                dtype=np.float32,
            ),
        },
    )

    with pytest.raises(
        DatasetManifestError,
        match="inconsistent dimensions",
    ):
        generate_manifest(
            repository_root=tmp_path,
            definitions=(
                DatasetDefinition(
                    key="heatmap_grids",
                    relative_path=Path(
                        "data/player_heatmap_grids.npz"
                    ),
                    artifact_type="heatmap_grid_npz",
                ),
            ),
        )
