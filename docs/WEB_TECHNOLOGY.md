# WC26 Web Technology and Repository Architecture

## Status

- **Phase:** 5A.2
- **Decision:** Accepted
- **Scope:** Frontend technology, repository structure, API integration, testing and deployment strategy
- **Related document:** `docs/WEB_PRODUCT.md`

## 1. Purpose

Phase 5 introduces a public web product on top of the existing WC26 production API.

The frontend must allow a user to:

1. Search for a player.
2. Open the player's profile.
3. configure transfer-analysis criteria.
4. Run the transfer analysis.
5. Review recommendation modes.
6. Compare the target player with a candidate.

The frontend is a presentation and interaction layer. It must not duplicate the transfer intelligence business logic already implemented in the Python service and FastAPI backend.

## 2. Final Technology Decisions

| Area | Decision |
|---|---|
| Frontend framework | Next.js with App Router |
| Language | TypeScript |
| Rendering model | Server Components and Client Components |
| Styling | Tailwind CSS with project-owned UI components |
| Package manager | npm |
| Node runtime | Node.js 24 |
| Remote server state | TanStack Query |
| Form management | React Hook Form |
| Client-side validation | Zod |
| API contract types | Generated from the FastAPI OpenAPI schema |
| Unit and component tests | Vitest and React Testing Library |
| End-to-end tests | Playwright |
| Frontend deployment | Vercel |
| Backend deployment | Railway |
| Repository strategy | Existing repository with a new `web/` directory |
| Global state library | Not required for the Phase 5 MVP |
| Visualization library | Deferred until Phase 5E.2 |

## 3. Framework Decision

The frontend will use **Next.js App Router**.

The product includes:

- a public landing page;
- player search;
- dynamic player profiles;
- transfer-analysis forms;
- recommendation result pages;
- player comparison pages;
- route metadata;
- frontend-to-backend integration.

Next.js provides a single structure for these requirements through file-based routing, layouts, Server Components, Client Components and route handlers.

The project will use only the framework capabilities that directly support the product. It will not introduce unnecessary server-side business logic into the frontend.

## 4. Rendering Strategy

The application will use both Server Components and Client Components.

### Server Component responsibilities

Server Components are preferred for:

- the landing page;
- initial player profile loading;
- static product explanations;
- metadata generation;
- API status information;
- sections that do not require browser interaction.

### Client Component responsibilities

Client Components are required for:

- live player search;
- search debouncing;
- filter and form controls;
- transfer-analysis submission;
- recommendation tabs;
- interactive comparison controls;
- responsive interactive elements.

A component must not be marked as a Client Component unless browser state, effects, event handlers or client-only libraries are required.

## 5. Backend Integration Model

The FastAPI service remains the source of truth for all analytics and transfer intelligence behavior.

The preferred request flow is:

```text
Browser
    ↓
Next.js page or route handler
    ↓
Railway FastAPI service
    ↓
Transfer Intelligence service
    ↓
Validated runtime catalog
```

The frontend may use thin route handlers as a backend-for-frontend layer.

These route handlers may:

- apply request timeouts;
- forward requests to the configured FastAPI base URL;
- preserve request IDs;
- normalize network failures into safe frontend responses;
- prevent the backend base URL from being repeated throughout the client code.

They must not:

- calculate transfer scores;
- rank candidates;
- read analytical CSV files;
- reproduce backend validation rules;
- alter recommendation meaning;
- expose internal dataset paths.

## 6. API Contract Strategy

The backend exposes an OpenAPI schema through:

```text
/openapi.json
```

Frontend request and response types will be generated from this schema.

Planned structure:

```text
web/src/lib/api/
├── client.ts
├── server-client.ts
├── errors.ts
├── request-id.ts
└── schema.d.ts
```

Responsibilities:

- `schema.d.ts`: generated API types;
- `client.ts`: browser-safe API client;
- `server-client.ts`: server-side FastAPI client;
- `errors.ts`: frontend-safe error mapping;
- `request-id.ts`: request ID extraction and propagation.

