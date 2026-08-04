# Deployment Guide

This guide is the source of truth for building, validating, deploying and operating the WC26 Transfer Intelligence API.

Frontend deployment and Vercel operations are documented in `docs/WEB_DEPLOYMENT.md`.

## Production Service

```text
Base URL:    https://world-cup-2026-production.up.railway.app
Swagger UI: https://world-cup-2026-production.up.railway.app/docs
Readiness:  https://world-cup-2026-production.up.railway.app/ready
Identity:   https://world-cup-2026-production.up.railway.app/deployment
```

The service is deployed on Railway from the repository Dockerfile. Railway health checks use `GET /ready`.

## Release Model

The deployment model tracks two independently identifiable artifacts:

```text
Application release
└── Git commit SHA and Railway deployment ID

Dataset release
└── Runtime manifest bundle SHA-256
```

The active identities are available from:

```bash
curl --fail --silent \
  https://world-cup-2026-production.up.railway.app/deployment \
  | python -m json.tool
```

Example response shape:

```json
{
  "service": "wc26-transfer-intelligence",
  "version": "0.1.0",
  "environment": "production",
  "provider": "railway",
  "commit_sha": "<40-character-git-sha>",
  "branch": "<deployed-branch>",
  "deployment_id": "<railway-deployment-id>",
  "dataset_bundle_sha256": "<64-character-bundle-sha>"
}
```

Application code and runtime datasets can therefore be verified or rolled back separately.

## Production Startup Flow

```text
Docker image
    ↓
Runtime environment validation
    ↓
Dataset manifest validation
    ↓
File size, SHA-256 and CSV contract validation
    ↓
Runtime catalog loading
    ↓
FastAPI readiness
    ↓
Railway traffic
```

The container starts with:

```bash
python -m wc26.api.server
```

The launcher validates the production environment before starting Uvicorn. Missing, unreadable, modified or structurally invalid datasets stop the process before it accepts traffic.

## Runtime Configuration

The application reads configuration from environment variables.

| Variable | Default | Purpose |
|---|---|---|
| `WC26_ENVIRONMENT` | `development` | `development`, `test` or `production` |
| `WC26_API_HOST` | `127.0.0.1` | Bind host |
| `WC26_API_PORT` | `8000` | Preferred API port |
| `PORT` | unset | Cloud-platform port fallback |
| `WC26_API_TITLE` | Project default | OpenAPI title |
| `WC26_API_SUMMARY` | Project default | OpenAPI summary |
| `WC26_SERVICE_NAME` | `wc26-transfer-intelligence` | Operational service name |
| `WC26_FEATURES_PATH` | Project default | Transfer feature table |
| `WC26_SIMILARITY_PATH` | Project default | Statistical similarity table |
| `WC26_HEATMAP_SIMILARITY_PATH` | Project default | Heatmap similarity table |
| `WC26_HEATMAP_PROFILES_PATH` | Project default | Heatmap profile table |
| `WC26_DATASET_MANIFEST_PATH` | Project default | Runtime dataset manifest |
| `WC26_CORS_ORIGINS` | empty | Comma-separated trusted origins |
| `WC26_LOG_LEVEL` | `INFO` | Python logging level |

Port resolution uses this priority:

```text
WC26_API_PORT → PORT → 8000
```

Railway build metadata is baked into the image so that the runtime can report the deployed commit and branch through `/deployment`.

See `.env.example` for a copyable local configuration template.

## Runtime Datasets

The production API requires four processed CSV files:

| Logical key | Default path |
|---|---|
| `features` | `data/processed/transfer_intelligence/transfer_feature_table.csv` |
| `similarity` | `data/processed/player_similarity/player_similarity_breakdown_long.csv` |
| `heatmap_similarity` | `data/processed/player_heatmaps/heatmap_similarity_long.csv` |
| `heatmap_profiles` | `data/processed/player_heatmaps/player_heatmap_profiles.csv` |

