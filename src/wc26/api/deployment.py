"""Runtime deployment identity resolution."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from wc26.deployment.dataset_integrity import (
    DEFAULT_MANIFEST_PATH,
    DatasetIntegrityError,
    load_dataset_manifest,
)

DATASET_MANIFEST_ENVIRONMENT_VARIABLE = "WC26_DATASET_MANIFEST_PATH"


@dataclass(frozen=True, slots=True)
class DeploymentIdentity:
    """Identify the deployed application and dataset release."""

    provider: str
    commit_sha: str | None
    branch: str | None
    deployment_id: str | None
    dataset_bundle_sha256: str | None


def _read_optional_text(
    environment: Mapping[str, str],
    *keys: str,
) -> str | None:
    """Return the first configured non-empty value."""

    for key in keys:
        value = environment.get(key)

        if value is None:
            continue

        normalized = value.strip()

        if normalized:
            return normalized

    return None


def _detect_provider(
    environment: Mapping[str, str],
) -> str:
    """Detect the active deployment provider."""

    explicit_provider = _read_optional_text(
        environment,
        "WC26_DEPLOYMENT_PROVIDER",
    )

    if explicit_provider is not None:
        return explicit_provider.casefold()

    if any(key.startswith("RAILWAY_") for key in environment):
        return "railway"

    return "local"


def _resolve_manifest_path(
    environment: Mapping[str, str],
) -> Path:
    """Return the configured runtime dataset manifest."""

    configured_path = _read_optional_text(
        environment,
        DATASET_MANIFEST_ENVIRONMENT_VARIABLE,
    )

    if configured_path is None:
        return DEFAULT_MANIFEST_PATH

    return Path(configured_path).expanduser()


def _read_dataset_bundle_sha256(
    manifest_path: Path,
) -> str | None:
    """Read the validated dataset bundle identity when available."""

    try:
        bundle_sha256, _ = load_dataset_manifest(manifest_path)
    except (
        DatasetIntegrityError,
        OSError,
    ):
        return None

    return bundle_sha256


def resolve_deployment_identity(
    environment: Mapping[str, str] | None = None,
    *,
    manifest_path: Path | None = None,
) -> DeploymentIdentity:
    """Resolve application and dataset release identity."""

    source = os.environ if environment is None else environment

    resolved_manifest_path = (
        manifest_path if manifest_path is not None else _resolve_manifest_path(source)
    )

    return DeploymentIdentity(
        provider=_detect_provider(source),
        commit_sha=_read_optional_text(
            source,
            "WC26_RELEASE_SHA",
            "RAILWAY_GIT_COMMIT_SHA",
        ),
        branch=_read_optional_text(
            source,
            "WC26_RELEASE_BRANCH",
            "RAILWAY_GIT_BRANCH",
        ),
        deployment_id=_read_optional_text(
            source,
            "WC26_DEPLOYMENT_ID",
            "RAILWAY_DEPLOYMENT_ID",
        ),
        dataset_bundle_sha256=(_read_dataset_bundle_sha256(resolved_manifest_path)),
    )


__all__ = [
    "DeploymentIdentity",
    "resolve_deployment_identity",
]
