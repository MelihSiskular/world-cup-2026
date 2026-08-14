# Phase 6 Reliability Matrix

## Status

Phase 6B reliability and UX hardening inventory.

The matrix records the edge cases that are already protected by the
backend or web application, the remaining verification gaps, and the
work that should be completed before Phase 6B is accepted.

## Reliability Matrix

| Scenario | Current protection | Test coverage | Status |
|---|---|---|---|
| Player not found | Dedicated player-not-found state | Backend coverage | Covered |
| Candidate unavailable | Dedicated comparison state | Component coverage | Covered |
| Player search failure | Error state with retry action | Component coverage | Covered |
| Transfer analysis failure | Error state with retry action | Component coverage | Covered |
| Empty recommendation mode | No-eligible-candidates state | Component coverage | Covered |
| Dataset unavailable | Dedicated dataset-unavailable handling | API client coverage | Covered |
| Generic upstream 5xx | Structured API error handling | API client coverage | Covered |
| Request ID diagnostics | Request ID preserved and displayed safely | API client coverage | Covered |
| Missing market value | Nullable API model and presentation fallback | Profile, recommendation and comparison component regression coverage | Covered |
| Missing heatmap evidence | Nullable measured evidence with neutral decision-score fallback | Backend semantics and comparison regression coverage distinguish measured missing/zero values from the decision fallback | Covered |
| API timeout | AbortController and upstream-timeout handling | Server client and route-handler regression coverage | Covered |
| Missing role or archetype | Presentation fallbacks exist | Profile, recommendation and comparison component regression coverage | Covered |
| Missing tournament minutes | Nullable API model and candidate eligibility handling | Profile presentation and candidate eligibility regression coverage | Covered |
| No appearances | Nullable API model; appearances do not independently filter candidates | Profile presentation and candidate eligibility regression coverage | Covered |
| Low-minute player | Minimum-minutes threshold applies to candidates, not the target | Boundary, zero, missing-minute and target regression coverage | Covered |
| Long player name | Explicit break-word and min-width hardening across player, analysis, recommendation and comparison views | Synthetic extreme-name Playwright journey passes in Chromium, WebKit, Mobile Chromium and Mobile WebKit | Covered |
| Mobile long-content overflow | Break-word hardening and page-level overflow protection | Chromium and WebKit journey assertions across players, profile, results and comparison | Covered |

## Phase 6B Priorities

1. Strengthen nullable player-data presentation coverage.
2. Add explicit upstream-timeout regression coverage.
3. Verify low-minute and no-appearance behavior.
4. [x] Harden long player names and constrained mobile layouts with synthetic cross-browser regression coverage.q
5. Expand mobile result and comparison reliability coverage.

## Principles

- Missing evidence must remain visibly distinct from measured zero.
- Missing heatmap evidence must not be presented as measured similarity.
- Backend semantics remain the source of truth.
- Frontend fallbacks must not invent analytical evidence.
- Recovery actions should remain available for recoverable API failures.
- Request diagnostics must be useful without exposing sensitive data.
