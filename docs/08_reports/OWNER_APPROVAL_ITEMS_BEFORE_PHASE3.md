# OWNER APPROVAL ITEMS BEFORE PHASE 3

Status: Active — Awaiting Owner Decision
Created: 2026-06-16
Phase: Pre-Frontend Doc-to-Code Delta Audit and Remediation

---

## PURPOSE

Registers every item identified during the pre-frontend delta audit and prior repository audit phases that requires an owner decision before proceeding. These items involve source code changes, configuration decisions, or file operations that are beyond safe documentation corrections.

Items are ordered: code-related first (from delta audit), then repository-structural (from repo audit phase).

---

## DELTA AUDIT ITEMS

### OA-001 — Remove dead function `_employee_domain_departments()` from service_runtime.py

| Attribute | Detail |
|---|---|
| **Issue** | `backend/docker/service_runtime.py` lines 132–218 contains `_employee_domain_departments()`, a 87-line function that parses `domain-seed.ts` and returns fallback department dicts. This function was used by the old inline employee-service stub. The new Python employee-service block (lines 445–469) uses `EmployeeService` directly and does not call `_employee_domain_departments()`. The function has no callers. |
| **Evidence** | `service_runtime.py` line 132: `def _employee_domain_departments():`. Grep for `_employee_domain_departments` in `backend/` returns only the function definition — zero call sites. |
| **Options** | A) Delete lines 132–218 from `service_runtime.py`. B) Leave in place (no functional impact — dead code). |
| **Risk** | Option A: Low risk — no callers exist. Reduces `service_runtime.py` from 595 to 508 lines and removes the `domain-seed.ts` parsing logic that implies a TypeScript dependency. Option B: Zero runtime risk, ongoing cognitive overhead. |
| **Recommendation** | Option A — delete. The function serves no purpose and increases reader confusion about TypeScript dependencies in a Python runtime file. |
| **Source** | DELTA-012 in `docs/08_reports/DOC_TO_CODE_DELTA_MATRIX.md` |

---

### OA-002 — Update legacy product name "Aura HRMS" in OpenAPI spec

| Attribute | Detail |
|---|---|
| **Issue** | `backend/docker/api_gateway_service.py` line 207 and line 237 use `"Aura HRMS API"` and `"Aura HRMS API Docs"` as the OpenAPI spec title and Swagger UI page title. The current product name per `docs/00_authority/PROJECT_CHARTER.md` is "Meridian HCM". These strings appear in the public `/openapi.json` and `/docs` routes, visible to any API consumer or developer. |
| **Evidence** | `api_gateway_service.py` line 207: `"title": "Aura HRMS API"`. Line 237: `"title": "Aura HRMS API Docs"`. `docs/00_authority/PROJECT_CHARTER.md`: product name is "Meridian HCM". |
| **Options** | A) Change both strings to `"Meridian HCM API"` and `"Meridian HCM API Docs"`. B) Leave as-is (legacy name persists in public-facing spec). |
| **Risk** | Option A: Cosmetic change only. No functional impact. Breaks no tests unless tests assert the exact API title string. Option B: Legacy name persists in all developer-facing API documentation. |
| **Recommendation** | Option A — update both strings. The naming inconsistency is visible to frontend developers consuming the API spec. |
| **Source** | DELTA-013 in `docs/08_reports/DOC_TO_CODE_DELTA_MATRIX.md` |

---

## REPOSITORY STRUCTURE ITEMS

These items were identified in the repository audit phase (`docs/10_repo_audit/OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md` or `REPOSITORY_RESTRUCTURING_PLAN.md`). They are carried forward here for consolidated owner review.

### OA-003 — Relocate Next.js frontend from `backend/ui/` to `frontend/`

| Attribute | Detail |
|---|---|
| **Issue** | The active Next.js 15 frontend app lives at `backend/ui/` (105+ files, Next.js app router, package.json). This is inside the `backend/` directory, which is conceptually and structurally wrong. The docker-compose service is named `frontend-ui` and maps to `context: ./backend/ui`. |
| **Evidence** | `backend/ui/package.json`, `backend/docker-compose.yml` lines 445–458, `docs/10_repo_audit/CODEBASE_PLACEMENT_AUDIT.md` CP-001 |
| **Options** | A) Move `backend/ui/` → `frontend/` at repo root; update `docker-compose.yml` build context; rename existing `frontend/` (wireframes) to `frontend-wireframes/`. B) Leave structure as-is and document the non-standard placement. |
| **Risk** | Option A: Path changes must propagate to `docker-compose.yml`, any import paths, and CI configs. Existing `frontend/` (62 HTML wireframes) must be renamed first. Medium effort. Option B: Continues to confuse contributors and any CI tooling that makes assumptions about frontend/backend separation. |
| **Recommendation** | Option A — relocate to repo root. This unblocks a clean Frontend Authority Capture (Phase 3). |
| **Source** | `docs/10_repo_audit/CODEBASE_PLACEMENT_AUDIT.md` CP-001; `docs/10_repo_audit/REPOSITORY_RESTRUCTURING_PLAN.md` item A |

