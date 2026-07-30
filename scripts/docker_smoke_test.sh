#!/usr/bin/env bash

set -Eeuo pipefail

readonly IMAGE_NAME="${1:-wc26-transfer-api:dev}"
readonly CONTAINER_NAME="${CONTAINER_NAME:-wc26-api-smoke}"
readonly HOST_PORT="${HOST_PORT:-8000}"
readonly STARTUP_TIMEOUT_SECONDS="${STARTUP_TIMEOUT_SECONDS:-120}"
readonly PLAYER_ID="${PLAYER_ID:-978838}"
readonly SEARCH_QUERY="${SEARCH_QUERY:-olise}"
readonly BASE_URL="http://127.0.0.1:${HOST_PORT}"

TMP_DIR="$(mktemp -d)"
CONTAINER_STARTED=0
PYTHON_BIN=""


log() {
    printf '[docker-smoke] %s\n' "$*"
}


print_container_logs() {
    if [[ "${CONTAINER_STARTED}" -eq 1 ]]; then
        printf '\n--- Container logs ---\n' >&2
        docker logs --tail 200 "${CONTAINER_NAME}" >&2 || true
        printf '%s\n\n' '----------------------' >&2
    fi
}


cleanup() {
    local exit_code=$?

    trap - EXIT INT TERM

    if [[ "${CONTAINER_STARTED}" -eq 1 ]]; then
        log "Removing smoke-test container: ${CONTAINER_NAME}"
        docker rm --force "${CONTAINER_NAME}" >/dev/null 2>&1 || true
    fi

    rm -rf "${TMP_DIR}"
    exit "${exit_code}"
}


fail() {
    printf '[docker-smoke] ERROR: %s\n' "$*" >&2
    print_container_logs
    exit 1
}


require_command() {
    local command_name="$1"

    if ! command -v "${command_name}" >/dev/null 2>&1; then
        fail "Required command not found: ${command_name}"
    fi
}


select_python() {
    if [[ -n "${PYTHON_COMMAND:-}" ]]; then
        PYTHON_BIN="${PYTHON_COMMAND}"
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_BIN="python"
    else
        fail "Python is required for JSON contract validation."
    fi
}


wait_for_readiness() {
    local deadline
    local container_running

    deadline=$((SECONDS + STARTUP_TIMEOUT_SECONDS))

    log "Waiting for API readiness: ${BASE_URL}/ready"

    while true; do
        if curl \
            --fail \
            --silent \
            --show-error \
            "${BASE_URL}/ready" \
            > "${TMP_DIR}/ready.json" \
            2>/dev/null
        then
            log "API is ready."
            return
        fi

        container_running="$(
            docker inspect \
                --format '{{.State.Running}}' \
                "${CONTAINER_NAME}" \
                2>/dev/null \
                || printf 'false'
        )"

        if [[ "${container_running}" != "true" ]]; then
            fail "Container stopped before the API became ready."
        fi

        if ((SECONDS >= deadline)); then
            fail "API did not become ready within ${STARTUP_TIMEOUT_SECONDS} seconds."
        fi

        sleep 1
    done
}


wait_for_docker_health() {
    local deadline
    local health_status

    deadline=$((SECONDS + STARTUP_TIMEOUT_SECONDS))

    log "Waiting for Docker healthcheck."

    while true; do
        health_status="$(
            docker inspect \
                --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}}' \
                "${CONTAINER_NAME}"
        )"

        case "${health_status}" in
            healthy)
                log "Docker healthcheck is healthy."
                return
                ;;
            unhealthy)
                fail "Docker marked the container as unhealthy."
                ;;
            starting)
                ;;
            missing)
                fail "The image does not define a Docker healthcheck."
                ;;
            *)
                fail "Unexpected Docker health status: ${health_status}"
                ;;
        esac

        if ((SECONDS >= deadline)); then
            fail "Docker healthcheck did not become healthy within ${STARTUP_TIMEOUT_SECONDS} seconds."
        fi

        sleep 1
    done
}


