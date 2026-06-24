# LEGACY AND ARCHIVE PLAN

Status: Active
Created: 2026-06-16
Phase: Full Repository Normalization and Reality Audit

---

## PURPOSE

Documents all legacy code and documentation in the repository. For each legacy item, specifies the recommended disposition: Archive, Annotate, Consolidate, or Requires Owner Approval.

Per the mandate: **Do not delete anything without explicit approval.**

---

## LEGACY CODE

### LC-001: TypeScript Employee-Service (`backend/services/employee-service/`)

| Attribute | Detail |
|-----------|--------|
| Path | `backend/services/employee-service/` |
| Files | 43 TypeScript files |
| Origin | Original TypeScript/NestJS employee-service from pre-Python architecture |
| Current status | **Dead code** — `backend/employee_service.py` + `backend/employee_api.py` replaced this service (EG-001 resolution, 2026-06-16). `service_runtime.py` now imports the Python implementation. |
| Risk of keeping | Developer confusion; `domain-seed.ts` inside this dir was previously referenced by old service_runtime.py (now removed) |
| Recommended disposition | **Archive** → move to `backend/docs/system/archive/typescript-employee-service/` |
| Requires owner approval? | YES — confirm dead code before archiving |

**Files in this service:**
`asset-management.*`, `compensation.*`, `contractor.controller.ts`, `department.*`, `document-compliance.*`, `domain-seed.ts`, `employee.*`, `event-outbox.ts`, `learning.*`, `org.*`, `rbac.middleware.ts`, `role.*`, `service.errors.ts`

---

### LC-002: TypeScript Settings-Service (`backend/services/settings-service/`)

| Attribute | Detail |
|-----------|--------|
| Path | `backend/services/settings-service/` |
| Files | 6 TypeScript files |
| Origin | Original TypeScript/NestJS settings-service |
| Current status | Uncertain — no Python `settings_service.py` confirmed at `backend/` root |
| Risk | May still be in active use if no Python counterpart exists |
| Recommended disposition | **Verify first** — if Python counterpart confirmed, archive to `backend/docs/system/archive/typescript-settings-service/` |
| Requires owner approval? | YES |

---

### LC-003: TypeScript Middleware (`backend/middleware/`)

| Attribute | Detail |
|-----------|--------|
| Path | `backend/middleware/` |
| Files | 11 TypeScript files (Express.js middleware) |
| Origin | Original Express.js/TypeScript middleware layer |
| Python equivalents | `rate_limiting.py`, `structured_logging.py`, `resilience.py`, `tenant_support.py`, `jwt_utils.py`, `audit_service/`, `error_registry.py` |
| Current status | Not imported by Python runtime |
| Recommended disposition | **Archive** → `backend/docs/system/archive/typescript-middleware/` |
| Requires owner approval? | YES |

---

### LC-004: TypeScript Infra Singles (`backend/cache/`, `backend/health/`, `backend/metrics/`, `backend/db/`)

| Attribute | Detail |
|-----------|--------|
| Files | `cache.service.ts`, `health.controller.ts`, `metrics.ts`, `optimization.ts` |
| Origin | TypeScript infrastructure modules |
| Python equivalents | `persistent_store.py` (cache), `backend/health/` had Python components, `structured_logging.py` (metrics), various |
| Note | `backend/health/` has only `health.controller.ts` (TS) — no Python health file; `backend/db/` has `idempotency.py` (Python) alongside `optimization.ts` (TS) |
| Recommended disposition | **Verify + Archive** — confirm Python equivalents before archiving TS files |
| Requires owner approval? | YES |

---

### LC-005: Services Root TypeScript/Python Mix (`backend/services/` root-level .py)

| Attribute | Detail |
|-----------|--------|
| Files at `backend/services/` root | `attendance_service.py`, `compliance_autopilot.py`, `compliance_service.py`, `decision_engine.py`, `experience_layer_service.py`, `mobile_gateway.py`, `payroll_policy_engine.py`, `payroll_service.py` |
| Status | These appear to be active Python service implementations inside `services/` rather than at `backend/` root. This creates a fragmented service layout — some services at `backend/` root, others at `backend/services/` root. |
| Not legacy — but structurally fragmented | See REPOSITORY_RESTRUCTURING_PLAN.md for consolidation proposal |

---

## LEGACY DOCUMENTATION

### LD-001: `backend/docs/canon/` (14 files)

All superseded by `docs/00_authority/` and `docs/01_backend/`. Retirement annotations specified in `docs/09_normalization/DOCUMENT_RETIREMENT_PLAN.md`.

| File | Superseded By |
|------|--------------|
| `domain-model.md` | `docs/00_authority/DOMAIN_MODEL.md` |
| `data-architecture.md` | `docs/01_backend/DATABASE_SCHEMA.md` |
| `release-scope.md` | `docs/00_authority/FEATURE_SCOPE.md` |
| `security-model.md` | `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md` |
| `service-map.md` | `docs/01_backend/SERVICE_CATALOG.md` |
| `api-standards.md` | Partially: `docs/01_backend/API_CONTRACT.md` (route content); retained for coding standards |
| `capability-matrix.md` | Retained as CAP-XXX registry — cross-ref to `docs/03_fullstack_contracts/USER_ROLES_AND_PERMISSIONS.md` |
| `event-catalog.md` | Cross-ref to `docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md`; retained |
| `workflow-catalog.md` | Cross-ref to `docs/00_authority/PRODUCT_WORKFLOWS.md`; retained |
| `country-layer.md` | No authority doc; retained pending D-016 resolution |
| `decision-system.md` | No authority doc; retained pending D-020 resolution |
| `read-model-catalog.md` | No authority doc; retained pending D-021 resolution |
| `read-models.md` | No authority doc; retained pending D-021 resolution |
| `ui-surface-map.md` | No authority doc; retained pending D-022 resolution |

