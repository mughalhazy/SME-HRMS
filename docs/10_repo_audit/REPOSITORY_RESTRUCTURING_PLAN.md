# REPOSITORY RESTRUCTURING PLAN

Status: Active
Created: 2026-06-16
Phase: Full Repository Normalization and Reality Audit

---

## OBJECTIVE

Propose a clean repository structure that eliminates confusion, correctly separates concerns, and positions the project for Frontend Authority Capture and future phases.

Per mandate: do not over-engineer. Keep it practical.

---

## CURRENT STRUCTURE PROBLEMS (SUMMARY)

1. **Frontend app buried inside `backend/`** — `backend/ui/` is the Next.js application but is invisible at root
2. **`frontend/` is misleadingly named** — contains HTML wireframe archives, not the application
3. **6 mandate .md files at root** — pollute the project entry point
4. **TypeScript dead code scattered** — 49 .ts legacy files in Python backend folders
5. **Two `.github/workflows/` locations** — root one runs; backend one does nothing
6. **`design/` folder not in docs framework** — contains authority docs outside their designated home
7. **Service source split** — Python services are split between `backend/` root and `backend/services/` root (fragmented service locations)
8. **`contracts/` folder** — UI contract JSONs have no clear home in docs framework
9. **Missing root files** — No root README.md, no root .gitignore

---

## PROPOSED CLEAN STRUCTURE

```
D:\SaaS\HRMS\
│
├── .claude/                     ← tool memory (unchanged)
├── .github/                     ← GitHub CI/CD (keep root only)
│   └── workflows/
│       ├── ci.yml               ← existing
│       ├── build.yml            ← merge from backend/.github/ (OWNER APPROVAL)
│       ├── deploy.yml           ← merge from backend/.github/ (OWNER APPROVAL)
│       └── test.yml             ← merge from backend/.github/ (OWNER APPROVAL)
│
├── backend/                     ← Python microservices runtime
│   ├── [*.py service files]     ← keep all Python source as-is
│   ├── api/                     ← keep
│   ├── api-gateway/             ← keep
│   ├── attendance_service/      ← keep (resolve CP-006 naming)
│   ├── audit_service/           ← keep
│   ├── config/                  ← keep
│   ├── core/                    ← keep
│   ├── country/                 ← keep (Pakistan adapters)
│   ├── db/                      ← keep (idempotency.py; move optimization.ts to archive)
│   ├── deployment/              ← keep (migrations + QC + config)
│   ├── docker/                  ← keep (service_runtime.py — critical)
│   ├── docs/                    ← keep (legacy canon; annotate as retired)
│   ├── integrations/            ← keep
│   ├── mobile/                  ← keep
│   ├── script/                  ← keep (+ receive hrms-audit-v1.py from ops/)
│   ├── services/                ← keep Python subdirs; archive TypeScript subdirs
│   ├── tests/                   ← keep (receive test_payroll_service.py from root)
│   ├── Dockerfile*, docker-compose.yml, requirements.txt, etc.
│   └── [NO ui/ — moved to frontend/]
│
├── contracts/                   ← UI JSON contracts (keep location; add to docs index)
│
├── design/                      ← UI design system (keep until Frontend Authority Capture)
│
├── docs/                        ← authority documentation framework
│   ├── 00_authority/            ← governance authority (complete)
│   ├── 01_backend/              ← backend authority (complete)
│   ├── 02_frontend/             ← EMPTY → populate during Frontend Authority Capture
│   ├── 03_fullstack_contracts/  ← fullstack contracts (complete)
│   ├── 04_testing/              ← EMPTY → populate during Testing Authority Capture
│   ├── 05_deployment/           ← EMPTY → populate during Deployment Authority Capture
│   ├── 06_decisions/            ← ADRs (ADR-001 exists; ADR-002+ pending)
│   ├── 07_governance/           ← AI context, escalation matrix
│   ├── 08_reports/              ← backend authority capture reports
│   ├── 09_normalization/        ← normalization phase outputs
│   ├── 10_repo_audit/           ← this audit's outputs
│   └── mandates/                ← NEW: receive 6 root-level mandate .md files
│
├── frontend/                    ← Next.js 15 application (moved from backend/ui/)
│   ├── app/                     ← Next.js App Router pages
│   ├── components/              ← React components
│   ├── lib/                     ← API clients, auth, utilities
│   ├── styles/                  ← CSS
│   ├── package.json             ← Next.js dependencies
│   ├── next.config.ts
│   ├── tsconfig.json
│   ├── .env.example
│   └── .gitignore
│
├── frontend-wireframes/         ← Renamed from frontend/ (HTML archetype wireframes)
│   ├── pages/                   ← h01–h13 HTML wireframes
│   └── seeds/                   ← p1–p13 HTML seed templates
│
├── ops/                         ← operational session artifacts (keep as-is)
│
├── README.md                    ← NEW root project readme
└── .gitignore                   ← NEW root gitignore
```