request_api_contracts() {
    log "Checking liveness endpoint."
    curl \
        --fail \
        --silent \
        --show-error \
        "${BASE_URL}/health" \
        > "${TMP_DIR}/health.json"

    log "Checking player search endpoint."
    curl \
        --fail \
        --silent \
        --show-error \
        --get \
        "${BASE_URL}/api/v1/players/search" \
        --data-urlencode "q=${SEARCH_QUERY}" \
        --data-urlencode "limit=5" \
        > "${TMP_DIR}/search.json"

    log "Checking player profile endpoint."
    curl \
        --fail \
        --silent \
        --show-error \
        "${BASE_URL}/api/v1/players/${PLAYER_ID}" \
        > "${TMP_DIR}/profile.json"

    log "Checking transfer analysis endpoint."
    curl \
        --fail \
        --silent \
        --show-error \
        --request POST \
        "${BASE_URL}/api/v1/transfer-intelligence/analyze" \
        --header "Content-Type: application/json" \
        --data "{\"player_id\":${PLAYER_ID}}" \
        > "${TMP_DIR}/analysis.json"
}


validate_json_contracts() {
    log "Validating API response contracts."

    "${PYTHON_BIN}" - "${TMP_DIR}" "${PLAYER_ID}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


responses_directory = Path(sys.argv[1])
expected_player_id = int(sys.argv[2])


def load_json(filename: str) -> dict[str, Any]:
    path = responses_directory / filename

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError(f"{filename} does not contain valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise AssertionError(f"{filename} must contain a JSON object.")

    return payload


health = load_json("health.json")
ready = load_json("ready.json")
search = load_json("search.json")
profile = load_json("profile.json")
analysis = load_json("analysis.json")


assert health.get("status") == "ok", health
assert health.get("environment") == "production", health
assert health.get("service") == "wc26-transfer-intelligence", health
assert isinstance(health.get("uptime_seconds"), int | float), health


assert ready.get("status") == "ready", ready
assert ready.get("environment") == "production", ready
assert ready.get("catalog_loaded_at"), ready


players = search.get("players")
assert isinstance(players, list), search
assert search.get("count") == len(players), search

matching_players = [
    player
    for player in players
    if isinstance(player, dict)
    and player.get("player_id") == expected_player_id
]

assert matching_players, (
    f"Player {expected_player_id} was not found in search response: {search}"
)


assert profile.get("player_id") == expected_player_id, profile
assert profile.get("player_name"), profile
assert profile.get("final_role"), profile
assert profile.get("archetype"), profile


target = analysis.get("target")
assert isinstance(target, dict), analysis
assert target.get("player_id") == expected_player_id, target
assert target.get("player_name") == profile.get("player_name"), target
assert target.get("final_role") == profile.get("final_role"), target


print(
    "Validated contracts for "
    f"{profile['player_name']} ({expected_player_id})."
)
PY
}


print_runtime_summary() {
    local health_status
    local image_size

    health_status="$(
        docker inspect \
            --format '{{.State.Health.Status}}' \
            "${CONTAINER_NAME}"
    )"

    image_size="$(
        docker image inspect \
            --format '{{.Size}}' \
            "${IMAGE_NAME}"
    )"

    printf '\n'
    log "Smoke test passed."
    printf '  Image:          %s\n' "${IMAGE_NAME}"
    printf '  Image size:     %s bytes\n' "${image_size}"
    printf '  Container:      %s\n' "${CONTAINER_NAME}"
    printf '  Base URL:       %s\n' "${BASE_URL}"
    printf '  Docker health:  %s\n' "${health_status}"
    printf '  Player ID:      %s\n' "${PLAYER_ID}"

    printf '\n--- Runtime resources ---\n'

    docker stats \
        --no-stream \
        --format \
        'Name={{.Name}} CPU={{.CPUPerc}} Memory={{.MemUsage}} PIDs={{.PIDs}}' \
        "${CONTAINER_NAME}"
}


main() {
    trap cleanup EXIT INT TERM

    require_command docker
    require_command curl
    select_python

    log "Using image: ${IMAGE_NAME}"

    if ! docker info >/dev/null 2>&1; then
        fail "Docker engine is not reachable."
    fi

    if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
        fail "Docker image does not exist locally: ${IMAGE_NAME}"
    fi

    if docker container inspect "${CONTAINER_NAME}" >/dev/null 2>&1; then
        fail "A container already exists with the name: ${CONTAINER_NAME}"
    fi

    log "Starting container on host port ${HOST_PORT}."

    docker run \
        --detach \
        --rm \
        --name "${CONTAINER_NAME}" \
        --publish "127.0.0.1:${HOST_PORT}:8000" \
        "${IMAGE_NAME}" \
        > "${TMP_DIR}/container-id.txt"

    CONTAINER_STARTED=1

    wait_for_readiness
    request_api_contracts
    validate_json_contracts
    wait_for_docker_health
    print_runtime_summary
}


main "$@"