---

### OA-004 — Archive TypeScript dead code: `backend/services/employee-service/` (43 files)

| Attribute | Detail |
|---|---|
| **Issue** | `backend/services/employee-service/` contains 43 TypeScript files (controllers, models, repositories, routes, validators, tests). These are superseded by the Python implementation in `backend/employee_service.py` + `backend/employee_api.py`. No Python runtime imports them. They cannot run in the Python ASGI runtime. |
| **Evidence** | `backend/docker/service_runtime.py` lines 445–469: imports from `employee_service` and `employee_api` (Python). `backend/services/employee-service/*.ts`: TypeScript, not importable by Python. `docs/10_repo_audit/LEGACY_AND_ARCHIVE_PLAN.md` LC-001. |
| **Options** | A) Move to `backend/docs/system/archive/typescript-employee-service/` (preserves for reference). B) Delete. |
| **Risk** | Option A: No functional risk. Preserves the TypeScript design for reference. Option B: Irreversible loss — confirm TypeScript is truly no longer needed before deleting. |
| **Recommendation** | Option A — archive. Preserves the design history without cluttering the active source tree. |
| **Source** | `docs/10_repo_audit/LEGACY_AND_ARCHIVE_PLAN.md` LC-001; `docs/10_repo_audit/CODEBASE_PLACEMENT_AUDIT.md` CP-002 |

---

### OA-005 — Verify and archive TypeScript dead code: `backend/services/settings-service/` (6 files)

| Attribute | Detail |
|---|---|
| **Issue** | `backend/services/settings-service/` contains 6 TypeScript files (`settings.controller.ts`, `settings.model.ts`, `settings.repository.ts`, `settings.routes.ts`, `settings.service.ts`, `settings.validation.ts`). The runtime uses an inline dict stub (OA-002 above). Whether the TypeScript was ever the production implementation is unclear. |
| **Evidence** | `backend/docker/service_runtime.py` lines 324–342: inline dict stub, no module imports. `docs/10_repo_audit/LEGACY_AND_ARCHIVE_PLAN.md` LC-002. |
| **Options** | A) Archive to `backend/docs/system/archive/typescript-settings-service/`. B) Promote the TypeScript design to a persistent Python settings-service implementation (future work). C) Delete. |
| **Risk** | The TypeScript files document the intended persistent settings API. Archiving preserves this for when a real settings-service is built. |
| **Recommendation** | Option A — archive pending a proper persistent settings-service implementation. |
| **Source** | `docs/10_repo_audit/LEGACY_AND_ARCHIVE_PLAN.md` LC-002 |

---

### OA-006 — Archive TypeScript middleware dead code: `backend/middleware/` (11 files)

| Attribute | Detail |
|---|---|
| **Issue** | `backend/middleware/` contains 11 TypeScript Express middleware files: `audit-store.ts`, `audit.ts`, `circuit-breaker.ts`, `error-handler.ts`, `logger.ts`, `rate-limit.ts`, `request-id.ts`, `retry.ts`, `tenant-context.ts`, `throttle.ts`, `validation.ts`. Python equivalents are in `resilience.py`, `rate_limiting.py`, `structured_logging.py`, `jwt_utils.py`. |
| **Evidence** | `docs/01_backend/BACKEND_ARCHITECTURE.md` §5; `docs/10_repo_audit/CODEBASE_PLACEMENT_AUDIT.md` CP-003; `docs/10_repo_audit/LEGACY_AND_ARCHIVE_PLAN.md` LC-003. |
| **Options** | A) Archive to `backend/docs/system/archive/typescript-middleware/`. B) Delete. |
| **Risk** | These files may still have reference value for understanding the original middleware design. Archiving is safer. |
| **Recommendation** | Option A — archive. |
| **Source** | `docs/10_repo_audit/LEGACY_AND_ARCHIVE_PLAN.md` LC-003 |

---

### OA-007 — Consolidate duplicate CI/CD workflow locations

