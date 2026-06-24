# APPROVAL RECLASSIFICATION REPORT

Status: Complete
Created: 2026-06-17
Phase: Governance Refinement — Safe Repository Hygiene
Mandate: `docs/mandates/GOVERNANCE REFINEMENT – SAFE REPOSITORY HYGIENE.md`

---

## PURPOSE

Records the reclassification of all open repository restructuring approval items following the introduction of the `SAFE_REPOSITORY_HYGIENE` execution tier. This report covers:

- All open items from `RESIDUAL_OWNER_DECISION_REGISTER.md` (ROD-001 through ROD-004)
- All deferred items from `APPROVAL_CLASSIFICATION_MATRIX.md` that had not been executed
- Assignment of each item to: `SAFE_REPOSITORY_HYGIENE`, `REQUIRES_APPROVAL`, or `PROHIBITED`

New policy reference: `docs/07_governance/SAFE_REPOSITORY_HYGIENE_POLICY.md`

---

## RECLASSIFICATION RESULTS SUMMARY

| ID | Item | Old Classification | New Classification | Change |
|----|------|--------------------|-------------------|--------|
| ROD-001 / OA-003 | Frontend app relocation (`backend/ui/` → `frontend/`) | Owner Decision Required | REQUIRES_APPROVAL | No change — retained |
| ROD-002 / OA-004 | TS employee-service archiving (43 files) | Repository Determinable (DEFERRED) | SAFE_REPOSITORY_HYGIENE | UPGRADED — owner approval no longer required |
| ROD-002 / OA-005 | TS settings-service archiving (6 files) | Repository Determinable (DEFERRED) | SAFE_REPOSITORY_HYGIENE | UPGRADED — owner approval no longer required |
| ROD-002 / OA-006 | TS middleware archiving (11 files) | Repository Determinable (DEFERRED) | SAFE_REPOSITORY_HYGIENE | UPGRADED — owner approval no longer required |
| ROD-003 / OA-007a | Deploy validation CI migration (deploy.yml) | Deployment Decision | REQUIRES_APPROVAL | No change — retained |
| ROD-004 / OA-007b | Docker build CI migration (build.yml) — file archive only | Repository Hygiene (DEFERRED) | SAFE_REPOSITORY_HYGIENE (archive) / REQUIRES_APPROVAL (activate) | SPLIT — archive is safe, activation is not |
| ROD-004 / OA-007c | Test/compose CI migration (test.yml) — file archive only | Repository Hygiene (DEFERRED) | SAFE_REPOSITORY_HYGIENE (archive) / REQUIRES_APPROVAL (activate) | SPLIT — archive is safe, activation is not |

**Net result:** 3 full items upgraded to SAFE_REPOSITORY_HYGIENE. 2 items split (archive portion safe; activation portion still REQUIRES_APPROVAL). 2 items unchanged at REQUIRES_APPROVAL.

---

## DETAILED RECLASSIFICATION RATIONALE

### ROD-001 / OA-003 — Frontend App Relocation

**Item:** Move `backend/ui/` (105+ file Next.js app) to `frontend/`. Rename existing `frontend/` to `frontend-wireframes/`. Update docker-compose.yml build context.

**Old classification:** Architecture Decision + Deployment Decision (Owner Decision Required)

**New classification: REQUIRES_APPROVAL** (unchanged)

**Rationale:** This action fails three disqualifying factors from `SAFE_REPOSITORY_HYGIENE_POLICY.md`:
1. Requires modification of `docker-compose.yml` — explicitly listed as REQUIRES_APPROVAL (Infrastructure Changes)
2. Carries hidden import path dependencies that cannot be confirmed without executing `next build` from the new location
3. Moving an active application directory is not equivalent to moving dead code — the app is served at runtime

The determination (relocation is structurally correct) is complete. The execution remains owner-gated.

**Action:** No change. Remains in `RESIDUAL_OWNER_DECISION_REGISTER.md` as ROD-001.

---

### ROD-002 / OA-004 — TypeScript Employee-Service Archiving (43 files)

**Item:** Move 43 TypeScript files from `backend/services/employee-service/` to `backend/docs/system/archive/typescript-employee-service/`.