The API loads the complete catalog once during process startup. A running process does not automatically reload files when dataset pointers change.

## Dataset Manifest

The manifest is stored at:

```text
config/runtime_dataset_manifest.json
```

It records:

- logical dataset keys;
- repository-relative paths;
- file sizes;
- SHA-256 checksums;
- row and column counts;
- ordered column names;
- one canonical bundle SHA-256.

Regenerate it after an intentional runtime dataset change:

```bash
python -m wc26.deployment.dataset_manifest
```

Check that the committed manifest is current:

```bash
python -m wc26.deployment.dataset_manifest --check
```

A dataset change without a matching manifest update is an incomplete release.

## Dataset Integrity Validation

Validate the manifest and all configured datasets:

```bash
python -m wc26.deployment.dataset_integrity
```

Equivalent console command:

```bash
wc26-validate-datasets
```

Validation covers:

- manifest structure and version;
- bundle checksum;
- required dataset keys;
- file existence and readability;
- file size and SHA-256;
- ordered columns;
- row and column counts.

Production startup runs the same checks through:

```bash
python -m wc26.api.environment
```

A failed validation exits with status code `1`.

## Docker Image

Build the production image:

```bash
docker build \
  --progress=plain \
  --tag wc26-transfer-api:dev \
  .
```

The final image:

- uses Python 3.12;
- runs as the non-root `wc26` user;
- exposes port `8000`;
- includes a Docker health check;
- validates datasets during build;
- contains only required runtime dependencies;
- starts through `python -m wc26.api.server`.

### Image Policy

```bash
./scripts/docker_image_policy.sh
```

The policy checks container metadata, the non-root user, the working directory, startup command, exposed port, health check, dependency boundaries and runtime filesystem contents.

The size budget is applied to the gzip-compressed Docker archive:

```text
Default archive budget: 140000000 bytes
```

Override it when intentionally changing the policy:

```bash
MAX_IMAGE_ARCHIVE_SIZE_BYTES=150000000 \
  ./scripts/docker_image_policy.sh
```

`MAX_IMAGE_SIZE_BYTES` remains supported as a legacy fallback.

### API Smoke Test

```bash
./scripts/docker_smoke_test.sh
```

This verifies readiness, liveness, player search, player profile, transfer analysis, response contracts and Docker health.

### Hardened Runtime Test

```bash
./scripts/docker_hardened_runtime_test.sh
```

The hardened test uses:

```text
read-only root filesystem
writable tmpfs at /tmp
all Linux capabilities dropped
no-new-privileges
PID limit
memory limit
loopback-only published port
```

### External Read-Only Dataset Test

```bash
./scripts/docker_external_dataset_test.sh
```

This verifies that externally mounted datasets override embedded paths, remain read-only and satisfy all startup and API contracts.

## Dataset Runtime Modes

### Embedded Mode

The production image includes the four runtime datasets and manifest under `/app`.

```bash
./scripts/docker_smoke_test.sh
```

This is the mode currently used by the Railway deployment.

### External Read-Only Mode

A host directory or managed volume may provide the datasets. All dataset and manifest mounts should be read-only.

```bash
./scripts/docker_external_dataset_test.sh
```

This mode supports dataset updates without rebuilding application dependencies.

### Versioned Release Mode

Immutable dataset releases are stored under:

```text
dist/runtime-datasets/
```

Example structure:

```text
dist/runtime-datasets/
├── <bundle-sha256>/
│   ├── config/runtime_dataset_manifest.json
│   └── data/processed/
├── current -> <active-bundle-sha256>
├── previous -> <previous-bundle-sha256>
├── wc26-runtime-datasets-<bundle-sha256>.tar.gz
└── wc26-runtime-datasets-<bundle-sha256>.tar.gz.sha256
```

Generated files under `dist/` are deployment artifacts and are ignored by Git.

## Build and Activate a Versioned Dataset Release

Build the current bundle:

