# Development Guide

This guide explains how to set up, test and extend the WC26 Transfer Intelligence Python core, CLI and FastAPI backend.

## Requirements

- Python 3.12 or newer
- Git
- Docker Desktop or Docker Engine for container validation
- Local processed datasets for real-data integration tests

## Local Setup

Clone the repository:

```bash
git clone https://github.com/MelihSiskular/world-cup-2026.git
cd world-cup-2026
```

Create and activate a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install the project with development dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Confirm the package and CLI are available:

```bash
python -c "import wc26; print(wc26.__version__)"
wc26-transfer --help
```

## Run Transfer Intelligence

Recommended command:

```bash
wc26-transfer \
  --player "Michael Olise" \
  --top-n 5
```

Example with recruitment constraints:

```bash
wc26-transfer \
  --player "Michael Olise" \
  --minimum-minutes 250 \
  --minimum-role-confidence 65 \
  --maximum-market-value 80000000 \
  --top-n 5
```

The legacy module command remains available for backward compatibility:

```bash
python -m src.transfer_intelligence.find_replacements \
  --player "Michael Olise" \
  --top-n 5
```

Both commands use the same application service.

## Core Architecture

The main analysis flow is:

```text
CLI or API input
      ↓
TransferAnalysisRequest
      ↓
TransferDataCatalog or configured dataset paths
      ↓
run_transfer_analysis()
      ↓
TransferAnalysisResult
      ├── console report
      ├── CSV export
      └── API response
```

The analysis layer should not depend on terminal output, HTTP, Docker or file-writing side effects. Presentation and infrastructure concerns belong in adapters around the core service.

### Important Modules

| Module | Responsibility |
|---|---|
| `config.py` | Paths, thresholds, modes and scoring weights |
| `datasets.py` | Dataset loading and validation |
| `catalog.py` | One-time runtime catalog loading |
| `models.py` | Request and result contracts |
| `matching.py` | Player resolution and similarity attachment |
| `candidates.py` | Candidate population preparation |
| `scoring.py` | Suitability calculations |
| `recommendations.py` | Filtering, ranking and modes |
| `explanations.py` | Recommendation labels and explanations |
| `service.py` | End-to-end analysis workflow |
| `reporting.py` | Console presentation |
| `exporting.py` | CSV output |
| `player_search.py` | Catalog player search |
| `player_profile.py` | Stable player profiles by ID |

Prefer the package public API:

```python
from wc26.analytics.transfer_intelligence import (
    TransferAnalysisRequest,
    run_transfer_analysis,
)
```

## FastAPI Backend

The deployable API lives under:

```text
src/wc26/api/
```

Current structure:

```text
src/wc26/api/
├── app.py
├── dependencies.py
├── deployment.py
├── environment.py
├── errors.py
├── exception_handlers.py
├── logging_config.py
├── main.py
├── request_context.py
├── runtime.py
├── server.py
├── settings.py
├── routes/
│   ├── deployment.py
│   ├── health.py
│   ├── players.py
│   └── transfer_intelligence.py
└── schemas/
```

| Module | Responsibility |
|---|---|
| `app.py` | FastAPI factory, middleware and lifespan |
| `main.py` | Environment-configured ASGI application |
| `server.py` | Production launcher and Uvicorn configuration |
| `settings.py` | Runtime environment parsing and validation |
| `environment.py` | Startup environment and dataset checks |
| `runtime.py` | Catalog, readiness and uptime state |
| `deployment.py` | Release and dataset identity |
| `logging_config.py` | JSON and console logging configuration |
| `request_context.py` | Request ID and request completion middleware |
| `dependencies.py` | Catalog-backed service dependencies |
| `exception_handlers.py` | Safe HTTP errors and structured error logs |
| `routes/` | HTTP endpoint definitions |
| `schemas/` | Request and response contracts |

## Run the API Locally

Development server with reload:

```bash
python -m uvicorn wc26.api.main:app \
  --reload \
  --host 127.0.0.1 \
  --port 8000
```

Production-style launcher:

```bash
WC26_ENVIRONMENT=production \
WC26_API_HOST=127.0.0.1 \
WC26_API_PORT=8000 \
python -m wc26.api.server
```

Interactive documentation:

```text
http://127.0.0.1:8000/docs
```

OpenAPI schema:

```text
http://127.0.0.1:8000/openapi.json
```

## Runtime Configuration

