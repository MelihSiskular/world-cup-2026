"""Atomically activate and roll back versioned dataset releases."""

from __future__ import annotations

import argparse
import os
import re
import secrets
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from wc26.deployment.dataset_bundle import (
    BUNDLE_MANIFEST_PATH,
    DEFAULT_OUTPUT_ROOT,
)
from wc26.deployment.dataset_integrity import (
    DatasetIntegrityError,
    load_dataset_manifest,
    validate_runtime_dataset_integrity,
)

CURRENT_LINK_NAME = "current"
PREVIOUS_LINK_NAME = "previous"

_BUNDLE_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class DatasetReleaseError(RuntimeError):
    """Raised when a dataset release cannot be managed safely."""


@dataclass(frozen=True, slots=True)
class DatasetReleaseStatus:
    """Describe the active and previous dataset bundles."""

    current_bundle_sha256: str | None
    previous_bundle_sha256: str | None


@dataclass(frozen=True, slots=True)
class DatasetReleaseResult:
    """Describe the result of a release operation."""

    action: str
    current_bundle_sha256: str
    previous_bundle_sha256: str | None
    changed: bool


def _resolve_path(
    repository_root: Path,
    path: Path,
) -> Path:
    if path.is_absolute():
        return path.expanduser().resolve()

    return (repository_root / path).expanduser().resolve()


def _require_bundle_sha256(
    value: str,
) -> str:
    normalized = value.strip().casefold()

    if not _BUNDLE_SHA256_PATTERN.fullmatch(normalized):
        raise DatasetReleaseError(
            "Bundle SHA-256 must contain exactly 64 lowercase hexadecimal characters."
        )

    return normalized


def _ensure_release_root(
    release_root: Path,
) -> Path:
    try:
        release_root.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as exc:
        raise DatasetReleaseError(
            f"Could not create dataset release root {release_root}: {exc}"
        ) from exc

    if not release_root.is_dir():
        raise DatasetReleaseError(f"Dataset release root is not a directory: {release_root}")

    return release_root


def _bundle_directory(
    release_root: Path,
    bundle_sha256: str,
) -> Path:
    validated_sha256 = _require_bundle_sha256(bundle_sha256)
    bundle_directory = release_root / validated_sha256

    if not bundle_directory.exists():
        raise DatasetReleaseError(f"Dataset bundle does not exist: {bundle_directory}")

    if bundle_directory.is_symlink():
        raise DatasetReleaseError(
            f"Dataset bundle directory must not be a symbolic link: {bundle_directory}"
        )

    if not bundle_directory.is_dir():
        raise DatasetReleaseError(f"Dataset bundle path is not a directory: {bundle_directory}")

    return bundle_directory


def _validate_bundle(
    release_root: Path,
    bundle_sha256: str,
) -> None:
    bundle_directory = _bundle_directory(
        release_root,
        bundle_sha256,
    )
    manifest_path = bundle_directory / BUNDLE_MANIFEST_PATH

    try:
        manifest_sha256, datasets = load_dataset_manifest(manifest_path)
    except DatasetIntegrityError as exc:
        raise DatasetReleaseError(f"Could not load dataset bundle manifest:\n{exc}") from exc

    if manifest_sha256 != bundle_sha256:
        raise DatasetReleaseError(
            "Bundle directory name does not match "
            "its manifest identity: "
            f"directory={bundle_sha256}, "
            f"manifest={manifest_sha256}"
        )

    dataset_paths = {dataset.key: (bundle_directory / dataset.path) for dataset in datasets}

    try:
        validate_runtime_dataset_integrity(
            manifest_path=manifest_path,
            dataset_paths=dataset_paths,
        )
    except DatasetIntegrityError as exc:
        raise DatasetReleaseError(f"Dataset release bundle is invalid:\n{exc}") from exc