**Action: Apply retirement annotations per DOCUMENT_RETIREMENT_PLAN.md — safe to execute.**

---

### LD-002: `backend/docs/system/` (14 files, excl. archive)

All superseded or historical. Retirement annotations specified in DOCUMENT_RETIREMENT_PLAN.md.

| File | Disposition |
|------|------------|
| `system-purpose.md` | ANNOTATE-SUPERSEDED → PROJECT_CHARTER.md |
| `MASTER BUILD SPEC.md` | ANNOTATE-SUPERSEDED → BACKEND_ARCHITECTURE.md |
| `MASTER BEHAVIOR SPEC.md` | ANNOTATE-SUPERSEDED → PRODUCT_WORKFLOWS.md |
| `service-manifest.md` | ANNOTATE-SUPERSEDED + STALE CLAIM (TypeScript employee-service) |
| `gap-register.md` | ANNOTATE-SUPERSEDED + HISTORICAL |
| `catalogue.md` | Keep as navigation aid; note workflow count error |
| `infrastructure.md` | Historical record; retain |
| `intent_build_alignment.md` | ANNOTATE-HISTORICAL |
| `progress.md` | Keep as historical build progress |
| `qc-suite.md` | Keep as QC suite reference |
| `roadmap.md` | Keep as historical roadmap |
| `success-criteria.md` | Keep as historical success criteria |
| `pending.md` | ANNOTATE-SUPERSEDED → ops/pending.md |
| `MASTER MARKET RESEARCH.md` | Historical record; retain |

---

### LD-003: `backend/docs/system/archive/` (7 files)

Already archived — no action needed. Keep as-is.

- `COMPLETE HRMS BUILD SPEC.md`
- `HRMS Repo Surgical Upgrade Spec.md`
- `HRMS SPEC.md`
- `HRMS SYSTEM BEHAVIOR SPEC.md`
- `MARKET-VALIDATED BEHAVIOR SPEC.md`
- `Pakistan_HRMS_Market_Research_Report_(2024–2026) MANUS AI.md`
- `RMS MARKET RESEARCH--CHAT GPT.md`

---

### LD-004: `backend/docs/design/` (15 files)

Build pass reports and design summaries from backend build sessions. These are historical records.

| File | Classification |
|------|---------------|
| `convergence-history.md` | Historical Record (actively referenced by build pass stubs) |
| `addon-certification-pass-p51.md` | Historical Record |
| `addon-convergence-report-p50.md` | Historical Record |
| `backward-compatibility-report-p28.md` | Historical Record (stub → convergence-history.md) |
| `data-integrity-report-p29.md` | Historical Record (stub) |
| `event-reliability-report-p30.md` | Historical Record (stub) |
| `workflow-integrity-report-p31.md` | Historical Record (stub) |
| `final-convergence-report-p32.md` | Historical Record (stub) |
| `final-system-certification-pass-p33.md` | Historical Record (stub) |
| `chaos-auto-healing-report.md` | Historical Record |
| `api-contract-standardization-summary.md` | Historical Record |
| `background-jobs-summary.md` | Historical Record |
| `design-system-anchor.md` | Supporting Documentation |
| `micro-fix-register.md` | Historical Record |
| `search-indexing-summary.md` | Historical Record |

**Action: Keep all. No retirement annotation needed — these are already in `design/` subfolder which signals their nature.**

---

### LD-005: `backend/docs/reports/` (2 files)

| File | Classification | Action |
|------|---------------|--------|
| `alignment_final.md` | Historical (2026-03-31 snapshot) | ANNOTATE-HISTORICAL |
| `platform_validation_2026-04-01.md` | Historical Record | Keep |

---

## ARCHIVE CANDIDATES REQUIRING OWNER APPROVAL

| Item | Type | Recommended Archive Path |
|------|------|--------------------------|
| `backend/services/employee-service/` (43 .ts) | Dead code | `backend/docs/system/archive/typescript-employee-service/` |
| `backend/services/settings-service/` (6 .ts) | Uncertain | `backend/docs/system/archive/typescript-settings-service/` (verify first) |
| `backend/middleware/` (11 .ts) | Dead code | `backend/docs/system/archive/typescript-middleware/` |
| `backend/cache/cache.service.ts` | Dead code | Merge into above archive |
| `backend/health/health.controller.ts` | Dead code | Merge into above archive |
| `backend/metrics/metrics.ts` | Dead code | Merge into above archive |
| `backend/db/optimization.ts` | Dead code | Merge into above archive |

---

## SAFE ACTIONS (can execute without owner approval)

1. Apply retirement annotations to `backend/docs/canon/` files (per DOCUMENT_RETIREMENT_PLAN.md)
2. Apply retirement annotations to `backend/docs/system/` files (per DOCUMENT_RETIREMENT_PLAN.md)
3. Annotate `backend/docs/reports/alignment_final.md` as historical
4. Annotate `ops/normalisation-tracker.md` and `ops/tracker.md` as completed
5. Move `ops/hrms-audit-v1.py` → `backend/script/hrms-audit-v1.py`
