#!/usr/bin/env bash

set -Eeuo pipefail


log() {
  printf '[cloud-observability] %s\n' "$*"
}


fail() {
  printf '[cloud-observability] ERROR: %s\n' "$*" >&2
  exit 1
}


base_url="${1:-${WC26_PRODUCTION_URL:-}}"
expected_commit_sha="${WC26_EXPECTED_COMMIT_SHA:-}"
max_attempts="${WC26_CLOUD_OBSERVABILITY_MAX_ATTEMPTS:-90}"
poll_interval_seconds="${WC26_CLOUD_OBSERVABILITY_POLL_INTERVAL:-2}"

if [[ -z "${base_url}" ]]; then
  fail \
    "Provide the production base URL as the first argument " \
    "or WC26_PRODUCTION_URL."
fi

base_url="${base_url%/}"

case "${base_url}" in
  http://* | https://*)
    ;;
  *)
    fail "Production base URL must use http or https."
    ;;
esac

if [[ -z "${expected_commit_sha}" ]]; then
  fail "WC26_EXPECTED_COMMIT_SHA must be configured."
fi

if [[ ! "${expected_commit_sha}" =~ ^[0-9a-fA-F]{40}$ ]]; then
  fail "WC26_EXPECTED_COMMIT_SHA must be a 40-character Git SHA."
fi

if [[ ! "${max_attempts}" =~ ^[1-9][0-9]*$ ]]; then
  fail \
    "WC26_CLOUD_OBSERVABILITY_MAX_ATTEMPTS " \
    "must be a positive integer."
fi

if [[ ! "${poll_interval_seconds}" =~ ^[1-9][0-9]*$ ]]; then
  fail \
    "WC26_CLOUD_OBSERVABILITY_POLL_INTERVAL " \
    "must be a positive integer."
fi

temporary_directory="$(
  mktemp -d \
    "${TMPDIR:-/tmp}/wc26-cloud-observability.XXXXXX"
)"

cleanup() {
  rm -rf "${temporary_directory}"
}

trap cleanup EXIT

ready_body="${temporary_directory}/ready.json"
deployment_body="${temporary_directory}/deployment.json"

health_body="${temporary_directory}/health.json"
health_headers="${temporary_directory}/health.headers"

client_error_body="${temporary_directory}/client-error.json"
client_error_headers="${temporary_directory}/client-error.headers"

run_identifier="$(
  printf '%s-%s' \
    "$(date -u '+%Y%m%dT%H%M%SZ')" \
    "$$"
)"

success_request_id="cloud-observability-success-${run_identifier}"
client_error_request_id="cloud-observability-client-error-${run_identifier}"

matched_deployment=false
production_commit_sha=""
deployment_attempt=0

log "Target: ${base_url}"
log "Expected commit: ${expected_commit_sha}"
log "Waiting for the expected production deployment."

for ((
  deployment_attempt = 1;
  deployment_attempt <= max_attempts;
  deployment_attempt++
)); do
  ready_status=""

  if ready_status="$(
    curl \
      --silent \
      --show-error \
      --connect-timeout 10 \
      --max-time 30 \
      --output "${ready_body}" \
      --write-out '%{http_code}' \
      "${base_url}/ready"
  )" && [[ "${ready_status}" == "200" ]]; then
    deployment_status=""

    if deployment_status="$(
      curl \
        --silent \
        --show-error \
        --connect-timeout 10 \
        --max-time 30 \
        --output "${deployment_body}" \
        --write-out '%{http_code}' \
        "${base_url}/deployment"
    )" && [[ "${deployment_status}" == "200" ]]; then
      if production_commit_sha="$(
        python - \
          "${deployment_body}" \
          <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path


document = json.loads(
    Path(sys.argv[1]).read_text(
        encoding="utf-8",
    )
)

commit_sha = document.get(
    "commit_sha",
)

if not isinstance(
    commit_sha,
    str,
):
    raise SystemExit(1)

print(commit_sha)
PY
      )"; then
        if [[ "${production_commit_sha}" == "${expected_commit_sha}" ]]; then
          matched_deployment=true

          log \
            "Expected deployment became ready after " \
            "${deployment_attempt} attempt(s)."

          break
        fi
      fi
    fi
  fi

  log \
    "Attempt ${deployment_attempt}/${max_attempts}: " \
    "expected deployment is not active yet."

  sleep "${poll_interval_seconds}"
done

if [[ "${matched_deployment}" != "true" ]]; then
  fail \
    "Production did not reach commit " \
    "${expected_commit_sha}. " \
    "Current observed commit: " \
    "${production_commit_sha:-unavailable}"
fi

log "Checking successful request-ID propagation."

health_status=""

