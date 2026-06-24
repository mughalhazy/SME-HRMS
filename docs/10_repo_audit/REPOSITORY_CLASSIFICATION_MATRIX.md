# REPOSITORY CLASSIFICATION MATRIX

Status: Active
Created: 2026-06-16
Phase: Full Repository Normalization and Reality Audit

Classifications: Active Source | Authority Documentation | Supporting Documentation |
Generated Report | Test Asset | Script / Tooling | Configuration | Infrastructure |
Migration / Database | Build Output | Temporary Artifact | Legacy | Archive |
Unknown | Misplaced | Duplicate Purpose

---

## ROOT LEVEL

| Path | Classification | Action |
|------|---------------|--------|
| `(C) Phoenix LiteOS.lnk` | Unknown | REQUIRES_OWNER_APPROVAL — Windows shortcut unrelated to project |
| `GOVERNANCE IMPLEMENTATION PHASE 1.md` | Legacy Mandate | Move → `docs/mandates/` |
| `PHASE 1 GOVERNANCE VALIDATION.md` | Legacy Mandate | Move → `docs/mandates/` |
| `AUDIT REMEDIATION.md` | Legacy Mandate | Move → `docs/mandates/` |
| `PHASE 2 – BACKEND AUTHORITY CAPTURE.md` | Legacy Mandate | Move → `docs/mandates/` |
| `DOCUMENTATION NORMALIZATION AND AUTHORITY CONSOLIDATION.md` | Legacy Mandate | Move → `docs/mandates/` |
| `FULL REPOSITORY NORMALIZATION AND REALITY AUDIT.md` | Active Mandate | Move → `docs/mandates/` after completion |

---

## `.github/`

| Path | Classification | Action |
|------|---------------|--------|
| `.github/workflows/ci.yml` | Infrastructure | Keep — root CI workflow |
| `backend/.github/workflows/build.yml` | Infrastructure | Duplicate Purpose — review vs root CI |
| `backend/.github/workflows/deploy.yml` | Infrastructure | Duplicate Purpose — review vs root CI |
| `backend/.github/workflows/test.yml` | Infrastructure | Duplicate Purpose — review vs root CI |

---

## `contracts/` (47 files)

| Path | Classification | Action |
|------|---------------|--------|
| `contracts/hrms-h01-*.json` through `hrms-h13-*.json` | Supporting Documentation | Keep — UI page data contracts. Correctly placed. |
| `contracts/hrms-schema-template.json` | Supporting Documentation | Keep — schema template |

---

## `design/` (10 files)

| Path | Classification | Action |
|------|---------------|--------|
| `design/hrms-archetype-system-v1.md` | Authority Documentation | Move → `docs/02_frontend/` during Frontend Authority Capture |
| `design/hrms-api-contracts.md` | Authority Documentation | Move → `docs/02_frontend/` or `docs/03_fullstack_contracts/` during Frontend Authority Capture |
| `design/hrms-doc-catalogue-v1.md` | Supporting Documentation | Move → `docs/02_frontend/` |
| `design/hrms-build-protocol-sop-v1.md` | Supporting Documentation | Move → `docs/mandates/` or `docs/02_frontend/` |
| `design/hrms-stabilisation-sop-v1.md` | Supporting Documentation | Move → `docs/mandates/` |
| `design/hrms-claude-code-prompt-v1.md` | Supporting Documentation | Move → `docs/mandates/` |
| `design/hrms-contract-structure-v1.md` | Supporting Documentation | Keep or move → `docs/02_frontend/` |
| `design/hrms-design-register-v1.md` | Supporting Documentation | Move → `docs/02_frontend/` |
| `design/hrms-ui-backend-gaps.md` | Supporting Documentation | Move → `docs/08_reports/` or `docs/02_frontend/` |
| `design/design-language.html` | Supporting Documentation | Keep in `design/` — HTML reference |

---

## `docs/` (43 files)

