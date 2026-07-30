"""Runtime environment validation for the WC26 API."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from wc26.api.settings import ApiSettings, ApiSettingsError


class RuntimeEnvironmentError(RuntimeError):
    """Raised when the API runtime environment is incomplete or unusable."""


@dataclass(frozen=True, slots=True)
class RuntimeFileRequirement:
    """A file required by the API at runtime."""

    environment_variable: str
    path: Path


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
            environment_variable="WC26_HEATMAP_SIMILARITY_PATH",
            path=dataset_paths.heatmap_similarity,
        ),
        RuntimeFileRequirement(
            environment_variable="WC26_HEATMAP_PROFILES_PATH",
            path=dataset_paths.heatmap_profiles,
        ),
    )


def validate_runtime_environment(
    settings: ApiSettings | None = None,
) -> ApiSettings:
    """Validate filesystem requirements for the API runtime."""

    runtime_settings = settings or ApiSettings.from_environment()
    errors: list[str] = []

    for requirement in _dataset_requirements(runtime_settings):
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

        if not os.access(resolved_path, os.R_OK):
            errors.append(
                f"{requirement.environment_variable}: file is not readable: {resolved_path}"
            )

    if errors:
        formatted_errors = "\n".join(f"- {error}" for error in errors)

        raise RuntimeEnvironmentError(
            f"WC26 API runtime environment validation failed:\n{formatted_errors}"
        )

    return runtime_settings


def main() -> None:
    """Validate and report the current API runtime environment."""

    try:
        settings = validate_runtime_environment()
    except (ApiSettingsError, RuntimeEnvironmentError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    print("WC26 API runtime environment is valid.")
    print(f"Environment: {settings.environment}")
    print(f"Bind address: {settings.host}:{settings.port}")
    print("Runtime datasets:")

    for requirement in _dataset_requirements(settings):
        print(f"  {requirement.environment_variable}={requirement.path.expanduser().resolve()}")


if __name__ == "__main__":
    main()


__all__ = [
    "RuntimeEnvironmentError",
    "main",
    "validate_runtime_environment",
]
