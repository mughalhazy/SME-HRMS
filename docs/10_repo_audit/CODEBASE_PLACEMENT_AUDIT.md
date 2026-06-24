# CODEBASE PLACEMENT AUDIT

Status: Active
Created: 2026-06-16
Phase: Full Repository Normalization and Reality Audit

---

## PURPOSE

Verifies that source code is in expected source folders. Identifies code in wrong locations, mixed language artifacts, misplaced test files, and structural issues in the codebase.

---

## BACKEND PYTHON SOURCE — PLACEMENT REVIEW

### Issue CP-001: Frontend Application Inside `backend/`

**Severity: High**

| Attribute | Detail |
|-----------|--------|
| Path | `backend/ui/` |
| Files | 105 files (Next.js 15 app: .tsx, .ts, .css, .json, .mjs) |
| Description | The complete Meridian HCM frontend application — Next.js 15 with React, TypeScript, Tailwind — is located inside the `backend/` directory |
| Problem | The frontend application has nothing to do with the Python backend. It has its own `package.json`, `next.config.ts`, `tsconfig.json`, `.env.example`, `.gitignore`. It is a completely separate application that happens to live under `backend/`. |
| Expected location | `frontend-app/` at repository root (or just `frontend/` — but `frontend/` is currently used for HTML wireframes) |
| Current `frontend/` | Contains HTML wireframe archives (62 .html files) — NOT the Next.js app |
| Impact | Conceptual confusion: "backend/" suggests Python microservices; the Next.js app is invisible at root scan |
| Safe to move now? | **REQUIRES_OWNER_APPROVAL** — Moving the Next.js app requires updating Dockerfiles (`Dockerfile.ui`), any CI references, and build scripts |

**Proposed rename:** `frontend/pages/` + `frontend/seeds/` → `frontend-wireframes/`, and `backend/ui/` → `frontend/`

---

### Issue CP-002: TypeScript Legacy Files in Python Backend — `backend/services/employee-service/`

**Severity: High**

| Attribute | Detail |
|-----------|--------|
| Path | `backend/services/employee-service/` |
| Files | 43 TypeScript files (.ts) |
| Description | Original TypeScript employee-service implementation (NestJS-style: controllers, models, repositories, services, validation) |
| Problem | The employee-service is now implemented in Python (`backend/employee_service.py` + `backend/employee_api.py`). The TypeScript files are dead code — the service_runtime.py registers the Python implementation. |
| The TypeScript files include | `employee.controller.ts`, `employee.service.ts`, `employee.model.ts`, `employee.repository.ts`, `department.*`, `role.*`, `compensation.*`, `asset-management.*`, `org.*`, `learning.*`, `document-compliance.*`, `rbac.middleware.ts`, `event-outbox.ts`, `domain-seed.ts` |
| Risk of keeping | Confusion for future developers about which implementation is active; `domain-seed.ts` was referenced by old service_runtime.py (now replaced) |
| Safe to archive? | **REQUIRES_OWNER_APPROVAL** — Dead code; moving to archive is safe but owner should confirm before deletion/archiving |

---

### Issue CP-003: TypeScript Legacy Files — `backend/services/settings-service/`

**Severity: Medium**

| Attribute | Detail |
|-----------|--------|
| Path | `backend/services/settings-service/` |
| Files | 6 TypeScript files: `settings.controller.ts`, `settings.model.ts`, `settings.repository.ts`, `settings.routes.ts`, `settings.service.ts`, `settings.validation.ts` |
| Description | TypeScript settings-service (NestJS style) |
| Python counterpart | No `settings_service.py` or `settings_api.py` found at `backend/` root. A Python settings service may exist inside `backend/services/` but was not confirmed. |
| Risk | May still be in use if no Python counterpart exists; or may be dead code if Python implementation is elsewhere |
| Action | **REQUIRES_OWNER_APPROVAL** — verify Python counterpart exists before archiving |

---

### Issue CP-004: TypeScript Files in Python Middleware/Infra Folders

**Severity: Medium**

| Attribute | Detail |
|-----------|--------|
| Paths | `backend/middleware/*.ts` (11 files), `backend/cache/cache.service.ts`, `backend/health/health.controller.ts`, `backend/metrics/metrics.ts`, `backend/db/optimization.ts` |
| Files | 15 TypeScript files total |
| Description | Express.js/TypeScript middleware and infra files from the original TypeScript architecture |
| Python equivalents | Python has `backend/rate_limiting.py`, `backend/structured_logging.py`, `backend/resilience.py`, `backend/tenant_support.py`, `backend/jwt_utils.py` — which appear to replace the TS middleware |
| Status | These TypeScript files are not imported or used by any Python code |
| Safe to archive? | **REQUIRES_OWNER_APPROVAL** — confirm Python equivalents cover all functionality before archiving |

