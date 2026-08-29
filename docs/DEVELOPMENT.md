# Development Guide

This guide covers local development for the WC26 Python analytics package, CLI, FastAPI backend and Next.js frontend.

## Requirements

- Python 3.12+
- Node.js 24 and npm
- Git
- Docker for container validation
- Processed runtime datasets for real-data integration tests

## Repository Setup

```bash
git clone https://github.com/MelihSiskular/world-cup-2026.git
cd world-cup-2026

python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

python -c "import wc26; print(wc26.__version__)"
wc26-transfer --help
```

## Run the Backend

```bash
python -m uvicorn \
  wc26.api.main:create_production_app \
  --factory \
  --reload \
  --host 127.0.0.1 \
  --port 8000
```

- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI: <http://127.0.0.1:8000/openapi.json>
- Readiness: <http://127.0.0.1:8000/ready>

The runtime catalog is validated and loaded once during application startup. A catalog failure prevents readiness.

## Run the Frontend

```bash
cd web
nvm use 24
npm ci
cp .env.example .env.local
npm run dev
```

`web/.env.local` must contain:

```env
WC26_API_BASE_URL=http://127.0.0.1:8000
```

The browser calls same-origin Next.js route handlers. Only the Next.js server reads the backend URL.

## Core Boundaries

```text
CLI or HTTP request
  → request model
  → validated runtime catalog
  → analytics service
  → result model
  → CLI, API or web presentation
```

Rules:

1. Keep scoring, ranking and evidence rules in `src/wc26/analytics/`.
2. Keep pandas objects inside the analytical layer.
3. Keep FastAPI routes and Next.js BFF handlers thin.
4. Generate frontend types from OpenAPI; do not duplicate response interfaces.
5. Represent missing evidence as nullable data, never a fabricated zero.
6. Use stable numeric player IDs at API and URL boundaries.

Key areas:

| Path | Responsibility |
|---|---|
| `src/wc26/analytics/transfer_intelligence/` | Analysis, comparison, role metrics and recommendations |
| `src/wc26/api/` | Runtime, routes, schemas and error mapping |
| `tests/` | Python unit and integration tests |
| `web/src/app/` | Pages and same-origin BFF routes |
| `web/src/components/` | Product UI components |
| `web/src/lib/api/` | Generated types and browser/server clients |
| `web/e2e/` | Playwright browser journeys |

## API Contract Workflow

When a FastAPI request or response schema changes:

```bash
cd web
npm run api:contract:refresh
npm run api:types:check
npm run typecheck
```

Commit these generated artifacts together:

```text
web/openapi/wc26.openapi.json
web/src/lib/api/generated/schema.d.ts
```

Never edit the generated declaration file manually.

## Backend Quality Gate

```bash
python -m ruff format --check src/wc26 tests
python -m ruff check src/wc26 tests
python -m mypy src/wc26
python -m pytest \
  -m "not integration" \
  --cov=wc26 \
  --cov-branch \
  --cov-report=term-missing
```

The enforced coverage baseline is 65%.

Real-data integration tests:

```bash
WC26_RUN_INTEGRATION=1 python -m pytest -m integration -v
```

## Frontend Quality Gate

Run from `web/`:

```bash
npm run env:check
npm run api:types:check
npm run lint
npm run typecheck
npm test
npm run build
npm audit --omit=dev
```

Focused Phase 8 browser matrix:

```bash
WC26_E2E_LOCAL_SERVER=1 npm run test:e2e -- \
  e2e/multi-player-comparison.spec.ts \
  --project=chromium \
  --project=webkit \
  --project=mobile-chromium \
  --project=mobile-webkit
```

The Playwright configuration manages the local API and Next.js servers. Ports `8000` and `3000` should be free before and after the run.

## Docker Validation

```bash
docker build --tag wc26-transfer-api:dev .
./scripts/docker_image_policy.sh
./scripts/docker_smoke_test.sh
./scripts/docker_hardened_runtime_test.sh
./scripts/docker_external_dataset_test.sh
```

## Feature Workflow

```bash
git switch main
git pull --ff-only origin main
git switch -c feat/example-feature
```

Before opening a pull request:

- add tests for the changed contract;
- run the relevant Python, web and browser gates;
- run `git diff --check`;
- update documentation only after behaviour stabilizes;
- confirm generated and temporary files are not accidentally staged.

Use focused imperative commits such as `feat:`, `fix:`, `test:`, `docs:` and `ci:`.

Deployment procedures are maintained in `docs/DEPLOYMENT.md` and `docs/WEB_DEPLOYMENT.md`.
