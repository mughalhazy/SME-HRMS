# RESIDUAL DECISION COLLAPSE REPORT

Status: Complete
Created: 2026-06-17
Phase: 2.95 — Residual Decision Collapse
Mandate: `docs/mandates/PHASE 2.95 — RESIDUAL DECISION COLLAPSE.md`

---

## PURPOSE

Applies the Decision Collapse Rule to every known residual decision across the project. For each item: exhausts repository evidence, produces a single recommended path, classifies the decision, and assesses frontend impact.

**Collapse Rule:** Produce a single recommended path. No undecided outcomes permitted.
**Mandatory Collapse Test:** "If the owner disappears today, which option should the project take?" That option becomes the recommended path.

**Decision Classifications:**
- `RESOLVED` — Repository evidence and architecture support a clear recommendation. Execute immediately.
- `OWNER_CONFIRMATION_ONLY` — A recommendation exists. Execution may proceed unless explicitly rejected.
- `TRUE_OWNER_DECISION` — Multiple valid business outcomes remain. Used sparingly; must prove why evidence cannot determine the answer.

---

## GROUP 1: REGISTERED RESIDUAL DECISIONS (ROD-001 to ROD-004)

### ROD-001 — Frontend App Location

**Decision question:** Should `backend/ui/` (the active Next.js 15 app) be relocated to the repository root `frontend/` directory?

**Repository evidence:**
- `backend/ui/` — 105+ files, Next.js app router, TypeScript, Tailwind, `package.json` naming it `hrms-frontend`
- `backend/docker-compose.yml` lines 445–458 — `frontend-ui` service: `context: ./backend/ui`
- Root `frontend/` — 62 HTML wireframes (archive-quality)
- `backend/.github/workflows/build.yml` — builds `Dockerfile.ui` from context `.` (inside `backend/`)
- No internal Next.js `import` path audit has been run — hidden `../` references not ruled out

**Options:**

Option A — Move `backend/ui/` → `frontend/`; rename existing `frontend/` → `frontend-wireframes/`; update docker-compose.yml build context
- Structurally correct
- Requires docker-compose.yml update (REQUIRES_APPROVAL)
- Requires running `next build` from new location to confirm no broken import paths
- Medium risk; cannot execute until after Phase 3 validation

Option B — Leave `backend/ui/` in place; document as known structural anomaly; all Phase 3 work proceeds from `backend/ui/` as the authoritative frontend location
- Zero execution risk
- Unblocks Phase 3 immediately
- Permanent technical debt until resolved post-Phase 3

Option C — Move but keep docker-compose.yml pointing to original path via symlink
- Not recommended — adds indirection without solving the root cause

**Mandatory Collapse Test:** If the owner disappears today, take Option B. Relocating a live frontend app mid-audit cycle is a risk with zero UX benefit. Phase 3 can proceed perfectly well from `backend/ui/`.

**Recommended Option: B** — Leave in place through Phase 3. Execute Option A post-Phase 3 as a tracked SAFE_REPOSITORY_HYGIENE action (once docker-compose.yml update is authorized).

**Classification: OWNER_CONFIRMATION_ONLY**
- Recommended path (B) may proceed without further approval
- Owner may choose to authorize Option A after Phase 3 completes

**Frontend Impact:** ZERO. The frontend app location in the file system does not affect navigation, menus, screens, workflows, permissions, user journeys, or product scope. Phase 3 proceeds from `backend/ui/`.

---

### ROD-002 — TypeScript Dead Code Archiving (60 files)

**Decision question:** Should 60 confirmed-dead TypeScript files across 3 directories be archived?

**Repository evidence:** Files confirmed dead by grep across all Python services. Zero TypeScript imports from any Python file. Three directories: `backend/services/employee-service/` (43 files), `backend/services/settings-service/` (6 files), `backend/middleware/` (11 files).

**Status:** RECLASSIFIED TO SAFE_REPOSITORY_HYGIENE in `APPROVAL_RECLASSIFICATION_REPORT.md` (2026-06-17).

**Mandatory Collapse Test:** Archive. The TypeScript settings-service files especially have design reference value. No deletion.

**Recommended Option:** Archive to `backend/docs/system/archive/` subdirectories. No owner approval required.

**Classification: RESOLVED** — Authorized as SAFE_REPOSITORY_HYGIENE. Execute in any session.

**Frontend Impact:** ZERO. Dead code archiving has no effect on any frontend concern.

---

### ROD-003 — Deploy Validation CI Migration (deploy.yml)