**TypeScript middleware files:**
- `audit-store.ts`, `audit.ts` → Python: `backend/audit_service/`
- `circuit-breaker.ts` → Python: `backend/resilience.py`
- `error-handler.ts` → Python: `backend/error_registry.py`
- `logger.ts` → Python: `backend/structured_logging.py`
- `rate-limit.ts` → Python: `backend/rate_limiting.py`
- `request-id.ts` → Python: part of `backend/resilience.py` (trace IDs)
- `retry.ts` → Python: `backend/resilience.py`
- `tenant-context.ts` → Python: `backend/tenant_support.py`
- `throttle.ts` → Python: `backend/rate_limiting.py`
- `validation.ts` → Python: `backend/api_contract.py` and service validation

---

### Issue CP-005: Misplaced Test File at `backend/` Root

**Severity: Low**

| Attribute | Detail |
|-----------|--------|
| Path | `backend/test_payroll_service.py` |
| Problem | Test file at backend root; all other test files are in `backend/tests/` |
| Fix | Move → `backend/tests/test_payroll_service.py` |
| Safe to move? | **REQUIRES_OWNER_APPROVAL** — moving test file may affect pytest discovery or import paths in `conftest.py` |

---

### Issue CP-006: Naming Conflict — `backend/attendance_service/` vs `backend/services/attendance_service.py`

**Severity: Medium**

| Attribute | Detail |
|-----------|--------|
| Path 1 | `backend/attendance_service/` — Python module with `api.py`, `models.py`, `service.py`, `ui.py`, `__init__.py` |
| Path 2 | `backend/services/attendance_service.py` — Python file at services root |
| Problem | Two attendance service implementations with different locations and structures |
| Which is active? | `service_runtime.py` determines which is registered — needs verification |
| Risk | Import ambiguity; tests may target one but runtime uses the other |
| Action | **REQUIRES_OWNER_APPROVAL** — need to determine which is authoritative before consolidating |

---

### Issue CP-007: Duplicate Pending Files

**Severity: Low**

| Attribute | Detail |
|-----------|--------|
| Files | `backend/pending.md`, `backend/docs/system/pending.md`, `ops/pending.md` |
| Active | `ops/pending.md` only |
| Stale | `backend/pending.md` and `backend/docs/system/pending.md` |
| Fix | Annotate stale files as superseded (specified in DOCUMENT_RETIREMENT_PLAN.md) |

---

### Issue CP-008: `ops/hrms-audit-v1.py` — Python Script in Ops Folder

**Severity: Low**

| Attribute | Detail |
|-----------|--------|
| Path | `ops/hrms-audit-v1.py` |
| Problem | Python script in ops/ (which is for operational markdown artifacts, not scripts) |
| Fix | Move → `backend/script/hrms-audit-v1.py` |
| Safe to move? | YES — pure documentation/tool move, no runtime import |

---

## CI/CD PLACEMENT REVIEW

### Issue CP-009: Duplicate CI Workflow Locations

**Severity: Medium**

| Attribute | Detail |
|-----------|--------|
| Root CI | `.github/workflows/ci.yml` — 1 file |
| Backend CI | `backend/.github/workflows/build.yml`, `deploy.yml`, `test.yml` — 3 files |
| Problem | Two `.github/workflows/` locations; GitHub only reads the root `.github/` |
| Consequence | The 3 workflow files in `backend/.github/workflows/` are **never executed by GitHub Actions** |
| Action | **REQUIRES_OWNER_APPROVAL** — determine if backend workflows should be merged into root `.github/workflows/` or remain as reference/documentation |

---

## MIGRATION / DATABASE PLACEMENT

### Current State: Correct but Undocumented

| Aspect | Detail |
|--------|--------|
| Migration files | `backend/deployment/migrations/001–015.sql` — correctly placed |
| Migration script | `backend/deployment/migrate.py` — correctly placed |
| Migration runner | `backend/deployment/scripts/run-migrations.sh` — correctly placed |
| DB init | `backend/deployment/config/postgres-init.sql` — correctly placed |
| Missing | No authority document in `docs/05_deployment/` pointing to these files |

---

## CODEBASE PLACEMENT SUMMARY

| Issue ID | Severity | Description | Action Type |
|---------|----------|-------------|-------------|
| CP-001 | High | `backend/ui/` (Next.js app) inside backend | REQUIRES_OWNER_APPROVAL |
| CP-002 | High | 43 TypeScript files in `backend/services/employee-service/` (dead code) | REQUIRES_OWNER_APPROVAL |
| CP-003 | Medium | 6 TypeScript files in `backend/services/settings-service/` | REQUIRES_OWNER_APPROVAL |
| CP-004 | Medium | 15 TypeScript files in middleware/cache/health/metrics/db | REQUIRES_OWNER_APPROVAL |
| CP-005 | Low | `backend/test_payroll_service.py` at root (should be in tests/) | REQUIRES_OWNER_APPROVAL |
| CP-006 | Medium | Naming conflict: `backend/attendance_service/` vs `backend/services/attendance_service.py` | REQUIRES_OWNER_APPROVAL |
| CP-007 | Low | Duplicate pending.md files | Safe to annotate per RETIREMENT_PLAN |
| CP-008 | Low | `ops/hrms-audit-v1.py` in ops instead of scripts | Safe to move |
| CP-009 | Medium | Duplicate `.github/workflows/` locations (root + backend) | REQUIRES_OWNER_APPROVAL |
