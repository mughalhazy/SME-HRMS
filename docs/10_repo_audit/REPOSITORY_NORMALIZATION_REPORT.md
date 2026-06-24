# REPOSITORY NORMALIZATION REPORT

Status: Active
Created: 2026-06-16
Phase: Full Repository Normalization and Reality Audit

---

## EXECUTIVE SUMMARY

This report synthesizes the findings from the Full Repository Normalization and Reality Audit. The audit inventoried the entire repository tree, classified every meaningful folder and file type, and identified structural issues across documentation, source code, configuration, and generated artifacts.

**Headline findings:**

- Repository contains approximately **650+ source files** and **258+ documentation files** across 9 major top-level folders
- The **documentation framework (`docs/`)** is correctly structured and complete for established domains — 3 of 10 subdirs are intentionally empty (awaiting future authority capture phases)
- The **Python backend is the authoritative runtime** — 272 Python source files across 24 microservices + infrastructure
- **49 TypeScript legacy files** remain in the Python backend from the original TypeScript architecture — all are dead code (except possibly settings-service)
- **The Next.js frontend application** (`backend/ui/`, 105 files) is buried inside `backend/` — the most significant structural issue in the repository
- **2,308 compiled `.pyc` files** and a Python virtual environment are present — correctly listed in `.gitignore` but not yet excluded (no git history exists yet)
- **6 session mandate `.md` files** clutter the repository root
- **3 docs/ subdirs are empty** (`docs/02_frontend/`, `docs/04_testing/`, `docs/05_deployment/`) — correctly reserved for future authority capture phases

---

## 1. REPOSITORY REALITY vs DOCUMENTATION

### What documentation says:

The documentation framework (especially `docs/01_backend/SERVICE_CATALOG.md`) describes a clean Python microservices backend with 24 services.

### What reality shows:

| Reality Finding | Documentation State |
|-----------------|---------------------|
| 24 Python microservices ✅ | Correctly documented |
| Python service files split between `backend/` root and `backend/services/` root | Not documented — fragmented layout |
| TypeScript remnants (49 files) in Python backend | CON-001 in CONFLICT_ANALYSIS_REPORT.md — service-manifest.md falsely claims TypeScript employee-service |
| Next.js frontend app at `backend/ui/` | No documentation describes this location |
| HTML wireframes at `frontend/pages/` | Not documented as "wireframes" — name suggests it's the frontend app |
| CI workflows at two locations (`backend/.github/` and root `.github/`) | Not documented |
| 15 SQL migrations at `backend/deployment/migrations/` | Correctly documented in `docs/01_backend/DATABASE_SCHEMA.md` |
| 85 test files at `backend/tests/` | Not covered by any test strategy document (`docs/04_testing/` is empty) |

---

## 2. STRUCTURAL ISSUES — RANKED BY IMPACT

### SI-001: Frontend Application Location (Critical)

**`backend/ui/`** is the 105-file Next.js 15 frontend application. It lives inside `backend/`, which is the Python microservices directory. This creates:
- Invisible frontend at root navigation
- `frontend/` folder name falsely suggests the app is there (it contains HTML wireframes)
- Dockerfile.ui at `backend/` root references `backend/ui/` — works but is non-standard
- Future frontend developer onboarding confusion

**Fix:** Move `backend/ui/` → `frontend/` (requires owner approval — see CODEBASE_PLACEMENT_AUDIT.md CP-001).

---

### SI-002: TypeScript Dead Code in Python Backend (High)

49 TypeScript files remain from the original architecture:
- `backend/services/employee-service/` (43 files) — superseded by Python
- `backend/services/settings-service/` (6 files) — status uncertain
- `backend/middleware/` (11 files) — superseded by Python equivalents
- Isolated `.ts` files in `backend/cache/`, `backend/health/`, `backend/metrics/`, `backend/db/`

**Fix:** Archive TypeScript files per LEGACY_AND_ARCHIVE_PLAN.md (requires owner approval).

---

### SI-003: Root-Level Clutter (Medium)

6 session execution mandate `.md` files at repository root, plus a Windows shortcut (`.lnk` file). Root should contain only standard project files (README, .gitignore, etc.).

