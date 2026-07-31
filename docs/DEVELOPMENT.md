# Development Guide

This guide explains how to set up, test and extend the WC26 Transfer
Intelligence Python core and FastAPI backend.

## Requirements

- Python 3.12 or newer
- Git
- Local processed datasets for real-data integration tests

## Local Setup

Clone the repository and enter the project directory:

```bash
git clone https://github.com/MelihSiskular/world-cup-2026.git
cd world-cup-2026
```

Create and activate a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Upgrade pip and install the project with development dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Confirm that the package and console command are available:

```bash
python -c "import wc26; print(wc26.__version__)"
wc26-transfer --help
```

## Running Transfer Intelligence

The recommended command is:

```bash
wc26-transfer \
  --player "Michael Olise" \
  --top-n 5
```

The legacy module command remains available for backward compatibility:

```bash
python -m src.transfer_intelligence.find_replacements \
  --player "Michael Olise" \
  --top-n 5
```

Both commands execute the same application entrypoint and analysis service.

## Python Core Architecture

The main application flow is:

```text
Command-line interface
        ↓
entrypoint.py
        ↓
TransferAnalysisRequest
        ↓
run_transfer_analysis()
        ↓
TransferAnalysisResult
        ├── console reporting adapter
        ├── CSV exporting adapter
        └── FastAPI JSON response adapter
```

The analysis service is intentionally side-effect free. It does not print to
the terminal, create directories or write CSV files.

`run_transfer_analysis()` accepts analytical inputs and returns a structured,
JSON-compatible `TransferAnalysisResult`.

Presentation and output concerns are handled by separate adapters:

- `print_transfer_report()` renders the console report.
- `export_transfer_csv()` writes recommendation files.
- `TransferAnalysisResult.to_dict()` produces a JSON-compatible response.

This separation allows the same application service to be reused by the CLI,
the FastAPI backend, scheduled pipelines, web clients and mobile applications.

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `config.py` | Paths, thresholds, mode configuration and scoring weights |
| `utils.py` | Shared formatting, normalization and conversion utilities |
| `datasets.py` | Loading and validating analytical datasets |
| `matching.py` | Resolving players and attaching similarity data |
| `models.py` | Backend-ready request and result contracts |
| `candidates.py` | Preparing the transfer candidate population |
| `scoring.py` | Transfer scoring rules and suitability calculations |
| `recommendations.py` | Mode filtering, ranking and result generation |
| `explanations.py` | Recommendation labels and data-driven explanations |
| `reporting.py` | Rendering structured results as console output |
| `entrypoint.py` | Mapping CLI input to the application request |
| `service.py` | Running the analysis workflow and returning a structured result |
| `exporting.py` | Generating CSV output from structured analysis results |
| `catalog.py` | Loading the complete runtime data catalog once |
| `player_search.py` | Searching and ranking player-name matches |
| `player_profile.py` | Returning stable player profiles by player ID |

The package-level public API is intentionally small:

```python
from wc26.analytics.transfer_intelligence import (
    TransferAnalysisRequest,
    run_transfer_analysis,
)
```

Internal modules may change as the project evolves. Code outside the package
should prefer the public API.

## Backend Development

The backend is implemented with FastAPI and exposed through an ASGI application
entrypoint.

### Package Structure

```text
src/wc26/api/
├── __init__.py
├── app.py
├── dependencies.py
├── errors.py
├── exception_handlers.py
├── main.py
├── runtime.py
├── settings.py
├── routes/
│   ├── __init__.py
│   ├── health.py
│   ├── players.py
│   └── transfer_intelligence.py
└── schemas/
    ├── __init__.py
    ├── errors.py
    ├── health.py
    ├── players.py
    └── transfer_intelligence.py
```

| Module | Responsibility |
|---|---|
| `api/app.py` | Creates and configures the FastAPI application |
| `api/main.py` | Builds the environment-configured deployable ASGI application |
| `api/settings.py` | Validates runtime settings and environment variables |
| `api/runtime.py` | Stores typed lifecycle state and operational metadata |
| `api/dependencies.py` | Supplies dataset paths and catalog-backed services |
| `api/routes/` | Defines HTTP endpoints grouped by domain |
| `api/schemas/` | Defines validated API request and response contracts |
| `api/exception_handlers.py` | Maps domain exceptions to safe HTTP responses |

### Run the API Locally

Production-style startup:

```bash
python -m uvicorn wc26.api.main:app \
  --host 127.0.0.1 \
  --port 8000
```

Development startup with automatic reload:

