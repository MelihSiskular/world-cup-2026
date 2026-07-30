#!/usr/bin/env bash

set -Eeuo pipefail

readonly IMAGE_NAME="${1:-wc26-transfer-api:dev}"
readonly TOP_N="${TOP_N:-25}"


log() {
    printf '\n[docker-baseline] %s\n' "$*"
}


fail() {
    printf '[docker-baseline] ERROR: %s\n' "$*" >&2
    exit 1
}


require_command() {
    local command_name="$1"

    if ! command -v "${command_name}" >/dev/null 2>&1; then
        fail "Required command not found: ${command_name}"
    fi
}


validate_top_n() {
    if [[ ! "${TOP_N}" =~ ^[1-9][0-9]*$ ]]; then
        fail "TOP_N must be a positive integer: ${TOP_N}"
    fi
}


print_image_metadata() {
    log "Image metadata"

    docker image inspect \
        "${IMAGE_NAME}" \
        --format='Image={{index .RepoTags 0}}
Architecture={{.Architecture}}
OS={{.Os}}
SizeBytes={{.Size}}
User={{.Config.User}}
WorkingDir={{.Config.WorkingDir}}
ExposedPorts={{json .Config.ExposedPorts}}
Command={{json .Config.Cmd}}
Healthcheck={{json .Config.Healthcheck}}'
}


print_layer_history() {
    log "Docker layer history"

    docker history \
        --no-trunc \
        --format \
        'Layer={{.ID}}
Size={{.Size}}
CreatedBy={{.CreatedBy}}
---' \
        "${IMAGE_NAME}"
}


print_container_filesystem_analysis() {
    log "Container filesystem and Python package analysis"

    docker run \
        --rm \
        --interactive \
        --entrypoint python \
        --env "WC26_BASELINE_TOP_N=${TOP_N}" \
        "${IMAGE_NAME}" \
        - <<'PY'
from __future__ import annotations

import importlib.metadata
import os
import platform
import site
import sys
from collections.abc import Iterable
from pathlib import Path


TOP_N = int(os.environ["WC26_BASELINE_TOP_N"])


def human_size(size_bytes: int) -> str:
    value = float(size_bytes)

    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.2f} {unit}"

        value /= 1024

    raise AssertionError("Unreachable size conversion branch.")


def filesystem_size(path: Path) -> int:
    if not path.exists():
        return 0

    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0

    total = 0

    for root, _, filenames in os.walk(path, followlinks=False):
        root_path = Path(root)

        for filename in filenames:
            file_path = root_path / filename

            try:
                if not file_path.is_symlink():
                    total += file_path.stat().st_size
            except OSError:
                continue

    return total


def print_size_rows(
    title: str,
    rows: Iterable[tuple[str, int]],
) -> None:
    sorted_rows = sorted(
        rows,
        key=lambda item: item[1],
        reverse=True,
    )

    print(f"\n--- {title} ---")

    for name, size in sorted_rows[:TOP_N]:
        print(f"{human_size(size):>12}  {name}")


print("--- Python runtime ---")
print(f"Python={platform.python_version()}")
print(f"Executable={sys.executable}")
print(f"Platform={platform.platform()}")
print(f"Prefix={sys.prefix}")

filesystem_paths = (
    Path("/usr/local"),
    Path("/usr/local/lib"),
    Path("/usr/local/lib/python3.12"),
    Path("/usr/local/lib/python3.12/site-packages"),
    Path("/usr/local/bin"),
    Path("/app"),
    Path("/app/data"),
)

print("\n--- Important filesystem paths ---")

for path in filesystem_paths:
    print(f"{human_size(filesystem_size(path)):>12}  {path}")

site_package_directories = [
    Path(path)
    for path in site.getsitepackages()
    if Path(path).is_dir()
]

for site_packages in site_package_directories:
    child_rows = [
        (child.name, filesystem_size(child))
        for child in site_packages.iterdir()
    ]

    print_size_rows(
        f"Largest entries in {site_packages}",
        child_rows,
    )

distribution_rows: list[tuple[str, int, str]] = []

for distribution in importlib.metadata.distributions():
    distribution_name = (
        distribution.metadata.get("Name")
        or distribution.name
        or "unknown"
    )
    distribution_version = distribution.version
    total_size = 0
    visited_paths: set[Path] = set()

    for relative_file in distribution.files or ():
        installed_path = Path(distribution.locate_file(relative_file))

        if installed_path in visited_paths:
            continue

        visited_paths.add(installed_path)

        try:
            if installed_path.is_file() and not installed_path.is_symlink():
                total_size += installed_path.stat().st_size
        except OSError:
            continue

    distribution_rows.append(
        (
            distribution_name,
            total_size,
            distribution_version,
        )
    )

distribution_rows.sort(
    key=lambda item: item[1],
    reverse=True,
)

print(f"\n--- Largest installed Python distributions: top {TOP_N} ---")

for name, size, version in distribution_rows[:TOP_N]:
    print(
        f"{human_size(size):>12}  "
        f"{name}=={version}"
    )

print("\n--- Installed distribution summary ---")
print(f"DistributionCount={len(distribution_rows)}")
print(
    "DistributionFilesTotal="
    f"{human_size(sum(row[1] for row in distribution_rows))}"
)

runtime_datasets = (
    Path(
        "/app/data/processed/transfer_intelligence/"
        "transfer_feature_table.csv"
    ),
    Path(
        "/app/data/processed/player_similarity/"
        "player_similarity_breakdown_long.csv"
    ),
    Path(
        "/app/data/processed/player_heatmaps/"
        "heatmap_similarity_long.csv"
    ),
    Path(
        "/app/data/processed/player_heatmaps/"
        "player_heatmap_profiles.csv"
    ),
)

print("\n--- Runtime datasets ---")

for dataset_path in runtime_datasets:
    print(
        f"{human_size(filesystem_size(dataset_path)):>12}  "
        f"{dataset_path}"
    )

print(
    f"{human_size(sum(filesystem_size(path) for path in runtime_datasets)):>12}  "
    "Runtime dataset total"
)
PY
}


main() {
    require_command docker
    validate_top_n

    if ! docker info >/dev/null 2>&1; then
        fail "Docker engine is not reachable."
    fi

    if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
        fail "Docker image does not exist locally: ${IMAGE_NAME}"
    fi

    log "Analyzing image: ${IMAGE_NAME}"
    log "Showing the largest ${TOP_N} filesystem and package entries."

    print_image_metadata
    print_layer_history
    print_container_filesystem_analysis

    log "Baseline analysis completed."
}


main "$@"
