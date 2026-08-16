"""Generate a deterministic manifest for production runtime datasets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from zipfile import BadZipFile

import numpy as np

MANIFEST_VERSION = 2

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_OUTPUT_PATH = Path("config/runtime_dataset_manifest.json")


class DatasetManifestError(RuntimeError):
    """Raised when runtime dataset metadata cannot be generated."""


type DatasetArtifactType = Literal[
    "csv",
    "heatmap_grid_npz",
]


@dataclass(frozen=True)
class DatasetDefinition:
    """Describe one dataset included in the runtime bundle."""

    key: str
    relative_path: Path
    artifact_type: DatasetArtifactType = "csv"


@dataclass(frozen=True)
class DatasetMetadata:
    """Serializable metadata describing one runtime dataset."""

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
        """Return artifact-specific deterministic manifest metadata."""

        payload: dict[str, Any] = {
            "key": self.key,
            "path": self.path,
            "artifact_type": self.artifact_type,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }

        if self.artifact_type == "csv":
            if self.row_count is None or self.column_count is None or self.columns is None:
                raise DatasetManifestError("CSV dataset metadata is incomplete.")

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
            raise DatasetManifestError("Heatmap grid dataset metadata is incomplete.")

        payload.update(
            {
                "grid_count": self.grid_count,
                "grid_height": self.grid_height,
                "grid_width": self.grid_width,
                "dtype": self.dtype,
            }
        )

        return payload


DEFAULT_DATASETS: tuple[DatasetDefinition, ...] = (
    DatasetDefinition(
        key="features",
        relative_path=Path("data/processed/transfer_intelligence/transfer_feature_table.csv"),
    ),
    DatasetDefinition(
        key="player_tournament_summary",
        relative_path=Path(
            "data/processed/player_matches_analysis/player_tournament_full_summary_enriched.csv"
        ),
    ),
    DatasetDefinition(
        key="similarity",
        relative_path=Path("data/processed/player_similarity/player_similarity_breakdown_long.csv"),
    ),
    DatasetDefinition(
        key="heatmap_similarity",
        relative_path=Path("data/processed/player_heatmaps/heatmap_similarity_long.csv"),
    ),
    DatasetDefinition(
        key="heatmap_profiles",
        relative_path=Path("data/processed/player_heatmaps/player_heatmap_profiles.csv"),
    ),
    DatasetDefinition(
        key="heatmap_grids",
        relative_path=Path("data/processed/player_heatmaps/player_heatmap_grids.npz"),
        artifact_type="heatmap_grid_npz",
    ),
)


def calculate_file_sha256(path: Path) -> str:
    """Calculate a file checksum without loading it fully into memory."""

    digest = hashlib.sha256()

    try:
        with path.open("rb") as file:
            for chunk in iter(
                lambda: file.read(1024 * 1024),
                b"",
            ):
                digest.update(chunk)
    except OSError as exc:
        raise DatasetManifestError(f"Could not calculate checksum for {path}: {exc}") from exc

    return digest.hexdigest()


def inspect_csv(path: Path) -> tuple[tuple[str, ...], int]:
    """Read and validate a CSV header while counting data rows."""

    try:
        file = path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        )
    except OSError as exc:
        raise DatasetManifestError(f"Could not open dataset {path}: {exc}") from exc

    try:
        reader = csv.reader(file)
        header = next(reader, None)

        if header is None:
            raise DatasetManifestError(f"Dataset is empty: {path}")

        columns = tuple(column.strip() for column in header)

        if not columns or any(not column for column in columns):
            raise DatasetManifestError(f"Dataset contains an empty column name: {path}")

        if len(set(columns)) != len(columns):
            raise DatasetManifestError(f"Dataset contains duplicate column names: {path}")

        row_count = 0

        for line_number, row in enumerate(
            reader,
            start=2,
        ):
            if not row or not any(field.strip() for field in row):
                continue

            if len(row) != len(columns):
                raise DatasetManifestError(
                    "CSV row has an unexpected column count: "
                    f"path={path}, "
                    f"line={line_number}, "
                    f"expected={len(columns)}, "
                    f"actual={len(row)}"
                )

            row_count += 1

        return columns, row_count
    except csv.Error as exc:
        raise DatasetManifestError(f"Could not parse CSV dataset {path}: {exc}") from exc
    finally:
        file.close()


def inspect_heatmap_grid_npz(
    path: Path,
) -> tuple[int, int, int, str]:
    """Inspect structural metadata for a player heatmap NPZ archive."""

    try:
        archive = np.load(
            path,
            allow_pickle=False,
        )
    except (
        OSError,
        ValueError,
        EOFError,
        BadZipFile,
    ) as exc:
        raise DatasetManifestError(f"Could not read heatmap grid archive {path}: {exc}") from exc

    if not isinstance(
        archive,
        np.lib.npyio.NpzFile,
    ):
        raise DatasetManifestError(f"Heatmap grid artifact is not an NPZ archive: {path}")

    player_ids: set[int] = set()
    expected_shape: tuple[int, int] | None = None
    expected_dtype: str | None = None

    try:
        if not archive.files:
            raise DatasetManifestError(f"Heatmap grid archive is empty: {path}")

        for key in archive.files:
            try:
                player_id = int(key)
            except ValueError as exc:
                raise DatasetManifestError(
                    f"Heatmap grid archive contains an invalid player key: {key!r}"
                ) from exc

            if player_id <= 0:
                raise DatasetManifestError(
                    f"Heatmap grid archive contains a non-positive player ID: {player_id}"
                )

            if player_id in player_ids:
                raise DatasetManifestError(
                    f"Heatmap grid archive contains duplicate player ID: {player_id}"
                )

            player_ids.add(player_id)

            grid = np.asarray(archive[key])

            if grid.ndim != 2:
                raise DatasetManifestError(
                    "Heatmap grid must be two-dimensional: "
                    f"player_id={player_id}, "
                    f"shape={grid.shape}"
                )

            shape = (
                int(grid.shape[0]),
                int(grid.shape[1]),
            )

            if min(shape) < 2:
                raise DatasetManifestError(
                    "Heatmap grid dimensions must both "
                    f"be at least 2: player_id={player_id}, "
                    f"shape={shape}"
                )

            if not np.issubdtype(
                grid.dtype,
                np.floating,
            ):
                raise DatasetManifestError(
                    "Heatmap grid must use a floating dtype: "
                    f"player_id={player_id}, "
                    f"dtype={grid.dtype}"
                )

            dtype = np.dtype(grid.dtype).name

            if expected_shape is None:
                expected_shape = shape
            elif shape != expected_shape:
                raise DatasetManifestError(
                    "Heatmap grid archive contains "
                    "inconsistent dimensions: "
                    f"expected={expected_shape}, "
                    f"actual={shape}, "
                    f"player_id={player_id}"
                )

            if expected_dtype is None:
                expected_dtype = dtype
            elif dtype != expected_dtype:
                raise DatasetManifestError(
                    "Heatmap grid archive contains "
                    "inconsistent dtypes: "
                    f"expected={expected_dtype}, "
                    f"actual={dtype}, "
                    f"player_id={player_id}"
                )

    except (
        OSError,
        ValueError,
        EOFError,
        BadZipFile,
    ) as exc:
        raise DatasetManifestError(f"Could not inspect heatmap grid archive {path}: {exc}") from exc
    finally:
        archive.close()

    if expected_shape is None or expected_dtype is None:
        raise DatasetManifestError(f"Heatmap grid archive contains no usable grids: {path}")

    return (
        len(player_ids),
        expected_shape[0],
        expected_shape[1],
        expected_dtype,
    )


def inspect_dataset(
    repository_root: Path,
    definition: DatasetDefinition,
) -> DatasetMetadata:
    """Build deterministic metadata for one configured dataset."""

    repository_root = repository_root.resolve()
    dataset_path = (repository_root / definition.relative_path).resolve()

    if repository_root not in dataset_path.parents:
        raise DatasetManifestError(
            f"Dataset path resolves outside repository root: {definition.relative_path}"
        )

    if not dataset_path.exists():
        raise DatasetManifestError(f"Dataset does not exist: {dataset_path}")

    if not dataset_path.is_file():
        raise DatasetManifestError(f"Dataset path is not a file: {dataset_path}")

    try:
        size_bytes = dataset_path.stat().st_size
    except OSError as exc:
        raise DatasetManifestError(f"Could not inspect dataset {dataset_path}: {exc}") from exc

    sha256 = calculate_file_sha256(dataset_path)

    if definition.artifact_type == "csv":
        columns, row_count = inspect_csv(dataset_path)

        return DatasetMetadata(
            key=definition.key,
            path=definition.relative_path.as_posix(),
            artifact_type="csv",
            size_bytes=size_bytes,
            sha256=sha256,
            row_count=row_count,
            column_count=len(columns),
            columns=columns,
        )

    if definition.artifact_type == "heatmap_grid_npz":
        (
            grid_count,
            grid_height,
            grid_width,
            dtype,
        ) = inspect_heatmap_grid_npz(dataset_path)

        return DatasetMetadata(
            key=definition.key,
            path=definition.relative_path.as_posix(),
            artifact_type="heatmap_grid_npz",
            size_bytes=size_bytes,
            sha256=sha256,
            grid_count=grid_count,
            grid_height=grid_height,
            grid_width=grid_width,
            dtype=dtype,
        )

    raise DatasetManifestError(f"Unsupported dataset artifact type: {definition.artifact_type}")


def calculate_bundle_sha256(
    datasets: Sequence[dict[str, Any]],
) -> str:
    """Create one stable identifier for the complete dataset bundle."""

    canonical_payload = json.dumps(
        datasets,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(canonical_payload).hexdigest()


def generate_manifest(
    repository_root: Path = REPOSITORY_ROOT,
    definitions: Sequence[DatasetDefinition] = DEFAULT_DATASETS,
) -> dict[str, Any]:
    """Generate a deterministic manifest for all runtime datasets."""

    if not definitions:
        raise DatasetManifestError("At least one dataset definition is required.")

    dataset_keys = [definition.key for definition in definitions]

    if len(set(dataset_keys)) != len(dataset_keys):
        raise DatasetManifestError("Dataset definition keys must be unique.")

    datasets = [
        inspect_dataset(
            repository_root,
            definition,
        ).to_manifest_payload()
        for definition in definitions
    ]

    return {
        "manifest_version": MANIFEST_VERSION,
        "bundle_sha256": calculate_bundle_sha256(datasets),
        "datasets": datasets,
    }


def render_manifest(
    manifest: dict[str, Any],
) -> str:
    """Serialize a manifest with stable formatting."""

    return (
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def resolve_output_path(
    repository_root: Path,
    output_path: Path,
) -> Path:
    """Resolve relative output paths against the repository root."""

    if output_path.is_absolute():
        return output_path

    return repository_root / output_path


def write_manifest(
    output_path: Path,
    rendered_manifest: str,
) -> None:
    """Write a generated manifest to disk."""

    try:
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        output_path.write_text(
            rendered_manifest,
            encoding="utf-8",
        )
    except OSError as exc:
        raise DatasetManifestError(f"Could not write manifest {output_path}: {exc}") from exc


def check_manifest(
    output_path: Path,
    rendered_manifest: str,
) -> None:
    """Fail when the checked-in manifest is missing or stale."""

    if not output_path.exists():
        raise DatasetManifestError(f"Dataset manifest does not exist: {output_path}")

    try:
        existing_manifest = output_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DatasetManifestError(f"Could not read manifest {output_path}: {exc}") from exc

    if existing_manifest != rendered_manifest:
        raise DatasetManifestError(
            "Dataset manifest is stale. Regenerate it with "
            "`python -m wc26.deployment.dataset_manifest`."
        )


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    """Parse dataset manifest command-line arguments."""

    parser = argparse.ArgumentParser(
        description=("Generate or validate the production runtime dataset manifest.")
    )

    parser.add_argument(
        "--repository-root",
        type=Path,
        default=REPOSITORY_ROOT,
        help="Repository root containing the runtime datasets.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Manifest output path.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=("Validate that the existing manifest matches the current datasets."),
    )

    return parser.parse_args(argv)


def main(
    argv: Sequence[str] | None = None,
) -> None:
    """Run the runtime dataset manifest command."""

    args = parse_args(argv)

    repository_root = args.repository_root.resolve()
    output_path = resolve_output_path(
        repository_root,
        args.output,
    )

    try:
        manifest = generate_manifest(
            repository_root=repository_root,
        )
        rendered_manifest = render_manifest(manifest)

        if args.check:
            check_manifest(
                output_path,
                rendered_manifest,
            )
            action = "validated"
        else:
            write_manifest(
                output_path,
                rendered_manifest,
            )
            action = "generated"
    except DatasetManifestError as exc:
        print(
            f"Dataset manifest error: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    print(f"Runtime dataset manifest {action}.")
    print(f"Path={output_path}")
    print(f"BundleSHA256={manifest['bundle_sha256']}")
    print(f"DatasetCount={len(manifest['datasets'])}")


if __name__ == "__main__":
    main()
