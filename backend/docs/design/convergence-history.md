# Convergence History

Consolidated record of sequential build convergence passes P28–P33. Individual pass reports are retained as stubs pointing here.

---

## P28 — Backward Compatibility Enforcement

**Scope:** Frozen canonical API standards, gateway routing, response shapes, event naming.

**Risks detected:**
- Gateway path drift: legacy unversioned paths (`/payroll/records`) still referenced by consumers.
- List response shape drift: `data.data` legacy alias vs. canonical `data.items + meta.pagination`.
- Event naming drift: PascalCase legacy event names vs. canonical dot-delimited D2 names.

**Actions applied:**
- Gateway route aliases added: `resolve_route()` recognizes both `/api/v1/...` and legacy unversioned paths.
- Legacy-route detector added for safe deprecation without removing old paths.
- Regression tests lock in legacy leave/payroll list aliases and event-name round-tripping.

**Deferred:** No endpoint removals. No payload field removals. No workflow path changes.

---

## P29 — Data Integrity Validation

**Scope:** Cross-service data consistency: employee, leave, payroll, hiring handoff, workflow state, projections, tenant ownership, audit/event alignment.

**What was added:**
- `DataIntegrityValidator` covering: employee/org integrity, leave balance, payroll cycle correctness, candidate-to-employee handoff, workflow/business-state alignment, projection drift, tenant ownership, audit/event alignment.
- Safe auto-repairs: `repair_minor_projection_drift`, `patch_orphan_reference_issues_where_safe`, `rebuild_inconsistent_indexes_or_projections`, `normalize_tenant_ownership_fields`.
- Background-job support for safe integrity repairs.
- CLI repair script: `deployment/repair_data_integrity.py`.

**Repair policy:** Only minor, deterministic drift auto-fixed. Source-of-truth conflicts remain hard failures.

**Re-QC:** `deployment/re_qc_validate_data_integrity.py` → 6/6.

---

## P30 — Event Consistency and Replay Safety

**Scope:** Event contract normalization, tenant-safe idempotency, outbox retry/failure, replay-safe downstream consumers.

**Findings and fixes:**
- Idempotency keys were not tenant-scoped → extended to scope by `tenant_id + event_type + idempotency_key`.
- Normalized events missing D2 aliases (`event_name`, `occurred_at`, `producer_service`, `trace_id`) → added.
- `auth-service` bypassed outbox via internal `_emit_event` helper → patched to route through `OutboxManager`.
- `search-service`: added canonical contract validation before event ingestion.
- `notification-service`: added per-event consumption persistence to prevent duplicate messages.
- `reporting-analytics`: added contract validation and tenant rejection on event ingress.

---

## P31 — Workflow Integrity

**Scope:** Approval centralization for leave, payroll, hiring, performance. State integrity and delegation safety.

**Validation summary:**
- Leave, payroll, hiring, performance approval decisions route through `WorkflowService`.
- Terminal business transitions gated on terminal workflow outcomes.
- Delegation scope safety enforced.

**Fixes applied:**
1. Performance review-cycle: fixed bypass where `submit_review_cycle` immediately opened the cycle before approval. `PerformanceReviewCycleOpened` now emitted only after workflow approval.
2. Terminal outcome enforcement for goals, calibration sessions, and PIPs.
3. Delegation safety: added assignment-scope validation.

**Regression coverage added:** Review cycle pending→approved→opened path; rejection preserves rejected trace; delegation rejects cross-scope reassignment.

---

## P32 — Final Convergence

**Scope:** Full end-to-end convergence pass — service topology, gateway routing, runtime executability, canonical docs.

**Changes applied:**
- Removed stale singular gateway aliases for project/workflow/integration/automation surfaces.
- Removed dead `jobs` gateway mapping.
- Updated compatibility/route tests to enforce canonical plural route policy.
- Expanded end-to-end alignment test coverage so every declared public gateway route is translated and executed against a real runtime handler.

**Evidence (2026-03-31):**
- `pytest -q` → `281 passed, 70 subtests passed` (historical baseline; most recent full run is 403 passed, 9 skipped, 2026-06-11 — see `docs/system/qc-suite.md` Provenance note)
- `python deployment/qc_validate.py` → `QC score: 11/11`
- `re_qc_validate_master_certification.py` → `5/5`
- `re_qc_validate_addon_convergence.py` → `5/5`
- `re_qc_validate_data_integrity.py` → `6/6`

**Status: FULLY ALIGNED (verified 2026-03-31)**

---

## P33 — System Certification

**Scope:** Final certification pass confirming all convergence changes from P28–P32 are integrated, tested, and registry-consistent.

**Certification outcome:**
- ✅ Every declared service is runnable in runtime handler space.
- ✅ Every declared public gateway route is executable through gateway translation and downstream runtime matching.
- ✅ Stale aliases, stale docs, and dead mappings removed.
- ✅ All QC/RE-QC gates pass.

**Full alignment declared (2026-03-31).** See `docs/system/intent_build_alignment.md` for the canonical alignment record.

---

## Country-layer alignment update (2026-04-01)

- Country abstraction layer implemented, aligned to `docs/canon/country-layer.md`.
- Pakistan adapter: `TaxEngineInterface`, `ComplianceEngineInterface`, `PayrollRulesInterface` all implemented.
- Resolver: resolves `organization_id` → country adapter.
- Error cases: `ORG_COUNTRY_NOT_FOUND`, `COUNTRY_ADAPTER_NOT_REGISTERED`.
- Pakistan compliance and payroll specs updated: `docs/specs/country/pakistan/compliance.md`, `payroll.md`.

---

*Individual pass report files (p28.md – p33.md) are retained as stubs and point to this document.*