| Path | Classification | Action |
|------|---------------|--------|
| `docs/00_authority/` (5 files) | Authority Documentation | Keep — fully established |
| `docs/01_backend/` (8 files) | Authority Documentation | Keep — fully established |
| `docs/02_frontend/` (0 files) | Authority Documentation (EMPTY) | Reserve — frontier authority gap |
| `docs/03_fullstack_contracts/` (5 files) | Authority Documentation | Keep — fully established |
| `docs/04_testing/` (0 files) | Authority Documentation (EMPTY) | Reserve — testing authority gap |
| `docs/05_deployment/` (0 files) | Authority Documentation (EMPTY) | Reserve — deployment authority gap |
| `docs/06_decisions/` (1 file) | Authority Documentation | Keep |
| `docs/07_governance/` (2 files) | Authority Documentation | Keep |
| `docs/08_reports/` (14 files) | Generated Report | Keep |
| `docs/09_normalization/` (7 files) | Generated Report | Keep |
| `docs/10_repo_audit/` (this session) | Generated Report | Keep |

---

## `frontend/` (62 files)

| Path | Classification | Action |
|------|---------------|--------|
| `frontend/pages/h01-*.html` through `h13-*.html` (49 files) | Archive / Design Artifact | Keep — HTML wireframes for UI archetype reference |
| `frontend/seeds/p1-*.html` through `p13-*.html` (13 files) | Archive / Design Artifact | Keep — archetype seed templates |

---

## `ops/` (10 files)

| Path | Classification | Action |
|------|---------------|--------|
| `ops/pending.md` | Operational Artifact (ACTIVE) | Keep — current pending work |
| `ops/answers.md` | Supporting Documentation | Keep — architectural decisions (C1–C5) |
| `ops/build-progress.md` | Operational Artifact | Keep — UI build status |
| `ops/hrms-progress.md` | Operational Artifact (Historical) | Annotate as completed |
| `ops/HRMS PRODUCT SPEC.md` | Legacy (self-annotated superseded) | Keep — already annotated |
| `ops/hrms-directory-structure-v1.md` | Historical Record | Annotate as historical (pre-2026-06-07) |
| `ops/normalisation-tracker.md` | Operational Artifact (Completed) | Annotate as completed |
| `ops/tracker.md` | Operational Artifact (Completed) | Annotate as completed |
| `ops/hrms-audit-manifest-v1.json` | Operational Artifact | Keep or move → `docs/08_reports/` |
| `ops/hrms-audit-v1.py` | Script / Tooling | **Misplaced** — Python script in ops/; move → `backend/script/` |

---

## `backend/` ROOT FILES (78 files)

| File Group | Classification | Notes |
|-----------|---------------|-------|
| `*_service.py` + `*_api.py` pairs (40+ files) | Active Source | Core service implementations |
| `api_contract.py`, `event_contract.py`, `workflow_contract.py`, `automation_contract.py` | Active Source | Contract definitions |
| `outbox_system.py`, `persistent_store.py`, `resilience.py` | Active Source | Infrastructure primitives |
| `tenant_support.py`, `jwt_utils.py`, `rate_limiting.py`, `secrets_config.py`, `structured_logging.py` | Active Source | Cross-cutting concerns |
| `chaos_engine.py`, `supervisor_engine.py`, `master_certification.py`, `data_integrity.py`, `insight_engine.py` | Active Source | Ops/QC modules |
| `addon_convergence.py`, `error_registry.py` | Active Source | Registry/convergence |
| `background_jobs.py`, `background_jobs_api.py` | Active Source | Background job system |
| `employee_ui.py`, `payroll_ui.py` | Active Source | UI data adapters |
| `Dockerfile`, `Dockerfile.*` (5 files) | Configuration / Infrastructure | Multi-service Dockerfiles |
| `docker-compose.yml` | Configuration / Infrastructure | Service orchestration |
| `requirements.txt` | Configuration | Python dependencies |
| `start.sh` | Script / Tooling | Startup script |
| `.env.example` | Configuration | Environment template |
| `.gitignore` | Configuration | Git ignore rules |
| `pytest.ini` | Configuration | Test configuration |
| `conftest.py` | Test Asset | Pytest fixtures |
| `test_payroll_service.py` | Test Asset | **Misplaced** — test file at backend root, should be in `backend/tests/` |
| `README.md` | Supporting Documentation | Backend README |
| `pending.md` | Operational Artifact (Legacy) | **Duplicate Purpose** — superseded by `ops/pending.md` |

