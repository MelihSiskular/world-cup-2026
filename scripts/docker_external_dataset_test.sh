#!/usr/bin/env bash

set -Eeuo pipefail

readonly IMAGE_NAME="${1:-wc26-transfer-api:dev}"
readonly CONTAINER_NAME="${CONTAINER_NAME:-wc26-api-external-data}"
readonly HOST_PORT="${HOST_PORT:-8020}"
readonly TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-120}"
readonly PLAYER_ID="${PLAYER_ID:-978838}"
readonly MEMORY_LIMIT="${MEMORY_LIMIT:-512m}"
readonly PIDS_LIMIT="${PIDS_LIMIT:-64}"

readonly SCRIPT_DIRECTORY="$(
    cd "$(dirname "${BASH_SOURCE[0]}")"
    pwd
)"
readonly REPOSITORY_ROOT="$(
    cd "${SCRIPT_DIRECTORY}/.."
    pwd
)"

readonly CONFIG_DIRECTORY="${REPOSITORY_ROOT}/config"
readonly TRANSFER_DIRECTORY="$(
    printf '%s' \
        "${REPOSITORY_ROOT}/data/processed/" \
        "transfer_intelligence"
)"
readonly SIMILARITY_DIRECTORY="$(
    printf '%s' \
        "${REPOSITORY_ROOT}/data/processed/" \
        "player_similarity"
)"
readonly HEATMAP_DIRECTORY="$(
    printf '%s' \
        "${REPOSITORY_ROOT}/data/processed/" \
        "player_heatmaps"
)"

readonly MANIFEST_SOURCE="$(
    printf '%s' \
        "${CONFIG_DIRECTORY}/" \
        "runtime_dataset_manifest.json"
)"
readonly FEATURES_SOURCE="$(
    printf '%s' \
        "${TRANSFER_DIRECTORY}/" \
        "transfer_feature_table.csv"
)"
readonly SIMILARITY_SOURCE="$(
    printf '%s' \
        "${SIMILARITY_DIRECTORY}/" \
        "player_similarity_breakdown_long.csv"
)"
readonly HEATMAP_SIMILARITY_SOURCE="$(
    printf '%s' \
        "${HEATMAP_DIRECTORY}/" \
        "heatmap_similarity_long.csv"
)"
readonly HEATMAP_PROFILES_SOURCE="$(
    printf '%s' \
        "${HEATMAP_DIRECTORY}/" \
        "player_heatmap_profiles.csv"
)"

readonly CONTAINER_MANIFEST_PATH="$(
    printf '%s' \
        "/runtime/config/" \
        "runtime_dataset_manifest.json"
)"
readonly CONTAINER_FEATURES_PATH="$(
    printf '%s' \
        "/runtime/data/transfer_intelligence/" \
        "transfer_feature_table.csv"
)"
readonly CONTAINER_SIMILARITY_PATH="$(
    printf '%s' \
        "/runtime/data/player_similarity/" \
        "player_similarity_breakdown_long.csv"
)"
readonly CONTAINER_HEATMAP_SIMILARITY_PATH="$(
    printf '%s' \
        "/runtime/data/player_heatmaps/" \
        "heatmap_similarity_long.csv"
)"
readonly CONTAINER_HEATMAP_PROFILES_PATH="$(
    printf '%s' \
        "/runtime/data/player_heatmaps/" \
        "player_heatmap_profiles.csv"
)"

readonly BASE_URL="http://127.0.0.1:${HOST_PORT}"
readonly TEMP_DIRECTORY="$(mktemp -d)"


log() {
    printf '\n[docker-external-data] %s\n' "$*"
}


fail() {
    printf \
        '[docker-external-data] ERROR: %s\n' \
        "$*" \
        >&2

    exit 1
}


require_command() {
    local command_name="$1"

    if ! command -v \
        "${command_name}" \
        >/dev/null 2>&1
    then
        fail \
            "Required command not found: " \
            "${command_name}"
    fi
}


require_positive_integer() {
    local value="$1"
    local variable_name="$2"

    if [[ ! "${value}" =~ ^[1-9][0-9]*$ ]]; then
        fail \
            "${variable_name} must be a positive " \
            "integer: ${value}"
    fi
}


require_file() {
    local path="$1"

    if [[ ! -f "${path}" ]]; then
        fail "Required file does not exist: ${path}"
    fi

    if [[ ! -r "${path}" ]]; then
        fail "Required file is not readable: ${path}"
    fi
}


