# WC26 Transfer Intelligence Web Product

## 1. Product Goal

The goal of Phase 5 is to transform the existing production API into a
public-facing football scouting and transfer intelligence web application.

The first product version must allow a user to:

1. Open the public web application.
2. Search for a football player by name.
3. View the selected player's profile.
4. Configure transfer-analysis criteria.
5. Run a transfer replacement analysis.
6. Explore recommendations across the available analysis modes.
7. Compare the target player with a recommended candidate.

The web application must use the deployed WC26 production API as its source of
truth. It must not read CSV files directly or reimplement transfer-analysis
business rules in the frontend.

## 2. Target User

The first version is designed for users interested in football scouting,
recruitment and player analysis.

Example users include:

- football analytics enthusiasts;
- recruitment analysts;
- scouts;
- data analysts;
- portfolio reviewers;
- users exploring player alternatives.

The Phase 5 MVP does not require user registration or organization accounts.

## 3. Core User Journey

```text
Landing page
    ↓
Player search
    ↓
Player profile
    ↓
Transfer analysis form
    ↓
Recommendation results
    ↓
Player comparison
```

A complete user session should be possible without authentication.

## 4. Product Routes

### `/`

Purpose:

- Introduce the product.
- Explain the Transfer Intelligence workflow.
- Provide a clear action to start searching for a player.
- Surface selected analytical capabilities without overwhelming the user.

Primary action:

```text
Search Players
```

The landing page must not contain the complete technical documentation of the
project.

### `/players`

Purpose:

- Search players by name.
- Display ranked search results.
- Allow the user to open a player profile.

Backend endpoint:

```text
GET /api/v1/players/search
```

Required states:

- initial state;
- query too short;
- loading;
- results found;
- no results;
- request failed.

### `/players/{player_id}`

Purpose:

- Display the selected player's recruitment profile.
- Provide access to transfer analysis.

Backend endpoint:

```text
GET /api/v1/players/{player_id}
```

The page should display available fields such as:

- player name;
- national team;
- position;
- age;
- tournament minutes;
- tournament rating;
- market value;
- archetype;
- discovered role;
- spatial profile;
- role confidence.

The exact field mapping must follow the production API response contract.

Required states:

- loading;
- profile loaded;
- optional field unavailable;
- player not found;
- request failed.

Primary action:

```text
Find Transfer Alternatives
```

### `/analysis/{player_id}`

Purpose:

- Configure the transfer-analysis request for the selected player.
- Explain the available recruitment filters.
- Submit the request to the backend.

Backend endpoint:

```text
POST /api/v1/transfer-intelligence/analyze
```

Initial configurable criteria:

- minimum tournament minutes;
- minimum role confidence;
- maximum market value;
- number of recommendations.

The frontend must validate obvious input errors before submission, while the
backend remains the authoritative validator.

Required states:

- form ready;
- validation error;
- submitting;
- analysis failed;
- analysis completed.

### `/analysis/{player_id}/results`

Purpose:

- Display transfer recommendations returned by the API.
- Organize recommendations by analysis mode.
- Explain why each candidate was recommended.
- Allow a candidate to be compared with the target player.

Analysis modes currently returned by the production backend:

```text
immediate
development
value
short_term
```

Each recommendation card should display available information such as:

- player identity;
- national team;
- position;
- age;
- market value;
- rating;
- recommendation score;
- similarity information;
- role compatibility;
- heatmap compatibility;
- recommendation explanation;
- data reliability.

The frontend must not calculate recommendation rankings.

Required states:

- loading;
- complete result;
- one mode without candidates;
- analysis request invalid;
- dataset unavailable;
- unexpected failure.

### `/compare/{target_id}/{candidate_id}`

Purpose:

- Compare the target player and one recommended candidate.
- Make the recommendation easier to understand.
- Show advantages, trade-offs and analytical compatibility.

The first comparison version should include available fields for:

- age;
- market value;
- tournament minutes;
- tournament rating;
- position;
- archetype;
- role;
- spatial profile;
- statistical similarity;
- role compatibility;
- heatmap compatibility;
- recommendation score;
- recommendation explanation.

Advanced visualizations may be added after the comparison data flow is stable.

## 5. Navigation

The first navigation structure should remain simple:

```text
Home
Players
About the Analysis
API Status
```

The application must always provide a clear path back to player search.

Authentication and account navigation are not part of Phase 5.

## 6. Backend Integration Rules

The frontend must communicate with the deployed FastAPI backend.

Production API:

```text
https://world-cup-2026-production.up.railway.app
```