---

## `backend/` SUBDIRECTORIES

| Path | Classification | Issues |
|------|---------------|--------|
| `backend/api/` | Active Source | Keep |
| `backend/api-gateway/` | Active Source | Keep |
| `backend/attendance_service/` | Active Source | **Naming conflict** with `backend/services/attendance_service.py` at services root |
| `backend/audit_service/` | Active Source | Keep |
| `backend/cache/` | Legacy / Misplaced | `cache.service.ts` is TypeScript in Python backend |
| `backend/config/` | Active Source | Keep |
| `backend/core/` | Active Source | Keep |
| `backend/country/` | Active Source | Keep — Pakistan compliance adapters |
| `backend/db/` | Mixed | `idempotency.py` = Active Source; `optimization.ts` = Legacy/Misplaced |
| `backend/deployment/` | Migration / Database + Script/Tooling | Keep — migrations authoritative |
| `backend/deployment/config/` | Configuration | Keep |
| `backend/deployment/frontend/` | Misplaced | `index.html` — frontend file in deployment folder |
| `backend/deployment/migrations/` | Migration / Database | Keep — 15 SQL migration files (authoritative) |
| `backend/deployment/scripts/` | Script / Tooling | Keep |
| `backend/docker/` | Active Source | Keep — critical service runtime |
| `backend/docs/` | Legacy Documentation | Full legacy canon layer — see docs/09_normalization/ |
| `backend/health/` | Legacy / Misplaced | `health.controller.ts` is TypeScript |
| `backend/integrations/` | Active Source | Keep — Pakistan + biometric + whatsapp + accounting adapters |
| `backend/metrics/` | Legacy / Misplaced | `metrics.ts` is TypeScript |
| `backend/middleware/` | Legacy | 11 TypeScript files — Express.js middleware from original TS architecture |
| `backend/mobile/` | Active Source | Mobile gateway Python modules |
| `backend/script/` | Script / Tooling | Keep |
| `backend/services/` | Active Source + Legacy | Python OK; TypeScript subdirs are legacy |
| `backend/services/employee-service/` | Legacy | 43 TypeScript files — **superseded** by `backend/employee_service.py` |
| `backend/services/settings-service/` | Legacy | 6 TypeScript files — Python counterpart status unknown |
| `backend/tests/` | Test Asset | Keep — 85 test files |
| `backend/ui/` | Active Source (Frontend) | **Misplaced** — Next.js app inside `backend/` |
| `backend/.venv/` | Temporary Artifact | Should be git-ignored; in `.gitignore` |
| `backend/Lib/` | Temporary Artifact | Python stdlib copy — should be git-ignored; in `.gitignore` |
| `backend/Scripts/` | Temporary Artifact | Venv scripts — should be git-ignored |
| `backend/.pytest_cache/` | Temporary Artifact | Should be git-ignored; in `.gitignore` |
| `backend/__pycache__/` (206 dirs) | Build Output | 2,308 .pyc files — should be git-ignored; in `.gitignore` |
| `backend/.github/workflows/` | Infrastructure | **Duplicate Purpose** — 3 workflow files vs root `.github/` |

---

## CLASSIFICATION SUMMARY

| Classification | Count (folders/file groups) |
|---------------|---------------------------|
| Active Source | 25 |
| Authority Documentation | 7 (docs/ subdirs) |
| Supporting Documentation | 12 |
| Generated Report | 3 (docs/08, 09, 10) |
| Test Asset | 1 (backend/tests/) |
| Script / Tooling | 3 |
| Configuration | 5 |
| Infrastructure | 2 (.github/ locations) |
| Migration / Database | 1 |
| Build Output / Temporary Artifact | 5 (venv, pycache, pytest_cache) |
| Legacy | 8 |
| Archive | 2 (frontend/, backend/docs/system/archive/) |
| Misplaced | 7 |
| Duplicate Purpose | 4 |
| Unknown | 1 (.lnk shortcut) |
