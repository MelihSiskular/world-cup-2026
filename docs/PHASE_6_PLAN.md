# Phase 6 — Product Validation, Reliability and Analytical Explainability

## Status

- Phase: 6
- Status: In progress
- Starting release: Phase 5 public web MVP
- Starting commit: `dbb94a05707b884eb145b839a4bcde5aecd5ff12`
- Target release: `v0.2.0`

## 1. Purpose

Phase 6 strengthens the production WC26 Transfer Intelligence product after the
completion of the public web MVP.

The phase focuses on four outcomes:

1. Validate the complete user journey in real browsers.
2. Harden reliability, responsive behaviour and edge-case handling.
3. Expand player intelligence and analytical explainability.
4. Release and verify the improved product in production.

Phase 6 does not introduce a new application architecture. The existing
FastAPI backend remains the analytical source of truth and the Next.js
application remains the product and interaction layer.

---

## 2. Phase 6A — Production Validation

### Goal

Validate the complete WC26 user journey through automated browser testing in
addition to the existing API and shell-based production smoke tests.

### Scope

- Introduce Playwright end-to-end testing.
- Validate the primary user journey:
  - open the application;
  - search for a player;
  - open the player profile;
  - configure a transfer analysis;
  - submit the analysis;
  - inspect recommendation modes;
  - open a target-versus-candidate comparison.
- Validate desktop and mobile viewports.
- Validate Chromium and WebKit.
- Capture screenshots, traces and diagnostics for failed E2E tests.
- Integrate stable E2E validation into GitHub Actions.
- Preserve the existing frontend unit/component tests and production smoke tests.

### Acceptance criteria

- Playwright is configured under the web application.
- The complete primary user journey has an automated E2E test.
- Chromium validation passes.
- WebKit validation passes.
- Mobile viewport validation passes.
- Failed CI runs provide useful browser diagnostics.
- Existing frontend quality checks continue to pass.
- Existing production smoke validation continues to pass.

---

## 3. Phase 6B — Reliability and UX Hardening

### Goal

Make the existing product robust when production data or runtime conditions are
incomplete, unusual or temporarily unavailable.

### Scope

Validate and improve behaviour for:

- low-minute players;
- players with no tournament appearances;
- missing market values;
- missing roles or archetypes;
- missing heatmap data;
- recommendation modes with no candidates;
- API timeouts and service failures;
- unavailable datasets;
- long player names;
- loading states;
- empty states;
- retry behaviour;
- mobile navigation;
- mobile recommendation layouts;
- mobile player comparison layouts;
- safe request-ID diagnostics.

### Acceptance criteria

- Critical data-availability edge cases have deterministic UI states.
- Service failures do not expose internal implementation details.
- Important actions remain usable on mobile layouts.
- Loading, empty, error and retry states are covered by tests.
- Existing production behaviour remains backward compatible.

---

## 4. Phase 6C — Analytical Visualization and Player Intelligence

Phase 6C adds analytical depth without moving analytical business logic into
the frontend.

### 6C.1 — Enriched Player Profile

Use `player_tournament_full_summary_enriched.csv` to transform the player page
into a richer tournament scouting profile.

Planned capabilities:

- tournament summary cards;
- detailed tournament statistics;
- position-specific metric groups;
- per-90 performance metrics;
- same-position percentile context;
- strengths;
- watch-outs;
- sample-size and minutes context;
- improved role and archetype presentation;
- player identity component prepared for future player imagery.

Analytical calculations and interpretations remain backend-owned.

### 6C.2 — Recommendation Explainability

Improve the transfer recommendation experience with visual explanations of
the signals contributing to candidate ranking.

Planned signals include:

- statistical similarity;
- role fit;
- spatial similarity;
- heatmap similarity;
- player quality;
- data reliability;
- market advantage;
- age suitability;
- weighted recommendation contributions.

The interface must clearly distinguish recommendation scores from probabilities
of transfer success.

### 6C.3 — Role and Spatial Visuals

Introduce visual representations of tactical and positional identity.

Planned capabilities:

- role compatibility panel;
- lateral profile;
- vertical profile;
- mobility profile;
- mini-pitch spatial profile;
- target and candidate positional occupation;
- positional-overlap explanations.

### 6C.4 — Heatmap Comparison

Introduce target-versus-candidate heatmap visualization.

Planned capabilities:

- target heatmap;
- candidate heatmap;
- side-by-side comparison;
- heatmap similarity context;
- shared and differing occupied areas;
- safe fallback when heatmap data is unavailable.

### 6C.5 — Radar Profiles

Introduce position-aware performance radar visualizations after the metric
registry and percentile model are established.

Planned capabilities:

- player profile radar;
- target-versus-candidate radar;
- position-specific metric selection;
- creation profile;
- progression profile;
- possession profile;
- defensive contribution profile;
- scoring or goalkeeping profiles where appropriate.

Radar charts must use meaningful position-specific metrics rather than a
single universal metric set.

---

## 5. Phase 6D — Release and Production Acceptance

### Goal

Ship the completed Phase 6 product as a verified production release.

### Scope

- run backend tests;
- run frontend tests;
- validate the OpenAPI contract;
- run Playwright E2E tests;
- run Docker validation;
- run Web Quality;
- validate the runtime dataset manifest;
- verify the new dataset bundle identity;
- deploy and verify Railway;
- deploy and verify Vercel;
- run frontend-to-backend production smoke validation;
- update documentation;
- prepare the `v0.2.0` release.

### Acceptance criteria

- All required CI workflows pass.
- Production serves the expected application commit.
- Production serves the expected dataset bundle.
- Vercel BFF reaches the expected Railway release.
- The complete browser journey passes.
- Production smoke testing passes.
- Phase 6 documentation reflects the shipped system.

---

## 6. Delivery Order

Phase 6 will be implemented in the following order:

```text
6A — Production Validation
 ↓
6B — Reliability and UX Hardening
 ↓
6C.1 — Enriched Player Profile
 ↓
6C.2 — Recommendation Explainability
 ↓
6C.3 — Role and Spatial Visuals
 ↓
6C.4 — Heatmap Comparison
 ↓
6C.5 — Radar Profiles
 ↓
6D — Release and Production Acceptance
```

---

## 7. Out Of Scope

The following are intentionally excluded from Phase 6:
- product analytics and behavioural tracking;
- authentication;
- user registration;
- PostgreSQL application persistence;
- saved shortlists;
- saved analyses;
- scout notes;
- team workspaces;
- iOS application development;
- Airflow;
- dbt;
- AWS migration;
- Terraform;
- multi-competition data;
- predictive machine-learning models;
- automatic production data ingestion.

These capabilities belong to later project phases.

---

## 8. Architectural Principles

### Backend remains the analytical source of truth
- FastAPI and the Python analytics layer own:
- dataset loading;
- metric calculations;
- percentile calculations;
- player intelligence;
- recommendation scoring;
- candidate ranking;
- analytical explanations.

### Frontend remains the product layer
- Next.js owns:
- navigation;
- interaction;
- presentation;
- charts and visual representation;
- responsive behaviour;
- loading and empty states;
- safe error presentation;
- accessibility.

### Explainability before decoration
Every visualization introduced in Phase 6 must answer a meaningful analytical
question.
Charts must not be added solely for visual complexity.

### Position-aware analysis
Player performance must be interpreted relative to meaningful positional
contexts rather than through one universal metric profile.

### Production identity remains verifiable
Application commit identity and runtime dataset bundle identity must remain
independently verifiable throughout Phase 6.