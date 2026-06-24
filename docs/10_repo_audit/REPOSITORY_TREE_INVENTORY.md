# REPOSITORY TREE INVENTORY

Status: Active
Created: 2026-06-16
Phase: Full Repository Normalization and Reality Audit

---

## ROOT LEVEL

| Path | Type | File Count | Key File Types | Classification |
|------|------|-----------|----------------|----------------|
| `/` (root) | Directory | 7 items | .md, .lnk | Mixed |
| `(C) Phoenix LiteOS.lnk` | File | — | .lnk shortcut | Unknown / Misplaced |
| `GOVERNANCE IMPLEMENTATION PHASE 1.md` | File | — | Mandate .md | Legacy Mandate |
| `PHASE 1 GOVERNANCE VALIDATION.md` | File | — | Mandate .md | Legacy Mandate |
| `AUDIT REMEDIATION.md` | File | — | Mandate .md | Legacy Mandate |
| `PHASE 2 – BACKEND AUTHORITY CAPTURE.md` | File | — | Mandate .md | Legacy Mandate |
| `DOCUMENTATION NORMALIZATION AND AUTHORITY CONSOLIDATION.md` | File | — | Mandate .md | Legacy Mandate |
| `FULL REPOSITORY NORMALIZATION AND REALITY AUDIT.md` | File | — | Current prompt | Active Mandate |

---

## TOP-LEVEL FOLDERS

### `.claude/`
- **Purpose:** Claude Code session memory (auto-memory system)
- **Files:** 1 (MEMORY.md index) + memory subfolder
- **Classification:** Tooling / Session Artifact
- **Notes:** Not application code. Not documentation. Tool-managed.

### `.github/`
- **Purpose:** GitHub Actions CI/CD configuration
- **Files:** 1 (`workflows/ci.yml`)
- **Classification:** Configuration / Infrastructure
- **Notes:** Single root-level workflow file. Backend also has its own `.github/workflows/` (3 files).

### `backend/`
- **Purpose:** Primary backend source tree — 24 Python microservices + API gateway + tests + UI app + deployment
- **Files:** 272 .py source files + 105 UI files + 85 test files + 49 TypeScript legacy files + docs + config
- **Classification:** Active Source (dominant); contains Legacy, Archive, Generated Artifact subdirs
- **See detail sections below**

### `contracts/`
- **Purpose:** UI page data contracts (JSON) — 47 files matching h01–h13 page archetypes
- **Files:** 47 .json files
- **Classification:** Supporting Documentation / UI Specification
- **Notes:** These are the data contract specifications for each UI page. Paired with `frontend/pages/` HTML wireframes.

### `design/`
- **Purpose:** UI design system documents and SOPs
- **Files:** 10 files (1 .html + 9 .md)
- **Classification:** Authority Documentation (3 files) + Supporting Documentation (7 files)
- **Key files:**
  - `design-language.html` — HTML design token reference
  - `hrms-archetype-system-v1.md` — UI archetype authority
  - `hrms-api-contracts.md` — Frontend API contract authority (canonical engagement enums)
  - `hrms-doc-catalogue-v1.md` — UI document catalogue

### `docs/`
- **Purpose:** Governance authority documentation framework (9 numbered subdirs)
- **Files:** 43 files (3 subdirs empty)
- **Classification:** Authority Documentation
- **See detail section below**

### `frontend/`
- **Purpose:** HTML wireframe/prototype pages (NOT the Next.js application)
- **Files:** 62 .html files across pages/ and seeds/
- **Classification:** Archive / Design Artifact
- **Notes:** These are static HTML wireframes built during the archetype phase. The actual Next.js frontend application is at `backend/ui/`.

### `ops/`
- **Purpose:** Operational session artifacts — trackers, progress files, pending lists
- **Files:** 10 files (.md, .json, .py)
- **Classification:** Operational Artifact
- **Key files:** `pending.md` (active), `answers.md` (architectural decisions), `build-progress.md` (UI status)

---

## BACKEND/ DETAIL

### `backend/` (root — 78 files)
- **Python services (core):** `api_contract.py`, `event_contract.py`, `outbox_system.py`, `persistent_store.py`, `resilience.py`, `tenant_support.py`, `jwt_utils.py`, `structured_logging.py`, `rate_limiting.py`, `secrets_config.py`
- **Service pairs (service + api):** automation, banking, compliance, cost_planning, decision, employee, engagement, expense, helpdesk, integration, leave, notification, payroll, performance, project, reporting_analytics, search, travel, whatsapp, workflow
- **Infra files:** `Dockerfile`, `Dockerfile.api`, `Dockerfile.render`, `Dockerfile.services`, `Dockerfile.ui`, `docker-compose.yml`, `requirements.txt`, `start.sh`, `.env.example`, `.gitignore`, `pytest.ini`
- **Other:** `README.md`, `pending.md`, `conftest.py`, `test_payroll_service.py`, `addon_convergence.py`, `background_jobs.py`, `background_jobs_api.py`, `chaos_engine.py`, `data_integrity.py`, `employee_ui.py`, `error_registry.py`, `insight_engine.py`, `master_certification.py`, `payroll_ui.py`, `supervisor_engine.py`
- **Classification:** Active Source

