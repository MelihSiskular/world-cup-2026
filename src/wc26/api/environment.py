"""Runtime environment validation for the WC26 API."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from wc26.api.settings import ApiSettings, ApiSettingsError
from wc26.deployment.dataset_integrity import (
    DEFAULT_MANIFEST_PATH,
    DatasetIntegrityError,
    validate_runtime_dataset_integrity,
)

DATASET_MANIFEST_ENVIRONMENT_VARIABLE = "WC26_DATASET_MANIFEST_PATH"


class RuntimeEnvironmentError(RuntimeError):
    """Raised when the API runtime environment is incomplete or unusable."""


@dataclass(frozen=True, slots=True)
class RuntimeFileRequirement:
    """A file required by the API at runtime."""

    environment_variable: str
    path: Path


def _is_production(
    settings: ApiSettings,
) -> bool:
    """Return whether strict production validation is required."""

    return str(settings.environment).casefold() == "production"


def _dataset_manifest_path() -> Path:
    """Return the configured runtime dataset manifest path."""

    configured_path = os.environ.get(DATASET_MANIFEST_ENVIRONMENT_VARIABLE)

    if configured_path:
        return Path(configured_path)

    return DEFAULT_MANIFEST_PATH


def _dataset_requirements(
    settings: ApiSettings,
) -> tuple[RuntimeFileRequirement, ...]:
    dataset_paths = settings.dataset_paths

    return (
        RuntimeFileRequirement(
            environment_variable="WC26_FEATURES_PATH",
            path=dataset_paths.features,
        ),
        RuntimeFileRequirement(
            environment_variable="WC26_SIMILARITY_PATH",
            path=dataset_paths.similarity,
        ),
        RuntimeFileRequirement(
            environment_variable=("WC26_HEATMAP_SIMILARITY_PATH"),
            path=dataset_paths.heatmap_similarity,
        ),
        RuntimeFileRequirement(
            environment_variable=("WC26_HEATMAP_PROFILES_PATH"),
            path=dataset_paths.heatmap_profiles,
        ),
    )


def _runtime_file_requirements(
    settings: ApiSettings,
) -> tuple[RuntimeFileRequirement, ...]:
    requirements = list(_dataset_requirements(settings))

    if _is_production(settings):
        requirements.append(
            RuntimeFileRequirement(
                environment_variable=(DATASET_MANIFEST_ENVIRONMENT_VARIABLE),
                path=_dataset_manifest_path(),
            )
        )

    return tuple(requirements)


def _runtime_dataset_paths(
    settings: ApiSettings,
) -> dict[str, Path]:
    dataset_paths = settings.dataset_paths

    return {
        "features": dataset_paths.features,
        "similarity": dataset_paths.similarity,
        "heatmap_similarity": (dataset_paths.heatmap_similarity),
        "heatmap_profiles": (dataset_paths.heatmap_profiles),
    }


def _validate_required_files(
    requirements: tuple[
        RuntimeFileRequirement,
        ...,
    ],
) -> None:
    errors: list[str] = []

    for requirement in requirements:
        resolved_path = requirement.path.expanduser().resolve()

        if not resolved_path.exists():
            errors.append(
                f"{requirement.environment_variable}: file does not exist: {resolved_path}"
            )
            continue

        if not resolved_path.is_file():
            errors.append(
                f"{requirement.environment_variable}: path must be a file: {resolved_path}"
            )
            continue

        if not os.access(
            resolved_path,
            os.R_OK,
        ):
            errors.append(
                f"{requirement.environment_variable}: file is not readable: {resolved_path}"
            )

    if errors:
        formatted_errors = "\n".join(f"- {error}" for error in errors)

        raise RuntimeEnvironmentError(
            f"WC26 API runtime environment validation failed:\n{formatted_errors}"
        )


def _validate_production_dataset_integrity(
    settings: ApiSettings,
) -> None:
    try:
        validate_runtime_dataset_integrity(
            manifest_path=_dataset_manifest_path(),
            dataset_paths=_runtime_dataset_paths(settings),
        )
    except DatasetIntegrityError as exc:
        raise RuntimeEnvironmentError(
            f"WC26 API runtime dataset integrity validation failed:\n{exc}"
        ) from exc


def validate_runtime_environment(
    settings: ApiSettings | None = None,
) -> ApiSettings:
    """Validate filesystem and integrity requirements."""

    runtime_settings = settings or ApiSettings.from_environment()

    _validate_required_files(_runtime_file_requirements(runtime_settings))

    if _is_production(runtime_settings):
        _validate_production_dataset_integrity(runtime_settings)

    return runtime_settings


def main() -> None:
    """Validate and report the current API runtime environment."""

    try:
        settings = validate_runtime_environment()
    except (
        ApiSettingsError,
        RuntimeEnvironmentError,
    ) as exc:
        print(
            str(exc),
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    print("WC26 API runtime environment is valid.")
    print(f"Environment: {settings.environment}")
    print(f"Bind address: {settings.host}:{settings.port}")
    print("Runtime datasets:")

    for requirement in _dataset_requirements(settings):
        resolved_path = requirement.path.expanduser().resolve()

        print(f"  {requirement.environment_variable}={resolved_path}")

    if _is_production(settings):
        print("Runtime dataset integrity: validated")
        print(f"  {DATASET_MANIFEST_ENVIRONMENT_VARIABLE}={_dataset_manifest_path().resolve()}")


if __name__ == "__main__":
    main()


__all__ = [
    "RuntimeEnvironmentError",
    "main",
    "validate_runtime_environment",
]
