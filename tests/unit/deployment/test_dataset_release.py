from __future__ import annotations

import csv
import os
from pathlib import Path

import pytest

from wc26.deployment.dataset_bundle import (
    DatasetBundleResult,
    build_dataset_bundle,
)
from wc26.deployment.dataset_manifest import (
    DatasetDefinition,
    generate_manifest,
    render_manifest,
)
from wc26.deployment.dataset_release import (
    DatasetReleaseError,
    activate_dataset_bundle,
    inspect_dataset_release,
    rollback_dataset_bundle,
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


def create_versioned_bundle(
    tmp_path: Path,
    *,
    player_name: str,
) -> DatasetBundleResult:
    definition = DatasetDefinition(
        key="features",
        relative_path=Path("data/processed/features.csv"),
    )

    write_csv(
        tmp_path / definition.relative_path,
        [
            ["player_id", "player_name"],
            ["978838", player_name],
        ],
    )

    manifest = generate_manifest(
        repository_root=tmp_path,
        definitions=(definition,),
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

    return build_dataset_bundle(
        repository_root=tmp_path,
        create_archive=False,
    )


def test_activate_dataset_bundle_updates_release_links(
    tmp_path: Path,
) -> None:
    first = create_versioned_bundle(
        tmp_path,
        player_name="Michael Olise",
    )
    second = create_versioned_bundle(
        tmp_path,
        player_name="Lamine Yamal",
    )
    release_root = first.bundle_directory.parent

    first_result = activate_dataset_bundle(
        release_root=release_root,
        bundle_sha256=first.bundle_sha256,
    )

    assert first_result.changed is True
    assert os.readlink(release_root / "current") == first.bundle_sha256
    assert not (release_root / "previous").exists()

    second_result = activate_dataset_bundle(
        release_root=release_root,
        bundle_sha256=second.bundle_sha256,
    )

    assert second_result.changed is True
    assert os.readlink(release_root / "current") == second.bundle_sha256
    assert os.readlink(release_root / "previous") == first.bundle_sha256

    status = inspect_dataset_release(
        release_root=release_root,
    )

    assert status.current_bundle_sha256 == (second.bundle_sha256)
    assert status.previous_bundle_sha256 == (first.bundle_sha256)


def test_activate_dataset_bundle_is_idempotent(
    tmp_path: Path,
) -> None:
    bundle = create_versioned_bundle(
        tmp_path,
        player_name="Michael Olise",
    )
    release_root = bundle.bundle_directory.parent

    activate_dataset_bundle(
        release_root=release_root,
        bundle_sha256=bundle.bundle_sha256,
    )
    second_result = activate_dataset_bundle(
        release_root=release_root,
        bundle_sha256=bundle.bundle_sha256,
    )

    assert second_result.changed is False
    assert second_result.current_bundle_sha256 == (bundle.bundle_sha256)
    assert second_result.previous_bundle_sha256 is None


def test_rollback_swaps_current_and_previous(
    tmp_path: Path,
) -> None:
    first = create_versioned_bundle(
        tmp_path,
        player_name="Michael Olise",
    )
    second = create_versioned_bundle(
        tmp_path,
        player_name="Lamine Yamal",
    )
    release_root = first.bundle_directory.parent

    activate_dataset_bundle(
        release_root=release_root,
        bundle_sha256=first.bundle_sha256,
    )
    activate_dataset_bundle(
        release_root=release_root,
        bundle_sha256=second.bundle_sha256,
    )

    result = rollback_dataset_bundle(
        release_root=release_root,
    )

    assert result.changed is True
    assert result.current_bundle_sha256 == (first.bundle_sha256)
    assert result.previous_bundle_sha256 == (second.bundle_sha256)
    assert os.readlink(release_root / "current") == first.bundle_sha256
    assert os.readlink(release_root / "previous") == second.bundle_sha256


def test_rollback_requires_previous_release(
    tmp_path: Path,
) -> None:
    bundle = create_versioned_bundle(
        tmp_path,
        player_name="Michael Olise",
    )
    release_root = bundle.bundle_directory.parent

    activate_dataset_bundle(
        release_root=release_root,
        bundle_sha256=bundle.bundle_sha256,
    )

    with pytest.raises(
        DatasetReleaseError,
        match="No previous dataset release",
    ):
        rollback_dataset_bundle(
            release_root=release_root,
        )


def test_activate_rejects_tampered_bundle(
    tmp_path: Path,
) -> None:
    bundle = create_versioned_bundle(
        tmp_path,
        player_name="Michael Olise",
    )
    release_root = bundle.bundle_directory.parent
    features_path = bundle.bundle_directory / "data" / "processed" / "features.csv"

    with features_path.open(
        "a",
        encoding="utf-8",
        newline="",
    ) as file:
        csv.writer(file).writerow(["100000", "Tampered Player"])

    with pytest.raises(
        DatasetReleaseError,
        match="bundle is invalid",
    ):
        activate_dataset_bundle(
            release_root=release_root,
            bundle_sha256=bundle.bundle_sha256,
        )


def test_activate_rejects_non_symlink_pointer(
    tmp_path: Path,
) -> None:
    bundle = create_versioned_bundle(
        tmp_path,
        player_name="Michael Olise",
    )
    release_root = bundle.bundle_directory.parent

    (release_root / "current").write_text(
        "invalid release state",
        encoding="utf-8",
    )

    with pytest.raises(
        DatasetReleaseError,
        match="must be a symbolic link",
    ):
        activate_dataset_bundle(
            release_root=release_root,
            bundle_sha256=bundle.bundle_sha256,
        )