| Variable | Default | Purpose |
|---|---|---|
| `WC26_ENVIRONMENT` | `development` | Runtime environment |
| `WC26_API_HOST` | `127.0.0.1` | Bind host |
| `WC26_API_PORT` | `8000` | Preferred API port |
| `PORT` | unset | Cloud-platform fallback port |
| `WC26_API_TITLE` | Project default | OpenAPI title |
| `WC26_API_SUMMARY` | Project default | OpenAPI summary |
| `WC26_SERVICE_NAME` | `wc26-transfer-intelligence` | Service identifier |
| `WC26_FEATURES_PATH` | Project default | Feature table |
| `WC26_SIMILARITY_PATH` | Project default | Statistical similarity table |
| `WC26_HEATMAP_SIMILARITY_PATH` | Project default | Heatmap similarity table |
| `WC26_HEATMAP_PROFILES_PATH` | Project default | Heatmap profile table |
| `WC26_DATASET_MANIFEST_PATH` | Project default | Runtime manifest |
| `WC26_CORS_ORIGINS` | empty | Trusted comma-separated origins |
| `WC26_LOG_LEVEL` | `INFO` | Application log level |

Port priority:

```text
WC26_API_PORT → PORT → 8000
```

Copy `.env.example` when preparing a local runtime configuration.

## Runtime Catalog and Lifespan

The production application loads the complete transfer catalog once during FastAPI startup:

```text
Environment
    ↓
ApiSettings
    ↓
Runtime integrity validation
    ↓
create_production_app()
    ↓
FastAPI lifespan
    ↓
load_transfer_data_catalog()
    ↓
ApiRuntimeState
```

Runtime state is available at:

```python
application.state.api_runtime
```

It contains validated settings, dataset paths, startup time, catalog load time, uptime, readiness and the cached catalog.

A production startup failure prevents the service from becoming ready. Test applications may omit the catalog loader and use path-based dependency fallbacks.

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Process liveness |
| `GET` | `/ready` | Catalog readiness |
| `GET` | `/deployment` | Release identity |
| `GET` | `/api/v1/players/search` | Search players by name |
| `GET` | `/api/v1/players/{player_id}` | Retrieve a player profile |
| `POST` | `/api/v1/transfer-intelligence/analyze` | Run transfer analysis |

### Player Search

```bash
curl --get \
  "http://127.0.0.1:8000/api/v1/players/search" \
  --data-urlencode "q=olise" \
  --data-urlencode "limit=10"
```

Search is case- and diacritic-insensitive. Exact matches, full-name prefixes and token prefixes rank before general partial matches. No-match searches return an empty list.

### Player Profile

```bash
curl \
  "http://127.0.0.1:8000/api/v1/players/978838"
```

Profiles use stable numeric `player_id` values.

### Transfer Analysis

The request accepts exactly one target:

```json
{
  "player": "Michael Olise"
}
```

or:

```json
{
  "player_id": 978838
}
```

Example:

```bash
curl -X POST \
  "http://127.0.0.1:8000/api/v1/transfer-intelligence/analyze" \
  -H "Content-Type: application/json" \
  -d '{"player_id": 978838}'
```

The HTTP layer delegates to the same structured service used by the CLI. Do not place scoring rules inside route functions.

## Error Responses

Known domain exceptions are mapped centrally.

| HTTP status | Example API code |
|---:|---|
| `400` | `invalid_transfer_analysis_request` |
| `404` | `player_not_found` |
| `409` | `ambiguous_player` |
| `503` | `dataset_unavailable` or `invalid_dataset` |
| `500` | `analysis_failed`, `player_profile_failed` or `player_search_failed` |

Error envelope:

```json
{
  "error": {
    "code": "player_not_found",
    "message": "Player could not be resolved."
  }
}
```

Dataset paths, stack traces and sensitive internal details must not be returned to clients.

## Request IDs

The middleware accepts:

```text
X-Request-ID: local-debug-001
```

A valid supplied ID is preserved and returned in the response. Otherwise, the middleware generates one.

Example:

```bash
curl \
  --include \
  --header "X-Request-ID: local-debug-001" \
  http://127.0.0.1:8000/health
```

Use the same ID to correlate request completion and API error logs.

## Logging

Development uses readable console logs. Production uses structured JSON logs.

Lifecycle events include:

```text
api.starting
catalog.loading
catalog.loaded
api.ready
api.shutdown.started
api.shutdown.completed
```

Request event:

```text
http.request.completed
```

Error events:

```text
api.error.client
api.error.dependency
api.error.internal
```

Do not log request bodies or query strings as part of generic request observability.

## CORS

CORS middleware is installed only when `WC26_CORS_ORIGINS` contains valid origins.

Configured origins are:

- limited to HTTP or HTTPS;
- normalized by removing trailing slashes;
- deduplicated;
- rejected when they include paths, query strings or fragments.