**Decision question:** Should `backend/.github/workflows/deploy.yml` be migrated to the root CI pipeline as an integration test?

**Repository evidence:**
- `deploy.yml` runs `docker compose up -d --build` + health checks + `docker compose down -v`
- Never executes (in `backend/.github/workflows/` — GitHub ignores non-root `.github/`)
- Root `ci.yml` has no integration/compose test
- Requires: GitHub runner with Docker + compose; database container; test env vars

**Options:**

Option A — Migrate to root `.github/workflows/integration.yml` as `workflow_dispatch`-only trigger; add database seeding step; promote to PR trigger once validated
- Provides real integration test coverage
- Medium setup cost: runner must support Docker/compose; `.env` generation step needed

Option B — Delete `backend/.github/workflows/deploy.yml` entirely
- Clean; removes dead CI definition
- Loses a well-structured integration test definition

Option C — Leave `deploy.yml` in `backend/.github/workflows/` (continue not executing)
- Status quo; no benefit

**Mandatory Collapse Test:** Option A. The integration test pattern is valuable. "workflow_dispatch"-only minimizes risk while the runner configuration is established. No reason to permanently delete a useful test definition.

**Recommended Option: A** — Migrate as `workflow_dispatch`-only integration.yml in root CI. Owner to confirm GitHub runner capabilities (self-hosted or GitHub-hosted with Docker). No frontend impact; proceed with Phase 3 regardless.

**Classification: OWNER_CONFIRMATION_ONLY**
- Recommendation is clear. Owner confirms runner strategy.
- If owner is unavailable, Option A is the default; Option C (status quo) is acceptable but accumulates debt.

**Frontend Impact:** ZERO. CI infrastructure does not affect navigation, screens, workflows, permissions, or user journeys.

---

### ROD-004 — Docker Build + Test CI Migration (build.yml + test.yml)

**Decision question:** Should `backend/.github/workflows/build.yml` and `test.yml` be migrated to the root CI pipeline?

**Repository evidence:**
- `build.yml` builds 3 Docker images (`api`, `services`, `ui`); uses `docker/build-push-action@v6`
- `test.yml` runs `python -m unittest discover` + `docker compose config` validation
- Both never execute (wrong directory)
- Root `ci.yml` uses `pytest`, no Docker build, no compose validation
- `build.yml` Dockerfile paths relative to `backend/` not repo root — path adjustment needed before root CI activation

**This decision is split into two sub-items (per APPROVAL_RECLASSIFICATION_REPORT.md):**

**Sub-item A: Archive as reference**
Option: Copy both files to `docs/archive/ci-legacy/`; remove from `backend/.github/workflows/`
Classification: SAFE_REPOSITORY_HYGIENE — execute immediately, no approval needed.

**Sub-item B: Migrate and activate in root CI**
Options:
- B1: Add Docker build job + compose-config validation to root `ci.yml`; standardize to `pytest`; trigger on push to `main`
- B2: Add compose-config validation only (lower risk); skip Docker build for now
- B3: Activate nothing; maintain archive reference only

**Mandatory Collapse Test for Sub-item B:** B2. Add `docker compose config` validation to root CI as a cheap, low-risk correctness check. Docker image builds require registry credentials and runner setup — defer that to infrastructure planning. Standardize all tests to `pytest` when migrating.

**Recommended Option:** Sub-item A immediately (SAFE_REPOSITORY_HYGIENE). Sub-item B2 (compose-config step in root CI) as OWNER_CONFIRMATION_ONLY.

**Classification: RESOLVED** (Sub-item A) / **OWNER_CONFIRMATION_ONLY** (Sub-item B)

**Frontend Impact:** ZERO. CI infrastructure does not affect frontend concerns.

---

## GROUP 2: AUTHORITY DOCUMENT TBDs — GATEWAY ROUTE STATUS

### Feature Scope: Compliance, Decision, Banking, WhatsApp — "Route Unconfirmed"

**Decision question:** Do compliance-service, decision-service, bank-service, and whatsapp-service have confirmed API Gateway routes?

**Repository evidence (Phase 2.8 confirmation):**
From `docs/01_backend/API_CONTRACT.md` §4 Gateway Route Table (25 confirmed routes):
| # | Route | Gateway Prefix | Upstream |
|---|-------|---------------|---------|
| 22 | compliance | `/compliance` | `/api/v1/compliance` | compliance-service |
| 23 | decisions | `/decisions` | `/api/v1/decisions` | decision-service |
| 24 | banking | `/banking` | `/api/v1/banking` | bank-service |
| 25 | whatsapp | `/whatsapp` | `/api/v1/whatsapp` | whatsapp-service |