```bash
python -m wc26.deployment.dataset_bundle
```

Equivalent command:

```bash
wc26-build-dataset-bundle
```

The build process validates source files, creates an immutable bundle directory, creates a deterministic archive and writes an archive checksum sidecar.

Read the active manifest identity:

```bash
bundle_sha256="$(
  python - <<'PY'
import json
from pathlib import Path

manifest = json.loads(
    Path("config/runtime_dataset_manifest.json").read_text(
        encoding="utf-8"
    )
)

print(manifest["bundle_sha256"])
PY
)"
```

Activate it:

```bash
python -m wc26.deployment.dataset_release \
  activate \
  "${bundle_sha256}"
```

Inspect release pointers:

```bash
python -m wc26.deployment.dataset_release status
```

Roll back to the previous validated dataset release:

```bash
python -m wc26.deployment.dataset_release rollback
```

Activation and rollback validate target bundles before updating symbolic links.

## Railway Deployment

Railway is configured through:

```text
railway.toml
Dockerfile
```

The service uses:

- the Dockerfile builder;
- `/ready` as the health-check path;
- Railway-provided `PORT` support;
- restart configuration from `railway.toml`;
- Railway build metadata for release identity.

Railway Serverless may place the service to sleep during inactivity, so the first request after an idle period can take longer than warm requests.

## Structured Logging and Observability

Production logs are emitted as one-line JSON documents.

Common lifecycle events:

```text
api.starting
catalog.loading
catalog.loaded
api.ready
api.shutdown.started
api.shutdown.completed
```

Request completion event:

```text
http.request.completed
```

Standard error events:

```text
api.error.client
api.error.dependency
api.error.internal
```

Important structured fields include:

```text
request_id
http_method
http_path
status_code
duration_ms
error_code
exception_type
commit_sha
deployment_id
dataset_bundle_sha256
```

### Request IDs

Clients may send:

```text
X-Request-ID: example-request-001
```

Valid request IDs are preserved and returned in the response header. Missing or invalid IDs are replaced with a generated identifier.

Do not log request bodies, query strings or sensitive values as part of request observability.

## Production Validation

### Cloud Smoke Test

```bash
latest_sha="$(git rev-parse HEAD)"

WC26_EXPECTED_COMMIT_SHA="${latest_sha}" \
  ./scripts/cloud_smoke_test.sh \
  "https://world-cup-2026-production.up.railway.app"
```

This validates:

- readiness and liveness;
- player search and profile;
- transfer analysis;
- deployment identity;
- expected commit SHA;
- OpenAPI and Swagger UI;
- public response contracts.

### Observability Acceptance Test

```bash
latest_sha="$(git rev-parse HEAD)"

WC26_EXPECTED_COMMIT_SHA="${latest_sha}" \
  ./scripts/cloud_observability_test.sh \
  "https://world-cup-2026-production.up.railway.app"
```

The script waits until Railway serves the expected commit, then validates successful and controlled-error request-ID propagation.

Optional wait configuration:

```text
WC26_CLOUD_OBSERVABILITY_MAX_ATTEMPTS
WC26_CLOUD_OBSERVABILITY_POLL_INTERVAL
```

## Frontend Production Validation

The Vercel frontend is validated independently through the same-origin Next.js BFF routes.

```bash
./scripts/web_production_smoke_test.sh \
  "https://your-vercel-domain.vercel.app"
```

The script checks public pages, readiness, health, deployment identity, player search, player profile and transfer analysis through the deployed frontend.

Vercel configuration and rollback procedures are documented in `docs/WEB_DEPLOYMENT.md`.

## CI/CD Workflows

The repository contains four GitHub Actions workflows.

### Python Quality

```text
.github/workflows/python-quality.yml
```

Runs shell syntax validation, Ruff linting, Ruff formatting, mypy and the portable test suite with branch coverage.

### Docker Validation

```text
.github/workflows/docker-validation.yml
```