```bash
python -m uvicorn wc26.api.main:app \
  --reload \
  --host 127.0.0.1 \
  --port 8000
```

Interactive documentation:

```text
http://127.0.0.1:8000/docs
```

OpenAPI schema:

```text
http://127.0.0.1:8000/openapi.json
```

### Runtime Configuration

`create_production_app()` reads process environment variables through
`ApiSettings.from_environment()`.

| Variable | Default | Purpose |
|---|---|---|
| `WC26_ENVIRONMENT` | `development` | Runtime environment: `development`, `test` or `production` |
| `WC26_API_HOST` | `127.0.0.1` | Host value available to deployment tooling |
| `WC26_API_PORT` | `8000` | API port value available to deployment tooling |
| `WC26_API_TITLE` | `WC26 Transfer Intelligence API` | OpenAPI application title |
| `WC26_API_SUMMARY` | Project summary | OpenAPI application summary |
| `WC26_SERVICE_NAME` | `wc26-transfer-intelligence` | Service identifier returned by operational endpoints |
| `WC26_FEATURES_PATH` | Project default | Player feature dataset path |
| `WC26_SIMILARITY_PATH` | Project default | Statistical similarity dataset path |
| `WC26_HEATMAP_SIMILARITY_PATH` | Project default | Heatmap similarity dataset path |
| `WC26_HEATMAP_PROFILES_PATH` | Project default | Heatmap profile dataset path |
| `WC26_CORS_ORIGINS` | Empty | Comma-separated trusted HTTP or HTTPS origins |

Example:

```bash
export WC26_ENVIRONMENT=production
export WC26_API_HOST=0.0.0.0
export WC26_API_PORT=8000
export WC26_CORS_ORIGINS="https://example.com,https://admin.example.com"

python -m uvicorn wc26.api.main:app \
  --host "$WC26_API_HOST" \
  --port "$WC26_API_PORT"
```

Dataset paths may also be supplied explicitly to `create_app()` for tests or
direct Python usage. Explicit `dataset_paths` override the paths stored in
`ApiSettings`.

### CORS

CORS middleware is installed only when `WC26_CORS_ORIGINS` contains at least
one valid origin.

Configured origins are:

- restricted to HTTP or HTTPS;
- normalized by removing a trailing slash;
- deduplicated;
- rejected when they contain a path, query string or fragment.

The middleware allows credentials, methods and headers for trusted origins.
Responses to untrusted origins do not include
`Access-Control-Allow-Origin`.

### Runtime Catalog and Application State

The production application loads the transfer data catalog once during the
FastAPI lifespan startup phase.

```text
Process environment
        ↓
ApiSettings
        ↓
create_production_app()
        ↓
create_app()
        ↓
FastAPI lifespan startup
        ↓
load_transfer_data_catalog()
        ↓
ApiRuntimeState
        ↓
catalog-backed player search, profile and transfer analysis
```

The typed runtime state is stored at:

```python
application.state.api_runtime
```

`ApiRuntimeState` contains:

- validated API settings;
- configured dataset paths;
- application startup timestamp;
- catalog load timestamp;
- the cached `TransferDataCatalog`;
- calculated uptime;
- readiness state.

The production process fails during startup when a required catalog dataset
cannot be loaded or does not satisfy its data contract. This prevents a
partially initialized analytics service from accepting traffic.

Test applications created with `create_app()` may omit a catalog loader. In
that case, analytics dependencies preserve the path-based fallback behavior.

### Operational Endpoints

#### `GET /health`

Liveness is independent of the analytics catalog. A running process returns
`200 OK`.

Example response:

```json
{
  "status": "ok",
  "service": "wc26-transfer-intelligence",
  "version": "0.1.0",
  "environment": "production",
  "started_at": "2026-07-25T07:00:00Z",
  "uptime_seconds": 125.432
}
```

#### `GET /ready`

Readiness reports whether the runtime transfer catalog is available.

Ready response:

```json
{
  "status": "ready",
  "service": "wc26-transfer-intelligence",
  "version": "0.1.0",
  "environment": "production",
  "started_at": "2026-07-25T07:00:00Z",
  "uptime_seconds": 125.432,
  "catalog_loaded_at": "2026-07-25T07:00:02Z"
}
```

A process without a runtime catalog returns `503 Service Unavailable`:

```json
{
  "status": "not_ready",
  "service": "wc26-transfer-intelligence",
  "version": "0.1.0",
  "environment": "test",
  "started_at": "2026-07-25T07:00:00Z",
  "uptime_seconds": 1.125,
  "catalog_loaded_at": null
}
```

