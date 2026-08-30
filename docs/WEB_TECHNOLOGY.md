# WC26 Web Technology and Architecture

## Status

- Product version: `0.5.0`
- Architecture: implemented through Phase 8
- Repository model: Python backend and Next.js frontend in one repository

## Technology Decisions

| Area | Decision |
|---|---|
| Framework | Next.js App Router |
| Language | TypeScript |
| UI | React and Tailwind CSS |
| Runtime | Node.js 24 |
| Package manager | npm |
| Remote state | TanStack Query |
| Forms | React Hook Form and Zod |
| API types | Generated from FastAPI OpenAPI |
| Component tests | Vitest and React Testing Library |
| Browser tests | Playwright |
| Frontend hosting | Vercel |
| Backend hosting | Railway |

These tools have explicit product responsibilities. New dependencies should be added only when a concrete requirement justifies them.

## Repository Boundary

```text
Repository root
  → Python analytics, FastAPI, datasets and deployment tooling

web/
  → Next.js pages, BFF routes, components and browser tests
```

Backend and frontend remain together because they share one product roadmap and checked-in API contract.

## Request Architecture

```text
Browser
  → same-origin Next.js BFF route
  → server-only WC26_API_BASE_URL
  → FastAPI route
  → analytical service
  → validated runtime catalog
```

Next.js route handlers may enforce timeouts, preserve request IDs and normalize upstream failures. They must not rank candidates, read analytical datasets or alter backend meaning.

## Rendering

Server Components are preferred for route shells, metadata and non-interactive content. Client Components are used only for search, filters, forms, shortlist persistence, query-driven data and interactive comparison controls.

A component should not become client-side unless it needs browser APIs, local interaction, effects or a client-only library.

## State Ownership

| State | Owner |
|---|---|
| Shareable discovery and comparison selection | URL parameters |
| API data and retries | TanStack Query |
| Transfer form | React Hook Form |
| Client validation | Zod |
| Shortlists | Browser storage through the shortlist provider |
| Small component interaction | Local React state |
| Analytical conclusions | FastAPI response |

A general-purpose global state library remains unnecessary.

## API Contract

```text
FastAPI schemas
  → web/openapi/wc26.openapi.json
  → web/src/lib/api/generated/schema.d.ts
  → stable aliases in web/src/lib/api/types.ts
```

Refresh after a backend contract change:

```bash
cd web
npm run api:contract:refresh
npm run api:types:check
npm run typecheck
```

Generated declarations are never edited manually.

Key API modules:

```text
web/src/lib/api/
├── browser-players.ts
├── browser-status.ts
├── browser-transfer-intelligence.ts
├── config.ts
├── errors.ts
├── generated/schema.d.ts
├── route-handler.ts
├── server-client.ts
└── types.ts
```

## Frontend Organization

```text
web/src/
├── app/
│   ├── api/
│   ├── analysis/
│   ├── compare/
│   ├── methodology/
│   ├── players/
│   ├── shortlists/
│   └── status/
├── components/
│   ├── feedback/
│   ├── layout/
│   ├── players/
│   ├── providers/
│   ├── shortlists/
│   └── transfer-intelligence/
├── hooks/
├── lib/
│   ├── api/
│   ├── query/
│   ├── shortlists/
│   └── transfer-intelligence/
└── test/
```

## Visualization

Radar and heatmap views use product-owned components rather than a general dashboard charting dependency. This keeps football-specific semantics, responsive behaviour, accessibility labels and evidence boundaries under project control.

The frontend visualizes backend-owned values; it does not derive new analytical scores.

## Environment

The only required frontend server variable is:

```env
WC26_API_BASE_URL=http://127.0.0.1:8000
```

It is server-only and must not use a `NEXT_PUBLIC_` prefix. Production and preview deployments require HTTPS backend URLs.

## Testing Strategy

- Vitest covers parsers, storage models, API clients and helpers.
- React Testing Library covers component behaviour, loading, missing evidence, retry and accessibility contracts.
- Playwright covers complete journeys on Chromium, WebKit, mobile Chromium and mobile WebKit.
- Production builds verify Server/Client boundaries and dynamic routes.
- OpenAPI checks prevent generated contract drift.

Phase 8 browser coverage includes advanced discovery, persistent shortlists, canonical multi-player URLs, synchronized candidate controls, responsive table containment, keyboard selection and WCAG validation.

## Architectural Principles

1. FastAPI is the analytical source of truth.
2. Next.js is the product and interaction layer.
3. OpenAPI is the integration contract.
4. Missing evidence remains nullable.
5. Shareable state belongs in the URL.
6. Browser-only persistence stays explicit and local.
7. Complexity must be earned by a real requirement.

Authentication, an application database, collaborative workspaces and frontend-owned analytical models remain out of scope for version `0.5.0`.
