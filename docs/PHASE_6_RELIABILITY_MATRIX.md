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
| Missing market value | Nullable API model and presentation fallback | Backend coverage; frontend null-state coverage should be strengthened | Partial |
| Missing heatmap evidence | Nullable measured evidence with neutral decision-score fallback | Strong backend coverage; frontend presentation coverage should be strengthened | Partial |
| API timeout | AbortController and upstream-timeout handling | Server client and route-handler regression coverage | Covered || Missing role or archetype | Presentation fallbacks exist | Explicit component coverage still required | Partial |
| Missing tournament minutes | Nullable API model | Explicit presentation coverage still required | Partial |
| No appearances | Nullable API model | Explicit presentation coverage still required | Partial |
| Low-minute player | Minimum-minutes candidate threshold exists | UX behavior coverage still required | Partial |
| Long player name | No dedicated hardening verified | No regression coverage | Missing |
| Mobile long-content overflow | Responsive primary journey passes | Dedicated overflow coverage still required | Missing |

## Phase 6B Priorities

1. Strengthen nullable player-data presentation coverage.
2. Add explicit upstream-timeout regression coverage.
3. Verify low-minute and no-appearance behavior.
4. Harden long player names and constrained mobile layouts.
5. Expand mobile result and comparison reliability coverage.

## Principles

- Missing evidence must remain visibly distinct from measured zero.
- Missing heatmap evidence must not be presented as measured similarity.
- Backend semantics remain the source of truth.
- Frontend fallbacks must not invent analytical evidence.
- Recovery actions should remain available for recoverable API failures.
- Request diagnostics must be useful without exposing sensitive data.
