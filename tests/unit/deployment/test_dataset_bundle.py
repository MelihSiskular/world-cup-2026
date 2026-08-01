from __future__ import annotations

import csv
from pathlib import Path

import pytest

from wc26.deployment.dataset_bundle import (
    DatasetBundleError,
    build_dataset_bundle,
)
from wc26.deployment.dataset_integrity import (
    validate_runtime_dataset_integrity,
)
from wc26.deployment.dataset_manifest import (
    DatasetDefinition,
    calculate_file_sha256,
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


def create_repository_bundle(
    tmp_path: Path,
) -> tuple[Path, tuple[DatasetDefinition, ...]]:
    definitions = (
        DatasetDefinition(
            key="features",
            relative_path=Path("data/processed/features.csv"),
        ),
        DatasetDefinition(
            key="similarity",
            relative_path=Path("data/processed/similarity.csv"),
        ),
    )

    write_csv(
        tmp_path / definitions[0].relative_path,
        [
            ["player_id", "player_name"],
            ["978838", "Michael Olise"],
        ],
    )
    write_csv(
        tmp_path / definitions[1].relative_path,
        [
            [
                "source_player_id",
                "target_player_id",
                "similarity",
            ],
            ["978838", "100000", "0.91"],
        ],
    )

    manifest = generate_manifest(
        repository_root=tmp_path,
        definitions=definitions,
    )

    manifest_path = tmp_path / "config" / "runtime_dataset_manifest.json"
    manifest_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    manifest_path.write_text(
        render_manifest(manifest),
        encoding="utf-8",
    )

    return manifest_path, definitions


def test_build_dataset_bundle_creates_versioned_artifacts(
    tmp_path: Path,
) -> None:
    manifest_path, definitions = create_repository_bundle(tmp_path)

    result = build_dataset_bundle(
        repository_root=tmp_path,
    )

    assert result.created is True
    assert result.bundle_directory.name == (result.bundle_sha256)
    assert result.dataset_count == 2
    assert result.total_size_bytes > 0

    bundled_manifest = result.bundle_directory / "config" / "runtime_dataset_manifest.json"

    assert bundled_manifest.read_bytes() == (manifest_path.read_bytes())

    runtime_paths = {
        definition.key: (result.bundle_directory / definition.relative_path)
        for definition in definitions
    }

    report = validate_runtime_dataset_integrity(
        manifest_path=bundled_manifest,
        dataset_paths=runtime_paths,
    )

    assert report.bundle_sha256 == (result.bundle_sha256)

    assert result.archive_path is not None
    assert result.archive_path.is_file()
    assert result.archive_sha256 == (calculate_file_sha256(result.archive_path))

    assert result.checksum_path is not None
    assert result.checksum_path.read_text(encoding="utf-8") == (
        f"{result.archive_sha256}  {result.archive_path.name}\n"
    )


def test_build_dataset_bundle_is_deterministic(
    tmp_path: Path,
) -> None:
    create_repository_bundle(tmp_path)

    first = build_dataset_bundle(
        repository_root=tmp_path,
    )
    second = build_dataset_bundle(
        repository_root=tmp_path,
    )

    assert first.created is True
    assert second.created is False
    assert first.bundle_sha256 == (second.bundle_sha256)
    assert first.archive_sha256 == (second.archive_sha256)
    assert first.bundle_directory == (second.bundle_directory)
    assert first.archive_path == (second.archive_path)


def test_build_dataset_bundle_rejects_tampered_source(
    tmp_path: Path,
) -> None:
    _, definitions = create_repository_bundle(tmp_path)

    tampered_path = tmp_path / definitions[0].relative_path

    with tampered_path.open(
        "a",
        encoding="utf-8",
        newline="",
    ) as file:
        csv.writer(file).writerow(["100000", "Tampered Player"])

    with pytest.raises(
        DatasetBundleError,
        match="Source runtime dataset bundle is invalid",
    ):
        build_dataset_bundle(
            repository_root=tmp_path,
        )

    output_root = tmp_path / "dist/runtime-datasets"

    if output_root.exists():
        assert not any(
            path.is_dir() and not path.name.startswith(".") for path in output_root.iterdir()
        )
