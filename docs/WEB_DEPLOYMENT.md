# Web Deployment Guide

This document is the source of truth for deploying and operating the WC26 Next.js application on Vercel.

## Production Topology

```text
Browser
  → Vercel Next.js application
  → same-origin BFF routes
  → server-only WC26_API_BASE_URL
  → Railway FastAPI service
```

The Railway URL is never required by browser code. Backend CORS does not need a Vercel origin for this request path.

## Environment

Required variable:

```text
WC26_API_BASE_URL
```

Local:

```env
WC26_API_BASE_URL=http://127.0.0.1:8000
```

Vercel Production:

```env
WC26_API_BASE_URL=https://world-cup-2026-production.up.railway.app
```

The variable is server-only and must not use `NEXT_PUBLIC_`. Preview and Production require HTTPS, no credentials, and no path, query or fragment.

## Vercel Configuration

| Setting | Value |
|---|---|
| Repository | `MelihSiskular/world-cup-2026` |
| Production branch | `main` |
| Framework | Next.js |
| Root directory | `web` |
| Install command | Vercel default (`npm ci`) |
| Build command | `npm run build` |
| Output directory | Next.js default |

Use a branch-specific Preview environment override when the frontend candidate must target an isolated Railway candidate. Do not repoint canonical Production for branch validation.

## Local Release Gate

```bash
cd web
npm run env:check
npm run api:types:check
npm run lint
npm run typecheck
npm test
npm run build
npm audit --omit=dev
```

Run browser validation with locally managed servers:

```bash
WC26_E2E_LOCAL_SERVER=1 npm run test:e2e
```

The release matrix covers desktop and mobile Chromium and WebKit.

## Deployment Flow

```text
Feature branch
  → Python, Docker, Web and Browser quality gates
  → Vercel Preview review
  → merge to main
  → Railway and Vercel production deployments
  → backend production verification
  → frontend smoke and browser acceptance
```

Environment changes affect only new Vercel deployments; redeploy after changing a value.

## Protected Preview Testing

If Vercel Deployment Protection is enabled, provide its automation bypass secret only through the environment:

```bash
export VERCEL_AUTOMATION_BYPASS_SECRET="<secret>"
WC26_E2E_BASE_URL="https://preview.example.vercel.app" npm run test:e2e
```

Never commit the secret.

## Production Acceptance

```bash
export WC26_WEB_URL="https://your-vercel-domain.vercel.app"

./scripts/web_production_smoke_test.sh "${WC26_WEB_URL}"
```

Acceptance verifies:

- landing, player discovery, profile, shortlist, methodology and status routes;
- health, readiness and deployment identity through the BFF;
- discovery filters and player search;
- transfer analysis and recommendation modes;
- canonical multi-player comparison requests;
- expected backend commit and runtime dataset identity;
- desktop and mobile Chromium/WebKit journeys.

Inspect backend identity through the frontend:

```bash
curl --fail --silent \
  "${WC26_WEB_URL}/api/status/deployment" \
  | python -m json.tool
```

## Security Headers

Production responses apply:

```text
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

```bash
curl --silent --show-error --head "${WC26_WEB_URL}/status"
```

## Release Verification

1. Vercel originates from the expected `main` commit.
2. `/api/status/ready` reports ready.
3. `/api/status/deployment` reports backend version `0.4.0` and the expected commit.
4. The dataset bundle matches `config/runtime_dataset_manifest.json`.
5. Player discovery, profile, shortlist and transfer analysis work.
6. One-target/multiple-candidate comparison loads and keeps radar/heatmap selection synchronized.
7. Role metrics show total and per-90 values without replacing missing data.
8. Production smoke and browser acceptance pass.

## Rollback

Frontend rollback:

1. Restore a previously healthy Vercel production deployment.
2. Re-run the frontend smoke test.
3. Confirm it still targets the intended Railway release.

Backend and dataset rollback remain independent and are documented in `docs/DEPLOYMENT.md`.

## Common Failures

| Symptom | Action |
|---|---|
| Missing `WC26_API_BASE_URL` | Add it to the correct Vercel environment and redeploy |
| HTTP backend rejected | Use HTTPS for Preview and Production |
| `upstream_unavailable` | Check Railway `/ready` and correlate the request ID |
| Older backend release shown | Wait for Railway health checks, then inspect `/deployment` |
| Preview tests blocked | Supply the automation bypass secret through the environment |