if ! health_status="$(
  curl \
    --silent \
    --show-error \
    --connect-timeout 10 \
    --max-time 30 \
    --request GET \
    --header 'Accept: application/json' \
    --header "X-Request-ID: ${success_request_id}" \
    --dump-header "${health_headers}" \
    --output "${health_body}" \
    --write-out '%{http_code}' \
    "${base_url}/health"
)"; then
  fail "Health observability request failed."
fi

if [[ "${health_status}" != "200" ]]; then
  fail \
    "Expected /health status 200, " \
    "received ${health_status}."
fi

log "Checking controlled client-error observability."

client_error_status=""

if ! client_error_status="$(
  curl \
    --silent \
    --show-error \
    --connect-timeout 10 \
    --max-time 30 \
    --request GET \
    --header 'Accept: application/json' \
    --header "X-Request-ID: ${client_error_request_id}" \
    --dump-header "${client_error_headers}" \
    --output "${client_error_body}" \
    --write-out '%{http_code}' \
    "${base_url}/api/v1/players/999999999"
)"; then
  fail "Controlled client-error request failed."
fi

if [[ "${client_error_status}" != "404" ]]; then
  fail \
    "Expected controlled client-error status 404, " \
    "received ${client_error_status}."
fi

log "Validating observability response contracts."

python - \
  "${deployment_body}" \
  "${expected_commit_sha}" \
  "${health_body}" \
  "${health_headers}" \
  "${success_request_id}" \
  "${client_error_body}" \
  "${client_error_headers}" \
  "${client_error_request_id}" \
  <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def load_json(
    path: str,
) -> dict[str, Any]:
    document = json.loads(
        Path(path).read_text(
            encoding="utf-8",
        )
    )

    if not isinstance(
        document,
        dict,
    ):
        raise AssertionError(
            f"Expected JSON object in {path}."
        )

    return document


def response_header(
    path: str,
    header_name: str,
) -> str | None:
    expected_name = (
        header_name.casefold()
    )
    matched_value: str | None = None

    for raw_line in Path(path).read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines():
        if ":" not in raw_line:
            continue

        name, value = raw_line.split(
            ":",
            1,
        )

        if (
            name.strip().casefold()
            == expected_name
        ):
            matched_value = value.strip()

    return matched_value


(
    _,
    deployment_path,
    expected_commit_sha,
    health_path,
    health_headers_path,
    success_request_id,
    client_error_path,
    client_error_headers_path,
    client_error_request_id,
) = sys.argv

deployment = load_json(
    deployment_path
)
health = load_json(
    health_path
)
client_error = load_json(
    client_error_path
)

assert (
    deployment.get("environment")
    == "production"
), "Deployment environment is not production."

assert (
    deployment.get("provider")
    == "railway"
), "Deployment provider is not Railway."

assert (
    deployment.get("commit_sha")
    == expected_commit_sha
), "Deployment commit SHA does not match."

assert deployment.get(
    "deployment_id"
), "Deployment ID is missing."

dataset_bundle_sha256 = deployment.get(
    "dataset_bundle_sha256"
)

assert isinstance(
    dataset_bundle_sha256,
    str,
), "Dataset bundle SHA is missing."

assert (
    len(dataset_bundle_sha256)
    == 64
), "Dataset bundle SHA is invalid."

assert (
    health.get("status")
    == "ok"
), "Health response status is invalid."

assert (
    response_header(
        health_headers_path,
        "X-Request-ID",
    )
    == success_request_id
), "Successful request ID was not preserved."

error = client_error.get(
    "error"
)

assert isinstance(
    error,
    dict,
), "Client-error response envelope is invalid."

assert (
    error.get("code")
    == "player_not_found"
), "Controlled error code is invalid."

assert error.get(
    "message"
), "Controlled error message is missing."

assert (
    response_header(
        client_error_headers_path,
        "X-Request-ID",
    )
    == client_error_request_id
), "Client-error request ID was not preserved."

print(
    "Production observability contracts validated."
)
print(
    "DeploymentCommitSHA="
    f"{deployment['commit_sha']}"
)
print(
    "DeploymentID="
    f"{deployment['deployment_id']}"
)
print(
    "DatasetBundleSHA256="
    f"{dataset_bundle_sha256}"
)
print(
    "SuccessRequestID="
    f"{success_request_id}"
)
print(
    "ClientErrorRequestID="
    f"{client_error_request_id}"
)
PY

log "Production observability acceptance test passed."

printf '\n'
printf '  Base URL:               %s\n' "${base_url}"
printf '  Deployment commit:      %s\n' "${expected_commit_sha}"
printf '  Success request ID:     %s\n' "${success_request_id}"
printf '  Client-error request ID:%s\n' " ${client_error_request_id}"
printf '\n'
printf '%s\n' \
  "Search the two request IDs in Railway Deploy Logs to inspect correlation."
