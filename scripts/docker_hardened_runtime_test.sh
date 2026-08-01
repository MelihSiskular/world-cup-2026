#!/usr/bin/env bash

set -Eeuo pipefail

readonly IMAGE_NAME="${1:-wc26-transfer-api:dev}"
readonly CONTAINER_NAME="${CONTAINER_NAME:-wc26-api-hardened}"
readonly HOST_PORT="${HOST_PORT:-8010}"
readonly TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-120}"
readonly PLAYER_ID="${PLAYER_ID:-978838}"
readonly MEMORY_LIMIT="${MEMORY_LIMIT:-512m}"
readonly PIDS_LIMIT="${PIDS_LIMIT:-64}"
readonly TMPFS_SIZE="${TMPFS_SIZE:-64m}"

readonly BASE_URL="http://127.0.0.1:${HOST_PORT}"
readonly TEMP_DIR="$(mktemp -d)"


log() {
    printf '\n[docker-hardened] %s\n' "$*"
}


fail() {
    printf '[docker-hardened] ERROR: %s\n' "$*" >&2
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
        log "Removing hardened test container: ${CONTAINER_NAME}"
        docker rm --force "${CONTAINER_NAME}" >/dev/null
    fi

    rm -rf "${TEMP_DIR}"

    exit "${exit_code}"
}


trap cleanup EXIT


start_container() {
    log "Starting container with hardened runtime settings."
    log "Image: ${IMAGE_NAME}"
    log "Base URL: ${BASE_URL}"

    docker run \
        --detach \
        --rm \
        --name "${CONTAINER_NAME}" \
        --publish "127.0.0.1:${HOST_PORT}:8000" \
        --read-only \
        --tmpfs "/tmp:rw,noexec,nosuid,nodev,size=${TMPFS_SIZE}" \
        --cap-drop ALL \
        --security-opt no-new-privileges=true \
        --pids-limit "${PIDS_LIMIT}" \
        --memory "${MEMORY_LIMIT}" \
        "${IMAGE_NAME}" \
        >"${TEMP_DIR}/container_id.txt"
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
            >"${TEMP_DIR}/ready.json" \
            2>/dev/null
        then
            log "API is ready."
            return
        fi

        if ! container_exists; then
            fail "Container stopped before becoming ready."
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
                fail "Docker healthcheck became unhealthy."
                ;;
            missing)
                fail "Container does not define a healthcheck."
                ;;
        esac

        if ((SECONDS >= deadline)); then
            fail \
                "Docker healthcheck did not become healthy within " \
                "${TIMEOUT_SECONDS} seconds."
        fi

        sleep 1
    done
}


validate_host_configuration() {
    log "Validating Docker host configuration."

    docker inspect \
        "${CONTAINER_NAME}" \
        >"${TEMP_DIR}/inspect.json"

    WC26_EXPECTED_PIDS_LIMIT="${PIDS_LIMIT}" \
    python - "${TEMP_DIR}/inspect.json" <<'PY'
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


inspect_path = Path(sys.argv[1])
container = json.loads(
    inspect_path.read_text(encoding="utf-8")
)[0]

host_config = container["HostConfig"]

if host_config.get("ReadonlyRootfs") is not True:
    raise SystemExit("ReadonlyRootfs is not enabled.")

cap_drop = {
    value.upper()
    for value in (host_config.get("CapDrop") or [])
}

if "ALL" not in cap_drop:
    raise SystemExit(
        f"ALL capabilities are not dropped: {sorted(cap_drop)}"
    )

security_options = host_config.get("SecurityOpt") or []

if not any(
    option.startswith("no-new-privileges")
    for option in security_options
):
    raise SystemExit(
        "no-new-privileges security option is not enabled."
    )

expected_pids_limit = int(
    os.environ["WC26_EXPECTED_PIDS_LIMIT"]
)
actual_pids_limit = host_config.get("PidsLimit")

if actual_pids_limit != expected_pids_limit:
    raise SystemExit(
        "Unexpected PID limit: "
        f"expected={expected_pids_limit}, "
        f"actual={actual_pids_limit}"
    )

memory_limit = int(host_config.get("Memory") or 0)

if memory_limit <= 0:
    raise SystemExit("Container memory limit is not enabled.")

tmpfs_mounts = host_config.get("Tmpfs") or {}

if "/tmp" not in tmpfs_mounts:
    raise SystemExit("/tmp tmpfs mount is missing.")

port_bindings = (
    host_config
    .get("PortBindings", {})
    .get("8000/tcp", [])
)

if not port_bindings:
    raise SystemExit("Port 8000 binding is missing.")

if not any(
    binding.get("HostIp") == "127.0.0.1"
    for binding in port_bindings
):
    raise SystemExit(
        "Port 8000 is not bound exclusively to loopback."
    )

print("Docker host configuration is hardened.")
print(f"ReadonlyRootfs={host_config['ReadonlyRootfs']}")
print(f"CapDrop={sorted(cap_drop)}")
print(f"SecurityOpt={security_options}")
print(f"PidsLimit={actual_pids_limit}")
print(f"MemoryBytes={memory_limit}")
print(f"Tmpfs={tmpfs_mounts}")
print(f"PortBindings={port_bindings}")
PY
}