| Attribute | Detail |
|---|---|
| **Issue** | CI/CD workflow files exist in two locations: root `.github/workflows/` (which GitHub Actions executes) and `backend/.github/workflows/` (which GitHub Actions never executes — hidden by being inside a subdirectory). |
| **Evidence** | `docs/10_repo_audit/CODEBASE_PLACEMENT_AUDIT.md` CP-009. |
| **Options** | A) Review `backend/.github/workflows/*.yml` files against root `.github/workflows/` — merge any missing workflows and delete `backend/.github/workflows/`. B) Leave both in place (duplicates never execute). |
| **Risk** | If `backend/.github/workflows/` contains any unique CI steps not in the root, those steps are silently never executing. Option A requires reading both sets to compare. |
| **Recommendation** | Option A — merge and delete. Silently-inactive CI configs are a maintenance hazard. |
| **Source** | `docs/10_repo_audit/CODEBASE_PLACEMENT_AUDIT.md` CP-009; `docs/10_repo_audit/REPOSITORY_RESTRUCTURING_PLAN.md` item G |

---

### OA-008 — Resolve naming conflict: `backend/attendance_service/` vs `backend/services/attendance_service.py`

| Attribute | Detail |
|---|---|
| **Issue** | `backend/attendance_service/` is a directory (the active attendance-service Python package: `api.py`, `service.py`, `models.py`, etc.). `backend/services/attendance_service.py` is a separate file. The naming overlap risks import confusion. |
| **Evidence** | `docs/10_repo_audit/CODEBASE_PLACEMENT_AUDIT.md` CP-006. |
| **Options** | A) Read `backend/services/attendance_service.py` to confirm its role; if it is a duplicate/stub, delete or archive. B) Rename one to avoid ambiguity. |
| **Risk** | Unknown until `backend/services/attendance_service.py` is read. |
| **Recommendation** | Read the file first, then decide. |
| **Source** | `docs/10_repo_audit/CODEBASE_PLACEMENT_AUDIT.md` CP-006 |

---

### OA-009 — Delete root shortcut `(C) Phoenix LiteOS.lnk`

| Attribute | Detail |
|---|---|
| **Issue** | A Windows shortcut file `(C) Phoenix LiteOS.lnk` exists at the repository root. It is an OS artifact unrelated to the project. |
| **Evidence** | `docs/10_repo_audit/ROOT_LEVEL_CLEANUP_PLAN.md`. |
| **Options** | A) Delete the file. B) Add to `.gitignore`. |
| **Risk** | Option A: No risk — clearly not a project file. |
| **Recommendation** | Option A — delete. If tracked in git, also add `*.lnk` to `.gitignore`. |
| **Source** | `docs/10_repo_audit/ROOT_LEVEL_CLEANUP_PLAN.md` |

---

### OA-010 — Add root `.gitignore` and root `README.md`

| Attribute | Detail |
|---|---|
| **Issue** | No `.gitignore` exists at the repository root. Python bytecode (`__pycache__/`, `*.pyc`), the virtual environment (`backend/.venv/`, `backend/Lib/`, `backend/Scripts/`), and pytest caches are present but unignored at the root level. No `README.md` exists at the repo root. |
| **Evidence** | `docs/10_repo_audit/REPOSITORY_NORMALIZATION_REPORT.md` SI-007. |
| **Options** | Create root `.gitignore` (Python + Node standard patterns) and a minimal `README.md` with project name, structure overview, and dev setup link. |
| **Risk** | None — purely additive. |
| **Recommendation** | Create both. The `.gitignore` is particularly important to prevent generated artifacts from being committed. |
| **Source** | `docs/10_repo_audit/REPOSITORY_NORMALIZATION_REPORT.md` SI-007 |

---

## SUMMARY TABLE

| ID | Category | Risk | Effort | Recommendation |
|----|----------|------|--------|----------------|
| OA-001 | Dead code removal | Low | Minutes | Delete |
| OA-002 | Code name correction | Cosmetic | Minutes | Update strings |
| OA-003 | Frontend relocation | Medium | Hours | Move `backend/ui/` → `frontend/` |
| OA-004 | TypeScript archive (employee-service) | Low | Minutes | Archive |
| OA-005 | TypeScript archive (settings-service) | Low | Minutes | Archive |
| OA-006 | TypeScript archive (middleware) | Low | Minutes | Archive |
| OA-007 | CI/CD consolidation | Medium | Hours | Merge and delete duplicate |
| OA-008 | Naming conflict resolution | Low | Minutes | Read file first |
| OA-009 | Delete OS artifact | None | Seconds | Delete |
| OA-010 | Add root .gitignore + README.md | None | Minutes | Create both |