container_exists() {
    docker container inspect \
        "${CONTAINER_NAME}" \
        >/dev/null 2>&1
}


cleanup() {
    local exit_code=$?

    trap - EXIT
    set +e

    if ((exit_code != 0)) && container_exists; then
        printf '\n--- Container logs ---\n' >&2
        docker logs "${CONTAINER_NAME}" >&2
    fi

    if container_exists; then
        log \
            "Removing external-data container: " \
            "${CONTAINER_NAME}"

        docker rm \
            --force \
            "${CONTAINER_NAME}" \
            >/dev/null
    fi

    rm -rf "${TEMP_DIRECTORY}"

    exit "${exit_code}"
}


trap cleanup EXIT


validate_local_bundle() {
    log "Validating the host dataset bundle."

    (
        cd "${REPOSITORY_ROOT}"

        python -m \
            wc26.deployment.dataset_manifest \
            --check

        python -m \
            wc26.deployment.dataset_integrity
    )

    log "Host dataset bundle is valid."
}


start_container() {
    log "Starting container with external read-only datasets."
    log "Image: ${IMAGE_NAME}"
    log "Base URL: ${BASE_URL}"

    docker run \
        --detach \
        --rm \
        --name "${CONTAINER_NAME}" \
        --publish "127.0.0.1:${HOST_PORT}:8000" \
        --read-only \
        --tmpfs "/tmp:rw,noexec,nosuid,nodev,size=64m" \
        --cap-drop ALL \
        --security-opt no-new-privileges=true \
        --pids-limit "${PIDS_LIMIT}" \
        --memory "${MEMORY_LIMIT}" \
        --env WC26_ENVIRONMENT=production \
        --env \
            "WC26_DATASET_MANIFEST_PATH=${CONTAINER_MANIFEST_PATH}" \
        --env \
            "WC26_FEATURES_PATH=${CONTAINER_FEATURES_PATH}" \
        --env \
            "WC26_SIMILARITY_PATH=${CONTAINER_SIMILARITY_PATH}" \
        --env \
            "WC26_HEATMAP_SIMILARITY_PATH=${CONTAINER_HEATMAP_SIMILARITY_PATH}" \
        --env \
            "WC26_HEATMAP_PROFILES_PATH=${CONTAINER_HEATMAP_PROFILES_PATH}" \
        --mount \
            "type=bind,source=${CONFIG_DIRECTORY},target=/runtime/config,readonly" \
        --mount \
            "type=bind,source=${TRANSFER_DIRECTORY},target=/runtime/data/transfer_intelligence,readonly" \
        --mount \
            "type=bind,source=${SIMILARITY_DIRECTORY},target=/runtime/data/player_similarity,readonly" \
        --mount \
            "type=bind,source=${HEATMAP_DIRECTORY},target=/runtime/data/player_heatmaps,readonly" \
        "${IMAGE_NAME}" \
        >"${TEMP_DIRECTORY}/container-id.txt"
}


wait_for_readiness() {
    local deadline
    local running

    deadline=$((SECONDS + TIMEOUT_SECONDS))

    log "Waiting for API readiness: ${BASE_URL}/ready"

    while true; do
        if curl \
            --fail \
            --silent \
            --show-error \
            --max-time 5 \
            "${BASE_URL}/ready" \
            >"${TEMP_DIRECTORY}/ready.json" \
            2>/dev/null
        then
            log "API is ready."
            return
        fi

        if ! container_exists; then
            fail \
                "Container stopped before becoming ready."
        fi

        running="$(
            docker inspect \
                --format '{{.State.Running}}' \
                "${CONTAINER_NAME}"
        )"

        if [[ "${running}" != "true" ]]; then
            fail "Container is no longer running."
        fi

        if ((SECONDS >= deadline)); then
            fail \
                "API did not become ready within " \
                "${TIMEOUT_SECONDS} seconds."
        fi

        sleep 1
    done
}