---

## RESTRUCTURING ACTIONS

### SAFE TO EXECUTE NOW

| # | Action | Type |
|---|--------|------|
| 1 | Create `docs/mandates/` directory | Documentation |
| 2 | Move 6 root mandate `.md` files → `docs/mandates/` | Documentation move |
| 3 | Move `ops/hrms-audit-v1.py` → `backend/script/hrms-audit-v1.py` | Script move |
| 4 | Apply retirement annotations per DOCUMENT_RETIREMENT_PLAN.md | Documentation annotation |
| 5 | Move `ops/hrms-audit-manifest-v1.json` → `docs/08_reports/` | Documentation move |
| 6 | Move `design/hrms-ui-backend-gaps.md` → `docs/08_reports/` | Documentation move |
| 7 | Move `design/hrms-build-protocol-sop-v1.md` → `docs/mandates/` | Documentation move |
| 8 | Move `design/hrms-stabilisation-sop-v1.md` → `docs/mandates/` | Documentation move |
| 9 | Move `design/hrms-claude-code-prompt-v1.md` → `docs/mandates/` | Documentation move |
| 10 | Create root `README.md` (minimal, 1 page) | Documentation create |

### REQUIRES_OWNER_APPROVAL

| # | Action | Why Owner Must Decide |
|---|--------|----------------------|
| A | Move `backend/ui/` → `frontend/` | Affects `Dockerfile.ui`, CI paths, build scripts, Next.js config. Must verify all references to `backend/ui` before moving. |
| B | Rename current `frontend/` → `frontend-wireframes/` | Paired with action A; cosmetic but part of the same restructure |
| C | Archive `backend/services/employee-service/` (43 .ts) | Dead code removal — confirm before archiving |
| D | Archive `backend/services/settings-service/` (6 .ts) | Verify no active use first |
| E | Archive `backend/middleware/*.ts` (11 .ts) | Confirm Python equivalents cover all functionality |
| F | Archive `backend/cache/`, `backend/health/`, `backend/metrics/`, `backend/db/optimization.ts` | Confirm Python equivalents |
| G | Merge `backend/.github/workflows/` → root `.github/workflows/` | CI change — must verify workflow content doesn't conflict |
| H | Delete `(C) Phoenix LiteOS.lnk` at root | Irreversible |
| I | Resolve `backend/attendance_service/` vs `backend/services/attendance_service.py` conflict | Code change — affects runtime behavior |
| J | Move `backend/test_payroll_service.py` → `backend/tests/` | May affect pytest import paths |
| K | Create root `.gitignore` | Verify covers .claude/, .venv/, generated artifacts |

---

## PRIORITY ORDER FOR EXECUTION

**Phase A (Safe — do now):**
Execute actions 1–10 above. Zero code impact. Zero runtime impact.

**Phase B (Owner approval — before Frontend Authority Capture):**
Complete actions A–B (frontend move) and C–F (TypeScript archive) first. The frontend folder structure confusion should be resolved before frontend work begins.

**Phase C (Owner approval — before git initialization):**
Complete action G (CI consolidation) and K (root .gitignore) before creating the git repository.

**Phase D (Post-Frontend Authority Capture):**
Move `design/hrms-archetype-system-v1.md`, `hrms-api-contracts.md`, `hrms-doc-catalogue-v1.md`, `hrms-contract-structure-v1.md`, `hrms-design-register-v1.md` → `docs/02_frontend/`.

---

## WHAT MUST NOT CHANGE

The following must not move without careful dependency analysis:

| Item | Reason |
|------|--------|
| `backend/docker/service_runtime.py` | Critical — registers all service routes |
| `backend/docker/api_gateway_service.py` | Gateway entry point |
| `backend/*.py` service files | All Python service files at backend root |
| `backend/deployment/migrations/` | Migration files — path referenced by migrate.py |
| `backend/tests/` | Test discovery paths in pytest.ini |
| `backend/country/`, `backend/integrations/` | Imported by services |
| `docs/` framework | Authority docs — referenced in working sessions |