Builds the production image and runs image policy, API smoke and hardened runtime tests on a Linux runner.

Every run uploads a diagnostic artifact containing build logs, Docker metadata, image inspection, policy output and runtime test output.

Artifact name:

```text
docker-validation-<run-id>-<attempt>
```

### Web Quality

```text
.github/workflows/web-quality.yml
```

Runs the frontend environment check, generated OpenAPI type check, Vitest suite, ESLint, TypeScript validation, production build and production-dependency audit using Node.js 24.

### Production Verification

```text
.github/workflows/production-verification.yml
```

The workflow:

1. validates production configuration;
2. waits for Python Quality, Docker Validation and Web Quality;
3. waits for Railway to serve the exact commit SHA;
4. runs observability acceptance;
5. runs the complete production smoke test;
6. writes a GitHub job summary;
7. uploads production diagnostics.

Required repository variable:

```text
WC26_PRODUCTION_URL=https://world-cup-2026-production.up.railway.app
```

Artifact name:

```text
production-verification-<run-id>-<attempt>
```

Artifacts are retained for 14 days and are uploaded even when validation fails.

## Application Rollback

Railway keeps deployment history. To roll back the application:

1. Open the Railway service.
2. Select a previously healthy deployment.
3. Redeploy or roll back to that release.
4. Confirm `/deployment` reports the expected commit SHA.
5. Run both cloud validation scripts against the restored release.

An application rollback should not change the dataset bundle identity unless the selected image contains a different embedded bundle.

## Dataset Rollback

For external or versioned dataset releases:

```bash
python -m wc26.deployment.dataset_release rollback
```

Restart the API after changing `current`, because the catalog is loaded once per process.

## Failure and Recovery

### Production serves an older commit

The new Railway deployment may still be building or health checking.

```bash
curl --fail --silent \
  https://world-cup-2026-production.up.railway.app/deployment \
  | python -m json.tool
```

Wait for `commit_sha` to match the expected release. The observability acceptance script performs this wait automatically.

### Manifest validation fails

Regenerate and recheck the manifest:

```bash
python -m wc26.deployment.dataset_manifest
python -m wc26.deployment.dataset_manifest --check
python -m wc26.deployment.dataset_integrity
```

### Container does not become ready

Inspect logs and validate the environment:

```bash
docker logs wc26-api

docker exec \
  wc26-api \
  python -m wc26.api.environment
```

### Request failure needs investigation

Search production logs by the returned `X-Request-ID`. A failed request should normally have both an API error event and an HTTP completion event with the same ID.

### GitHub Actions validation fails

Download the diagnostic artifact from the workflow run. It contains the command output and runtime metadata needed to reproduce the failure.

## Release Checklist

```bash
python -m ruff check \
  src/transfer_intelligence/find_replacements.py \
  src/wc26 \
  tests

python -m ruff format --check \
  src/transfer_intelligence/find_replacements.py \
  src/wc26 \
  tests

python -m mypy src/wc26

python -m pytest \
  -m "not integration" \
  --cov=wc26 \
  --cov-branch \
  --cov-report=term-missing

python -m wc26.deployment.dataset_manifest --check
python -m wc26.deployment.dataset_integrity

docker build \
  --tag wc26-transfer-api:dev \
  .

./scripts/docker_image_policy.sh
./scripts/docker_smoke_test.sh
./scripts/docker_hardened_runtime_test.sh
./scripts/docker_external_dataset_test.sh
```

Frontend release checks:

```bash
cd web

npm run env:check
npm run api:types:check
npm test
npm run lint
npm run typecheck
npm run build
npm audit --omit=dev

cd ..
bash -n scripts/web_production_smoke_test.sh
```

After the frontend is deployed:

```bash
./scripts/web_production_smoke_test.sh \
  "https://your-vercel-domain.vercel.app"
```

After push, confirm that all four GitHub Actions workflows pass, Railway `/deployment` reports the exact release SHA and the Vercel frontend smoke test succeeds.