def _read_release_link(
    release_root: Path,
    link_name: str,
) -> str | None:
    link_path = release_root / link_name

    if not link_path.is_symlink():
        if link_path.exists():
            raise DatasetReleaseError(
                f"Dataset release pointer must be a symbolic link: {link_path}"
            )

        return None

    try:
        raw_target = os.readlink(link_path)
    except OSError as exc:
        raise DatasetReleaseError(
            f"Could not read dataset release pointer {link_path}: {exc}"
        ) from exc

    target = Path(raw_target)

    if target.is_absolute() or len(target.parts) != 1:
        raise DatasetReleaseError(
            "Dataset release pointer must use a "
            "single relative bundle SHA-256: "
            f"{link_path} -> {raw_target}"
        )

    bundle_sha256 = _require_bundle_sha256(target.name)

    _bundle_directory(
        release_root,
        bundle_sha256,
    )

    return bundle_sha256


def _atomic_replace_link(
    *,
    release_root: Path,
    link_name: str,
    bundle_sha256: str,
) -> None:
    validated_sha256 = _require_bundle_sha256(bundle_sha256)
    link_path = release_root / link_name

    if link_path.exists() and not link_path.is_symlink():
        raise DatasetReleaseError(f"Cannot replace non-symbolic release pointer: {link_path}")

    temporary_path: Path | None = None

    for _ in range(20):
        candidate = release_root / (f".{link_name}.{os.getpid()}.{secrets.token_hex(6)}.tmp")

        try:
            os.symlink(
                validated_sha256,
                candidate,
            )
        except FileExistsError:
            continue
        except OSError as exc:
            raise DatasetReleaseError(
                f"Could not create temporary dataset release pointer: {exc}"
            ) from exc

        temporary_path = candidate
        break

    if temporary_path is None:
        raise DatasetReleaseError("Could not allocate a temporary dataset release pointer.")

    try:
        os.replace(
            temporary_path,
            link_path,
        )
    except OSError as exc:
        raise DatasetReleaseError(
            f"Could not atomically replace dataset release pointer {link_path}: {exc}"
        ) from exc
    finally:
        if temporary_path.exists() or (temporary_path.is_symlink()):
            temporary_path.unlink(missing_ok=True)


def inspect_dataset_release(
    *,
    release_root: Path,
    validate_bundles: bool = True,
) -> DatasetReleaseStatus:
    """Inspect the active dataset release pointers."""

    if not release_root.exists():
        return DatasetReleaseStatus(
            current_bundle_sha256=None,
            previous_bundle_sha256=None,
        )

    if not release_root.is_dir():
        raise DatasetReleaseError(f"Dataset release root is not a directory: {release_root}")

    current = _read_release_link(
        release_root,
        CURRENT_LINK_NAME,
    )
    previous = _read_release_link(
        release_root,
        PREVIOUS_LINK_NAME,
    )

    if current is None and previous is not None:
        raise DatasetReleaseError(
            "Dataset release state is inconsistent: "
            "a previous bundle exists without "
            "an active current bundle."
        )

    if validate_bundles:
        for bundle_sha256 in {
            value
            for value in (
                current,
                previous,
            )
            if value is not None
        }:
            _validate_bundle(
                release_root,
                bundle_sha256,
            )

    return DatasetReleaseStatus(
        current_bundle_sha256=current,
        previous_bundle_sha256=previous,
    )


def activate_dataset_bundle(
    *,
    release_root: Path,
    bundle_sha256: str,
) -> DatasetReleaseResult:
    """Atomically activate one validated dataset bundle."""

    release_root = _ensure_release_root(release_root)
    bundle_sha256 = _require_bundle_sha256(bundle_sha256)

    _validate_bundle(
        release_root,
        bundle_sha256,
    )

    status = inspect_dataset_release(
        release_root=release_root,
    )

    if status.current_bundle_sha256 == bundle_sha256:
        return DatasetReleaseResult(
            action="activate",
            current_bundle_sha256=bundle_sha256,
            previous_bundle_sha256=(status.previous_bundle_sha256),
            changed=False,
        )

    if status.current_bundle_sha256 is not None:
        _atomic_replace_link(
            release_root=release_root,
            link_name=PREVIOUS_LINK_NAME,
            bundle_sha256=(status.current_bundle_sha256),
        )

    _atomic_replace_link(
        release_root=release_root,
        link_name=CURRENT_LINK_NAME,
        bundle_sha256=bundle_sha256,
    )

    final_status = inspect_dataset_release(
        release_root=release_root,
    )

    if final_status.current_bundle_sha256 != bundle_sha256:
        raise DatasetReleaseError(
            "Dataset activation did not produce the expected current release."
        )

    return DatasetReleaseResult(
        action="activate",
        current_bundle_sha256=bundle_sha256,
        previous_bundle_sha256=(final_status.previous_bundle_sha256),
        changed=True,
    )


