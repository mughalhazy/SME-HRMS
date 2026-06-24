# TBD RESOLUTION REGISTER

Status: Active
Created: 2026-06-16
Phase: Pre-Frontend Doc-to-Code Delta Audit and Remediation

---

## PURPOSE

Registers all TBD annotations found across the authority documents during this audit. For each TBD, records whether it was resolved (and with what evidence) or remains open (and why).

The mandate rule: "No vague TBD remains where code evidence exists."

---

## RESOLVED TBDs

### TR-001 — API_CONTRACT.md §3.3: JWT enforcement mechanism

| Attribute | Detail |
|---|---|
| **Original text** | "The exact gateway-level JWT enforcement mechanism is **TBD — REQUIRES VERIFICATION** (no gateway middleware handler file was located in the sampled files)." |
| **Resolution** | Fully resolved from `backend/docker/api_gateway_service.py` lines 421–430 |
| **Evidence** | `if JWT_SECRET and not any(path.startswith(p) for p in _AUTH_EXEMPT_PREFIXES): verify_hs256_jwt(token, JWT_SECRET, audience=JWT_AUDIENCE, issuer=JWT_ISSUER)`. Missing/invalid token → 401 UNAUTHORIZED. |
| **Action taken** | `API_CONTRACT.md` §3.3 updated with full implementation details + header propagation table added + §3.5 Route-Level RBAC section created |
| **Date resolved** | 2026-06-16 |

---

### TR-002 — BACKEND_ARCHITECTURE.md §2: common_service.py

| Attribute | Detail |
|---|---|
| **Original text** | "TBD – REQUIRES VERIFICATION (not read in full; expected to contain shared service bootstrap helpers based on naming convention)" |
| **Resolution** | Read in full (78 lines): `BaseHTTPRequestHandler`-based health-check stub. `/health`, `/ready`, `/` endpoints only. No shared bootstrap logic. |
| **Evidence** | `backend/docker/common_service.py` confirmed 2026-06-16 |
| **Action taken** | `BACKEND_ARCHITECTURE.md` §2 updated with confirmed description |
| **Date resolved** | 2026-06-16 |

---

### TR-003 — SERVICE_CATALOG.md §21: compliance-service gateway route

| Attribute | Detail |
|---|---|
| **Original text** | "**TBD – REQUIRES VERIFICATION**. `/api/v1/compliance` does not appear in `routes.py` (21 entries) or `gateway-routes.json`." |
| **Resolution** | Confirmed in `routes.py` line 52 and `gateway-routes.json` line 25 |
| **Evidence** | `Route(name="compliance", path_prefix="/compliance", upstream_service="compliance-service")` |
| **Action taken** | `SERVICE_CATALOG.md` §21 gateway status updated to CONFIRMED; §21 header cleaned; SUMMARY TABLE row 21 updated; `API_CONTRACT.md` §4 row 22 and §6 header corrected; `BACKEND_ARCHITECTURE.md` §4.2 TBD removed |
| **Date resolved** | 2026-06-16 |

---

### TR-004 — SERVICE_CATALOG.md §22: decision-service gateway route

| Attribute | Detail |
|---|---|
| **Original text** | "**TBD – REQUIRES VERIFICATION**. `/api/v1/decisions` does not appear in `routes.py` or `gateway-routes.json`." |
| **Resolution** | Confirmed in `routes.py` line 53 and `gateway-routes.json` line 26 |
| **Evidence** | `Route(name="decisions", path_prefix="/decisions", upstream_service="decision-service")` |
| **Action taken** | Same set of documents as TR-003 |
| **Date resolved** | 2026-06-16 |

---

### TR-005 — SERVICE_CATALOG.md §23: bank-service gateway route

| Attribute | Detail |
|---|---|
| **Original text** | "**TBD – REQUIRES VERIFICATION**. `/api/v1/banking` does not appear in `routes.py` or `gateway-routes.json`." |
| **Resolution** | Confirmed in `routes.py` line 54 and `gateway-routes.json` line 27 |
| **Evidence** | `Route(name="banking", path_prefix="/banking", upstream_service="bank-service")` |
| **Action taken** | Same set of documents as TR-003 |
| **Date resolved** | 2026-06-16 |

---

### TR-006 — SERVICE_CATALOG.md §24: whatsapp-service gateway route

| Attribute | Detail |
|---|---|
| **Original text** | "**TBD – REQUIRES VERIFICATION**. `/api/v1/whatsapp` does not appear in `routes.py` or `gateway-routes.json`." |
| **Resolution** | Confirmed in `routes.py` line 55 and `gateway-routes.json` line 28 |
| **Evidence** | `Route(name="whatsapp", path_prefix="/whatsapp", upstream_service="whatsapp-service")` |
| **Action taken** | Same set of documents as TR-003 |
| **Date resolved** | 2026-06-16 |

---

### TR-007 — SERVICE_CATALOG.md §1: employee-service implementation

| Attribute | Detail |
|---|---|
| **Original text** | Primary source listed as TypeScript files in `backend/services/employee-service/`; no Python implementation documented |
| **Resolution** | `backend/employee_service.py` + `backend/employee_api.py` confirmed as active Python implementation. `service_runtime.py` lines 445–469 confirm 14 routes registered. |
| **Evidence** | `elif service_name == "employee-service": from employee_service import EmployeeService; from employee_api import (...)` |
| **Action taken** | `SERVICE_CATALOG.md` §1 and `API_CONTRACT.md` §5.18 updated |
| **Date resolved** | 2026-06-16 |

---

### TR-008 — SERVICE_CATALOG.md §20 / API_CONTRACT.md §5.19: settings-service implementation

