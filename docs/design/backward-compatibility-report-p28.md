# P28 Backward Compatibility Enforcement Report

## Scope
- Reviewed frozen canonical sources in `docs/canon/*`, especially D1-aligned API guidance in `docs/canon/api-standards.md` and the prior standardization summary in `docs/design/api-contract-standardization-summary.md`.
- Verified compatibility-sensitive surfaces across the gateway, response wrappers, workflow/event contracts, and existing regression coverage.

## Risks detected
1. **Gateway path drift risk**
   - Canonical routing is versioned under `/api/v1`, but legacy service docs and earlier integrations still reference unversioned paths such as `/payroll/records`.
   - Without a compatibility alias, consumers pinned to pre-standardization paths would fail at the gateway boundary.
2. **List response shape drift risk**
   - D1 list responses prefer canonical `data.items` plus `meta.pagination`.
   - Existing leave/payroll consumers still depend on the legacy embedded list alias at `data.data`.
3. **Event naming drift risk**
   - D2 canonical event types are dot-delimited, while several producers/consumers still reason in PascalCase legacy event names.
   - Compatibility must preserve round-tripping between canonical and legacy identifiers.

## Compatibility actions applied
- Added **gateway route aliases** so `resolve_route()` continues to recognize both `/api/v1/...` and legacy unversioned service paths.
- Added an explicit **legacy-route detector** to support safe deprecation handling without removing old paths yet.
- Added **regression tests** that lock in legacy leave/payroll list aliases and event-name round-tripping.

## Validation summary
- Gateway: legacy and canonical paths now resolve to the same upstream service.
- Service responses: leave/payroll wrappers continue exposing both D1 `items` and legacy `data` list aliases.
- Events: canonical/legacy event naming remains reversible for current consumers.
- Existing targeted regression suite passed after the changes.

## Deferred items
- No service endpoint removals were introduced.
- No payload fields were removed from existing wrappers.
- No workflow initiation path changes were required in this pass because existing workflow APIs remained stable under current tests.
