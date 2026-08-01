#!/usr/bin/env bash

set -Eeuo pipefail

readonly IMAGE_NAME="${1:-wc26-transfer-api:dev}"
readonly MAX_IMAGE_ARCHIVE_SIZE_BYTES="${MAX_IMAGE_ARCHIVE_SIZE_BYTES:-${MAX_IMAGE_SIZE_BYTES:-140000000}}"


log() {
    printf '[docker-policy] %s\n' "$*"
}


fail() {
    printf '[docker-policy] ERROR: %s\n' "$*" >&2
    exit 1
}


require_command() {
    local command_name="$1"

    if ! command -v "${command_name}" >/dev/null 2>&1; then
        fail "Required command not found: ${command_name}"
    fi
}


require_positive_integer() {
    local value="$1"
    local variable_name="$2"

    if [[ ! "${value}" =~ ^[1-9][0-9]*$ ]]; then
        fail "${variable_name} must be a positive integer: ${value}"
    fi
}


inspect_value() {
    local format="$1"

    docker image inspect \
        "${IMAGE_NAME}" \
        --format "${format}"
}


measure_compressed_archive_size() {
    docker image save \
        "${IMAGE_NAME}" \
        | gzip -9 -c \
        | wc -c \
        | tr -d '[:space:]'
}


assert_equals() {
    local actual="$1"
    local expected="$2"
    local label="$3"

    if [[ "${actual}" != "${expected}" ]]; then
        fail "${label}: expected '${expected}', received '${actual}'"
    fi
}


validate_image_metadata() {
    local engine_size
    local compressed_archive_size
    local image_os
    local architecture
    local runtime_user
    local working_directory
    local command
    local port_exposed
    local healthcheck_defined

    engine_size="$(inspect_value '{{.Size}}')"
    compressed_archive_size="$(
        measure_compressed_archive_size
    )"
    image_os="$(inspect_value '{{.Os}}')"
    architecture="$(inspect_value '{{.Architecture}}')"
    runtime_user="$(inspect_value '{{.Config.User}}')"
    working_directory="$(inspect_value '{{.Config.WorkingDir}}')"
    command="$(inspect_value '{{json .Config.Cmd}}')"

    port_exposed="$(
        inspect_value \
            '{{if index .Config.ExposedPorts "8000/tcp"}}true{{else}}false{{end}}'
    )"

    healthcheck_defined="$(
        inspect_value \
            '{{if .Config.Healthcheck}}true{{else}}false{{end}}'
    )"

    if ((
        compressed_archive_size
        > MAX_IMAGE_ARCHIVE_SIZE_BYTES
    )); then
        fail \
            "Compressed image archive size " \
            "${compressed_archive_size} bytes exceeds budget " \
            "${MAX_IMAGE_ARCHIVE_SIZE_BYTES} bytes."
    fi

    assert_equals "${image_os}" "linux" "Operating system"
    assert_equals "${runtime_user}" "wc26" "Runtime user"
    assert_equals "${working_directory}" "/app" "Working directory"
    assert_equals \
        "${command}" \
        '["python","-m","wc26.api.server"]' \
        "Container command"
    assert_equals "${port_exposed}" "true" "Port 8000 exposure"
    assert_equals "${healthcheck_defined}" "true" "Docker healthcheck"

    log "Image metadata policy passed."
    printf '  Image:          %s\n' "${IMAGE_NAME}"
    printf '  Architecture:   %s\n' "${architecture}"
    printf '  Engine size:    %s bytes\n' "${engine_size}"
    printf '  Archive size:   %s bytes\n' "${compressed_archive_size}"
    printf '  Archive budget: %s bytes\n' \
        "${MAX_IMAGE_ARCHIVE_SIZE_BYTES}"
    printf '  Runtime user:   %s\n' "${runtime_user}"
    printf '  Working dir:    %s\n' "${working_directory}"
}