### `backend/api/`
- **Files:** 4 (`employee_portal.py`, `manager_dashboard.py`, `workforce.py`, `dashboard_ui.py`, `__init__.py`)
- **Purpose:** Composite API handlers that aggregate across services for specific UI surfaces
- **Classification:** Active Source

### `backend/api-gateway/`
- **Files:** 5 (`load_control.py`, `routes.py`, `tenant.py`, `README.md`, `__init__.py`)
- **Purpose:** API Gateway support code (load control, tenant routing, route config)
- **Classification:** Active Source

### `backend/attendance_service/`
- **Files:** 5 (`api.py`, `models.py`, `service.py`, `ui.py`, `__init__.py`)
- **Purpose:** Attendance service module (separate from `backend/services/attendance/`)
- **Classification:** Active Source
- **Note:** Naming conflict with `backend/services/attendance_service.py` at services root

### `backend/audit_service/`
- **Files:** 3 (`api.py`, `service.py`, `__init__.py`)
- **Purpose:** Audit service module
- **Classification:** Active Source

### `backend/cache/`
- **Files:** 1 (`cache.service.ts`)
- **Purpose:** Cache service
- **Classification:** Legacy / Misplaced (TypeScript file in Python backend)

### `backend/config/`
- **Files:** 1 (`config.py`)
- **Purpose:** Central configuration module
- **Classification:** Active Source

### `backend/core/`
- **Files:** 2 (`country_resolver.py`, `__init__.py`)
- **Purpose:** Core country-resolution logic
- **Classification:** Active Source

### `backend/country/`
- **Files:** 1 (`__init__.py`) + subdirs
- **Subdirs:** `base/` (5 .py), `dummy/` (5 .py), `pakistan/` (7 .py)
- **Purpose:** Country compliance adapter layer (Pakistan-specific tax, payroll, EOBI, FBR, PESSI adapters)
- **Classification:** Active Source

### `backend/db/`
- **Files:** 2 (`idempotency.py`, `optimization.ts`)
- **Purpose:** Database utilities — idempotency (Python), optimization (TypeScript)
- **Classification:** Active Source (Python) + Legacy/Misplaced (TypeScript)

### `backend/deployment/`
- **Files:** 19 across 3 subdirs
- **Subdirs:** `config/` (3 files: gateway-routes.json, postgres-init.sql, services.env), `frontend/` (1: index.html), `migrations/` (15: 001–015 SQL), `scripts/` (1: run-migrations.sh)
- **Also:** `migrate.py`, `qc_validate*.py` (5 files), `re_qc_validate*.py` (11 files), `repair_data_integrity.py`, `README.md`
- **Purpose:** Database migrations, QC validation scripts, deployment config
- **Classification:** Migration / Database + Script / Tooling

### `backend/docker/`
- **Files:** 3 (`common_service.py`, `api_gateway_service.py`, `service_runtime.py`)
- **Purpose:** ASGI service runtime — the core service dispatcher
- **Classification:** Active Source (critical — this is the main service runtime)

### `backend/docs/`
- **Files:** ~85 files across 6 subdirs + 1 root file
- **Subdirs:** `canon/` (14), `system/` (14 + archive/7), `services/` (29), `design/` (15), `reports/` (2), `specs/` (6)
- **Classification:** Legacy Documentation (canon, system) + Supporting Documentation (services, specs) + Historical Record (design, reports, archive)
- **See docs/09_normalization/ outputs for detail**

### `backend/health/`
- **Files:** 1 (`health.controller.ts`)
- **Classification:** Legacy / Misplaced (TypeScript in Python backend)

### `backend/integrations/`
- **Files:** 1 (`http_client.py`) + subdirs
- **Subdirs:** `accounting/` (1), `biometric/` (2), `pakistan/` (8), `whatsapp/` (2)
- **Purpose:** External integration adapters
- **Classification:** Active Source

### `backend/metrics/`
- **Files:** 1 (`metrics.ts`)
- **Classification:** Legacy / Misplaced (TypeScript in Python backend)

### `backend/middleware/`
- **Files:** 11 (all `.ts`: audit-store.ts, audit.ts, circuit-breaker.ts, error-handler.ts, logger.ts, rate-limit.ts, request-id.ts, retry.ts, tenant-context.ts, throttle.ts, validation.ts)
- **Purpose:** Express.js middleware (TypeScript) — from original TypeScript architecture
- **Classification:** Legacy (TypeScript remnants in Python backend)

### `backend/mobile/`
- **Files:** 3 (`contracts.py`, `session.py`, `__init__.py`) + subdirs
- **Subdirs:** `app/` (2: product.py, __init__.py)
- **Purpose:** Mobile gateway support
- **Classification:** Active Source