**Old classification:** Repository Determinable (DEFERRED — awaiting owner execution)

**New classification: SAFE_REPOSITORY_HYGIENE**

**Rationale:**
- Dead code confirmed: grep across all Python files found zero TypeScript imports
- `service_runtime.py` does not reference any TypeScript module
- The Python employee-service implementation (`employee_api.py`) fully supersedes the TypeScript files
- Archive (not deletion) — files are preserved for reference at a new location
- Reversible: the move can be undone with no production impact
- No docker-compose, CI, or build tool path references the source location

All five qualifying criteria for `SAFE_REPOSITORY_HYGIENE` are met. No disqualifying factor applies.

**Action:** Removed from RESIDUAL_OWNER_DECISION_REGISTER. May be executed by any AI session without owner approval.

**Execution target:** `backend/docs/system/archive/typescript-employee-service/`

---

### ROD-002 / OA-005 — TypeScript Settings-Service Archiving (6 files)

**Item:** Move 6 TypeScript files from `backend/services/settings-service/` to `backend/docs/system/archive/typescript-settings-service/`.

**Old classification:** Repository Determinable (DEFERRED — awaiting owner execution)

**New classification: SAFE_REPOSITORY_HYGIENE**

**Rationale:** Same as OA-004. Additionally:
- The settings-service Python implementation is an in-memory dict stub in `service_runtime.py` lines 324–342 — it does not import the TypeScript files
- The TypeScript files document the intended schema for a future persistent settings implementation and have archive reference value
- No active runtime path references these files

**Action:** Removed from RESIDUAL_OWNER_DECISION_REGISTER. May be executed by any AI session without owner approval.

**Execution target:** `backend/docs/system/archive/typescript-settings-service/`

---

### ROD-002 / OA-006 — TypeScript Middleware Archiving (11 files)

**Item:** Move 11 TypeScript files from `backend/middleware/` to `backend/docs/system/archive/typescript-middleware/`.

**Old classification:** Repository Determinable (DEFERRED — awaiting owner execution)

**New classification: SAFE_REPOSITORY_HYGIENE**

**Rationale:** Same as OA-004. The middleware layer is implemented in Python (`service_runtime.py` handles auth, rate limiting, routing). TypeScript middleware files are vestigial from an earlier TypeScript architecture that was replaced.

**Action:** Removed from RESIDUAL_OWNER_DECISION_REGISTER. May be executed by any AI session without owner approval.

**Execution target:** `backend/docs/system/archive/typescript-middleware/`

---

### ROD-003 / OA-007a — Deploy Validation CI Migration (deploy.yml)

**Item:** Migrate `backend/.github/workflows/deploy.yml` to root `.github/workflows/integration.yml`. Modify its content to run `docker compose up -d --build`, health-check all services, then `docker compose down -v`. Decide trigger strategy (PR vs push vs manual).

**Old classification:** Deployment Decision (Owner Decision Required)

**New classification: REQUIRES_APPROVAL** (unchanged)

**Rationale:** This action fails two disqualifying factors:
1. Requires modifying active CI workflow content (from a non-executing location to the executing root `.github/workflows/`)
2. Activates a currently inactive workflow — changes deployment behavior
3. Requires infrastructure decisions: GitHub runner capabilities (Docker, compose), test database seeding, trigger conditions (PR / push / manual)

The `SAFE_REPOSITORY_HYGIENE` tier does not cover activation of inactive CI workflows or modification of CI YAML content.

**Action:** No change. Remains REQUIRES_APPROVAL. Owner must decide runner strategy, database seeding approach, and trigger conditions before execution.

---

### ROD-004 / OA-007b — Docker Build CI Migration (build.yml) — SPLIT

**Item:** `backend/.github/workflows/build.yml` — builds 3 Docker images (`api`, `services`, `ui`). Never executes (wrong directory for GitHub). Contains valuable Docker build definitions.

**Old classification:** Repository Hygiene (DEFERRED — owner to migrate to root CI)

**New classification:** SPLIT into two sub-items:

**Sub-item A — Archive as reference (do not activate)**
**Classification: SAFE_REPOSITORY_HYGIENE**
Copy `backend/.github/workflows/build.yml` to `docs/archive/ci-legacy/build.yml` as a reference document. Remove from `backend/.github/workflows/` (as it is dead — never executes).
Rationale: Moving a never-executing file to an archive location is pure repository hygiene. No CI behavior is affected.

**Sub-item B — Migrate and activate in root CI**
**Classification: REQUIRES_APPROVAL**
Modifying the YAML content (adjusting Dockerfile paths from `backend/`-relative to repo-root-relative), adding a `build-images` job to root `.github/workflows/ci.yml`, and activating Docker builds in the CI pipeline.
Rationale: Modifying active CI content, changing Dockerfile path resolution, and activating new CI jobs are all REQUIRES_APPROVAL (CI/CD pipeline change + infrastructure).

**Action:** Sub-item A (archive) may be executed without owner approval. Sub-item B (activation) remains REQUIRES_APPROVAL.

---

### ROD-004 / OA-007c — Test/Compose CI Migration (test.yml) — SPLIT

**Item:** `backend/.github/workflows/test.yml` — runs `python -m unittest discover` + `docker compose config` validation. Never executes (wrong directory). Contains a compose config validation step not present in root CI.

**Old classification:** Repository Hygiene (DEFERRED — merge unique steps to root CI)

**New classification:** SPLIT into two sub-items:

**Sub-item A — Archive as reference (do not activate)**
**Classification: SAFE_REPOSITORY_HYGIENE**
Copy `backend/.github/workflows/test.yml` to `docs/archive/ci-legacy/test.yml` as reference. Remove from `backend/.github/workflows/`.

**Sub-item B — Merge unique step (compose config validation) into root CI**
**Classification: REQUIRES_APPROVAL**
Adding `docker compose config > /tmp/compose.rendered.yaml` as a step to root `.github/workflows/ci.yml` modifies the active CI pipeline. Also requires standardizing from `python -m unittest` to `pytest` — a framework change.
Rationale: Modifying active CI pipeline content.

**Action:** Sub-item A (archive) may be executed without owner approval. Sub-item B (root CI merge) remains REQUIRES_APPROVAL.

---

## REMAINING REQUIRES_APPROVAL ITEMS

After reclassification, the following items remain in REQUIRES_APPROVAL status and require owner decisions:

| ID | Item | Decision Required |
|----|------|-------------------|
| ROD-001 | Frontend app relocation | Architecture + deployment direction; confirm docker-compose.yml update; verify no hidden import breaks |
| ROD-003 | Deploy validation CI | Runner strategy, database seeding, trigger conditions |
| ROD-004-B | Docker build CI activation | Dockerfile path adjustments, CI job design |
| ROD-004-C | Compose config CI step | Active CI modification, test framework standardization |

---

## NEWLY AUTHORIZED SAFE_REPOSITORY_HYGIENE ACTIONS

These items may now be executed by any AI session without owner approval:

| Action | Execution Target |
|--------|-----------------|
| Archive TypeScript employee-service files (43 files) | `backend/docs/system/archive/typescript-employee-service/` |
| Archive TypeScript settings-service files (6 files) | `backend/docs/system/archive/typescript-settings-service/` |
| Archive TypeScript middleware files (11 files) | `backend/docs/system/archive/typescript-middleware/` |
| Archive dead `build.yml` as reference | `docs/archive/ci-legacy/build.yml` |
| Archive dead `test.yml` as reference | `docs/archive/ci-legacy/test.yml` |

Total items reclassified to SAFE_REPOSITORY_HYGIENE: **5 executable actions** (covering 60 TypeScript files + 2 CI YAML files)

---

## GOVERNANCE IMPACT

This reclassification reduces the active RESIDUAL_OWNER_DECISION_REGISTER from 4 items to effectively 2 core decisions (ROD-001 and ROD-003/004 activation), with the TypeScript archiving work fully unblocked.

Future repository audit phases should apply `SAFE_REPOSITORY_HYGIENE_POLICY.md` at item classification time, preventing unnecessary accumulation in owner decision registers.