**Fix:** Move mandate files to `docs/mandates/` (safe, immediate). Owner approval needed for `.lnk` deletion.

---

### SI-004: Empty Authority Folders (Low — Intentional)

`docs/02_frontend/`, `docs/04_testing/`, `docs/05_deployment/` are empty. This is correct per phase plan — they await their respective authority capture phases.

**No action needed.** Empty folders are correctly reserved.

---

### SI-005: Duplicate CI Workflow Locations (Medium)

- Root `.github/workflows/ci.yml` — executes on GitHub
- `backend/.github/workflows/build.yml`, `deploy.yml`, `test.yml` — **never execute** on GitHub

**Fix:** Requires owner approval — either consolidate into root or explicitly document backend workflows as reference-only.

---

### SI-006: Python Service Files Split Between Two Locations (Medium)

Python services are split:
- `backend/*.py` — primary location (60+ service files)
- `backend/services/` root-level `.py` — secondary location (8 service files: `attendance_service.py`, `compliance_service.py`, etc.)
- `backend/services/*/` subdirs — sub-modules (ai, analytics, attendance, finance, governance, etc.)

This creates a 3-level service hierarchy that is undocumented. `SERVICE_CATALOG.md` does not map which service names correspond to which file locations.

**Fix:** Document the layout in `docs/01_backend/SERVICE_CATALOG.md`. Long-term consolidation into a single service layer requires owner decision.

---

### SI-007: No Root README or Root .gitignore (Medium)

The repository root has no `README.md` and no `.gitignore`. The backend has both. When this project is initialized as a git repository:
- Generated artifacts (`.venv/`, `Lib/`, `__pycache__/`) will need root-level exclusion
- `.claude/` memory files should be excluded
- A root README should orient new contributors

**Fix:** Create root `README.md` and root `.gitignore` (safe, immediate — no code impact).

---

## 3. DOCUMENTATION LAYER STATUS

| Layer | Status | Notes |
|-------|--------|-------|
| Governance Authority (`docs/00_authority/`) | ✅ Complete | 5 authority docs |
| Backend Authority (`docs/01_backend/`) | ✅ Complete | 8 authority docs |
| Frontend Authority (`docs/02_frontend/`) | ⬜ Empty | Awaiting Frontend Authority Capture |
| Fullstack Contracts (`docs/03_fullstack_contracts/`) | ✅ Complete | 5 contract docs |
| Testing Authority (`docs/04_testing/`) | ⬜ Empty | Awaiting Testing Authority Capture |
| Deployment Authority (`docs/05_deployment/`) | ⬜ Empty | Awaiting Deployment Authority Capture |
| Decision Records (`docs/06_decisions/`) | 🔶 Partial | ADR-001 only; 5 informal decisions in ops/answers.md |
| Governance (`docs/07_governance/`) | ✅ Complete | 2 docs |
| Reports (`docs/08_reports/`) | ✅ Complete | 14 reports |
| Normalization (`docs/09_normalization/`) | ✅ Complete | 7 outputs |
| Repo Audit (`docs/10_repo_audit/`) | ✅ Complete (this run) | 9 outputs |
| Mandates (`docs/mandates/`) | ⬜ Missing | Needs to be created; 6 root mandate files should move here |
| Legacy Canon (`backend/docs/`) | 🟡 Retirement pending | Annotations not yet applied |

---

## 4. SOURCE CODE STATUS

| Area | Status | Notes |
|------|--------|-------|
| Python microservices (24 services) | ✅ Active | 272 .py source files |
| API Gateway | ✅ Active | `backend/docker/` + `backend/api-gateway/` |
| Next.js frontend | ✅ Active | `backend/ui/` — misplaced but functional |
| Test suite | ✅ Active | 85 test files in `backend/tests/` |
| Database migrations | ✅ Active | 15 SQL files in `backend/deployment/migrations/` |
| QC validation scripts | ✅ Active | 17 files in `backend/deployment/` |
| Pakistan country adapters | ✅ Active | `backend/country/`, `backend/integrations/pakistan/` |
| TypeScript legacy (employee-service) | ❌ Dead | 43 .ts files — superseded by Python |
| TypeScript legacy (middleware) | ❌ Dead | 11 .ts files — superseded by Python |
| TypeScript legacy (settings-service) | ❓ Uncertain | 6 .ts files — Python counterpart unconfirmed |
| Python venv / compiled bytecode | 🚫 Build output | 2308+ files — correctly gitignored |

