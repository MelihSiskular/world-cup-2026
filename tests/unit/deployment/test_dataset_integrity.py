from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest

from wc26.deployment.dataset_integrity import (
    DatasetIntegrityError,
    validate_runtime_dataset_integrity,
)
from wc26.deployment.dataset_manifest import (
    DatasetDefinition,
    calculate_bundle_sha256,
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
        csv.writer(file).writerows(rows)


def create_runtime_bundle(
    tmp_path: Path,
) -> tuple[Path, Path]:
    dataset_path = tmp_path / "runtime/players.csv"

    write_csv(
        dataset_path,
        [
            ["player_id", "player_name"],
            ["978838", "Michael Olise"],
            ["100000", "Lamine Yamal"],
        ],
    )

    manifest = generate_manifest(
        repository_root=tmp_path,
        definitions=(
            DatasetDefinition(
                key="players",
                relative_path=Path("runtime/players.csv"),
            ),
        ),
    )

    manifest_path = tmp_path / "config/manifest.json"
    manifest_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    manifest_path.write_text(
        render_manifest(manifest),
        encoding="utf-8",
    )

    return manifest_path, dataset_path


def test_runtime_dataset_integrity_passes(
    tmp_path: Path,
) -> None:
    manifest_path, dataset_path = create_runtime_bundle(tmp_path)

    report = validate_runtime_dataset_integrity(
        manifest_path=manifest_path,
        dataset_paths={
            "players": dataset_path,
        },
    )

    assert report.dataset_count == 1
    assert report.total_size_bytes == (dataset_path.stat().st_size)
    assert len(report.bundle_sha256) == 64


def test_runtime_dataset_integrity_rejects_tampered_file(
    tmp_path: Path,
) -> None:
    manifest_path, dataset_path = create_runtime_bundle(tmp_path)

    with dataset_path.open(
        "a",
        encoding="utf-8",
        newline="",
    ) as file:
        csv.writer(file).writerow(["200000", "Tampered Player"])

    with pytest.raises(
        DatasetIntegrityError,
        match="integrity validation failed",
    ) as error:
        validate_runtime_dataset_integrity(
            manifest_path=manifest_path,
            dataset_paths={
                "players": dataset_path,
            },
        )

    message = str(error.value)

    assert "size mismatch" in message
    assert "SHA-256 mismatch" in message
    assert "row count mismatch" in message


def test_runtime_dataset_integrity_rejects_schema_change(
    tmp_path: Path,
) -> None:
    manifest_path, dataset_path = create_runtime_bundle(tmp_path)

    content = dataset_path.read_text(encoding="utf-8")
    dataset_path.write_text(
        content.replace(
            "player_name",
            "player_namo",
            1,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        DatasetIntegrityError,
        match="column names mismatch",
    ):
        validate_runtime_dataset_integrity(
            manifest_path=manifest_path,
            dataset_paths={
                "players": dataset_path,
            },
        )


def test_runtime_dataset_integrity_rejects_bundle_hash_change(
    tmp_path: Path,
) -> None:
    manifest_path, dataset_path = create_runtime_bundle(tmp_path)

    manifest = json.loads(
        manifest_path.read_text(
            encoding="utf-8",
        )
    )
    manifest["bundle_sha256"] = "0" * 64

    manifest_path.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        DatasetIntegrityError,
        match="bundle checksum mismatch",
    ):
        validate_runtime_dataset_integrity(
            manifest_path=manifest_path,
            dataset_paths={
                "players": dataset_path,
            },
        )


def test_runtime_dataset_integrity_rejects_missing_key(
    tmp_path: Path,
) -> None:
    manifest_path, _ = create_runtime_bundle(tmp_path)

    with pytest.raises(
        DatasetIntegrityError,
        match=r"missing=\[\'players\'\]",
    ):
        validate_runtime_dataset_integrity(
            manifest_path=manifest_path,
            dataset_paths={},
        )


def test_runtime_dataset_can_use_external_path(
    tmp_path: Path,
) -> None:
    manifest_path, dataset_path = create_runtime_bundle(tmp_path)

    external_path = tmp_path / "mounted-data/players.csv"
    external_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    external_path.write_bytes(dataset_path.read_bytes())

    report = validate_runtime_dataset_integrity(
        manifest_path=manifest_path,
        dataset_paths={
            "players": external_path,
        },
    )

    assert report.dataset_count == 1
    assert report.total_size_bytes == (external_path.stat().st_size)



def test_runtime_heatmap_grid_integrity_passes(
    tmp_path: Path,
) -> None:
    dataset_path = (
        tmp_path
        / "runtime/player_heatmap_grids.npz"
    )
    dataset_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    np.savez(
        dataset_path,
        **{
            "978838": np.full(
                (2, 3),
                1.0 / 6.0,
                dtype=np.float32,
            ),
            "789071": np.full(
                (2, 3),
                1.0 / 6.0,
                dtype=np.float32,
            ),
        },
    )

    manifest = generate_manifest(
        repository_root=tmp_path,
        definitions=(
            DatasetDefinition(
                key="heatmap_grids",
                relative_path=Path(
                    "runtime/player_heatmap_grids.npz"
                ),
                artifact_type="heatmap_grid_npz",
            ),
        ),
    )

    manifest_path = (
        tmp_path
        / "config/heatmap-manifest.json"
    )
    manifest_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    manifest_path.write_text(
        render_manifest(manifest),
        encoding="utf-8",
    )

    report = validate_runtime_dataset_integrity(
        manifest_path=manifest_path,
        dataset_paths={
            "heatmap_grids": dataset_path,
        },
    )

    assert report.dataset_count == 1
    assert report.total_size_bytes == (
        dataset_path.stat().st_size
    )


def test_runtime_heatmap_grid_integrity_rejects_metadata_mismatch(
    tmp_path: Path,
) -> None:
    dataset_path = (
        tmp_path
        / "runtime/player_heatmap_grids.npz"
    )
    dataset_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    np.savez(
        dataset_path,
        **{
            "978838": np.full(
                (2, 3),
                1.0 / 6.0,
                dtype=np.float32,
            ),
        },
    )

    manifest = generate_manifest(
        repository_root=tmp_path,
        definitions=(
            DatasetDefinition(
                key="heatmap_grids",
                relative_path=Path(
                    "runtime/player_heatmap_grids.npz"
                ),
                artifact_type="heatmap_grid_npz",
            ),
        ),
    )

    manifest["datasets"][0]["grid_width"] = 99
    manifest["bundle_sha256"] = (
        calculate_bundle_sha256(
            manifest["datasets"]
        )
    )

    manifest_path = (
        tmp_path
        / "config/heatmap-manifest.json"
    )
    manifest_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    manifest_path.write_text(
        render_manifest(manifest),
        encoding="utf-8",
    )

    with pytest.raises(
        DatasetIntegrityError,
        match="grid width mismatch",
    ):
        validate_runtime_dataset_integrity(
            manifest_path=manifest_path,
            dataset_paths={
                "heatmap_grids": dataset_path,
            },
        )