**Decision:** NO DECISION NEEDED. These routes ARE confirmed. The "TBD – REQUIRES VERIFICATION" markers in `FEATURE_SCOPE.md` (F-011, F-014, F-015, F-016) and `FULLSTACK_STITCHING_CONTRACT.md` are **documentation drift** from documents that predate Phase 2.8 confirmation. The routes exist.

**Classification: RESOLVED** — Documentation drift, not an open decision. `FEATURE_SCOPE.md` requires a cleanup update to remove stale "unconfirmed" markers on these 4 features.

**Frontend Impact:** CLEAR. All 4 services are reachable via the API Gateway. Frontend can call `/api/v1/compliance`, `/api/v1/decisions`, `/api/v1/banking`, `/api/v1/whatsapp`.

---

## GROUP 3: FEATURE SCOPE TBDs — UI ROUTE DEFAULTS

### F-007 (Workflow) — Approval Inbox UI Route

**Decision question:** What is the UI route for the workflow approval inbox?

**Evidence:**
- `FULLSTACK_STITCHING_CONTRACT.md` T-005: "H05 approval inbox archetype (TBD – REQUIRES VERIFICATION exact route)"
- `API_CONTRACT.md`: 6 workflow endpoints confirmed under `/api/v1/workflows`
- H05 archetype: defined in `design/hrms-archetype-system-v1.md`
- Gateway route 11: `workflows → /api/v1/workflows`