---

## 5. SAFE ACTIONS RECOMMENDED FOR IMMEDIATE EXECUTION

These actions have zero code impact and zero runtime risk:

| # | Action | Outcome |
|---|--------|---------|
| 1 | Create `docs/mandates/` directory | Clean location for mandate files |
| 2 | Move 6 root mandate `.md` files → `docs/mandates/` | Clean root level |
| 3 | Create root `README.md` | Project entry point |
| 4 | Apply retirement annotations to `backend/docs/canon/` (per RETIREMENT_PLAN.md) | Legacy docs marked |
| 5 | Apply retirement annotations to `backend/docs/system/` (per RETIREMENT_PLAN.md) | Legacy docs marked |
| 6 | Move `ops/hrms-audit-v1.py` → `backend/script/` | Script in correct location |
| 7 | Move `design/hrms-ui-backend-gaps.md` → `docs/08_reports/` | Report in correct location |
| 8 | Move design SOPs → `docs/mandates/` (3 files: build-protocol, stabilisation, claude-code-prompt) | Documentation clean-up |
| 9 | Annotate `ops/normalisation-tracker.md` and `ops/tracker.md` as completed | Operational cleanup |
| 10 | Update `docs/00_authority/DOMAIN_MODEL.md` "57+" → "58 tables" | Minor CON-004 fix |

---

## 6. OWNER APPROVAL ACTIONS (no code changes without approval)

| # | Action | Impact Assessment |
|---|--------|------------------|
| A | Move `backend/ui/` → `frontend/` | Touches Dockerfile.ui, CI paths, build scripts |
| B | Rename `frontend/` → `frontend-wireframes/` | Paired with action A |
| C | Archive TypeScript employee-service (43 .ts) | Dead code — but irreversible |
| D | Archive TypeScript settings-service (6 .ts) | Verify Python counterpart first |
| E | Archive TypeScript middleware (11 .ts + 4 isolated files) | Confirm Python coverage |
| F | Consolidate `backend/.github/` into root `.github/` | CI change |
| G | Delete `(C) Phoenix LiteOS.lnk` | Irreversible |
| H | Create root `.gitignore` | Low impact but structural |
| I | Move `backend/test_payroll_service.py` → `backend/tests/` | May affect pytest discovery |
| J | Resolve `backend/attendance_service/` vs `backend/services/attendance_service.py` | Runtime behavior |

---

## 7. READINESS FOR FRONTEND AUTHORITY CAPTURE

**Current blockers:**
1. `docs/02_frontend/` is empty — normal (authority docs don't exist yet)
2. `backend/ui/` location needs resolution (CP-001) — **this should be resolved before frontend work begins**
3. `frontend/` name is misleading — renaming clarifies what "frontend" means in this project

**Pre-conditions for Frontend Authority Capture (recommended):**
- [ ] Resolve CP-001: clarify `backend/ui/` vs `frontend/` structure
- [ ] Move or at least confirm location of Next.js app as the canonical frontend
- [ ] Establish `docs/02_frontend/` as the authority target for upcoming work

**Not blocking but recommended:**
- [ ] Archive TypeScript dead code (CP-002 through CP-004)
- [ ] Move design authority docs to staging position in `design/` (already there)

---

## 8. AUDIT SUCCESS CRITERIA VERIFICATION

Per mandate success criteria:

| Criterion | Status |
|-----------|--------|
| Every root folder accounted for | ✅ |
| Every major subfolder accounted for | ✅ |
| Every major file type accounted for | ✅ |
| `docs/` normalized | ✅ |
| Backend source structure understood | ✅ |
| Scripts/tooling classified | ✅ |
| Tests classified | ✅ |
| Configs/infra classified | ✅ |
| Generated artifacts classified | ✅ |
| Legacy folders classified | ✅ |
| Root-level clutter identified | ✅ |
| Duplicate folder purposes identified | ✅ |
| Misplaced documents/files identified | ✅ |
| No frontend authority capture started | ✅ |
| Stopped after audit + safe restructuring + reporting | ✅ |