### `backend/script/`
- **Files:** 1 (`integrations.py`, `import_smoke.py`)
- **Wait — 2 files found (integrations.py from integrations folder, import_smoke.py from script)**
- **Classification:** Script / Tooling

### `backend/services/`
- **Files:** 35 .py + 49 .ts (total across all subdirs)
- **Python:** services at root + `ai/` (3), `analytics/` (3), `attendance/` (2), `auth-service/` (2), `finance/` (2), `governance/` (1), `hiring_service/` (2), `payroll/` (1), `performance/` (1), `product/` (3), `recruitment/` (1), `settings` TBD
- **TypeScript (Legacy):** `employee-service/` (43 .ts files), `settings-service/` (6 .ts files)
- **Root-level .py files:** `attendance_service.py`, `compliance_autopilot.py`, `compliance_service.py`, `decision_engine.py`, `experience_layer_service.py`, `mobile_gateway.py`, `payroll_policy_engine.py`, `payroll_service.py`
- **Classification:** Active Source (Python) + Legacy (TypeScript)

### `backend/tests/`
- **Files:** 85 files (83 test .py + `conftest.py` + `__init__.py`) across root + `api/` + `unit/`
- **Classification:** Test Asset

### `backend/ui/`
- **Files:** 105 files (Next.js/React application: .tsx, .ts, .css, .json, .mjs)
- **Purpose:** The Meridian HCM Next.js 15 frontend application
- **Classification:** Active Source (Frontend)
- **Note:** Frontend app living inside `backend/` directory — significant structural issue

### `backend/.venv/`, `backend/Lib/`, `backend/Scripts/`
- **Files:** Many (Python virtual environment)
- **Classification:** Generated Artifact (should be git-ignored)
- **Note:** `.gitignore` lists these as ignored but they appear to be present in the working tree

### `backend/.pytest_cache/`
- **Files:** 5
- **Classification:** Generated Artifact (should be git-ignored)

### `backend/__pycache__/` (and all sub-__pycache__)
- **Dirs:** 206 `__pycache__` directories
- **Files:** 2,308 `.pyc` compiled bytecode files
- **Classification:** Generated Artifact (should be git-ignored)

### `backend/.github/workflows/`
- **Files:** 3 (`build.yml`, `deploy.yml`, `test.yml`)
- **Classification:** Configuration / Infrastructure
- **Note:** Separate from root-level `.github/workflows/ci.yml` — duplicate CI location

---

## DOCS/ DETAIL

| Subfolder | Files | Status | Notes |
|-----------|-------|--------|-------|
| `docs/00_authority/` | 5 | Active Authority | DOMAIN_MODEL, FEATURE_SCOPE, PRODUCT_WORKFLOWS, PROJECT_CHARTER, FULLSTACK_STITCHING_CONTRACT |
| `docs/01_backend/` | 8 | Active Authority | API_CONTRACT, BACKEND_ARCHITECTURE, DATABASE_SCHEMA, ERROR_CONTRACT, EVENT_AND_QUEUE_ARCHITECTURE, INTEGRATION_CATALOG, SERVICE_CATALOG, VALIDATION_RULES |
| `docs/02_frontend/` | 0 | **EMPTY** | Authority gap D-022 |
| `docs/03_fullstack_contracts/` | 5 | Active Authority | AUTH_AND_TENANCY_CONTRACT, CONTRACT_VERSION_REGISTRY, DATA_SHAPE_REGISTRY, USER_ROLES_AND_PERMISSIONS, VALIDATION_PARITY |
| `docs/04_testing/` | 0 | **EMPTY** | Authority gap D-026 |
| `docs/05_deployment/` | 0 | **EMPTY** | Authority gap D-025 |
| `docs/06_decisions/` | 1 | Active Authority | ADR-001_PROJECT_FOUNDATION |
| `docs/07_governance/` | 2 | Active Authority | AI_OPERATING_CONTEXT, DECISION_ESCALATION_MATRIX |
| `docs/08_reports/` | 14 | Generated Report | All backend authority capture reports |
| `docs/09_normalization/` | 7 | Generated Report | All normalization phase outputs |
| `docs/10_repo_audit/` | 9 (this run) | Generated Report | This audit's outputs |

---

## SUMMARY COUNTS

| Area | Folders | Source Files | Doc Files | Notes |
|------|---------|-------------|-----------|-------|
| Root | 1 | 0 | 6 | + 1 .lnk shortcut |
| `.github/` | 1 | 0 | 1 | CI workflow |
| `backend/` | 100+ | 272 py + 105 tsx/ts | ~85 | + 49 ts legacy + 2308 .pyc generated |
| `contracts/` | 0 | 0 | 47 | JSON UI specs |
| `design/` | 0 | 0 | 10 | Design authority |
| `docs/` | 10 | 0 | 43 | Authority framework |
| `frontend/` | 2 | 0 | 62 | HTML wireframes |
| `ops/` | 0 | 1 | 9 | Ops artifacts |
| **Total** | | **~650 source** | **~258 doc** | |
