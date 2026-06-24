# RESIDUAL OWNER DECISION REGISTER

Status: Active — Awaiting Owner Decisions
Created: 2026-06-16
Phase: Repository Determinability Review, Approval Elimination, and Pre-Frontend Go/No-Go

---

## PURPOSE

Contains only the items that survive the Approval Elimination Pass — items where repository evidence has been exhausted and a genuine business, architecture, or deployment decision is required.

Each entry proves why repository evidence cannot determine the answer.

---

## RESIDUAL DECISIONS

### ROD-001 — Frontend App Relocation

**Issue:** The active Next.js 15 frontend app lives at `backend/ui/` (inside the Python backend directory). This is architecturally wrong. The repo root `frontend/` currently contains HTML wireframes.

**Evidence reviewed:**
- `backend/ui/` — Next.js app router, TypeScript, Tailwind, `package.json` naming it `hrms-frontend` (105+ files)
- `backend/docker-compose.yml` lines 445–458 — `frontend-ui` service: `context: ./backend/ui`, `dockerfile: Dockerfile.ui`
- `backend/.github/workflows/build.yml` — builds `Dockerfile.ui` from context `.` (inside `backend/`)
- `backend/ui/next.config.js` or equivalent — path rewrites may reference `backend/` relative paths
- `frontend/` — 62 HTML wireframe files (archive-quality, not active development)

**Repository evidence exhausted:** Yes. The problem is clear. The solution direction is clear. What cannot be determined without running the app:
- Whether any Next.js `import` paths use `../` or absolute paths referencing `backend/` structure
- Whether any build tool config references `backend/ui/` explicitly in a way that breaks after move

**Possible resolutions:**

| Option | Description | Risk |
|---|---|---|
| A | Move `backend/ui/` → `frontend/`; rename `frontend/` → `frontend-wireframes/`; update docker-compose.yml build context | Medium — requires testing all imports; docker-compose must be updated |
| B | Leave in place and document as a known structural anomaly | Low — no execution risk, permanent technical debt |
| C | Move but keep docker-compose.yml pointing to original path via symlink | Not recommended — adds indirection |

**Tradeoffs:** Option A is correct but requires validation. Option B unblocks Phase 3 with no risk but leaves the structural problem unresolved.

**Recommended option:** A — but execute after Phase 3 is complete to avoid blocking frontend authority capture.

**Why repository cannot determine:** Hidden path dependencies in Next.js imports, Tailwind config, and build tools cannot be confirmed without running a build. The move is safe only after `next build` succeeds from the new location.

---

### ROD-002 — TypeScript Dead Code Archiving (60 files)

**Issue:** 60 TypeScript files across 3 directories are confirmed dead code not used by any Python service. They should be archived.

**Evidence reviewed:**
- Grep for TypeScript imports from Python files: zero results
- `service_runtime.py`: no TypeScript module referenced
- `backend/services/employee-service/`: 43 TypeScript files
- `backend/services/settings-service/`: 6 TypeScript files
- `backend/middleware/`: 11 TypeScript files

**Repository evidence exhausted:** Yes. These files are definitively dead code.

**Possible resolutions:**

| Option | Description | Risk |
|---|---|---|
| A | Move all 60 files to `backend/docs/system/archive/` subdirectories | None functional — files preserved for reference |
| B | Delete all 60 files | Low — no callers; irreversible but safe |
| C | Leave in place | No risk; permanent dead code clutter |

**Archive paths (determined from evidence):**
- `backend/docs/system/archive/typescript-employee-service/` (43 files)
- `backend/docs/system/archive/typescript-settings-service/` (6 files)
- `backend/docs/system/archive/typescript-middleware/` (11 files)

**Tradeoffs:** Option A preserves TypeScript design as reference — useful if a settings-service persistent implementation is ever built (TypeScript files document the intended schema). Option B is cleaner but loses design history.

**Recommended option:** A — archive. The TypeScript settings-service files especially have design reference value.