def rollback_dataset_bundle(
    *,
    release_root: Path,
) -> DatasetReleaseResult:
    """Swap the current and previous dataset releases."""

    status = inspect_dataset_release(
        release_root=release_root,
    )

    current = status.current_bundle_sha256
    previous = status.previous_bundle_sha256

    if current is None:
        raise DatasetReleaseError("No active dataset release is available.")

    if previous is None:
        raise DatasetReleaseError("No previous dataset release is available for rollback.")

    if current == previous:
        raise DatasetReleaseError("Current and previous dataset releases refer to the same bundle.")

    _validate_bundle(
        release_root,
        current,
    )
    _validate_bundle(
        release_root,
        previous,
    )

    _atomic_replace_link(
        release_root=release_root,
        link_name=CURRENT_LINK_NAME,
        bundle_sha256=previous,
    )
    _atomic_replace_link(
        release_root=release_root,
        link_name=PREVIOUS_LINK_NAME,
        bundle_sha256=current,
    )

    final_status = inspect_dataset_release(
        release_root=release_root,
    )

    if (
        final_status.current_bundle_sha256 != previous
        or final_status.previous_bundle_sha256 != current
    ):
        raise DatasetReleaseError("Dataset rollback did not produce the expected release state.")

    return DatasetReleaseResult(
        action="rollback",
        current_bundle_sha256=previous,
        previous_bundle_sha256=current,
        changed=True,
    )


def _print_status(
    status: DatasetReleaseStatus,
) -> None:
    print(f"CurrentBundleSHA256={status.current_bundle_sha256 or 'none'}")
    print(f"PreviousBundleSHA256={status.previous_bundle_sha256 or 'none'}")


def _print_result(
    result: DatasetReleaseResult,
) -> None:
    print("Dataset release operation completed.")
    print(f"Action={result.action}")
    print(f"Changed={str(result.changed).lower()}")
    print(f"CurrentBundleSHA256={result.current_bundle_sha256}")
    print(f"PreviousBundleSHA256={result.previous_bundle_sha256 or 'none'}")


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    """Parse dataset release command arguments."""

    parser = argparse.ArgumentParser(
        description=("Activate, inspect or roll back versioned runtime dataset bundles.")
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root.",
    )
    parser.add_argument(
        "--release-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Versioned dataset release directory.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    activate_parser = subparsers.add_parser(
        "activate",
        help="Activate one dataset bundle.",
    )
    activate_parser.add_argument(
        "bundle_sha256",
        help="Bundle SHA-256 to activate.",
    )

    subparsers.add_parser(
        "status",
        help="Show current and previous releases.",
    )
    subparsers.add_parser(
        "rollback",
        help="Roll back to the previous release.",
    )

    return parser.parse_args(argv)


def main(
    argv: Sequence[str] | None = None,
) -> None:
    """Run a dataset release management command."""

    args = parse_args(argv)

    repository_root = args.repository_root.expanduser().resolve()
    release_root = _resolve_path(
        repository_root,
        args.release_root,
    )

    try:
        if args.command == "activate":
            result = activate_dataset_bundle(
                release_root=release_root,
                bundle_sha256=(args.bundle_sha256),
            )
            _print_result(result)
            return

        if args.command == "rollback":
            result = rollback_dataset_bundle(
                release_root=release_root,
            )
            _print_result(result)
            return

        status = inspect_dataset_release(
            release_root=release_root,
        )

        print("Dataset release status.")
        print(f"ReleaseRoot={release_root}")
        _print_status(status)
    except DatasetReleaseError as exc:
        print(
            f"Dataset release error: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()


__all__ = [
    "DatasetReleaseError",
    "DatasetReleaseResult",
    "DatasetReleaseStatus",
    "activate_dataset_bundle",
    "inspect_dataset_release",
    "main",
    "rollback_dataset_bundle",
]