validate_mount_configuration() {
    log "Validating external Docker mounts."

    docker inspect \
        "${CONTAINER_NAME}" \
        >"${TEMP_DIRECTORY}/inspect.json"

    python - \
        "${TEMP_DIRECTORY}/inspect.json" \
        <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path


inspect_path = Path(sys.argv[1])

container = json.loads(
    inspect_path.read_text(encoding="utf-8")
)[0]

expected_destinations = {
    "/runtime/config",
    "/runtime/data/transfer_intelligence",
    "/runtime/data/player_similarity",
    "/runtime/data/player_heatmaps",
}

mounts = {
    mount["Destination"]: mount
    for mount in container.get("Mounts", [])
}

missing = expected_destinations - set(mounts)

if missing:
    raise SystemExit(
        f"External dataset mounts are missing: "
        f"{sorted(missing)}"
    )

for destination in sorted(expected_destinations):
    mount = mounts[destination]

    if mount.get("Type") != "bind":
        raise SystemExit(
            f"Mount is not a bind mount: "
            f"{destination}"
        )

    if mount.get("RW") is not False:
        raise SystemExit(
            f"Mount is not read-only: "
            f"{destination}"
        )

    print(
        f"Validated mount: "
        f"source={mount['Source']} "
        f"destination={destination} "
        f"read_only={not mount['RW']}"
    )

print("External dataset mount configuration is valid.")
PY
}


validate_container_environment() {
    log "Validating runtime paths inside the container."

    docker exec \
        --interactive \
        "${CONTAINER_NAME}" \
        python - <<'PY'
from __future__ import annotations

import os
from pathlib import Path


expected = {
    "WC26_DATASET_MANIFEST_PATH": (
        "/runtime/config/"
        "runtime_dataset_manifest.json"
    ),
    "WC26_FEATURES_PATH": (
        "/runtime/data/transfer_intelligence/"
        "transfer_feature_table.csv"
    ),
    "WC26_SIMILARITY_PATH": (
        "/runtime/data/player_similarity/"
        "player_similarity_breakdown_long.csv"
    ),
    "WC26_HEATMAP_SIMILARITY_PATH": (
        "/runtime/data/player_heatmaps/"
        "heatmap_similarity_long.csv"
    ),
    "WC26_HEATMAP_PROFILES_PATH": (
        "/runtime/data/player_heatmaps/"
        "player_heatmap_profiles.csv"
    ),
}

for variable, expected_path in expected.items():
    actual_path = os.environ.get(variable)

    if actual_path != expected_path:
        raise SystemExit(
            f"Unexpected {variable}: "
            f"expected={expected_path}, "
            f"actual={actual_path}"
        )

    path = Path(actual_path)

    if not path.is_file():
        raise SystemExit(
            f"Runtime file is missing: {path}"
        )

    print(
        f"{variable}={path} "
        f"bytes={path.stat().st_size}"
    )

print("Container is using external runtime paths.")
PY
}


validate_container_integrity() {
    log "Validating mounted datasets against the manifest."

    docker exec \
        "${CONTAINER_NAME}" \
        python -m \
        wc26.deployment.dataset_integrity

    log "Mounted dataset integrity is valid."
}


validate_read_only_mounts() {
    log "Checking that mounted datasets reject writes."

    if docker exec \
        "${CONTAINER_NAME}" \
        sh -c \
        'printf "\ntamper\n" >> "$WC26_FEATURES_PATH"' \
        >/dev/null 2>&1
    then
        fail \
            "A write unexpectedly succeeded on an " \
            "external dataset mount."
    fi

    if docker exec \
        "${CONTAINER_NAME}" \
        sh -c \
        'printf "\ntamper\n" >> "$WC26_DATASET_MANIFEST_PATH"' \
        >/dev/null 2>&1
    then
        fail \
            "A write unexpectedly succeeded on the " \
            "external manifest mount."
    fi

    log "External files correctly rejected writes."
}