### API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Process liveness and runtime metadata |
| `GET` | `/ready` | Catalog readiness and runtime metadata |
| `GET` | `/api/v1/players/search` | Search players by name |
| `GET` | `/api/v1/players/{player_id}` | Retrieve a stable player profile |
| `POST` | `/api/v1/transfer-intelligence/analyze` | Run transfer replacement analysis |

### Player Search

Example:

```bash
curl --get \
  "http://127.0.0.1:8000/api/v1/players/search" \
  --data-urlencode "q=olise" \
  --data-urlencode "limit=10"
```

Search rules:

1. Normalize whitespace.
2. Apply case folding.
3. Remove common Unicode diacritics.
4. Match normalized player names.
5. Rank exact matches first.
6. Rank full-name prefixes second.
7. Rank token-prefix matches third.
8. Rank remaining partial matches last.
9. Remove duplicate player IDs.
10. Apply the requested result limit.

Current limits:

```text
Minimum query length: 2
Minimum result limit: 1
Maximum result limit: 25
Default API limit: 10
```

No-match searches return an empty player list rather than a not-found error.

### Player Profile

Player profiles use the stable numeric `player_id` identity.

```bash
curl \
  "http://127.0.0.1:8000/api/v1/players/978838"
```

The response includes the player's identity and recruitment profile fields
available in the feature dataset.

### Transfer Analysis

The request accepts exactly one transfer target:

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

Example request:

```bash
curl -X POST \
  "http://127.0.0.1:8000/api/v1/transfer-intelligence/analyze" \
  -H "Content-Type: application/json" \
  -d '{"player_id": 978838}'
```

The API delegates to the same structured analysis service used by the CLI. The
HTTP layer does not expose local dataset paths and does not contain scoring
business rules.

### Transfer Analysis Request Flow

```text
POST /api/v1/transfer-intelligence/analyze
                    ↓
TransferAnalysisPayload
                    ↓
FastAPI dependency resolution
                    ↓
TransferDatasetPaths
TransferAnalysisRunner
                    ↓
TransferAnalysisRequest
                    ↓
run_transfer_analysis_from_catalog()
                    ↓
TransferAnalysisResult
                    ↓
TransferAnalysisResponse
                    ↓
JSON response
```

### Shared Error Responses

Known domain exceptions are mapped centrally to safe HTTP responses.

| Analytics exception | HTTP status | API code |
|---|---:|---|
| `InvalidTransferAnalysisRequestError` | `400` | `invalid_transfer_analysis_request` |
| `InvalidPlayerProfileError` | `400` | `invalid_player_profile` |
| `InvalidPlayerSearchError` | `400` | `invalid_player_search` |
| `PlayerNotFoundError` | `404` | `player_not_found` |
| `AmbiguousPlayerError` | `409` | `ambiguous_player` |
| `DatasetNotFoundError` | `503` | `dataset_unavailable` |
| `InvalidDatasetError` | `503` | `invalid_dataset` |
| `TransferAnalysisExecutionError` | `500` | `analysis_failed` |
| `PlayerProfileExecutionError` | `500` | `player_profile_failed` |
| `PlayerSearchExecutionError` | `500` | `player_search_failed` |

Error envelope:

```json
{
  "error": {
    "code": "player_not_found",
    "message": "Player could not be resolved."
  }
}
```

Dataset-related responses must not expose local file-system paths or internal
implementation details.

### Dependency Overrides

API unit tests should replace expensive application services with controlled
test implementations.

```python
from wc26.api.dependencies import (
    get_transfer_analysis_runner,
)

application.dependency_overrides[
    get_transfer_analysis_runner
] = override_analysis_runner
```

Available dependency boundaries include:

```python
get_transfer_dataset_paths
get_player_search_runner
get_player_profile_runner
get_transfer_analysis_runner
```

This keeps route tests fast and deterministic while integration tests verify
the complete real-data path.

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

Run portable tests:

```bash
python -m pytest -m "not integration"
```

Run tests with branch coverage:

```bash
python -m pytest \
  -m "not integration" \
  --cov=wc26 \
  --cov-branch \
  --cov-report=term-missing
```

The current minimum coverage baseline is 65%.

## Integration Tests

Real-data integration tests require the processed World Cup datasets to exist
locally.

Run all real-data tests explicitly:

```bash
WC26_RUN_INTEGRATION=1 \
python -m pytest -m integration -v
```

Run the complete runtime-catalog API flow:

```bash
WC26_RUN_INTEGRATION=1 \
python -m pytest \
  tests/integration/api/test_runtime_catalog_api.py \
  -v
```

