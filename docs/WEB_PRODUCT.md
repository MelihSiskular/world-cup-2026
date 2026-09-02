# WC26 Web Product Contract

## Status

- Product version: `0.6.0`
- Phase 8: complete
- Authentication: not required
- Analytical source of truth: FastAPI and the validated runtime catalog

## Product Goal

WC26 is a public recruitment decision-support product. It helps users discover tournament players, understand their profiles, build shortlists, compare alternatives and run explainable transfer analysis.

It is designed for scouts, recruitment analysts, football analytics enthusiasts and portfolio reviewers. Tournament evidence supports a decision; it does not replace long-term scouting.

## Core Journeys

### Recruitment analysis

```text
Player discovery → Profile → Transfer criteria → Recommendations → Pair comparison
```

### Shortlist comparison

```text
Player discovery → Shortlist → Target + 1–3 candidates → Multi-player comparison
```

Both journeys work without an account.

## Product Routes

| Route | User outcome |
|---|---|
| `/` | Understand the product and begin discovery |
| `/players` | Search and filter the player pool |
| `/players/[playerId]` | Inspect a player and take recruitment actions |
| `/shortlists` | Create, rename and manage local shortlists |
| `/analysis/[playerId]` | Configure transfer criteria |
| `/analysis/[playerId]/results` | Review grouped recommendations |
| `/compare/[targetId]/[candidateId]` | Inspect one recommendation pair |
| `/compare/multi/[targetId]?candidates=...` | Compare one target with up to three candidates |
| `/methodology` | Understand evidence and limitations |
| `/status` | Check API readiness and release identity |

## Player Discovery Contract

- Filter state is canonical and shareable through the URL.
- Available filter options come from the API.
- Results expose identity, country, position, final role, spatial role and selected performance context.
- Loading, empty, invalid-query and service-error states provide a clear next action.
- A result can open the profile or be added directly to a shortlist.

## Shortlist Contract

- Shortlists persist in browser storage.
- Users can create, rename and delete shortlists and add or remove players.
- The same player is not duplicated inside one shortlist.
- Storage changes remain synchronized across relevant browser surfaces.
- No account, database or server-side synchronization is implied.

## Multi-player Comparison Contract

- Exactly one target and one to three unique candidates are required.
- Candidates must share the target's broad position.
- Candidate order is preserved in the URL, request and response.
- The overview compares position, final role, age, market value, minutes and available target-relative evidence.
- Role metrics are selected from the target player's final-role duties.
- Each role metric displays tournament total followed by the per-90 rate, for example `5 (0.42/90)`.
- Radar and heatmap controls share one focused candidate state.
- Changing the candidate in either section updates both evidence views.
- Missing statistical or heatmap evidence remains explicitly unavailable.

## Transfer-analysis Contract

The backend returns four recruitment modes:

```text
immediate, development, value, short_term
```

The frontend presents backend-owned ranking, scores and explanations. It does not recalculate suitability or silently change request criteria.

## Shared Experience Requirements

Every API-driven surface handles:

- loading;
- empty or unavailable evidence;
- correctable client errors;
- upstream or dataset failure;
- retry where safe;
- request ID visibility where useful.

Responsive behaviour must prevent document-level horizontal overflow. Wide comparison tables may scroll inside their own labelled region.

Accessibility requirements include semantic headings and tables, keyboard-operable controls, visible focus, WCAG AA contrast, meaningful labels and non-color-only states.

## Evidence Boundary

Phase 8 runtime coverage contains sparse same-position pair evidence. A selected player may therefore have complete profile data but no measured statistical or heatmap pair. That is a valid unavailable state, not an error.

## Out of Scope

- Authentication and user accounts
- Server-synchronized shortlists
- Collaborative notes or team workspaces
- Admin and payment systems
- Frontend-owned analytical models
- Fabricated all-pairs similarity
- Automatic production data collection

## Release Acceptance

Version `0.6.0` is acceptable when the Python, Docker, web and browser quality gates pass; the OpenAPI contract is current; production builds succeed; and the complete user journeys work on Chromium, WebKit and their mobile projects.
