#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_LABEL="cloud-smoke"

log() {
    printf '[%s] %s\n' \
        "${SCRIPT_LABEL}" \
        "$*"
}

fail() {
    printf '[%s] ERROR: %s\n' \
        "${SCRIPT_LABEL}" \
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
        fail "Required command is unavailable: ${command_name}"
    fi
}

require_positive_integer() {
    local variable_name="$1"
    local value="$2"

    if [[ ! "${value}" =~ ^[1-9][0-9]*$ ]]; then
        fail "${variable_name} must be a positive integer."
    fi
}

require_command curl
require_command python
require_command grep

BASE_URL="${1:-${WC26_PRODUCTION_URL:-}}"

if [[ -z "${BASE_URL}" ]]; then
    printf '%s\n' \
        "Usage:" \
        "  WC26_PRODUCTION_URL=https://example.up.railway.app \\" \
        "    ./scripts/cloud_smoke_test.sh" \
        "" \
        "or:" \
        "  ./scripts/cloud_smoke_test.sh https://example.up.railway.app" \
        >&2

    exit 2
fi

BASE_URL="${BASE_URL%/}"

READY_TIMEOUT_SECONDS="${WC26_CLOUD_READY_TIMEOUT_SECONDS:-180}"
READY_INTERVAL_SECONDS="${WC26_CLOUD_READY_INTERVAL_SECONDS:-2}"
REQUEST_TIMEOUT_SECONDS="${WC26_CLOUD_REQUEST_TIMEOUT_SECONDS:-60}"
ALLOW_HTTP="${WC26_CLOUD_SMOKE_ALLOW_HTTP:-0}"
EXPECTED_COMMIT_SHA="${WC26_EXPECTED_COMMIT_SHA:-}"

PLAYER_ID=978838
PLAYER_NAME="Michael Olise"
SEARCH_QUERY="olise"

require_positive_integer \
    "WC26_CLOUD_READY_TIMEOUT_SECONDS" \
    "${READY_TIMEOUT_SECONDS}"

require_positive_integer \
    "WC26_CLOUD_READY_INTERVAL_SECONDS" \
    "${READY_INTERVAL_SECONDS}"

require_positive_integer \
    "WC26_CLOUD_REQUEST_TIMEOUT_SECONDS" \
    "${REQUEST_TIMEOUT_SECONDS}"

if [[
    -n "${EXPECTED_COMMIT_SHA}"
    && ! "${EXPECTED_COMMIT_SHA}" =~ ^[0-9a-fA-F]{40}$
]]; then
    fail \
        "WC26_EXPECTED_COMMIT_SHA must be " \
        "a 40-character Git commit SHA."
fi

python - \
    "${BASE_URL}" \
    "${ALLOW_HTTP}" <<'PY'
from __future__ import annotations

import sys
from urllib.parse import urlsplit


base_url = sys.argv[1]
allow_http = sys.argv[2] == "1"

parsed = urlsplit(base_url)

allowed_schemes = (
    {"http", "https"}
    if allow_http
    else {"https"}
)

if parsed.scheme not in allowed_schemes:
    expected = (
        "http or https"
        if allow_http
        else "https"
    )

    raise SystemExit(
        "Cloud smoke-test URL must use "
        f"{expected}: {base_url}"
    )

if not parsed.netloc:
    raise SystemExit(
        "Cloud smoke-test URL must include "
        f"a hostname: {base_url}"
    )

if parsed.path not in {"", "/"}:
    raise SystemExit(
        "Cloud smoke-test URL must not include "
        f"a path: {base_url}"
    )

if parsed.query or parsed.fragment:
    raise SystemExit(
        "Cloud smoke-test URL must not include "
        f"a query or fragment: {base_url}"
    )
PY

TEMP_DIRECTORY="$(
    mktemp -d \
        "${TMPDIR:-/tmp}/wc26-cloud-smoke.XXXXXX"
)"

cleanup() {
    rm -rf "${TEMP_DIRECTORY}"
}

trap cleanup EXIT

request_json() {
    local method="$1"
    local path="$2"
    local output_path="$3"
    local request_body="${4:-}"

    local curl_arguments=(
        --silent
        --show-error
        --fail
        --location
        --connect-timeout
        10
        --max-time
        "${REQUEST_TIMEOUT_SECONDS}"
        --request
        "${method}"
        --header
        "Accept: application/json"
        --output
        "${output_path}"
    )

    if [[ -n "${request_body}" ]]; then
        curl_arguments+=(
            --header
            "Content-Type: application/json"
            --data
            "${request_body}"
        )
    fi

    curl \
        "${curl_arguments[@]}" \
        "${BASE_URL}${path}"
}

