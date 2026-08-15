"""Validate runtime datasets against the checked-in dataset manifest."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np

from wc26.deployment.dataset_manifest import (
    MANIFEST_VERSION,
    DatasetArtifactType,
    DatasetManifestError,
    calculate_bundle_sha256,
    calculate_file_sha256,
    inspect_csv,
    inspect_heatmap_grid_npz,
)

DEFAULT_MANIFEST_PATH = Path("config/runtime_dataset_manifest.json")

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class DatasetIntegrityError(RuntimeError):
    """Raised when runtime data does not match its manifest."""


@dataclass(frozen=True, slots=True)
class ManifestDataset:
    """Validated metadata for one manifest dataset."""

    key: str
    path: str
    artifact_type: DatasetArtifactType
    size_bytes: int
    sha256: str
    row_count: int | None = None
    column_count: int | None = None
    columns: tuple[str, ...] | None = None
    grid_count: int | None = None
    grid_height: int | None = None
    grid_width: int | None = None
    dtype: str | None = None

    def to_manifest_payload(self) -> dict[str, Any]:
        """Return the canonical payload used by the bundle hash."""

        payload: dict[str, Any] = {
            "key": self.key,
            "path": self.path,
            "artifact_type": self.artifact_type,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }

        if self.artifact_type == "csv":
            if (
                self.row_count is None
                or self.column_count is None
                or self.columns is None
            ):
                raise DatasetIntegrityError(
                    "CSV manifest metadata is incomplete."
                )

            payload.update(
                {
                    "row_count": self.row_count,
                    "column_count": self.column_count,
                    "columns": self.columns,
                }
            )

            return payload

        if (
            self.grid_count is None
            or self.grid_height is None
            or self.grid_width is None
            or self.dtype is None
        ):
            raise DatasetIntegrityError(
                "Heatmap grid manifest metadata is incomplete."
            )

        payload.update(
            {
                "grid_count": self.grid_count,
                "grid_height": self.grid_height,
                "grid_width": self.grid_width,
                "dtype": self.dtype,
            }
        )

        return payload


@dataclass(frozen=True, slots=True)
class DatasetIntegrityReport:
    """Summary returned after a successful integrity check."""

    bundle_sha256: str
    dataset_count: int
    total_size_bytes: int


def _require_mapping(
    value: object,
    *,
    label: str,
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise DatasetIntegrityError(f"{label} must be a JSON object.")

    if not all(isinstance(key, str) for key in value):
        raise DatasetIntegrityError(f"{label} contains a non-string key.")

    return cast(dict[str, object], value)


def _require_string(
    value: object,
    *,
    label: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DatasetIntegrityError(f"{label} must be a non-empty string.")

    return value.strip()


def _require_integer(
    value: object,
    *,
    label: str,
    minimum: int,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise DatasetIntegrityError(f"{label} must be an integer >= {minimum}.")

    return value


def _require_columns(
    value: object,
    *,
    label: str,
) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise DatasetIntegrityError(f"{label} must be a non-empty JSON array.")

    columns: list[str] = []

    for index, column in enumerate(value):
        columns.append(
            _require_string(
                column,
                label=f"{label}[{index}]",
            )
        )

    if len(set(columns)) != len(columns):
        raise DatasetIntegrityError(f"{label} contains duplicate column names.")

    return tuple(columns)


def _parse_manifest_dataset(
    value: object,
    *,
    index: int,
) -> ManifestDataset:
    label = f"datasets[{index}]"

    item = _require_mapping(
        value,
        label=label,
    )

    key = _require_string(
        item.get("key"),
        label=f"{label}.key",
    )
    manifest_path = _require_string(
        item.get("path"),
        label=f"{label}.path",
    )
    artifact_type_raw = _require_string(
        item.get("artifact_type"),
        label=f"{label}.artifact_type",
    )
    size_bytes = _require_integer(
        item.get("size_bytes"),
        label=f"{label}.size_bytes",
        minimum=0,
    )
    sha256 = _require_string(
        item.get("sha256"),
        label=f"{label}.sha256",
    )

    if artifact_type_raw not in {
        "csv",
        "heatmap_grid_npz",
    }:
        raise DatasetIntegrityError(
            f"{label}.artifact_type is unsupported: "
            f"{artifact_type_raw}"
        )

    artifact_type = cast(
        DatasetArtifactType,
        artifact_type_raw,
    )

    relative_path = Path(
        manifest_path
    )

    if (
        relative_path.is_absolute()
        or ".." in relative_path.parts
    ):
        raise DatasetIntegrityError(
            f"{label}.path must be repository-relative."
        )

    if not _SHA256_PATTERN.fullmatch(
        sha256
    ):
        raise DatasetIntegrityError(
            f"{label}.sha256 must contain "
            "64 lowercase hexadecimal characters."
        )

    if artifact_type == "csv":
        row_count = _require_integer(
            item.get("row_count"),
            label=f"{label}.row_count",
            minimum=0,
        )
        column_count = _require_integer(
            item.get("column_count"),
            label=f"{label}.column_count",
            minimum=1,
        )
        columns = _require_columns(
            item.get("columns"),
            label=f"{label}.columns",
        )

        if column_count != len(columns):
            raise DatasetIntegrityError(
                f"{label}.column_count does not match "
                "the number of columns."
            )

        return ManifestDataset(
            key=key,
            path=manifest_path,
            artifact_type=artifact_type,
            size_bytes=size_bytes,
            sha256=sha256,
            row_count=row_count,
            column_count=column_count,
            columns=columns,
        )

    grid_count = _require_integer(
        item.get("grid_count"),
        label=f"{label}.grid_count",
        minimum=1,
    )
    grid_height = _require_integer(
        item.get("grid_height"),
        label=f"{label}.grid_height",
        minimum=2,
    )
    grid_width = _require_integer(
        item.get("grid_width"),
        label=f"{label}.grid_width",
        minimum=2,
    )
    dtype = _require_string(
        item.get("dtype"),
        label=f"{label}.dtype",
    )

    try:
        parsed_dtype = np.dtype(
            dtype
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise DatasetIntegrityError(
            f"{label}.dtype is not a valid NumPy dtype."
        ) from exc

    if not np.issubdtype(
        parsed_dtype,
        np.floating,
    ):
        raise DatasetIntegrityError(
            f"{label}.dtype must be a floating dtype."
        )

    if parsed_dtype.name != dtype:
        raise DatasetIntegrityError(
            f"{label}.dtype must use its canonical name."
        )

    return ManifestDataset(
        key=key,
        path=manifest_path,
        artifact_type=artifact_type,
        size_bytes=size_bytes,
        sha256=sha256,
        grid_count=grid_count,
        grid_height=grid_height,
        grid_width=grid_width,
        dtype=dtype,
    )


def load_dataset_manifest(
    manifest_path: Path,
) -> tuple[str, tuple[ManifestDataset, ...]]:
    """Load and validate the structure of a dataset manifest."""

    try:
        raw_manifest: object = json.loads(
            manifest_path.read_text(
                encoding="utf-8",
            )
        )
    except FileNotFoundError as exc:
        raise DatasetIntegrityError(f"Dataset manifest does not exist: {manifest_path}") from exc
    except OSError as exc:
        raise DatasetIntegrityError(
            f"Could not read dataset manifest {manifest_path}: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise DatasetIntegrityError(
            f"Dataset manifest is not valid JSON: {manifest_path}: {exc}"
        ) from exc

    manifest = _require_mapping(
        raw_manifest,
        label="manifest",
    )

    manifest_version = _require_integer(
        manifest.get("manifest_version"),
        label="manifest.manifest_version",
        minimum=1,
    )

    if manifest_version != MANIFEST_VERSION:
        raise DatasetIntegrityError(
            "Unsupported dataset manifest version: "
            f"expected={MANIFEST_VERSION}, "
            f"actual={manifest_version}"
        )

    bundle_sha256 = _require_string(
        manifest.get("bundle_sha256"),
        label="manifest.bundle_sha256",
    )

    if not _SHA256_PATTERN.fullmatch(bundle_sha256):
        raise DatasetIntegrityError(
            "manifest.bundle_sha256 must contain 64 lowercase hexadecimal characters."
        )

    raw_datasets = manifest.get("datasets")

    if not isinstance(raw_datasets, list):
        raise DatasetIntegrityError("manifest.datasets must be a JSON array.")

    if not raw_datasets:
        raise DatasetIntegrityError("manifest.datasets must not be empty.")

    datasets = tuple(
        _parse_manifest_dataset(
            item,
            index=index,
        )
        for index, item in enumerate(raw_datasets)
    )

    dataset_keys = [dataset.key for dataset in datasets]

    if len(set(dataset_keys)) != len(dataset_keys):
        raise DatasetIntegrityError("Manifest dataset keys must be unique.")

    calculated_bundle_sha256 = calculate_bundle_sha256(
        [dataset.to_manifest_payload() for dataset in datasets]
    )

    if calculated_bundle_sha256 != bundle_sha256:
        raise DatasetIntegrityError(
            "Manifest bundle checksum mismatch: "
            f"expected={bundle_sha256}, "
            f"calculated={calculated_bundle_sha256}"
        )

    return bundle_sha256, datasets


def _format_key_difference(
    *,
    expected_keys: set[str],
    actual_keys: set[str],
) -> str:
    missing = sorted(expected_keys - actual_keys)
    unexpected = sorted(actual_keys - expected_keys)

    details: list[str] = []

    if missing:
        details.append(f"missing={missing}")

    if unexpected:
        details.append(f"unexpected={unexpected}")

    return ", ".join(details)


def validate_runtime_dataset_integrity(
    *,
    manifest_path: Path,
    dataset_paths: Mapping[str, Path],
) -> DatasetIntegrityReport:
    """Validate runtime files against size, hash and artifact metadata."""

    bundle_sha256, datasets = load_dataset_manifest(manifest_path.resolve())

    manifest_keys = {dataset.key for dataset in datasets}
    runtime_keys = set(dataset_paths)

    if manifest_keys != runtime_keys:
        difference = _format_key_difference(
            expected_keys=manifest_keys,
            actual_keys=runtime_keys,
        )

        raise DatasetIntegrityError(f"Runtime dataset keys do not match the manifest: {difference}")

    errors: list[str] = []
    total_size_bytes = 0

    for dataset in datasets:
        runtime_path = dataset_paths[dataset.key].resolve()

        if not runtime_path.exists():
            errors.append(f"{dataset.key}: file does not exist: {runtime_path}")
            continue

        if not runtime_path.is_file():
            errors.append(f"{dataset.key}: path is not a file: {runtime_path}")
            continue

        try:
            actual_size_bytes = runtime_path.stat().st_size
        except OSError as exc:
            errors.append(f"{dataset.key}: could not inspect file: {exc}")
            continue

        total_size_bytes += actual_size_bytes

        if actual_size_bytes != dataset.size_bytes:
            errors.append(
                f"{dataset.key}: size mismatch: "
                f"expected={dataset.size_bytes}, "
                f"actual={actual_size_bytes}"
            )

        try:
            actual_sha256 = calculate_file_sha256(runtime_path)
        except DatasetManifestError as exc:
            errors.append(f"{dataset.key}: checksum failed: {exc}")
        else:
            if actual_sha256 != dataset.sha256:
                errors.append(
                    f"{dataset.key}: SHA-256 mismatch: "
                    f"expected={dataset.sha256}, "
                    f"actual={actual_sha256}"
                )

        if dataset.artifact_type == "csv":
            assert dataset.columns is not None
            assert dataset.column_count is not None
            assert dataset.row_count is not None

            try:
                (
                    actual_columns,
                    actual_row_count,
                ) = inspect_csv(
                    runtime_path
                )
            except DatasetManifestError as exc:
                errors.append(
                    f"{dataset.key}: "
                    f"CSV inspection failed: {exc}"
                )
                continue

            if actual_columns != dataset.columns:
                errors.append(
                    f"{dataset.key}: "
                    "column names mismatch: "
                    f"expected={dataset.columns}, "
                    f"actual={actual_columns}"
                )

            if (
                len(actual_columns)
                != dataset.column_count
            ):
                errors.append(
                    f"{dataset.key}: "
                    "column count mismatch: "
                    f"expected={dataset.column_count}, "
                    f"actual={len(actual_columns)}"
                )

            if (
                actual_row_count
                != dataset.row_count
            ):
                errors.append(
                    f"{dataset.key}: "
                    "row count mismatch: "
                    f"expected={dataset.row_count}, "
                    f"actual={actual_row_count}"
                )

            continue

        assert dataset.grid_count is not None
        assert dataset.grid_height is not None
        assert dataset.grid_width is not None
        assert dataset.dtype is not None

        try:
            (
                actual_grid_count,
                actual_grid_height,
                actual_grid_width,
                actual_dtype,
            ) = inspect_heatmap_grid_npz(
                runtime_path
            )
        except DatasetManifestError as exc:
            errors.append(
                f"{dataset.key}: "
                "heatmap grid inspection failed: "
                f"{exc}"
            )
            continue

        if actual_grid_count != dataset.grid_count:
            errors.append(
                f"{dataset.key}: "
                "grid count mismatch: "
                f"expected={dataset.grid_count}, "
                f"actual={actual_grid_count}"
            )

        if actual_grid_height != dataset.grid_height:
            errors.append(
                f"{dataset.key}: "
                "grid height mismatch: "
                f"expected={dataset.grid_height}, "
                f"actual={actual_grid_height}"
            )

        if actual_grid_width != dataset.grid_width:
            errors.append(
                f"{dataset.key}: "
                "grid width mismatch: "
                f"expected={dataset.grid_width}, "
                f"actual={actual_grid_width}"
            )

        if actual_dtype != dataset.dtype:
            errors.append(
                f"{dataset.key}: "
                "dtype mismatch: "
                f"expected={dataset.dtype}, "
                f"actual={actual_dtype}"
            )

    if errors:
        formatted_errors = "\n".join(f"- {error}" for error in errors)

        raise DatasetIntegrityError(
            f"Runtime dataset integrity validation failed:\n{formatted_errors}"
        )

    return DatasetIntegrityReport(
        bundle_sha256=bundle_sha256,
        dataset_count=len(datasets),
        total_size_bytes=total_size_bytes,
    )


def _default_manifest_path() -> Path:
    configured_path = os.environ.get("WC26_DATASET_MANIFEST_PATH")

    if configured_path:
        return Path(configured_path)

    return DEFAULT_MANIFEST_PATH


def _runtime_dataset_paths() -> dict[str, Path]:
    from wc26.api.settings import ApiSettings

    settings = ApiSettings.from_environment()
    paths = settings.dataset_paths

    return {
        "features": paths.features,
        "player_tournament_summary": (paths.player_tournament_summary),
        "similarity": paths.similarity,
        "heatmap_similarity": (paths.heatmap_similarity),
        "heatmap_profiles": (paths.heatmap_profiles),
        "heatmap_grids": (paths.heatmap_grids),
    }


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    """Parse runtime integrity command arguments."""

    parser = argparse.ArgumentParser(
        description=("Validate production runtime datasets against the checked-in manifest.")
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=_default_manifest_path(),
        help="Path to the runtime dataset manifest.",
    )

    return parser.parse_args(argv)


def main(
    argv: Sequence[str] | None = None,
) -> None:
    """Run runtime dataset integrity validation."""

    from wc26.api.settings import ApiSettingsError

    args = parse_args(argv)

    try:
        report = validate_runtime_dataset_integrity(
            manifest_path=args.manifest,
            dataset_paths=_runtime_dataset_paths(),
        )
    except (
        ApiSettingsError,
        DatasetIntegrityError,
    ) as exc:
        print(
            f"Dataset integrity error: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    print("Runtime dataset integrity validated.")
    print(f"ManifestPath={args.manifest.resolve()}")
    print(f"BundleSHA256={report.bundle_sha256}")
    print(f"DatasetCount={report.dataset_count}")
    print(f"TotalSizeBytes={report.total_size_bytes}")


if __name__ == "__main__":
    main()