validate_runtime_contents() {
    log "Validating runtime filesystem and dependency boundary."

    docker run \
        --rm \
        --interactive \
        --entrypoint python \
        "${IMAGE_NAME}" \
        - <<'PY'
from __future__ import annotations

import importlib.metadata
import importlib.util
import os
import pwd
import shutil
from pathlib import Path

from wc26.api.environment import validate_runtime_environment


REQUIRED_DEPENDENCIES = {
    "fastapi": "fastapi",
    "numpy": "numpy",
    "pandas": "pandas",
    "uvicorn": "uvicorn",
    "h11": "h11",
}

EXCLUDED_DEPENDENCIES = {
    "matplotlib": "matplotlib",
    "Pillow": "PIL",
    "playwright": "playwright",
    "scikit-learn": "sklearn",
    "scipy": "scipy",
    "uvloop": "uvloop",
    "httptools": "httptools",
    "watchfiles": "watchfiles",
    "websockets": "websockets",
    "PyYAML": "yaml",
    "python-dotenv": "dotenv",
}


def distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def assert_dependency_present(
    distribution_name: str,
    module_name: str,
) -> None:
    installed_version = distribution_version(distribution_name)
    module_available = importlib.util.find_spec(module_name) is not None

    print(
        f"REQUIRED {distribution_name}: "
        f"version={installed_version} "
        f"module_available={module_available}"
    )

    if installed_version is None or not module_available:
        raise SystemExit(
            f"Required dependency is missing: {distribution_name}"
        )


def assert_dependency_absent(
    distribution_name: str,
    module_name: str,
) -> None:
    installed_version = distribution_version(distribution_name)
    module_available = importlib.util.find_spec(module_name) is not None

    print(
        f"EXCLUDED {distribution_name}: "
        f"version={installed_version} "
        f"module_available={module_available}"
    )

    if installed_version is not None or module_available:
        raise SystemExit(
            f"Excluded dependency exists: {distribution_name}"
        )


runtime_user = pwd.getpwuid(os.geteuid()).pw_name

if os.geteuid() == 0:
    raise SystemExit("Container must not run as root.")

if runtime_user != "wc26":
    raise SystemExit(
        f"Unexpected runtime user: {runtime_user}"
    )

if Path.cwd() != Path("/app"):
    raise SystemExit(
        f"Unexpected working directory: {Path.cwd()}"
    )

if Path("/wheels").exists():
    raise SystemExit(
        "Builder wheel directory exists in final image."
    )

if shutil.which("gcc") is not None:
    raise SystemExit(
        "Build compiler exists in final image."
    )

apt_lists = Path("/var/lib/apt/lists")

if apt_lists.exists():
    cached_apt_files = [
        path
        for path in apt_lists.rglob("*")
        if path.is_file()
    ]

    if cached_apt_files:
        raise SystemExit(
            "APT package-list cache exists in final image."
        )

validate_runtime_environment()

print("--- Required production dependencies ---")

for distribution_name, module_name in REQUIRED_DEPENDENCIES.items():
    assert_dependency_present(
        distribution_name,
        module_name,
    )

print("\n--- Excluded optional dependencies ---")

for distribution_name, module_name in EXCLUDED_DEPENDENCIES.items():
    assert_dependency_absent(
        distribution_name,
        module_name,
    )

print("\nRuntime image content policy passed.")
print(f"RuntimeUser={runtime_user}")
print(f"WorkingDirectory={Path.cwd()}")
PY
}


main() {
    require_command docker
    require_command gzip
    require_command wc
    require_command tr

    require_positive_integer \
        "${MAX_IMAGE_ARCHIVE_SIZE_BYTES}" \
        "MAX_IMAGE_ARCHIVE_SIZE_BYTES"

    if ! docker info >/dev/null 2>&1; then
        fail "Docker engine is not reachable."
    fi

    if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
        fail "Docker image does not exist locally: ${IMAGE_NAME}"
    fi

    log "Checking image: ${IMAGE_NAME}"

    validate_image_metadata
    validate_runtime_contents

    log "Docker image policy passed."
}


main "$@"
