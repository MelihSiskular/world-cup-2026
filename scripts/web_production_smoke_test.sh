#!/usr/bin/env bash

set -euo pipefail

if [[ "$#" -ne 1 ]]; then
  echo "Usage: $0 <web-base-url>" >&2
  exit 2
fi

WEB_BASE_URL="${1%/}"

case "${WEB_BASE_URL}" in
  https://*)
    ;;
  *)
    echo "Web production URL must use HTTPS." >&2
    exit 2
    ;;
esac

ARTIFACT_DIRECTORY="$(
  mktemp -d
)"

cleanup() {
  rm -rf \
    "${ARTIFACT_DIRECTORY}"
}

trap cleanup EXIT

curl_common=(
  --silent
  --show-error
  --location
  --connect-timeout
  10
  --max-time
  90
  --header
  "Accept: application/json"
)

capture_page() {
  local name="$1"
  local path="$2"

  echo "Checking page ${path}"

  curl \
    --fail \
    --silent \
    --show-error \
    --location \
    --connect-timeout 10 \
    --max-time 90 \
    --header "Accept: text/html" \
    --output \
    "${ARTIFACT_DIRECTORY}/${name}.html" \
    "${WEB_BASE_URL}${path}"
}

capture_json() {
  local name="$1"
  local path="$2"

  echo "Checking API route ${path}"

  curl \
    --fail \
    "${curl_common[@]}" \
    --output \
    "${ARTIFACT_DIRECTORY}/${name}.json" \
    "${WEB_BASE_URL}${path}"
}

capture_readiness() {
  local attempts=30
  local interval_seconds=2
  local attempt
  local status_code

  for attempt in $(
    seq 1 "${attempts}"
  ); do
    status_code="$(
      curl \
        "${curl_common[@]}" \
        --output \
        "${ARTIFACT_DIRECTORY}/ready.json" \
        --write-out "%{http_code}" \
        "${WEB_BASE_URL}/api/status/ready" \
        || true
    )"

    if [[ "${status_code}" == "200" ]]; then
      echo "Frontend BFF readiness succeeded."
      return 0
    fi

    echo \
      "Readiness attempt ${attempt}/${attempts} returned HTTP ${status_code:-unavailable}."

    sleep \
      "${interval_seconds}"
  done

  echo "Frontend BFF did not become ready." >&2
  return 1
}

capture_page \
  "home" \
  "/"

capture_page \
  "players" \
  "/players"

capture_page \
  "methodology" \
  "/methodology"

capture_page \
  "status" \
  "/status"

capture_readiness

capture_json \
  "health" \
  "/api/status/health"

capture_json \
  "deployment" \
  "/api/status/deployment"

capture_json \
  "search" \
  "/api/players/search?q=olise&limit=5"

capture_json \
  "profile" \
  "/api/players/978838"

echo \
  "Checking transfer analysis BFF route"

curl \
  --fail \
  "${curl_common[@]}" \
  --request POST \
  --header \
  "Content-Type: application/json" \
  --data \
  '{
    "player_id": 978838,
    "minimum_minutes": 150,
    "minimum_role_confidence": 50,
    "maximum_market_value": null,
    "neutral_heatmap_score": 70
  }' \
  --output \
  "${ARTIFACT_DIRECTORY}/analysis.json" \
  "${WEB_BASE_URL}/api/transfer-intelligence/analyze"

ARTIFACT_DIRECTORY="${ARTIFACT_DIRECTORY}" \
python - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path


directory = Path(
    os.environ[
        "ARTIFACT_DIRECTORY"
    ]
)


def load_json(
    name: str,
) -> dict[str, object]:
    value = json.loads(
        (
            directory /
            f"{name}.json"
        ).read_text(
            encoding="utf-8",
        )
    )

    if not isinstance(
        value,
        dict,
    ):
        raise SystemExit(
            f"{name} response is not a JSON object."
        )

    return value


ready = load_json(
    "ready",
)

if ready.get(
    "status",
) != "ready":
    raise SystemExit(
        "Readiness response is not ready."
    )


health = load_json(
    "health",
)

if health.get(
    "status",
) != "ok":
    raise SystemExit(
        "Health response is not operational."
    )


deployment = load_json(
    "deployment",
)

dataset_sha = deployment.get(
    "dataset_bundle_sha256",
)

if (
    not isinstance(
        dataset_sha,
        str,
    )
    or len(
        dataset_sha,
    ) != 64
):
    raise SystemExit(
        "Deployment response has no valid dataset bundle SHA."
    )


search = load_json(
    "search",
)

players = search.get(
    "players",
)

if (
    not isinstance(
        players,
        list,
    )
    or not any(
        isinstance(
            player,
            dict,
        )
        and player.get(
            "player_id",
        ) == 978838
        for player in players
    )
):
    raise SystemExit(
        "Michael Olise was not found through the frontend BFF."
    )


profile = load_json(
    "profile",
)

if profile.get(
    "player_id",
) != 978838:
    raise SystemExit(
        "Player profile response has the wrong player identity."
    )


analysis = load_json(
    "analysis",
)

target = analysis.get(
    "target",
)

if (
    not isinstance(
        target,
        dict,
    )
    or target.get(
        "player_id",
    ) != 978838
):
    raise SystemExit(
        "Transfer analysis returned the wrong target."
    )

modes = analysis.get(
    "modes",
)

expected_modes = {
    "immediate",
    "development",
    "value",
    "short_term",
}

if (
    not isinstance(
        modes,
        dict,
    )
    or set(
        modes,
    ) != expected_modes
):
    raise SystemExit(
        "Transfer analysis mode contract is invalid."
    )


print(
    "Frontend production smoke test passed."
)

print(
    "BackendCommitSHA="
    f"{deployment.get('commit_sha')}"
)

print(
    "DatasetBundleSHA256="
    f"{dataset_sha}"
)
PY
