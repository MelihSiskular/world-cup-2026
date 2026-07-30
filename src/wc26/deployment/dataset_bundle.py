"""Build immutable, versioned runtime dataset deployment bundles."""

from __future__ import annotations

import argparse
import gzip
import os
import shutil
import sys
import tarfile
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from wc26.deployment.dataset_integrity import (
    DatasetIntegrityError,
    ManifestDataset,
    load_dataset_manifest,
    validate_runtime_dataset_integrity,
)
from wc26.deployment.dataset_manifest import (
    calculate_file_sha256,
)

DEFAULT_MANIFEST_PATH = Path("config/runtime_dataset_manifest.json")
DEFAULT_OUTPUT_ROOT = Path("dist/runtime-datasets")
BUNDLE_MANIFEST_PATH = Path("config/runtime_dataset_manifest.json")
ARCHIVE_PREFIX = "wc26-runtime-datasets"


class DatasetBundleError(RuntimeError):
    """Raised when a deployment bundle cannot be built safely."""


@dataclass(frozen=True, slots=True)
class DatasetBundleResult:
    """Summary of a completed dataset bundle build."""

    bundle_sha256: str
    bundle_directory: Path
    dataset_count: int
    total_size_bytes: int
    created: bool
    archive_path: Path | None = None
    archive_sha256: str | None = None
    checksum_path: Path | None = None


def _resolve_path(
    repository_root: Path,
    path: Path,
) -> Path:
    if path.is_absolute():
        return path.resolve()

    return (repository_root / path).resolve()


def _runtime_dataset_paths(
    bundle_root: Path,
    datasets: Sequence[ManifestDataset],
) -> dict[str, Path]:
    return {dataset.key: (bundle_root / dataset.path) for dataset in datasets}


def _validate_source_bundle(
    *,
    manifest_path: Path,
    repository_root: Path,
    datasets: Sequence[ManifestDataset],
) -> int:
    try:
        report = validate_runtime_dataset_integrity(
            manifest_path=manifest_path,
            dataset_paths=_runtime_dataset_paths(
                repository_root,
                datasets,
            ),
        )
    except DatasetIntegrityError as exc:
        raise DatasetBundleError(f"Source runtime dataset bundle is invalid:\n{exc}") from exc

    return report.total_size_bytes


def _validate_built_bundle(
    *,
    bundle_directory: Path,
    datasets: Sequence[ManifestDataset],
) -> int:
    manifest_path = bundle_directory / BUNDLE_MANIFEST_PATH

    try:
        report = validate_runtime_dataset_integrity(
            manifest_path=manifest_path,
            dataset_paths=_runtime_dataset_paths(
                bundle_directory,
                datasets,
            ),
        )
    except DatasetIntegrityError as exc:
        raise DatasetBundleError(f"Built runtime dataset bundle is invalid:\n{exc}") from exc

    return report.total_size_bytes


def _copy_file(
    *,
    source: Path,
    destination: Path,
) -> None:
    try:
        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        shutil.copyfile(
            source,
            destination,
        )
    except OSError as exc:
        raise DatasetBundleError(
            f"Could not copy bundle file: source={source}, destination={destination}: {exc}"
        ) from exc


def _copy_bundle_contents(
    *,
    repository_root: Path,
    source_manifest_path: Path,
    destination_root: Path,
    datasets: Sequence[ManifestDataset],
) -> None:
    _copy_file(
        source=source_manifest_path,
        destination=(destination_root / BUNDLE_MANIFEST_PATH),
    )

    for dataset in datasets:
        _copy_file(
            source=(repository_root / dataset.path),
            destination=(destination_root / dataset.path),
        )


def _normalize_tar_info(
    information: tarfile.TarInfo,
    *,
    is_directory: bool,
) -> tarfile.TarInfo:
    information.uid = 0
    information.gid = 0
    information.uname = ""
    information.gname = ""
    information.mtime = 0
    information.mode = 0o755 if is_directory else 0o644
    information.pax_headers = {}

    return information