Backend endpoints used by the web application:

| Method | Endpoint | Frontend purpose |
|---|---|---|
| `GET` | `/health` | Display basic service availability |
| `GET` | `/ready` | Confirm analytics catalog readiness |
| `GET` | `/deployment` | Optional release information |
| `GET` | `/api/v1/players/search` | Player search |
| `GET` | `/api/v1/players/{player_id}` | Player profile |
| `POST` | `/api/v1/transfer-intelligence/analyze` | Transfer analysis |

Frontend rules:

1. Do not read analytics CSV files.
2. Do not reproduce scoring rules in JavaScript or TypeScript.
3. Do not calculate recommendation rankings.
4. Do not expose internal dataset paths.
5. Treat the backend response as the source of truth.
6. Show safe user-facing messages for backend errors.
7. Preserve the backend request ID when available for diagnostics.

## 7. Shared UI States

Every API-driven page must handle the following states deliberately.

### Loading

The interface must show that data is being fetched without replacing the whole
page with an empty screen.

Preferred patterns:

- skeleton cards;
- inline loading indicators;
- disabled submit controls during requests.

### Empty

An empty result is not always an error.

Examples:

- no player matches;
- no candidate satisfies a strict filter;
- an optional profile value is unavailable.

The page must explain the situation and provide a next action.

### Client Error

Examples:

- invalid search query;
- invalid analysis criteria;
- player not found;
- ambiguous player target.

The message should help the user correct the request.

### Service Error

Examples:

- dataset unavailable;
- API not ready;
- network failure;
- unexpected backend failure.

The interface must avoid exposing internal implementation details.

Where available, a request ID may be shown in a small diagnostic section.

## 8. Responsive Requirements

The first version must support:

- desktop;
- tablet;
- mobile.

Desktop may use multi-column analytical layouts.

Mobile layouts must:

- use a single-column flow where necessary;
- preserve readable recommendation cards;
- avoid horizontally overflowing tables;
- keep primary actions reachable;
- maintain usable search and filter controls.

## 9. Accessibility Baseline

The MVP should include:

- semantic headings;
- keyboard-accessible controls;
- visible focus states;
- associated form labels;
- sufficient text contrast;
- meaningful button labels;
- non-color-only status communication;
- descriptive alternative text for analytical images.

## 10. MVP Acceptance Criteria

Phase 5 is complete only when:

- [ ] A public production website is available.
- [ ] A user can search players by name.
- [ ] Search results can open a player profile.
- [ ] A player profile is rendered from the production API.
- [ ] A user can configure transfer-analysis criteria.
- [ ] A user can submit a transfer-analysis request.
- [ ] Recommendations are grouped by analysis mode.
- [ ] Candidate explanations are visible.
- [ ] A target player can be compared with a candidate.
- [ ] Loading states are implemented.
- [ ] Empty states are implemented.
- [ ] Client and service errors are handled.
- [ ] Mobile and desktop layouts are usable.
- [ ] The frontend contains no duplicated transfer business logic.
- [ ] Frontend quality checks pass.
- [ ] The frontend is deployed.
- [ ] A production frontend-to-backend smoke test passes.

## 11. Out of Scope for Phase 5

The following features are intentionally excluded:

- authentication;
- user registration;
- password management;
- PostgreSQL;
- saved shortlists;
- saved analyses;
- scout notes;
- team workspaces;
- admin panel;
- payment or subscription systems;
- automatic data collection;
- new machine-learning models;
- user-editable analytics data;
- multi-user collaboration.

These features may be considered in later phases after the public web MVP has
been validated.

## 12. Phase 5 Delivery Plan

```text
5A.1 Product contract
5A.2 Frontend technology and repository structure
5A.3 Information architecture and visual direction
5B.1 Frontend project foundation
5B.2 API client and typed contracts
5B.3 Shared layout and UI components
5C.1 Player search
5C.2 Player profile
5D.1 Transfer analysis form
5D.2 Recommendation results
5E.1 Player comparison
5E.2 Analytical visualizations
5F.1 Frontend tests and quality workflow
5F.2 Production deployment
5F.3 Frontend-to-backend production validation
5F.4 Final Phase 5 documentation
```

## 13. Product Principle

The first web version should prioritize clarity over feature quantity.

The product is successful when a new visitor can understand and complete the
following workflow without technical knowledge:

```text
Search a player
    ↓
Understand the player profile
    ↓
Run a transfer analysis
    ↓
Understand the recommendations
    ↓
Compare a candidate
```
