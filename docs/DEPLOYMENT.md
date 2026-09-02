# Backend Deployment Guide

This document is the source of truth for deploying and operating the WC26 FastAPI service. Frontend deployment is covered in `docs/WEB_DEPLOYMENT.md`.

## Production Service

```text
Base URL:    https://world-cup-2026-production.up.railway.app
Swagger UI: https://world-cup-2026-production.up.railway.app/docs
Readiness:  https://world-cup-2026-production.up.railway.app/ready
Identity:   https://world-cup-2026-production.up.railway.app/deployment
```

Railway builds the repository Dockerfile and uses `GET /ready` as its health check.

## Release Identity

Application and dataset releases are independently identifiable:

```text
Application → version, commit SHA and Railway deployment ID
Dataset     → runtime bundle SHA-256
```

```bash
curl --fail --silent \
  https://world-cup-2026-production.up.railway.app/deployment \
  | python -m json.tool
```

Expected release version for the Phase 8.6 product checkpoint is `0.6.0`. The response also reports the active commit and dataset bundle.

## Runtime Configuration

| Variable | Default | Purpose |
|---|---|---|
| `WC26_ENVIRONMENT` | `development` | Runtime environment |
| `WC26_API_HOST` | `127.0.0.1` | Bind host |
| `WC26_API_PORT` | `8000` | Preferred API port |
| `PORT` | unset | Cloud-platform port fallback |
| `WC26_SERVICE_NAME` | `wc26-transfer-intelligence` | Service identity |
| `WC26_FEATURES_PATH` | project default | Transfer feature table |
| `WC26_PLAYER_TOURNAMENT_SUMMARY_PATH` | project default | Tournament summary |
| `WC26_SIMILARITY_PATH` | project default | Statistical pair evidence |
| `WC26_HEATMAP_SIMILARITY_PATH` | project default | Heatmap pair evidence |
| `WC26_HEATMAP_PROFILES_PATH` | project default | Heatmap profiles |
| `WC26_HEATMAP_GRIDS_PATH` | project default | Heatmap grid bundle |
| `WC26_DATASET_MANIFEST_PATH` | project default | Runtime manifest |
| `WC26_CORS_ORIGINS` | empty | Trusted origins |
| `WC26_LOG_LEVEL` | `INFO` | Log level |

Port priority is `WC26_API_PORT → PORT → 8000`.

## Runtime Datasets

The service loads six artifacts once at startup:

| Key | Default path |
|---|---|
| `features` | `data/processed/transfer_intelligence/transfer_feature_table.csv` |
| `player_tournament_summary` | `data/processed/player_matches_analysis/player_tournament_full_summary_enriched.csv` |
| `similarity` | `data/processed/player_similarity/player_similarity_breakdown_long.csv` |
| `heatmap_similarity` | `data/processed/player_heatmaps/heatmap_similarity_long.csv` |
| `heatmap_profiles` | `data/processed/player_heatmaps/player_heatmap_profiles.csv` |
| `heatmap_grids` | `data/processed/player_heatmaps/player_heatmap_grids.npz` |

The manifest at `config/runtime_dataset_manifest.json` records paths, sizes, checksums, shapes, columns and one bundle checksum.

```bash
python -m wc26.deployment.dataset_manifest --check
python -m wc26.deployment.dataset_integrity
```

After an intentional dataset change:

```bash
python -m wc26.deployment.dataset_manifest
python -m wc26.deployment.dataset_integrity
```

A dataset change without a matching manifest update is not releasable.

## Docker Validation

```bash
docker build --progress=plain --tag wc26-transfer-api:dev .
./scripts/docker_image_policy.sh
./scripts/docker_smoke_test.sh
./scripts/docker_hardened_runtime_test.sh
./scripts/docker_external_dataset_test.sh
```

The production image runs as a non-root user, validates datasets before readiness and supports embedded or read-only external datasets.

## Dataset Releases and Rollback

```bash
python -m wc26.deployment.dataset_bundle
python -m wc26.deployment.dataset_release status
python -m wc26.deployment.dataset_release activate <bundle-sha256>
python -m wc26.deployment.dataset_release rollback
```

Restart the API after changing the active dataset pointer because the catalog is loaded once per process.

## Observability

Production emits structured JSON logs for lifecycle, request completion and controlled errors. Important fields include:

```text
request_id, http_method, http_path, status_code, duration_ms,
error_code, commit_sha, deployment_id, dataset_bundle_sha256
```

Clients may send `X-Request-ID`; valid values are preserved in the response. Request bodies and query strings are not included in generic request logs.

## Production Validation

```bash
production_url="https://world-cup-2026-production.up.railway.app"
expected_sha="$(git rev-parse HEAD)"

WC26_EXPECTED_COMMIT_SHA="${expected_sha}" \
  ./scripts/cloud_observability_test.sh "${production_url}"

WC26_EXPECTED_COMMIT_SHA="${expected_sha}" \
  ./scripts/cloud_smoke_test.sh "${production_url}"
```

The smoke test covers readiness, deployment identity, player discovery and profile contracts, transfer analysis and comparison endpoints.

## CI/CD

| Workflow | Responsibility |
|---|---|
| Python Quality | Ruff, formatting, mypy and Python tests |
| Docker Validation | Image policy and runtime tests |
| Web Quality | Contract, frontend tests, lint, typecheck and build |
| Browser Validation | Chromium and WebKit desktop/mobile journeys |
| Production Verification | Exact deployed SHA, observability and smoke tests |

## Application Rollback

1. Restore a previously healthy Railway deployment.
2. Verify `/deployment` reports the intended commit and dataset bundle.
3. Run both cloud validation scripts.
4. If the dataset also changed, restore it independently and restart the API.

## Release Checklist

- Package and OpenAPI versions are `0.6.0`.
- Python, Docker, web and browser workflows pass.
- Dataset manifest and integrity checks pass.
- Railway serves the exact release commit.
- `/deployment` reports the expected dataset bundle.
- Frontend production smoke testing passes through the deployed BFF.
- `git diff --check` passes and release artifacts are intentionally staged.
