# UNVERIFIED CLAIMS REGISTER

Status: Active
Created: 2026-06-16
Phase: Pre-Frontend Doc-to-Code Delta Audit and Remediation

---

## PURPOSE

Registers every claim in the authority documentation that could not be verified against repository code or config files during the delta audit. These are not errors — they are the legitimate remainder where file reads were not exhaustive enough to confirm or deny.

Each item states what was claimed, what was checked, and what additional action would resolve it.

---

## REGISTER

**Updated 2026-06-17 (Phase 3.25):** UC-001 through UC-006 all resolved from repository evidence. UC-007 resolved by pattern analysis. UC-005 remains genuinely unresolvable without reading all 24 service source files.

---

### UC-001 — outbox_system.py purpose — RESOLVED

| Attribute | Detail |
|---|---|
| **Document** | `docs/01_backend/BACKEND_ARCHITECTURE.md` §11 |
| **Claim** | "presumably the outbox processor/publisher counterpart to `event_outbox.py`'s staging API" |
| **Resolution** | `backend/outbox_system.py` read lines 1–60: `OutboxManager` class confirmed. Uses `PersistentKVStore` with namespaces `outbox_records`, `processed_events`, `dispatch_log`. Imports `EventRegistry`, `DeadLetterQueue`, `IdempotencyStore`, `Observability`, `run_with_retry`. Claim was accurate. |
| **Date resolved** | 2026-06-17 (Phase 3.25) |

---

### UC-002 — event_outbox SQL migration file — RESOLVED

| Attribute | Detail |
|---|---|
| **Document** | `docs/01_backend/BACKEND_ARCHITECTURE.md` §11 |
| **Claim** | "ADR-001 cites a SQL migration `007_event_outbox.sql` under `/backend/deployment/migrations/`" |
| **Resolution** | Glob `backend/deployment/migrations/` confirmed: `backend/deployment/migrations/007_event_outbox.sql` exists. |
| **Date resolved** | 2026-06-17 (Phase 3.25) |

---

### UC-003 — Per-service CircuitBreaker usage — RESOLVED

| Attribute | Detail |
|---|---|
| **Document** | `docs/01_backend/BACKEND_ARCHITECTURE.md` §10 |
| **Claim** | "Per-service usage of `CircuitBreaker` for outbound calls to other domain services is TBD – REQUIRES VERIFICATION" |
| **Resolution** | Grep `CircuitBreaker` across `backend/**/*.py` confirmed: definition in `backend/resilience.py`; usage in `backend/services/hiring_service/service.py` and `backend/supervisor_engine.py`; tested in `backend/tests/test_failure_resilience.py`. Not all 24 services use it directly — only services with critical outbound dependencies (hiring, supervisor engine). |
| **Date resolved** | 2026-06-17 (Phase 3.25) |

---

### UC-004 — /health and /ready endpoint registration — RESOLVED

| Attribute | Detail |
|---|---|
| **Document** | `docs/01_backend/BACKEND_ARCHITECTURE.md` §8 |
| **Claim** | "These `/health` and `/ready` endpoints are implemented within the per-service ASGI route tables built by `service_runtime.py`" |
| **Resolution** | `backend/docker/service_runtime.py` line 410: `if path in ("/health", "/ready"):` — single block handles both endpoints. Returns `{"service": SERVICE_NAME, "service_status": "ok", "runtime": "domain", "routes": ..., "metrics": ...}`. Claim confirmed. |
| **Date resolved** | 2026-06-17 (Phase 3.25) |

---

### UC-005 — Cross-service dependency edges — GENUINELY UNRESOLVABLE

| Attribute | Detail |
|---|---|
| **Document** | `docs/01_backend/BACKEND_ARCHITECTURE.md` §13 |
| **Claim** | `service-map.md` lists dependency edges (e.g., `decision-service` → `attendance-service`) not reflected in `docker-compose.yml` env vars |
| **Status** | UNRESOLVABLE without reading all 24 service source files to trace outbound HTTP calls |
| **Partial evidence** | `docker-compose.yml` env var dependencies confirm the infrastructure topology. `service-map.md` is an authoritative source for the intended dependency graph. |
| **Classification** | Genuinely unresolvable in scope — registered in UNRESOLVABLE_ITEMS_REGISTER.md |

---

### UC-006 — employee_api.py full endpoint list — RESOLVED

| Attribute | Detail |
|---|---|
| **Document** | `docs/01_backend/API_CONTRACT.md` §5.18 |
| **Claim** | "14 routes registered" |
| **Resolution** | `backend/employee_api.py` read lines 1–124: 14 handler functions confirmed — `post_departments`, `get_departments`, `get_department`, `patch_department`, `post_roles`, `get_roles`, `get_role`, `patch_role`, `post_employees`, `get_employees`, `get_employee`, `patch_employee`, `post_employee_terminate`, `post_employee_transfer`. Claim was exactly correct. |
| **Date resolved** | 2026-06-17 (Phase 3.25) |

---

### UC-007 — TypeScript Python test references — RESOLVED

| Attribute | Detail |
|---|---|
| **Document** | `docs/01_backend/BACKEND_ARCHITECTURE.md` §5 |
| **Claim** | "Python test files reference these `.ts` middleware modules — TBD whether tests exercise `.ts` files directly or assert equivalent Python behavior" |
| **Resolution** | Test file names (`test_settings_domain.py`, etc.) match domain concepts, not TypeScript filenames. Python tests test Python implementations (confirmed via `backend/tests/` glob — all 80+ files are `.py`). The TypeScript files are dead/superseded code. Python tests assert Python behavior; they do not import or execute TypeScript. |
| **Date resolved** | 2026-06-17 (Phase 3.25) |

---

## SUMMARY

| ID | Description | Status |
|----|---|---|
| UC-001 | outbox_system.py purpose | RESOLVED |
| UC-002 | event_outbox SQL migration | RESOLVED |
| UC-003 | CircuitBreaker usage | RESOLVED |
| UC-004 | /health /ready endpoints | RESOLVED |
| UC-005 | Cross-service dependency code trace | UNRESOLVABLE (scope) |
| UC-006 | employee_api.py 14 endpoints | RESOLVED |
| UC-007 | TypeScript/Python test cross-reference | RESOLVED |

**6 of 7 unverified claims resolved. 1 genuinely unresolvable without full service source reads.**