The runtime-catalog integration test verifies:

- each required dataset is loaded once during startup;
- player search uses the cached catalog;
- player profile retrieval uses the same catalog;
- transfer analysis uses the same catalog;
- repeated requests do not reload CSV files;
- readiness reports `ready`;
- catalog memory is released during shutdown.

Real-data tests are excluded from normal GitHub Actions runs because processed
datasets are not guaranteed to exist on the runner.

## Test Organization

```text
tests/
├── unit/
│   ├── api/
│   │   ├── test_app.py
│   │   ├── test_cors.py
│   │   ├── test_health.py
│   │   ├── test_main.py
│   │   ├── test_readiness.py
│   │   ├── test_runtime.py
│   │   ├── test_runtime_catalog_lifespan.py
│   │   └── test_settings.py
│   └── transfer_intelligence/
│       ├── test_candidates.py
│       ├── test_cli.py
│       ├── test_datasets.py
│       ├── test_entrypoint.py
│       ├── test_matching.py
│       ├── test_recommendations.py
│       ├── test_reporting.py
│       ├── test_scoring.py
│       └── test_service.py
└── integration/
    ├── api/
    │   └── test_runtime_catalog_api.py
    └── transfer_intelligence/
        └── test_cli_smoke.py
```

### Unit Tests

Unit tests verify individual modules and business rules using small,
deterministic inputs.

### Characterization Tests

Characterization tests preserve important behavior inherited from the original
transfer intelligence script. They allow internal refactoring without
unintentionally changing recommendation behavior.

### Integration Tests

Integration tests exercise complete workflows using real processed datasets.

## Adding a New Feature

When adding or changing application behavior:

1. Create a focused branch from the latest `main`.
2. Add or update tests before changing critical behavior.
3. Keep business rules out of CLI, route and reporting modules.
4. Keep pandas objects inside the analytics layer.
5. Prefer package public APIs over legacy imports.
6. Run all local quality checks.
7. Review the coverage result.
8. Open a Pull Request and wait for the Python Quality workflow.
9. Finalize documentation after the implementation stage is complete.

Example branch:

```bash
git switch main
git pull --ff-only origin main
git switch -c feat/example-feature
```

## Legacy Compatibility

The file:

```text
src/transfer_intelligence/find_replacements.py
```

is a compatibility wrapper for existing commands, imports and tests.

Do not remove its explicit re-exports as part of an unrelated refactor.
Removing them should be treated as an intentional breaking change.

New application behavior should be implemented under:

```text
src/wc26/
```

## Commit Style

Prefer focused commits with imperative messages:

```text
feat: add transfer intelligence console command
fix: handle missing heatmap profile
refactor: separate recommendation exporters
test: cover value recommendation filtering
docs: document backend runtime workflow
ci: add Python quality workflow
```

Avoid combining unrelated refactoring, feature and documentation changes in
one commit.

## Pull Request Checklist

Before opening a Pull Request:

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

Also verify:

- new behavior has tests;
- existing behavior remains compatible unless a breaking change is intended;
- public API and environment changes are documented;
- generated datasets and local output files are not committed accidentally;
- startup and readiness behavior are covered;
- the GitHub Actions Python Quality workflow passes.

## Deployment Preparation

Before deploying the API:

1. Set `WC26_ENVIRONMENT=production`.
2. Configure all four dataset paths.
3. Configure only trusted CORS origins.
4. Confirm `GET /health` returns `200`.
5. Confirm `GET /ready` returns `200` after startup.
6. Confirm `/docs` and `/openapi.json` match the intended exposure policy.
7. Run strict type checking and the full portable test suite.
8. Run real-data integration tests against deployment datasets.
9. Start Uvicorn through the target process manager or container runtime.

The current repository provides a deployment-ready ASGI application entrypoint.
Infrastructure packaging and hosting configuration belong to the deployment
stage.

## Deployment and Runtime Datasets

Production deployment, Docker hardening, runtime dataset manifests, integrity
validation, versioned bundles, atomic activation and rollback are documented
in:

```text
docs/DEPLOYMENT.md
```

Before changing deployment behavior:

1. Keep Docker and dataset changes in focused commits.
2. Preserve the non-root runtime.
3. Preserve build-time and startup integrity validation.
4. Keep externally mounted runtime datasets read-only.
5. Validate both embedded and external dataset modes.
6. Treat versioned bundle directories as immutable.
7. Run the Docker image policy, smoke and hardened runtime tests.
8. Update `docs/DEPLOYMENT.md` when commands or environment variables change.

The deployment guide is the source of truth for production runtime procedures.
