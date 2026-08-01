#!/usr/bin/env bash

set -Eeuo pipefail

readonly IMAGE_NAME="${1:-wc26-transfer-api:dev}"


log() {
    printf '\n[docker-dependency-audit] %s\n' "$*"
}


fail() {
    printf '[docker-dependency-audit] ERROR: %s\n' "$*" >&2
    exit 1
}


require_command() {
    local command_name="$1"

    if ! command -v "${command_name}" >/dev/null 2>&1; then
        fail "Required command not found: ${command_name}"
    fi
}


run_runtime_audit() {
    docker run \
        --rm \
        --interactive \
        --entrypoint python \
        "${IMAGE_NAME}" \
        - <<'PY'
from __future__ import annotations

import asyncio
import importlib.metadata
import re
import sys
from collections import defaultdict


PROJECT_DISTRIBUTION = "wc26-transfer-intelligence"

HEAVY_DISTRIBUTIONS = (
    "playwright",
    "matplotlib",
    "pillow",
    "scikit-learn",
    "scipy",
    "pandas",
    "numpy",
    "fastapi",
    "uvicorn",
)


def normalize_distribution_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def requirement_name(requirement: str) -> str:
    match = re.match(r"^[A-Za-z0-9_.-]+", requirement)

    if match is None:
        raise ValueError(f"Could not parse requirement: {requirement}")

    return normalize_distribution_name(match.group(0))


def distribution_index() -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}

    for distribution in importlib.metadata.distributions():
        display_name = (
            distribution.metadata.get("Name")
            or distribution.name
            or "unknown"
        )

        result[normalize_distribution_name(display_name)] = (
            display_name,
            distribution.version,
        )

    return result


def loaded_distributions(
    loaded_top_level_modules: set[str],
) -> set[str]:
    package_mapping = importlib.metadata.packages_distributions()
    result: set[str] = set()

    for module_name in loaded_top_level_modules:
        for distribution_name in package_mapping.get(module_name, ()):
            result.add(normalize_distribution_name(distribution_name))

    return result


def production_requirements() -> list[str]:
    distribution = importlib.metadata.distribution(PROJECT_DISTRIBUTION)
    requirements = distribution.requires or []

    return sorted(
        {
            requirement_name(requirement)
            for requirement in requirements
            if "extra ==" not in requirement
        }
    )


before_imports = set(sys.modules)

# Import the same launcher and application modules used in production.
from wc26.api import server  # noqa: E402
from wc26.api.main import app  # noqa: E402


async def audit_runtime() -> None:
    async with app.router.lifespan_context(app):
        after_startup_imports = set(sys.modules)

        newly_loaded_modules = after_startup_imports - before_imports
        loaded_top_level_modules = {
            module_name.split(".", maxsplit=1)[0]
            for module_name in newly_loaded_modules
        }

        loaded_distribution_names = loaded_distributions(
            loaded_top_level_modules
        )
        installed_distributions = distribution_index()
        declared_requirements = production_requirements()

        modules_by_distribution: dict[str, set[str]] = defaultdict(set)
        package_mapping = importlib.metadata.packages_distributions()

        for module_name in loaded_top_level_modules:
            for distribution_name in package_mapping.get(module_name, ()):
                normalized_name = normalize_distribution_name(
                    distribution_name
                )
                modules_by_distribution[normalized_name].add(module_name)

        print("--- Runtime dependency audit ---")
        print(f"Python={sys.version.split()[0]}")
        print(f"LauncherModule={server.__name__}")
        print(f"Application={app.title}")
        print(
            "NewlyLoadedTopLevelModuleCount="
            f"{len(loaded_top_level_modules)}"
        )
        print(
            "LoadedDistributionCount="
            f"{len(loaded_distribution_names)}"
        )

        print("\n--- Declared production dependencies ---")

        for normalized_name in declared_requirements:
            display_name, version = installed_distributions.get(
                normalized_name,
                (normalized_name, "unknown"),
            )
            status = (
                "LOADED"
                if normalized_name in loaded_distribution_names
                else "NOT_LOADED"
            )
            imported_modules = ", ".join(
                sorted(modules_by_distribution.get(normalized_name, ()))
            )

            suffix = (
                f" modules=[{imported_modules}]"
                if imported_modules
                else ""
            )

            print(
                f"{status:10} "
                f"{display_name}=={version}"
                f"{suffix}"
            )

        print("\n--- Heavy dependency focus ---")

        for dependency_name in HEAVY_DISTRIBUTIONS:
            normalized_name = normalize_distribution_name(
                dependency_name
            )
            display_name, version = installed_distributions.get(
                normalized_name,
                (dependency_name, "not-installed"),
            )
            status = (
                "LOADED"
                if normalized_name in loaded_distribution_names
                else "NOT_LOADED"
            )
            imported_modules = ", ".join(
                sorted(modules_by_distribution.get(normalized_name, ()))
            )

            suffix = (
                f" modules=[{imported_modules}]"
                if imported_modules
                else ""
            )

            print(
                f"{status:10} "
                f"{display_name}=={version}"
                f"{suffix}"
            )

        print("\n--- All newly loaded third-party distributions ---")

        for normalized_name in sorted(loaded_distribution_names):
            display_name, version = installed_distributions.get(
                normalized_name,
                (normalized_name, "unknown"),
            )
            imported_modules = ", ".join(
                sorted(modules_by_distribution.get(normalized_name, ()))
            )

            print(
                f"{display_name}=={version} "
                f"modules=[{imported_modules}]"
            )


asyncio.run(audit_runtime())
PY
}


main() {
    require_command docker

    if ! docker info >/dev/null 2>&1; then
        fail "Docker engine is not reachable."
    fi

    if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
        fail "Docker image does not exist locally: ${IMAGE_NAME}"
    fi

    log "Auditing image: ${IMAGE_NAME}"
    run_runtime_audit
    log "Runtime dependency audit completed."
}


main "$@"