def _write_deterministic_archive(
    *,
    bundle_directory: Path,
    archive_path: Path,
    archive_root_name: str,
) -> None:
    try:
        archive_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with archive_path.open("wb") as raw_file:
            with gzip.GzipFile(
                filename="",
                mode="wb",
                fileobj=raw_file,
                mtime=0,
            ) as gzip_file:
                with tarfile.open(
                    fileobj=gzip_file,
                    mode="w",
                    format=tarfile.PAX_FORMAT,
                ) as archive:
                    paths = [
                        bundle_directory,
                        *sorted(
                            bundle_directory.rglob("*"),
                            key=lambda path: path.relative_to(bundle_directory).as_posix(),
                        ),
                    ]

                    for path in paths:
                        if path == bundle_directory:
                            archive_name = archive_root_name
                        else:
                            archive_name = (
                                Path(archive_root_name) / path.relative_to(bundle_directory)
                            ).as_posix()

                        if not (path.is_file() or path.is_dir()):
                            raise DatasetBundleError(f"Unsupported entry in dataset bundle: {path}")

                        information = archive.gettarinfo(
                            str(path),
                            arcname=archive_name,
                        )
                        information = _normalize_tar_info(
                            information,
                            is_directory=(path.is_dir()),
                        )

                        if path.is_file():
                            with path.open("rb") as source_file:
                                archive.addfile(
                                    information,
                                    source_file,
                                )
                        else:
                            archive.addfile(information)
    except DatasetBundleError:
        raise
    except OSError as exc:
        raise DatasetBundleError(f"Could not create archive {archive_path}: {exc}") from exc
    except tarfile.TarError as exc:
        raise DatasetBundleError(f"Could not create dataset archive: {exc}") from exc


def _publish_archive(
    *,
    bundle_directory: Path,
    output_root: Path,
    bundle_sha256: str,
) -> tuple[Path, str, Path]:
    archive_name = f"{ARCHIVE_PREFIX}-{bundle_sha256}.tar.gz"
    archive_path = output_root / archive_name
    checksum_path = output_root / f"{archive_name}.sha256"
    archive_root_name = f"{ARCHIVE_PREFIX}-{bundle_sha256}"

    temporary_archive_file = tempfile.NamedTemporaryFile(
        prefix=f".{archive_name}.",
        suffix=".tmp",
        dir=output_root,
        delete=False,
    )
    temporary_archive_file.close()

    temporary_archive_path = Path(temporary_archive_file.name)

    try:
        _write_deterministic_archive(
            bundle_directory=bundle_directory,
            archive_path=temporary_archive_path,
            archive_root_name=archive_root_name,
        )

        generated_sha256 = calculate_file_sha256(temporary_archive_path)

        if archive_path.exists():
            existing_sha256 = calculate_file_sha256(archive_path)

            if existing_sha256 != generated_sha256:
                raise DatasetBundleError(
                    "Existing archive differs from the "
                    "deterministically generated archive: "
                    f"{archive_path}"
                )

            temporary_archive_path.unlink()
        else:
            os.replace(
                temporary_archive_path,
                archive_path,
            )

        checksum_content = f"{generated_sha256}  {archive_path.name}\n"

        if checksum_path.exists():
            existing_checksum = checksum_path.read_text(
                encoding="utf-8",
            )

            if existing_checksum != checksum_content:
                raise DatasetBundleError(
                    f"Existing archive checksum file does not match: {checksum_path}"
                )
        else:
            temporary_checksum = checksum_path.with_name(f".{checksum_path.name}.tmp")
            temporary_checksum.write_text(
                checksum_content,
                encoding="utf-8",
            )
            os.replace(
                temporary_checksum,
                checksum_path,
            )

        return (
            archive_path,
            generated_sha256,
            checksum_path,
        )
    except DatasetBundleError:
        raise
    except OSError as exc:
        raise DatasetBundleError(f"Could not publish dataset archive: {exc}") from exc
    finally:
        if temporary_archive_path.exists():
            temporary_archive_path.unlink()