validate_container_security_state() {
    log "Validating security state from inside the container."

    docker exec \
        --interactive \
        "${CONTAINER_NAME}" \
        python - <<'PY'
from __future__ import annotations

import os
from pathlib import Path


def mount_options(mount_point: str) -> set[str]:
    for line in Path("/proc/mounts").read_text(
        encoding="utf-8"
    ).splitlines():
        fields = line.split()

        if len(fields) >= 4 and fields[1] == mount_point:
            return set(fields[3].split(","))

    raise SystemExit(
        f"Mount point not found: {mount_point}"
    )


def process_status() -> dict[str, str]:
    result: dict[str, str] = {}

    for line in Path("/proc/1/status").read_text(
        encoding="utf-8"
    ).splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", maxsplit=1)
        result[key] = value.strip()

    return result


if os.geteuid() == 0:
    raise SystemExit("Container is running as root.")

if Path.cwd() != Path("/app"):
    raise SystemExit(
        f"Unexpected working directory: {Path.cwd()}"
    )

root_options = mount_options("/")

if "ro" not in root_options:
    raise SystemExit(
        f"Root filesystem is not read-only: {root_options}"
    )

tmp_options = mount_options("/tmp")

required_tmp_options = {
    "rw",
    "noexec",
    "nosuid",
    "nodev",
}

missing_tmp_options = required_tmp_options - tmp_options

if missing_tmp_options:
    raise SystemExit(
        "Missing /tmp mount options: "
        f"{sorted(missing_tmp_options)}"
    )

status = process_status()

if status.get("NoNewPrivs") != "1":
    raise SystemExit(
        "NoNewPrivs is not enabled for PID 1."
    )

effective_capabilities = int(
    status.get("CapEff", "0"),
    16,
)

if effective_capabilities != 0:
    raise SystemExit(
        "PID 1 still has effective Linux capabilities: "
        f"{status.get('CapEff')}"
    )

temporary_file = Path("/tmp/wc26-hardened-write-test.txt")
temporary_file.write_text(
    "temporary filesystem is writable",
    encoding="utf-8",
)

if temporary_file.read_text(encoding="utf-8") != (
    "temporary filesystem is writable"
):
    raise SystemExit("Could not verify /tmp write.")

temporary_file.unlink()

print("Container security state is valid.")
print(f"EffectiveUID={os.geteuid()}")
print(f"WorkingDirectory={Path.cwd()}")
print(f"RootMountOptions={sorted(root_options)}")
print(f"TmpMountOptions={sorted(tmp_options)}")
print(f"NoNewPrivs={status['NoNewPrivs']}")
print(f"CapEff={status['CapEff']}")
PY

    if docker exec \
        "${CONTAINER_NAME}" \
        sh -c 'touch /app/data/.wc26-write-test' \
        >/dev/null 2>&1
    then
        docker exec \
            "${CONTAINER_NAME}" \
            rm -f /app/data/.wc26-write-test \
            >/dev/null 2>&1 \
            || true

        fail "A write unexpectedly succeeded on the read-only filesystem."
    fi

    log "Read-only filesystem correctly rejected persistent writes."
}


validate_api_requests() {
    log "Checking API endpoints under hardened runtime."

    curl \
        --fail \
        --silent \
        --show-error \
        --max-time 10 \
        "${BASE_URL}/health" \
        >"${TEMP_DIR}/health.json"

    curl \
        --fail \
        --silent \
        --show-error \
        --max-time 20 \
        "${BASE_URL}/api/v1/players/${PLAYER_ID}" \
        >"${TEMP_DIR}/profile.json"

    curl \
        --fail \
        --silent \
        --show-error \
        --max-time 60 \
        --request POST \
        --header "Content-Type: application/json" \
        --data "{\"player_id\": ${PLAYER_ID}}" \
        "${BASE_URL}/api/v1/transfer-intelligence/analyze" \
        >"${TEMP_DIR}/analysis.json"

    python - \
        "${TEMP_DIR}/health.json" \
        "${TEMP_DIR}/profile.json" \
        "${TEMP_DIR}/analysis.json" \
        <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path


for raw_path in sys.argv[1:]:
    path = Path(raw_path)

    with path.open(encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, dict):
        raise SystemExit(
            f"Expected JSON object from {path.name}."
        )

    if not payload:
        raise SystemExit(
            f"Received empty JSON object from {path.name}."
        )

    print(
        f"Validated {path.name}: "
        f"keys={sorted(payload)[:8]}"
    )
PY

    log "API endpoints passed under hardened runtime."
}


print_runtime_summary() {
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

    printf '\n[docker-hardened] Hardened runtime test passed.\n'
    printf '  Image:          %s\n' "${IMAGE_NAME}"
    printf '  Image size:     %s bytes\n' "${image_size}"
    printf '  Container:      %s\n' "${CONTAINER_NAME}"
    printf '  Base URL:       %s\n' "${BASE_URL}"
    printf '  Docker health:  %s\n' "${health_status}"
    printf '  Memory limit:   %s\n' "${MEMORY_LIMIT}"
    printf '  PID limit:      %s\n' "${PIDS_LIMIT}"
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

    if ! docker info >/dev/null 2>&1; then
        fail "Docker engine is not reachable."
    fi

    if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
        fail "Docker image does not exist locally: ${IMAGE_NAME}"
    fi

    if container_exists; then
        fail \
            "Container name is already in use: " \
            "${CONTAINER_NAME}"
    fi

    start_container
    wait_for_readiness
    validate_host_configuration
    validate_container_security_state
    validate_api_requests
    wait_for_docker_health
    print_runtime_summary
}


main "$@"