validate_api_requests() {
    log "Checking API endpoints with external datasets."

    curl \
        --fail \
        --silent \
        --show-error \
        --max-time 10 \
        "${BASE_URL}/health" \
        >"${TEMP_DIRECTORY}/health.json"

    curl \
        --fail \
        --silent \
        --show-error \
        --max-time 20 \
        "${BASE_URL}/api/v1/players/search?q=olise&limit=5" \
        >"${TEMP_DIRECTORY}/search.json"

    curl \
        --fail \
        --silent \
        --show-error \
        --max-time 20 \
        "${BASE_URL}/api/v1/players/${PLAYER_ID}" \
        >"${TEMP_DIRECTORY}/profile.json"

    curl \
        --fail \
        --silent \
        --show-error \
        --max-time 60 \
        --request POST \
        --header "Content-Type: application/json" \
        --data "{\"player_id\": ${PLAYER_ID}}" \
        "${BASE_URL}/api/v1/transfer-intelligence/analyze" \
        >"${TEMP_DIRECTORY}/analysis.json"

    python - \
        "${TEMP_DIRECTORY}/health.json" \
        "${TEMP_DIRECTORY}/search.json" \
        "${TEMP_DIRECTORY}/profile.json" \
        "${TEMP_DIRECTORY}/analysis.json" \
        <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path


for raw_path in sys.argv[1:]:
    path = Path(raw_path)

    payload = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(payload, dict):
        raise SystemExit(
            f"Expected JSON object: {path.name}"
        )

    if not payload:
        raise SystemExit(
            f"Received empty response: {path.name}"
        )

    print(
        f"Validated {path.name}: "
        f"keys={sorted(payload)[:8]}"
    )
PY

    log "API endpoints passed with external datasets."
}


wait_for_docker_health() {
    local deadline
    local health_status

    deadline=$((SECONDS + TIMEOUT_SECONDS))

    log "Waiting for Docker healthcheck."

    while true; do
        health_status="$(
            docker inspect \
                --format \
                '{{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}}' \
                "${CONTAINER_NAME}"
        )"

        case "${health_status}" in
            healthy)
                log "Docker healthcheck is healthy."
                return
                ;;
            unhealthy)
                fail \
                    "Docker healthcheck became unhealthy."
                ;;
            missing)
                fail \
                    "Container does not define a healthcheck."
                ;;
        esac

        if ((SECONDS >= deadline)); then
            fail \
                "Docker healthcheck did not become " \
                "healthy within ${TIMEOUT_SECONDS} seconds."
        fi

        sleep 1
    done
}


print_summary() {
    local image_size
    local health_status

    image_size="$(
        docker image inspect \
            "${IMAGE_NAME}" \
            --format '{{.Size}}'
    )"

    health_status="$(
        docker inspect \
            "${CONTAINER_NAME}" \
            --format '{{.State.Health.Status}}'
    )"

    printf \
        '\n[docker-external-data] External dataset test passed.\n'

    printf '  Image:          %s\n' "${IMAGE_NAME}"
    printf '  Image size:     %s bytes\n' "${image_size}"
    printf '  Container:      %s\n' "${CONTAINER_NAME}"
    printf '  Base URL:       %s\n' "${BASE_URL}"
    printf '  Docker health:  %s\n' "${health_status}"
    printf '  Dataset mode:   external read-only mounts\n'
    printf '  Player ID:      %s\n' "${PLAYER_ID}"

    printf '\n--- Runtime resources ---\n'

    docker stats \
        --no-stream \
        --format \
        'Name={{.Name}} CPU={{.CPUPerc}} Memory={{.MemUsage}} PIDs={{.PIDs}}' \
        "${CONTAINER_NAME}"
}


main() {
    require_command docker
    require_command curl
    require_command python

    require_positive_integer \
        "${HOST_PORT}" \
        "HOST_PORT"
    require_positive_integer \
        "${TIMEOUT_SECONDS}" \
        "TIMEOUT_SECONDS"
    require_positive_integer \
        "${PLAYER_ID}" \
        "PLAYER_ID"
    require_positive_integer \
        "${PIDS_LIMIT}" \
        "PIDS_LIMIT"

    require_file "${MANIFEST_SOURCE}"
    require_file "${FEATURES_SOURCE}"
    require_file "${SIMILARITY_SOURCE}"
    require_file "${HEATMAP_SIMILARITY_SOURCE}"
    require_file "${HEATMAP_PROFILES_SOURCE}"

    if ! docker info >/dev/null 2>&1; then
        fail "Docker engine is not reachable."
    fi

    if ! docker image inspect \
        "${IMAGE_NAME}" \
        >/dev/null 2>&1
    then
        fail \
            "Docker image does not exist locally: " \
            "${IMAGE_NAME}"
    fi

    if container_exists; then
        fail \
            "Container name is already in use: " \
            "${CONTAINER_NAME}"
    fi

    validate_local_bundle
    start_container
    wait_for_readiness
    validate_mount_configuration
    validate_container_environment
    validate_container_integrity
    validate_read_only_mounts
    validate_api_requests
    wait_for_docker_health
    print_summary
}


main "$@"
