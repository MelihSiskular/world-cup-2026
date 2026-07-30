"""Generate a deterministic manifest for production runtime datasets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

MANIFEST_VERSION = 1

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_OUTPUT_PATH = Path("config/runtime_dataset_manifest.json")


class DatasetManifestError(RuntimeError):
    """Raised when runtime dataset metadata cannot be generated."""


@dataclass(frozen=True)
class DatasetDefinition:
    """Describe one dataset included in the runtime bundle."""

    key: str
    relative_path: Path


@dataclass(frozen=True)
class DatasetMetadata:
    """Serializable metadata describing one runtime dataset."""

    key: str
    path: str
    size_bytes: int
    sha256: str
    row_count: int
    column_count: int
    columns: tuple[str, ...]


DEFAULT_DATASETS: tuple[DatasetDefinition, ...] = (
    DatasetDefinition(
        key="features",
        relative_path=Path("data/processed/transfer_intelligence/transfer_feature_table.csv"),
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

    columns, row_count = inspect_csv(dataset_path)

    return DatasetMetadata(
        key=definition.key,
        path=definition.relative_path.as_posix(),
        size_bytes=size_bytes,
        sha256=calculate_file_sha256(dataset_path),
        row_count=row_count,
        column_count=len(columns),
        columns=columns,
    )


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
        asdict(
            inspect_dataset(
                repository_root,
                definition,
            )
        )
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