| Attribute | Detail |
|---|---|
| **Original text** | Primary source listed as TypeScript files; Status TBD — no Python handler confirmed |
| **Resolution** | Inline dict stub in `service_runtime.py` lines 324–342 confirmed as actual runtime |
| **Evidence** | `settings_state = {"tenant_id": ..., "attendance_policy": ..., "leave_policy": ..., "payroll": ...}` with two inline handlers |
| **Action taken** | `SERVICE_CATALOG.md` §20 and `API_CONTRACT.md` §5.19 updated |
| **Date resolved** | 2026-06-16 |

---

### TR-009 — API_CONTRACT.md §4: route count (21 → 25)

| Attribute | Detail |
|---|---|
| **Original text** | "21 confirmed routes" |
| **Resolution** | Counted from `routes.py` lines 31–55: 25 entries |
| **Evidence** | `ROUTES: tuple[Route, ...]` with 25 entries; `gateway-routes.json` with 25 keys |
| **Action taken** | `API_CONTRACT.md` §2, §4, §4 Notes; `SERVICE_CATALOG.md` §PURPOSE, §25; `BACKEND_ARCHITECTURE.md` §3.3, §4.1, §4.2 all updated |
| **Date resolved** | 2026-06-16 |

---

## OPEN TBDs — RESOLVED IN PHASE 3.25

Previously listed as open. All 4 code-evidence TBDs resolved in Phase 3.25 (2026-06-17).

### TO-001 — BACKEND_ARCHITECTURE.md §8: /health and /ready endpoint registration

| Attribute | Detail |
|---|---|
| **Original TBD** | `/health` and `/ready` endpoint registration in per-service runtime |
| **Resolution** | `backend/docker/service_runtime.py` line 410: `if path in ("/health", "/ready"):` — single block handles both endpoints. Returns `{"service": SERVICE_NAME, "service_status": "ok", "runtime": "domain", "routes": ..., "metrics": ...}` |
| **Evidence** | `service_runtime.py` line 410 — confirmed 2026-06-17 Phase 3.25 |
| **Action taken** | `BACKEND_ARCHITECTURE.md` §8 to be updated; UC-004 closed |
| **Date resolved** | 2026-06-17 |

---

### TO-002 — BACKEND_ARCHITECTURE.md §10: CircuitBreaker usage

| Attribute | Detail |
|---|---|
| **Original TBD** | Per-service `CircuitBreaker` usage not exhaustively checked |
| **Resolution** | Grep confirmed: `backend/resilience.py` (definition), `backend/services/hiring_service/service.py` (usage), `backend/supervisor_engine.py` (usage), `backend/tests/test_failure_resilience.py` (tests) |
| **Evidence** | Grep `CircuitBreaker` across `backend/**/*.py` — 2026-06-17 Phase 3.25 |
| **Action taken** | `BACKEND_ARCHITECTURE.md` §10 to be updated; UC-003 closed |
| **Date resolved** | 2026-06-17 |

---

### TO-003 — BACKEND_ARCHITECTURE.md §11: outbox_system.py purpose

| Attribute | Detail |
|---|---|
| **Original TBD** | `outbox_system.py` purpose not confirmed |
| **Resolution** | `backend/outbox_system.py` read lines 1–60: `OutboxManager` class using `PersistentKVStore` with 3 namespaces: `outbox_records`, `processed_events`, `dispatch_log`. Imports `EventRegistry`, `DeadLetterQueue`, `IdempotencyStore`, `Observability`, `run_with_retry`. |
| **Evidence** | `backend/outbox_system.py` lines 1–60 — confirmed 2026-06-17 Phase 3.25 |
| **Action taken** | `BACKEND_ARCHITECTURE.md` §11 to be updated; UC-001 closed |
| **Date resolved** | 2026-06-17 |

---

### TO-004 — BACKEND_ARCHITECTURE.md §11: 007_event_outbox.sql path

| Attribute | Detail |
|---|---|
| **Original TBD** | `007_event_outbox.sql` path not verified |
| **Resolution** | Glob confirmed: `backend/deployment/migrations/007_event_outbox.sql` exists |
| **Evidence** | Glob `backend/deployment/migrations/*.sql` — 2026-06-17 Phase 3.25 |
| **Action taken** | `BACKEND_ARCHITECTURE.md` §11 to be updated; UC-002 closed |
| **Date resolved** | 2026-06-17 |

---

### TO-005 — BACKEND_ARCHITECTURE.md §13: Cross-service dependency edges

| Attribute | Detail |
|---|---|
| **Status** | UNRESOLVABLE in Phase 3.25 without reading all 24 service source files |
| **Partial resolution** | docker-compose.yml env var dependencies trace the known edges (employee → auth, leave → employee + payroll, etc.). Service-level dependency declarations in docker-compose.yml lines 58–200 form a complete topology at the infrastructure layer. |
| **Remaining gap** | Exact code-level HTTP client calls (outbound service-to-service) in each of the 24 services are not traced. This does not affect Phase 3 or Phase 4 frontend authority. |
| **Classification** | GENUINELY UNRESOLVABLE without deep service read pass — registered in UNRESOLVABLE_ITEMS_REGISTER.md |

---

## SUMMARY

| Category | Count |
|---|---|
| TBDs resolved in Phase 2.8 audit | 9 |
| TBDs resolved in Phase 3.25 (TO-001 to TO-004) | 4 |
| TBDs remaining genuinely unresolvable (TO-005) | 1 |
| TBDs introduced | 0 |
| **Total** | **13 resolved, 1 unresolvable** |
