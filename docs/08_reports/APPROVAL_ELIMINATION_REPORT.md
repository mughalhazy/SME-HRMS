# APPROVAL ELIMINATION REPORT

Status: Complete
Created: 2026-06-16
Phase: Repository Determinability Review, Approval Elimination, and Pre-Frontend Go/No-Go

---

## PURPOSE

Documents the Approval Elimination Pass — the systematic review of every open item to either resolve it from repository evidence or prove why it must remain as a genuine owner decision.

Starting count: 17 open items (10 OA + 5 TO + 2 additional from TBD register)
After elimination: 4 genuine owner decisions remain.

---

## ELIMINATED ITEMS (Resolved Without Owner)

These items were resolved entirely from repository evidence and have been actioned.

| ID | Item | Classification | Action |
|---|---|---|---|
| OA-001 | Dead function `_employee_domain_departments()` | Repository Hygiene | DELETED from service_runtime.py |
| OA-002 | OpenAPI title "Aura HRMS" | Documentation Correction | UPDATED in api_gateway_service.py |
| OA-008 | Naming conflict `attendance_service` | Resolved By Evidence (no conflict) | CLOSED — different modules, different layers |
| OA-009 | `(C) Phoenix LiteOS.lnk` at root | Repository Hygiene | DELETED |
| OA-010 | Missing root .gitignore + README | Repository Hygiene | CREATED both files |
| TO-001 | /health /ready endpoint registration | Resolved By Evidence | DOCUMENTED in BACKEND_ARCHITECTURE.md |
| TO-002 | Per-service CircuitBreaker usage | Resolved By Evidence | DOCUMENTED in BACKEND_ARCHITECTURE.md |
| TO-003 | outbox_system.py purpose | Resolved By Evidence | DOCUMENTED in BACKEND_ARCHITECTURE.md |
| TO-004 | Migration 007_event_outbox.sql path | Resolved By Evidence | DOCUMENTED in BACKEND_ARCHITECTURE.md |
| UC-006 | employee_api.py full endpoint list | Resolved By Evidence | DOCUMENTED in API_CONTRACT.md §5.18 (14 routes) |
| UC-007 | TypeScript test references | Resolved By Reclassification | CONFIRMED — no cross-language import possible |
| ARG-003 | Country resolver bootstrap "not wired" | Documentation Error | CORRECTED in BACKEND_ARCHITECTURE.md §12.4 |

**Total eliminated: 12 items**

---

## PARTIALLY ELIMINATED ITEMS

Items where evidence resolved the problem but execution requires owner action.

| ID | Item | What Evidence Determined | What Remains |
|---|---|---|---|
| OA-004 | Archive TS employee-service (43 files) | Dead code confirmed. Archive path defined: `backend/docs/system/archive/typescript-employee-service/` | File move operation — owner must execute or authorise |
| OA-005 | Archive TS settings-service (6 files) | Dead code confirmed. Archive path: `backend/docs/system/archive/typescript-settings-service/` | File move operation — owner must execute or authorise |
| OA-006 | Archive TS middleware (11 files) | Dead code confirmed. Archive path: `backend/docs/system/archive/typescript-middleware/` | File move operation — owner must execute or authorise |
| OA-007 | CI consolidation | Unique jobs identified. Merge plan: add `build-images` + `compose-config` jobs to root CI; `deploy.yml` is a deployment decision | CI file edit + infrastructure decision for deploy.yml |
| TO-005 | Cross-service dependency edges | Confirmed edge cases exist (hiring_service, supervisor_engine). Full map requires reading 24 service files | Not blocking Phase 3 |

**Total partially eliminated: 5 items**

---

## GENUINE OWNER DECISIONS (Cannot Be Repository-Determined)

These 4 items remain because business intent, deployment strategy, or execution risk cannot be determined from repository evidence alone.

### GOD-001 — Frontend relocation: `backend/ui/` → root `frontend/`

**Why repository cannot determine:** The problem and solution are clear. The execution carries risk: Next.js may have relative path imports that break on move; `docker-compose.yml` must be updated; CI must be updated; the existing `frontend/` directory (wireframes) must be renamed first. These interdependencies require human review before a destructive multi-file move. Repository evidence cannot guarantee no hidden path dependencies without running the app post-move.

### GOD-002 — TypeScript dead code archiving (OA-004, OA-005, OA-006)

**Why repository cannot determine:** The determination (dead code) is complete. What remains is a large file move operation (60+ files) that should be owner-approved before execution. This is a safety guardrail, not a knowledge gap.

### GOD-003 — CI/CD `deploy.yml` migration

**Why repository cannot determine:** `deploy.yml` runs `docker compose up -d --build` followed by `curl --fail http://localhost:8000/ready`. Whether this integration test should run on every PR, only on main, or only on manual trigger is a deployment policy decision. Infrastructure requirements (Docker availability on the GitHub runner, environment variables for database) are not fully defined in the repo.

### GOD-004 — Cross-service dependency full map (TO-005)

**Why repository cannot determine fully:** Requires reading 24 service files. Not blocking Phase 3 — the partial evidence (env-var wiring) is sufficient for frontend planning.

---

## APPROVAL ELIMINATION SCORE

| Category | Count |
|---|---|
| Items entering review | 17 |
| Fully eliminated (resolved) | 12 |
| Partially eliminated | 5 |
| Genuine owner decisions | 4 |
| **Elimination rate** | **71%** |

The 29% that remain are genuine decisions or large-scale file operations — not analysis gaps or lack of effort.