HEALTH_PATH="${TEMP_DIRECTORY}/health.json"
READY_PATH="${TEMP_DIRECTORY}/ready.json"
SEARCH_PATH="${TEMP_DIRECTORY}/search.json"
PROFILE_PATH="${TEMP_DIRECTORY}/profile.json"
ANALYSIS_PATH="${TEMP_DIRECTORY}/analysis.json"
DEPLOYMENT_PATH="${TEMP_DIRECTORY}/deployment.json"
OPENAPI_PATH="${TEMP_DIRECTORY}/openapi.json"
DOCS_PATH="${TEMP_DIRECTORY}/docs.html"

log "Target: ${BASE_URL}"
log "Waiting for production readiness."

ready=false
attempt=0
deadline="$((SECONDS + READY_TIMEOUT_SECONDS))"

while ((SECONDS <= deadline)); do
    attempt="$((attempt + 1))"

    if curl \
        --silent \
        --fail \
        --location \
        --connect-timeout 10 \
        --max-time "${REQUEST_TIMEOUT_SECONDS}" \
        --output "${READY_PATH}" \
        "${BASE_URL}/ready" \
        2>/dev/null
    then
        if python - \
            "${READY_PATH}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path


path = Path(sys.argv[1])

try:
    document = json.loads(
        path.read_text(encoding="utf-8")
    )
except (OSError, json.JSONDecodeError):
    raise SystemExit(1)

if (
    document.get("status") == "ready"
    and document.get("catalog_loaded_at")
):
    raise SystemExit(0)

raise SystemExit(1)
PY
        then
            ready=true
            break
        fi
    fi

    sleep "${READY_INTERVAL_SECONDS}"
done

if [[ "${ready}" != "true" ]]; then
    fail \
        "Production API did not become ready within " \
        "${READY_TIMEOUT_SECONDS} seconds."
fi

log "API ready after ${attempt} attempt(s)."

log "Checking liveness endpoint."

request_json \
    GET \
    "/health" \
    "${HEALTH_PATH}"

log "Checking readiness endpoint."

request_json \
    GET \
    "/ready" \
    "${READY_PATH}"

log "Checking player search endpoint."

request_json \
    GET \
    "/api/v1/players/search?q=${SEARCH_QUERY}&limit=5" \
    "${SEARCH_PATH}"

log "Checking player profile endpoint."

request_json \
    GET \
    "/api/v1/players/${PLAYER_ID}" \
    "${PROFILE_PATH}"

log "Checking transfer analysis endpoint."

request_json \
    POST \
    "/api/v1/transfer-intelligence/analyze" \
    "${ANALYSIS_PATH}" \
    "{\"player_id\":${PLAYER_ID}}"

log "Checking deployment identity endpoint."

request_json \
    GET \
    "/deployment" \
    "${DEPLOYMENT_PATH}"

log "Checking OpenAPI endpoint."

request_json \
    GET \
    "/openapi.json" \
    "${OPENAPI_PATH}"

log "Checking Swagger UI."

curl \
    --silent \
    --show-error \
    --fail \
    --location \
    --connect-timeout 10 \
    --max-time "${REQUEST_TIMEOUT_SECONDS}" \
    --output "${DOCS_PATH}" \
    "${BASE_URL}/docs"

if ! grep \
    --quiet \
    "Swagger UI" \
    "${DOCS_PATH}"
then
    fail \
        "Swagger UI response did not contain " \
        "the expected marker."
fi

log "Validating production response contracts."

python - \
    "${HEALTH_PATH}" \
    "${READY_PATH}" \
    "${SEARCH_PATH}" \
    "${PROFILE_PATH}" \
    "${ANALYSIS_PATH}" \
    "${OPENAPI_PATH}" \
    "${DEPLOYMENT_PATH}" \
    "${PLAYER_ID}" \
    "${PLAYER_NAME}" \
    "${EXPECTED_COMMIT_SHA}" <<'PY'
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


def load_json(path: str) -> dict[str, Any]:
    try:
        document = json.loads(
            Path(path).read_text(
                encoding="utf-8"
            )
        )
    except OSError as exc:
        raise SystemExit(
            f"Could not read response file "
            f"{path}: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"Response is not valid JSON "
            f"{path}: {exc}"
        ) from exc

    if not isinstance(document, dict):
        raise SystemExit(
            f"Response root must be an object: {path}"
        )

    return document


def require(
    condition: object,
    message: str,
) -> None:
    if not condition:
        raise SystemExit(
            f"Contract validation failed: {message}"
        )


health = load_json(sys.argv[1])
ready = load_json(sys.argv[2])
search = load_json(sys.argv[3])
profile = load_json(sys.argv[4])
analysis = load_json(sys.argv[5])
openapi = load_json(sys.argv[6])
deployment = load_json(sys.argv[7])

player_id = int(sys.argv[8])
player_name = sys.argv[9]
expected_commit_sha = sys.argv[10]