def build_dataset_bundle(
    *,
    repository_root: Path,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    create_archive: bool = True,
) -> DatasetBundleResult:
    """Build and validate one immutable runtime dataset bundle."""

    repository_root = repository_root.expanduser().resolve()
    source_manifest_path = _resolve_path(
        repository_root,
        manifest_path,
    )
    resolved_output_root = _resolve_path(
        repository_root,
        output_root,
    )

    try:
        bundle_sha256, datasets = load_dataset_manifest(source_manifest_path)
    except DatasetIntegrityError as exc:
        raise DatasetBundleError(f"Could not load runtime dataset manifest:\n{exc}") from exc

    total_size_bytes = _validate_source_bundle(
        manifest_path=source_manifest_path,
        repository_root=repository_root,
        datasets=datasets,
    )

    try:
        resolved_output_root.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as exc:
        raise DatasetBundleError(
            f"Could not create bundle output directory {resolved_output_root}: {exc}"
        ) from exc

    bundle_directory = resolved_output_root / bundle_sha256
    created = False

    if bundle_directory.exists():
        if not bundle_directory.is_dir():
            raise DatasetBundleError(
                f"Bundle destination exists but is not a directory: {bundle_directory}"
            )

        existing_size = _validate_built_bundle(
            bundle_directory=bundle_directory,
            datasets=datasets,
        )

        if existing_size != total_size_bytes:
            raise DatasetBundleError("Existing bundle total size differs from the source bundle.")
    else:
        staging_directory = Path(
            tempfile.mkdtemp(
                prefix=f".{bundle_sha256}.",
                dir=resolved_output_root,
            )
        )

        try:
            _copy_bundle_contents(
                repository_root=repository_root,
                source_manifest_path=(source_manifest_path),
                destination_root=(staging_directory),
                datasets=datasets,
            )

            staged_size = _validate_built_bundle(
                bundle_directory=(staging_directory),
                datasets=datasets,
            )

            if staged_size != total_size_bytes:
                raise DatasetBundleError("Staged bundle total size differs from the source bundle.")

            os.replace(
                staging_directory,
                bundle_directory,
            )
            created = True
        except DatasetBundleError:
            raise
        except OSError as exc:
            raise DatasetBundleError(
                f"Could not publish versioned bundle directory: {exc}"
            ) from exc
        finally:
            if staging_directory.exists():
                shutil.rmtree(
                    staging_directory,
                    ignore_errors=True,
                )

    archive_path: Path | None = None
    archive_sha256: str | None = None
    checksum_path: Path | None = None

    if create_archive:
        (
            archive_path,
            archive_sha256,
            checksum_path,
        ) = _publish_archive(
            bundle_directory=bundle_directory,
            output_root=resolved_output_root,
            bundle_sha256=bundle_sha256,
        )

    return DatasetBundleResult(
        bundle_sha256=bundle_sha256,
        bundle_directory=bundle_directory,
        dataset_count=len(datasets),
        total_size_bytes=total_size_bytes,
        created=created,
        archive_path=archive_path,
        archive_sha256=archive_sha256,
        checksum_path=checksum_path,
    )


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    """Parse dataset bundle command-line arguments."""

    parser = argparse.ArgumentParser(
        description=("Build a versioned runtime dataset deployment bundle.")
    )

    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing runtime data.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Runtime dataset manifest path.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Directory receiving versioned bundles.",
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Build only the versioned directory.",
    )

    return parser.parse_args(argv)


def main(
    argv: Sequence[str] | None = None,
) -> None:
    """Build and report a runtime dataset bundle."""

    args = parse_args(argv)

    try:
        result = build_dataset_bundle(
            repository_root=(args.repository_root),
            manifest_path=args.manifest,
            output_root=args.output_root,
            create_archive=(not args.no_archive),
        )
    except DatasetBundleError as exc:
        print(
            f"Dataset bundle error: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    print("Runtime dataset deployment bundle ready.")
    print(f"BundleSHA256={result.bundle_sha256}")
    print(f"BundleDirectory={result.bundle_directory}")
    print(f"DatasetCount={result.dataset_count}")
    print(f"TotalSizeBytes={result.total_size_bytes}")
    print(f"Created={str(result.created).lower()}")

    if result.archive_path is not None:
        print(f"ArchivePath={result.archive_path}")
        print(f"ArchiveSHA256={result.archive_sha256}")
        print(f"ChecksumPath={result.checksum_path}")


if __name__ == "__main__":
    main()


__all__ = [
    "DatasetBundleError",
    "DatasetBundleResult",
    "build_dataset_bundle",
    "main",
]