Generated schema files must not be edited manually.

When the FastAPI contract changes, the TypeScript schema must be regenerated and frontend checks must run again.

## 7. State Management Strategy

The application will avoid a global state library during the Phase 5 MVP.

State ownership will be divided as follows:

| State type | Owner |
|---|---|
| Backend and remote data | TanStack Query |
| Route identity and shareable filters | URL parameters |
| Transfer-analysis form values | React Hook Form |
| Client-side form validation | Zod |
| Local interaction state | React `useState` |
| Server-rendered initial data | Next.js Server Components |

Redux, Zustand, MobX and similar tools are intentionally excluded until a real cross-page state requirement appears.

## 8. TanStack Query Usage

TanStack Query will manage interactive server state where client-side fetching is useful.

Initial use cases:

- live player search;
- player profile refresh;
- API readiness checks;
- transfer-analysis submission;
- recommendation result reuse.

Project-specific query behavior must be configured deliberately.

The implementation must define:

- retry behavior;
- stale time;
- cache lifetime;
- request cancellation;
- query keys;
- error mapping;
- loading behavior.

Default library behavior must not be accepted without review.

## 9. Form and Validation Strategy

Transfer-analysis forms will use:

```text
React Hook Form
+
Zod
```

The frontend will validate obvious input problems such as:

- negative minutes;
- invalid confidence percentages;
- invalid market values;
- recommendation counts outside the interface limits;
- missing required identifiers.

Frontend validation improves the user experience, but FastAPI remains the authoritative validator.

Backend validation errors must be presented as understandable field or form messages rather than raw JSON responses.

## 10. Styling and Component Strategy

The project will use Tailwind CSS with a small, project-owned component system.

Planned shared components:

```text
web/src/components/ui/
├── alert.tsx
├── badge.tsx
├── button.tsx
├── card.tsx
├── input.tsx
├── select.tsx
├── skeleton.tsx
└── tabs.tsx
```

The design system will define:

- color tokens;
- typography;
- spacing;
- borders;
- radius;
- shadows;
- focus states;
- success, warning and error states;
- football analytics visual language.

The product must not look like an unmodified dashboard template.

External component libraries may be used selectively for accessibility-heavy interactions such as:

- dialogs;
- tooltips;
- complex selects;
- dropdown menus;
- accessible tabs.

They must not determine the complete visual identity of the application.

## 11. Repository Decision

The frontend will be developed inside the existing repository.

Planned root structure:

```text
world-cup-2026/
├── .github/
│   └── workflows/
├── config/
├── data/
├── docs/
├── scripts/
├── src/
│   └── wc26/
├── tests/
├── web/
│   ├── public/
│   ├── src/
│   ├── package.json
│   ├── package-lock.json
│   └── next.config.ts
├── Dockerfile
├── pyproject.toml
└── README.md
```

Repository boundaries:

```text
Repository root
→ Python analytics, FastAPI backend and deployment tooling

web/
→ Next.js frontend
```

Python commands will run from the repository root.

Frontend commands will run from `web/`.

A separate repository is not justified during Phase 5 because the backend and frontend belong to the same product and share the same API contract and release roadmap.

## 12. Initial Frontend Structure

The first expected application structure is:

```text
web/
├── public/
├── src/
│   ├── app/
│   │   ├── api/
│   │   ├── analysis/
│   │   ├── compare/
│   │   ├── players/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── analysis/
│   │   ├── comparison/
│   │   ├── layout/
│   │   ├── players/
│   │   └── ui/
│   ├── lib/
│   │   ├── api/
│   │   ├── formatters/
│   │   ├── query/
│   │   └── validation/
│   └── types/
├── tests/
├── .env.example
├── .nvmrc
├── next.config.ts
├── package.json
├── package-lock.json
└── tsconfig.json
```

The exact file list may evolve, but feature ownership and API boundaries should remain clear.

## 13. Environment Configuration

The frontend server will use:

```text
WC26_API_BASE_URL
```

Local example:

```env
WC26_API_BASE_URL=http://127.0.0.1:8000
```