require(
    health.get("status") == "ok",
    "health status is not ok",
)
require(
    health.get("environment") == "production",
    "health environment is not production",
)
require(
    health.get("service")
    == "wc26-transfer-intelligence",
    "health service name is invalid",
)
require(
    bool(health.get("started_at")),
    "health started_at is missing",
)

require(
    ready.get("status") == "ready",
    "readiness status is not ready",
)
require(
    ready.get("environment") == "production",
    "readiness environment is not production",
)
require(
    bool(ready.get("catalog_loaded_at")),
    "catalog_loaded_at is missing",
)

require(
    search.get("query") == "olise",
    "player search query is invalid",
)

players = search.get("players")

require(
    isinstance(players, list),
    "player search players must be a list",
)
require(
    search.get("count") == len(players),
    "player search count does not match players",
)

search_player = next(
    (
        player
        for player in players
        if (
            isinstance(player, dict)
            and player.get("player_id")
            == player_id
        )
    ),
    None,
)

require(
    search_player is not None,
    "expected player was not found in search",
)
require(
    search_player.get("player_name")
    == player_name,
    "search player name is invalid",
)

require(
    profile.get("player_name") == player_name,
    "profile player name is invalid",
)

profile_player_id = profile.get("player_id")

if profile_player_id is not None:
    require(
        profile_player_id == player_id,
        "profile player ID is invalid",
    )

target = analysis.get("target")

require(
    isinstance(target, dict),
    "analysis target must be an object",
)
require(
    target.get("player_id") == player_id,
    "analysis target player ID is invalid",
)
require(
    target.get("player_name") == player_name,
    "analysis target player name is invalid",
)

modes = analysis.get("modes")

require(
    isinstance(modes, (dict, list)),
    "analysis modes must be an object or list",
)
require(
    bool(modes),
    "analysis modes must not be empty",
)

require(
    deployment.get("service")
    == "wc26-transfer-intelligence",
    "deployment service name is invalid",
)
require(
    deployment.get("environment")
    == "production",
    "deployment environment is not production",
)
require(
    deployment.get("provider") == "railway",
    "deployment provider is not railway",
)

commit_sha = deployment.get("commit_sha")

require(
    isinstance(commit_sha, str)
    and re.fullmatch(
        r"[0-9a-fA-F]{40}",
        commit_sha,
    )
    is not None,
    "deployment commit SHA is invalid",
)

if expected_commit_sha:
    require(
        commit_sha.casefold()
        == expected_commit_sha.casefold(),
        (
            "deployment commit SHA does not match "
            "WC26_EXPECTED_COMMIT_SHA"
        ),
    )

branch = deployment.get("branch")

require(
    isinstance(branch, str)
    and bool(branch.strip()),
    "deployment branch is missing",
)

deployment_id = deployment.get(
    "deployment_id"
)

require(
    isinstance(deployment_id, str)
    and bool(deployment_id.strip()),
    "Railway deployment ID is missing",
)

dataset_bundle_sha256 = deployment.get(
    "dataset_bundle_sha256"
)

require(
    isinstance(dataset_bundle_sha256, str)
    and re.fullmatch(
        r"[0-9a-fA-F]{64}",
        dataset_bundle_sha256,
    )
    is not None,
    "dataset bundle SHA256 is invalid",
)

paths = openapi.get("paths")

require(
    isinstance(paths, dict),
    "OpenAPI paths must be an object",
)

expected_paths = {
    "/health",
    "/ready",
    "/deployment",
    "/api/v1/players/search",
    "/api/v1/players/{player_id}",
    "/api/v1/transfer-intelligence/analyze",
}

missing_paths = expected_paths - set(paths)

require(
    not missing_paths,
    "OpenAPI paths are missing: "
    f"{sorted(missing_paths)}",
)

print(
    "Production API contracts validated."
)
print(
    f"Environment={health['environment']}"
)
print(
    f"Service={health['service']}"
)
print(
    f"Player={player_name} ({player_id})"
)
print(
    f"OpenAPIPathCount={len(paths)}"
)
print(
    f"DeploymentProvider="
    f"{deployment['provider']}"
)
print(
    f"DeploymentCommitSHA="
    f"{commit_sha}"
)
print(
    f"DeploymentBranch="
    f"{branch}"
)
print(
    f"DeploymentID="
    f"{deployment_id}"
)
print(
    "DatasetBundleSHA256="
    f"{dataset_bundle_sha256}"
)

if isinstance(modes, dict):
    print(
        f"AnalysisModes={list(modes)}"
    )
else:
    print(
        f"AnalysisModeCount={len(modes)}"
    )
PY

log "Cloud smoke test passed."

printf '%s\n' \
    "  Base URL:       ${BASE_URL}" \
    "  Environment:    production" \
    "  Player:         ${PLAYER_NAME} (${PLAYER_ID})" \
    "  Readiness:      ready" \
    "  Swagger UI:     available"