**Mandatory Collapse Test:** Adopt convention-based route `/approvals`.
- Consistent with feature name (approvals inbox)
- Not `/workflows` (that's the backend concept; the UI should surface the user action: approving things)
- Pattern matches HR SaaS conventions (similar products use `/approvals`)

**Recommended route: `/approvals`**
**Classification: RESOLVED** — Route determined by convention. No product input required.
**Frontend Impact:** Navigation item exists. Route `/approvals` should appear in the sidebar for Manager and Admin roles.

---

### F-008 (Audit) — Audit Log Viewer UI Route

**Decision question:** What is the UI route for the audit log viewer?

**Evidence:**
- Gateway route 12: `audit → /api/v1/audit`
- RBAC: Admin only (`_ROUTE_ROLE_MAP` confirmed)
- Feature F-008: Status IMPLEMENTED, service confirmed

**Mandatory Collapse Test:** Route `/audit`. Mirrors the gateway prefix. Admin-only — does not appear in navigation for non-Admin roles.

**Recommended route: `/audit`**
**Classification: RESOLVED**
**Frontend Impact:** Admin-only navigation item `/audit`. Not visible to other roles.

---

### F-011 (Compliance) — Compliance Screen UI Route

**Decision question:** What is the UI route for compliance submission management?

**Evidence:**
- Gateway route 22: `compliance → /api/v1/compliance`
- Target users: Admin, PayrollAdmin (per WF-007)
- Workflow WF-007 confirmed: FBR/EOBI/PESSI report generation and submission

**Mandatory Collapse Test:** Route `/compliance`. Mirrors gateway prefix. Consistent with WF-007 trigger point.

**Recommended route: `/compliance`**
**Classification: RESOLVED**
**Frontend Impact:** Navigation item `/compliance` visible to Admin and PayrollAdmin roles.

---

### F-013 (Automation) — Automation Rules UI Route

**Decision question:** What is the UI route for the automation engine management?

**Evidence:**
- Gateway route 20: `automations → /api/v1/automations`
- Feature F-013: Status IMPLEMENTED, event-triggered rules confirmed

**Mandatory Collapse Test:** Route `/automations`. Mirrors gateway prefix.

**Recommended route: `/automations`**
**Classification: RESOLVED**
**Frontend Impact:** Navigation item `/automations` visible to Admin role (no explicit RBAC restriction — accessible to any authenticated user by gateway rule; Admin likely intended by product).

---

## GROUP 4: PRODUCT SCOPE DECISIONS

### Shift/Roster Scheduling — In Scope or Out?

**Evidence:** `FEATURE_SCOPE.md` OUT OF SCOPE section: "Shift/Roster scheduling (TBD – REQUIRES VERIFICATION)". `FULLSTACK_STITCHING_CONTRACT.md` KNOWN GAPS: "No shift-service found in codebase."

**Classification: RESOLVED** — OUT OF SCOPE. No service implementation exists. No gateway route. No migration table. No frontend work needed.

---

### Native Mobile App — In or Out of Current Phase Scope?

**Evidence:** `FEATURE_SCOPE.md` OUT OF SCOPE: "Native mobile app (mobile directory exists but scope TBD)". The current frontend is Next.js 15 web-first.

**Classification: RESOLVED** — Out of current phase scope. The web frontend is the current delivery target. Mobile is a future roadmap item (OAQ-004). No impact on Phase 3 frontend authority capture.

---

### Document Management — In Scope?

**Evidence:** `FEATURE_SCOPE.md` OUT OF SCOPE: "Document Management — no service, no gateway route, no DB table; `contracts/hrms-h02-documents-contract.json` is an orphaned frontend contract artifact."

**Classification: RESOLVED** — OUT OF SCOPE. The orphaned `hrms-h02-documents-contract.json` is an artifact from an earlier product scope that was cut. Phase 3 should not build a documents screen.

---

## GROUP 5: WORKFLOW TBDs — IMPLEMENTATION DETAIL RESOLUTION

These are not product decisions — they are implementation details discovered during authority document review. They are collapsed here to prevent Phase 3 from treating them as open questions.

| Item | Source | Resolution |
|------|--------|-----------|
| WF-001 "Document Collection" step TBD | `PRODUCT_WORKFLOWS.md` | Implementation detail. Frontend shows a document upload step in the onboarding workflow. Upload endpoint to be discovered in Phase 3. Not a product scope decision. |
| WF-002 calendar update TBD | `PRODUCT_WORKFLOWS.md` | attendance-service marks attendance as Leave type. Implementation detail, not a product decision. |
| WF-003 payroll approval step TBD | `PRODUCT_WORKFLOWS.md` | Default: treat payroll approval as optional (PayrollAdmin reviews manually, no workflow instance required). Phase 3 implements payroll run UI without a mandatory approval step. |
| WF-006 Finance review 2nd approval TBD | `PRODUCT_WORKFLOWS.md` | ADD-ON feature. Not required for Phase 3. Deferred. |
| Employee offboarding checklist | `PRODUCT_WORKFLOWS.md` | Not in FEATURE_SCOPE. Out of current scope. |
| Survey distribution workflow | `PRODUCT_WORKFLOWS.md` | ADD-ON (F-018 engagement). Not required for Phase 3 core. |
| Exact approval chain for multi-manager leave | `PRODUCT_WORKFLOWS.md` | Default: single manager approval. Phase 3 frontend implements one approver; escalation chain is implementation detail. |

**Classification: RESOLVED** — All items are implementation details, not product scope decisions.

---

## FULL COLLAPSE SUMMARY

| ID | Decision | Classification | Recommended Path | Frontend Impact |
|----|----------|---------------|-----------------|----------------|
| ROD-001 | Frontend app location | OWNER_CONFIRMATION_ONLY | Stay in `backend/ui/` through Phase 3 | Zero |
| ROD-002 | TypeScript archiving (60 files) | RESOLVED | Execute as SAFE_REPOSITORY_HYGIENE | Zero |
| ROD-003 | Deploy CI migration | OWNER_CONFIRMATION_ONLY | Migrate as workflow_dispatch | Zero |
| ROD-004-A | CI files archive | RESOLVED | Archive as SAFE_REPOSITORY_HYGIENE | Zero |
| ROD-004-B | CI activation | OWNER_CONFIRMATION_ONLY | Compose-config validation step only | Zero |
| Compliance/Decision/Banking/WhatsApp routes | RESOLVED | Documentation drift; routes confirmed | All 4 reachable from frontend |
| F-007 approval inbox route | RESOLVED | `/approvals` | Navigation item for Admin + Manager |
| F-008 audit viewer route | RESOLVED | `/audit` | Admin-only navigation item |
| F-011 compliance screen route | RESOLVED | `/compliance` | Admin + PayrollAdmin navigation item |
| F-013 automation rules route | RESOLVED | `/automations` | Admin navigation item |
| Shift/Roster scope | RESOLVED | Out of scope | No screen needed |
| Mobile scope | RESOLVED | Future scope, not current phase | No impact on web frontend |
| Document Management scope | RESOLVED | Out of scope | No screen needed |
| WF-001/002/003/006 TBDs | RESOLVED | Implementation details, not decisions | No scope impact |

**Count by classification:**
- RESOLVED: 11 of 14 items
- OWNER_CONFIRMATION_ONLY: 3 of 14 items (ROD-001, ROD-003, ROD-004-B)
- TRUE_OWNER_DECISION: 0

**Burden of proof test passed:** Zero items left as undecided. All have a recommended default path.