Production example:

```env
WC26_API_BASE_URL=https://world-cup-2026-production.up.railway.app
```

The variable must not use the `NEXT_PUBLIC_` prefix because the backend base URL will be consumed by the Next.js server and route-handler layer.

Secrets must never be committed.

The repository will include only a safe `web/.env.example`.

## 14. Testing Strategy

### Unit and component tests

Vitest and React Testing Library will cover:

- formatting utilities;
- API error mapping;
- validation schemas;
- loading states;
- empty states;
- recommendation cards;
- player profile sections;
- transfer-analysis form behavior.

### End-to-end tests

Playwright will validate the primary product journey:

```text
Open the website
    ↓
Search for a player
    ↓
Open the player profile
    ↓
Configure and run analysis
    ↓
View recommendations
    ↓
Compare a candidate
```

Browser coverage should include Chromium and WebKit for the production-critical path.

### Contract confidence

Frontend validation will also include:

- OpenAPI type generation;
- TypeScript checks;
- production build;
- frontend-to-backend smoke tests.

## 15. Deployment Strategy

The production topology will be:

```text
Next.js frontend
→ Vercel

FastAPI backend
→ Railway
```

Vercel will use:

```text
Root Directory: web
```

Expected deployment flow:

```text
Feature branch
    ↓
Frontend quality checks
    ↓
Vercel preview deployment
    ↓
Pull Request review
    ↓
Merge to main
    ↓
Vercel production deployment
    ↓
Frontend-to-backend production validation
```

The Railway backend remains independently deployable.

The frontend must not require a backend rebuild for visual-only changes.

## 16. Visualization Decision

A charting library is intentionally not selected during Phase 5A.2.

The decision is deferred until Phase 5E.2 because it depends on:

- the final comparison response contract;
- the available radar metrics;
- the heatmap representation;
- whether existing generated images remain useful;
- accessibility requirements;
- mobile rendering requirements.

Candidate approaches may include:

- custom SVG;
- a React charting library;
- D3-based components;
- backend-generated analytical images.

No visualization dependency should be installed before the data requirement is defined.

## 17. Explicit Non-Decisions

The following are not part of the Phase 5A.2 foundation:

- authentication;
- application database;
- saved analyses;
- saved shortlists;
- admin tools;
- payment systems;
- new machine-learning models;
- automatic dataset pipelines;
- global state libraries;
- a fixed charting library;
- frontend ownership of analytical rules.

## 18. Architectural Principles

### Backend as source of truth

FastAPI owns:

- player resolution;
- data loading;
- validation;
- transfer scoring;
- candidate ranking;
- recommendation explanations.

### Frontend as product layer

Next.js owns:

- navigation;
- presentation;
- interaction;
- forms;
- loading states;
- empty states;
- safe error messages;
- responsive layouts;
- accessibility.

### Contract-first integration

The OpenAPI contract connects both systems.

### Complexity must be earned

New libraries and state layers will be introduced only when an identified product requirement justifies them.

## 19. Phase 5A.2 Acceptance Criteria

- [x] Frontend framework selected.
- [x] TypeScript selected.
- [x] Rendering strategy defined.
- [x] Styling strategy defined.
- [x] API integration boundary defined.
- [x] OpenAPI type strategy defined.
- [x] Repository structure selected.
- [x] Runtime and package manager selected.
- [x] Server-state strategy selected.
- [x] Form strategy selected.
- [x] Testing tools selected.
- [x] Deployment platform selected.
- [x] Global state intentionally excluded.
- [x] Visualization decision deferred to the correct phase.

## 20. Final Decision Summary

```text
Next.js App Router
TypeScript
Server and Client Components
Tailwind CSS
Thin Next.js route-handler layer
TanStack Query
React Hook Form and Zod
OpenAPI-generated TypeScript contracts
Vitest and React Testing Library
Playwright
Node.js 24 and npm
Existing repository under /web
Vercel frontend deployment
Railway backend deployment
```

This architecture is accepted as the technical foundation for the WC26 Phase 5 web product.