**Why repository cannot determine the FINAL action:** Moving 60 files is a large operation requiring owner authorisation. The determination (dead code) is complete; the execution decision is owner's.

---

### ROD-003 — Deploy Validation CI Workflow Migration

**Issue:** `backend/.github/workflows/deploy.yml` runs `docker compose up -d --build` + health checks but never executes (wrong location for GitHub). The deploy validation pattern is valuable but requires infrastructure decisions before it can run in GitHub Actions.

**Evidence reviewed:**
- `backend/.github/workflows/deploy.yml`: `docker compose up -d --build` → `curl http://localhost:8000/ready` → `curl http://localhost:3000/` → `docker compose down -v`
- Root `.github/workflows/ci.yml`: no integration/compose test
- `backend/docker-compose.yml`: requires `DATABASE_URL`, various service env vars

**Repository evidence exhausted:** Yes.

**Possible resolutions:**

| Option | Description | Risk |
|---|---|---|
| A | Migrate `deploy.yml` to root `.github/workflows/integration.yml`; trigger on push to `main` only; requires GitHub runner with Docker + compose; requires `.env` generation step | Medium — runners need Docker; database container needed |
| B | Remove `deploy.yml` entirely (it never ran anyway) | Low — removes dead CI |
| C | Leave `deploy.yml` in `backend/.github/` (continue not executing) | No change |

**Tradeoffs:** Option A provides real integration test coverage but needs infrastructure setup. Option B is clean but removes a useful test definition.

**Recommended option:** A — migrate to root CI as a `workflow_dispatch`-only job initially, then promote to PR trigger after confirming it runs cleanly.

**Why repository cannot determine:** Requires decision on: (1) CI runner capabilities (self-hosted vs GitHub-hosted), (2) test database seeding strategy, (3) trigger conditions (PR vs push vs manual).

---

### ROD-004 — `backend/.github/workflows/` Migration (build.yml + test.yml)

**Issue:** `build.yml` (Docker image builds) and `test.yml` (unittest + compose config validation) have unique value not in root CI but are never executed.

**Evidence reviewed:**
- `backend/.github/workflows/build.yml`: builds 3 Docker images (`api`, `services`, `ui`) using `docker/build-push-action@v6`; uses `python -m unittest` not `pytest`
- `backend/.github/workflows/test.yml`: `python -m unittest discover` + `docker compose config > /tmp/compose.rendered.yaml` (compose config validation)
- Root `.github/workflows/ci.yml`: uses `pytest`, no Docker build, no compose validation

**Unique jobs to migrate:**
- Docker image builds (from `build.yml`) → add `build-images` job to root CI
- `docker compose config` validation (from `test.yml`) → add step to root CI `test` job
- Note: `build.yml` uses `python -m unittest` (inconsistent with root CI's `pytest`) — should standardize to `pytest`

**Possible resolutions:**

| Option | Description | Risk |
|---|---|---|
| A | Migrate Docker build + compose-config steps to root CI; standardize on pytest; trigger builds on push to main | Low-medium — Docker build needs Dockerfile paths adjusted for root context |
| B | Delete `backend/.github/workflows/` (all 3 files never ran) | Low — no functional impact |

**Why repository cannot determine the final execution:** Docker build paths in `build.yml` use `context: .` and `file: ./Dockerfile.api` — these paths are relative to `backend/` not the repo root. Migration requires path adjustment and verification that Dockerfiles can build from the root context.

**Recommended option:** A — migrate with path adjustments. Owner should verify Dockerfile paths before committing.

---

## DECISIONS NOT BLOCKING PHASE 3

ROD-001 (frontend relocation) — Frontend Authority Capture can proceed at `backend/ui/` as its known location.

ROD-002 (TypeScript archiving) — Dead code does not affect frontend planning.

ROD-003 and ROD-004 (CI) — CI issues do not affect frontend authority documentation.

**None of the 4 residual decisions block Frontend Authority Capture.**
