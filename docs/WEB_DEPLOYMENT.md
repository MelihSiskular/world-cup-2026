# Web Deployment Guide

This guide is the source of truth for deploying, validating and operating the WC26 Transfer Intelligence web application.

## Production Architecture

```text
Browser
    ↓ same-origin requests
Vercel Next.js application
    ↓
Next.js BFF route handlers
    ↓ server-only WC26_API_BASE_URL
Railway FastAPI service
    ↓
Validated transfer-intelligence catalog
```

The browser never requires the Railway base URL.

Frontend requests use same-origin routes under:

```text
/api/players/*
/api/status/*
/api/transfer-intelligence/*
```

The Next.js server forwards those requests to the configured FastAPI service.

Because browser clients do not directly access Railway, the backend does not require a Vercel origin in `WC26_CORS_ORIGINS`.

## Runtime Environment

The web application requires:

```text
WC26_API_BASE_URL
```

Local development:

```env
WC26_API_BASE_URL=http://127.0.0.1:8000
```

Vercel Production:

```env
WC26_API_BASE_URL=https://world-cup-2026-production.up.railway.app
```

Release-validation Preview deployments should use a branch-specific override that points to the matching isolated Railway validation environment instead of changing canonical Production.

The variable must remain server-only and must not use the `NEXT_PUBLIC_` prefix.

The build runs:

```bash
npm run env:check
```

Validation requires:

- a configured URL;
- an HTTP or HTTPS protocol;
- no embedded credentials;
- no path, query string or fragment;
- HTTPS in CI, Vercel Preview and Vercel Production.

## Local Development

Start the production-style FastAPI application from the repository root:

```bash
source .venv/bin/activate

python -m uvicorn \
  wc26.api.main:create_production_app \
  --factory \
  --host 127.0.0.1 \
  --port 8000
```

In another terminal:

```bash
cd web
nvm use 24
npm ci
cp .env.example .env.local
npm run dev
```

Open:

```text
http://localhost:3000
```

## Local Web Quality Gate

Run from `web/`:

```bash
npm run env:check
npm run api:types:check
npm test
npm run lint
npm run typecheck
npm run build
npm audit --omit=dev
```

The Phase 5F.3 baseline includes Vitest and React Testing Library coverage for API errors, form and payload validation, player search, transfer results, player comparison, application errors and not-found recovery.

## GitHub Actions

### Web Quality

```text
.github/workflows/web-quality.yml
```

Runs on every branch push, pull request to `main` and manual dispatch.

It validates:

- Node.js 24;
- deterministic dependency installation with `npm ci`;
- frontend environment configuration;
- generated OpenAPI types;
- unit and component tests;
- ESLint;
- TypeScript;
- the production Next.js build;
- production dependency vulnerabilities.

### Browser Validation

```text
.github/workflows/browser-validation.yml
```

Runs the Playwright browser suite across desktop and mobile Chromium and WebKit. This workflow validates a built frontend independently from the deployed Vercel Preview release-acceptance step.

### Production Verification

```text
.github/workflows/production-verification.yml
```

The Railway production verification workflow waits for:

```text
Python Quality
Docker Validation
Web Quality
```

before validating the deployed FastAPI application.

## Vercel Project Configuration

Create one Vercel project for the web application.

| Setting | Value |
|---|---|
| Git repository | `MelihSiskular/world-cup-2026` |
| Production branch | `main` |
| Framework preset | Next.js |
| Root Directory | `web` |
| Package manager | npm |
| Install command | Vercel default |
| Build command | `npm run build` |
| Output directory | Next.js default |

Do not configure a second frontend backend URL through a `NEXT_PUBLIC_*` variable.

## Vercel Environment Variables

Canonical Production uses the canonical Railway production service:

```text
Environment: Production
Name:        WC26_API_BASE_URL
Value:       https://world-cup-2026-production.up.railway.app
```

For isolated release validation, create a branch-specific Preview override so the candidate frontend talks to the matching Railway candidate without changing Production. The Phase 6 validation setup is:

```text
Environment: Preview
Branch:      test/phase-6-production-validation
Name:        WC26_API_BASE_URL
Value:       https://world-cup-2026-phase-6-validation.up.railway.app
```

Branch-specific Preview values override the shared Preview value for that branch. Environment-variable changes affect only new deployments, so redeploy the Preview after changing a value.

## Deployment Flow