`X-Request-ID` is exposed to allowed browser clients.

## Dependency Overrides in Tests

Route tests should replace expensive application services with deterministic implementations.

```python
from wc26.api.dependencies import get_transfer_analysis_runner

application.dependency_overrides[
    get_transfer_analysis_runner
] = override_analysis_runner
```

Available boundaries include player search, player profile, transfer analysis and dataset path providers.

## Quality Checks

Run Ruff linting:

```bash
python -m ruff check \
  src/transfer_intelligence/find_replacements.py \
  src/wc26 \
  tests
```

Check formatting:

```bash
python -m ruff format --check \
  src/transfer_intelligence/find_replacements.py \
  src/wc26 \
  tests
```

Run strict type checking:

```bash
python -m mypy src/wc26
```

Run portable tests with coverage:

```bash
python -m pytest \
  -m "not integration" \
  --cov=wc26 \
  --cov-branch \
  --cov-report=term-missing
```

The minimum coverage baseline is 65%.

Validate shell scripts:

```bash
find scripts \
  -type f \
  -name '*.sh' \
  -print0 \
  | while IFS= read -r -d '' script_path; do
      bash -n "${script_path}"
    done
```

## Integration Tests

Real-data integration tests require the processed datasets.

```bash
WC26_RUN_INTEGRATION=1 \
python -m pytest -m integration -v
```

Runtime catalog API integration test:

```bash
WC26_RUN_INTEGRATION=1 \
python -m pytest \
  tests/integration/api/test_runtime_catalog_api.py \
  -v
```

These tests verify one-time catalog loading, search, profile, transfer analysis, readiness and shutdown cleanup.

## Docker Development

Build the current production image:

```bash
docker build \
  --progress=plain \
  --tag wc26-transfer-api:dev \
  .
```

Run the full local Docker checks:

```bash
./scripts/docker_image_policy.sh
./scripts/docker_smoke_test.sh
./scripts/docker_hardened_runtime_test.sh
./scripts/docker_external_dataset_test.sh
```

The Docker policy uses the compressed image archive for the size budget and also verifies metadata, dependency boundaries and the non-root runtime.

## Production Validation from Local

```bash
production_url="https://world-cup-2026-production.up.railway.app"
expected_sha="$(git rev-parse HEAD)"

WC26_EXPECTED_COMMIT_SHA="${expected_sha}" \
  ./scripts/cloud_observability_test.sh \
  "${production_url}"

WC26_EXPECTED_COMMIT_SHA="${expected_sha}" \
  ./scripts/cloud_smoke_test.sh \
  "${production_url}"
```

The observability script waits for Railway to serve the expected commit. The smoke script validates public API contracts and release identity.

## GitHub Actions

Three workflows protect the release pipeline:

| Workflow | Purpose |
|---|---|
| `Python Quality` | Shell syntax, Ruff, formatting, mypy and tests |
| `Docker Validation` | Build, policy, smoke and hardened runtime |
| `Production Verification` | Wait for quality gates, exact Railway SHA and production acceptance |

Docker and production runs upload diagnostic artifacts even on failure. Use them before trying to reproduce CI-only issues locally.

## Adding a Feature

1. Create a focused branch from the latest target branch.
2. Add or update tests for critical behaviour.
3. Keep business rules out of CLI, HTTP route and reporting layers.
4. Keep pandas objects inside the analytics layer.
5. Prefer package public APIs over legacy imports.
6. Run all local quality and Docker checks that apply.
7. Update documentation after implementation stabilizes.
8. Push and wait for the required GitHub Actions workflows.
9. Open a focused pull request.

Example:

```bash
git switch main
git pull --ff-only origin main
git switch -c feat/example-feature
```

## Legacy Compatibility

The compatibility wrapper remains at:

```text
src/transfer_intelligence/find_replacements.py
```

Do not remove its explicit re-exports during unrelated work. New application behaviour belongs under:

```text
src/wc26/
```

## Commit Style

Prefer focused imperative messages:

```text
feat: add transfer scoring mode
fix: preserve request ID header
refactor: separate catalog service
test: cover dataset integrity failure
ci: add production verification
docs: document deployment workflow
```


## Pull Request Checklist

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

git diff --check
```

Also confirm:

- shell scripts pass `bash -n`;
- public API and environment changes are documented;
- generated datasets and local artifacts are not committed accidentally;
- startup, readiness, request IDs and error contracts remain covered;
- Python Quality and Docker Validation pass;
- production verification passes for deployment changes.

## Deployment Documentation

Production runtime, Railway, dataset releases, rollback, observability and CI/CD are documented in:

```text
docs/DEPLOYMENT.md
```