```text
Feature branch
    ↓
Python Quality
Docker Validation
Web Quality
Browser Validation
    ↓
Vercel preview deployment
    ↓
Pull request review
    ↓
Merge to main
    ↓
Railway backend deployment
Vercel frontend deployment
    ↓
Production verification
    ↓
Frontend production smoke test
```

Vercel Preview deployments should be used to inspect branch changes before merging.

The production deployment must originate from `main`.

### Protected Preview Browser Validation

When Vercel Deployment Protection is enabled, deployed Playwright tests use an automation bypass secret through the optional `VERCEL_AUTOMATION_BYPASS_SECRET` environment variable. The secret value must never be committed.

```bash
read -s "VERCEL_AUTOMATION_BYPASS_SECRET?Vercel bypass secret: "
echo
export VERCEL_AUTOMATION_BYPASS_SECRET

WC26_E2E_BASE_URL="https://your-preview-domain.vercel.app" \
  npm run test:e2e
```

The Playwright configuration sends the protection-bypass header only when the secret is present. Without the variable, local and public-production browser validation behaves normally.

## Production Acceptance

Set the deployed frontend URL:

```bash
export WC26_WEB_URL="https://your-vercel-domain.vercel.app"
```

Run:

```bash
./scripts/web_production_smoke_test.sh \
  "${WC26_WEB_URL}"
```

The smoke test verifies:

- landing page availability;
- player-search page availability;
- methodology page availability;
- status page availability;
- FastAPI readiness through the Next.js BFF;
- health and deployment identity;
- player search;
- player profile;
- transfer analysis;
- all four recommendation modes.

Inspect the backend identity through the frontend:

```bash
curl \
  --fail \
  --silent \
  --show-error \
  "${WC26_WEB_URL}/api/status/deployment" \
  | python -m json.tool
```

Compare the deployed dataset bundle with the committed manifest:

```bash
python - <<'PY'
import json
from pathlib import Path

manifest = json.loads(
    Path(
        "config/runtime_dataset_manifest.json"
    ).read_text(
        encoding="utf-8",
    )
)

print(
    manifest["bundle_sha256"]
)
PY
```

The backend response and committed manifest must report the same bundle SHA-256.

## Production Security Headers

The Next.js application applies:

```text
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

Check the deployed response:

```bash
curl \
  --silent \
  --show-error \
  --head \
  "${WC26_WEB_URL}/status"
```

## Release Verification

After deployment, verify:

1. The Vercel deployment originates from the expected `main` commit.
2. `/api/status/ready` reports `ready`.
3. `/api/status/deployment` reports the expected Railway commit.
4. The dataset bundle matches `config/runtime_dataset_manifest.json`.
5. Player search returns Michael Olise.
6. Player profile `978838` opens.
7. Transfer analysis completes.
8. Recommendation and comparison pages work.
9. `/methodology` shows the active dataset identity.
10. The production smoke script passes.
11. The deployed Playwright journey passes on Chromium and WebKit.
12. The deployed Playwright journey passes on mobile Chromium and mobile WebKit.

## Frontend Rollback

To roll back the frontend:

1. Open the Vercel project.
2. Open its deployment history.
3. Select a previously healthy production deployment.
4. Promote or restore that deployment.
5. Run the production frontend smoke test again.

A frontend rollback does not automatically roll back Railway or the runtime dataset bundle.

## Backend Rollback

The Railway application and dataset release procedures remain documented in:

```text
docs/DEPLOYMENT.md
```

Always verify all three release identities after recovery:

```text
Vercel frontend deployment
Railway backend commit
Runtime dataset bundle SHA-256
```

## Failure Recovery

### Build reports that WC26_API_BASE_URL is missing

Add the variable to the relevant Vercel environment and redeploy.

### Build rejects an HTTP URL

Preview and Production require an HTTPS backend origin.

### BFF routes return upstream_unavailable

Check Railway readiness:

```bash
curl \
  --fail \
  --silent \
  https://world-cup-2026-production.up.railway.app/ready \
  | python -m json.tool
```

Then inspect the request ID returned by the frontend error response.

### Frontend displays an older backend release

Railway may still be building or completing its health check. Inspect:

```bash
curl \
  --fail \
  --silent \
  https://world-cup-2026-production.up.railway.app/deployment \
  | python -m json.tool
```

Wait until the reported commit and dataset bundle match the intended release.
