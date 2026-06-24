# DOC-TO-CODE DELTA MATRIX

Status: Active
Created: 2026-06-16
Phase: Pre-Frontend Doc-to-Code Delta Audit and Remediation

---

## PURPOSE

Tabulates every difference found between documentation claims and actual repository/code evidence. Each row records the document, the claim, the code evidence, severity, and resolution status.

Code evidence is the source of truth. Documentation must match.

---

## DELTA REGISTER

### DELTA-001 — Gateway Route Count: 21 (docs) vs 25 (code)

| Attribute | Detail |
|-----------|--------|
| **Severity** | Critical |
| **Document** | `docs/01_backend/API_CONTRACT.md` §4 Gateway Route Table |
| **Document claim** | "Source: `api-gateway/routes.py` — **21 confirmed routes** in the `ROUTES` tuple." Table lists routes 1–21, ending at `settings`. |
| **Code evidence** | `backend/api-gateway/routes.py` lines 31–55: **25 routes** defined in the `ROUTES` tuple. The last 4 routes are `compliance`, `decisions`, `banking`, `whatsapp`. `backend/deployment/config/gateway-routes.json` also has 25 entries (including `compliance`, `decisions`, `banking`, `whatsapp`). |
| **Delta** | 4 routes missing from API_CONTRACT.md route table. Route count is wrong (21 vs 25). |
| **Remediation** | Update API_CONTRACT.md §4 route count and table. **APPLIED** — see remediation log. |

---

### DELTA-002 — SERVICE_CATALOG: 4 services marked TBD gateway route when routes ARE confirmed

| Attribute | Detail |
|-----------|--------|
| **Severity** | Critical |
| **Document** | `docs/01_backend/SERVICE_CATALOG.md` §21–24 and SUMMARY TABLE |
| **Document claim** | compliance-service, decision-service, bank-service, whatsapp-service all listed as "TBD – REQUIRES VERIFICATION" for gateway route status. |
| **Code evidence** | `backend/api-gateway/routes.py` lines 52–55: all 4 routes confirmed (`compliance`, `decisions`, `banking`, `whatsapp`). `backend/deployment/config/gateway-routes.json` lines 25–28: all 4 confirmed. service_runtime.py: all 4 have full route blocks. |
| **Delta** | Gateway status incorrectly marked TBD for 4 services that have confirmed gateway routes. |
| **Remediation** | Update SERVICE_CATALOG.md §21–24 gateway route status to CONFIRMED. Update SUMMARY TABLE rows. **APPLIED** — see remediation log. |

---

### DELTA-003 — SERVICE_CATALOG: employee-service primary source is TypeScript (dead code)

| Attribute | Detail |
|-----------|--------|
| **Severity** | Critical |
| **Document** | `docs/01_backend/SERVICE_CATALOG.md` §1 employee-service |
| **Document claim** | "Primary source: `backend/services/employee-service/` (TypeScript model files: `employee.controller.ts`, `employee.model.ts`, `employee.repository.ts`, `employee.routes.ts`, `employee.service.ts`, `employee.validation.ts`)" |
| **Code evidence** | `backend/docker/service_runtime.py` lines 445–469: `elif service_name == "employee-service":` imports `from employee_service import EmployeeService` and `from employee_api import (...)`. Python files `backend/employee_service.py` and `backend/employee_api.py` are the active implementation. The TypeScript files in `backend/services/employee-service/` are dead code. |
| **Delta** | SERVICE_CATALOG documents the dead TypeScript implementation as the primary source. Python implementation is undocumented. |
| **Remediation** | Update SERVICE_CATALOG.md §1 to reflect Python primary source. **APPLIED** — see remediation log. |

---

### DELTA-004 — SERVICE_CATALOG: settings-service primary source is TypeScript (not used)

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Document** | `docs/01_backend/SERVICE_CATALOG.md` §20 settings-service |
| **Document claim** | "Primary source: `backend/services/settings-service/` (TypeScript model files: `settings.controller.ts`, …)" |
| **Code evidence** | `backend/docker/service_runtime.py` lines 324–342: `elif service_name == "settings-service":` uses an **inline in-memory Python dict stub** — no Python settings_service.py imported, no TypeScript files used. The `settings_state` dict is initialized with `tenant_id`, `attendance_policy`, `leave_policy`, `payroll` and served by two inline handlers. |
| **Delta** | SERVICE_CATALOG documents a TypeScript implementation that is not used. The actual runtime is an in-memory Python stub. |
| **Remediation** | Update SERVICE_CATALOG.md §20 primary source. **APPLIED** — see remediation log. |

---

### DELTA-005 — API_CONTRACT.md §3.3: JWT enforcement marked TBD (it is implemented)

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Document** | `docs/01_backend/API_CONTRACT.md` §3.3 |
| **Document claim** | "The exact gateway-level JWT enforcement mechanism is TBD — REQUIRES VERIFICATION (no gateway middleware handler file was located in the sampled files)." |
| **Code evidence** | `backend/docker/api_gateway_service.py` lines 421–430: JWT enforcement is fully implemented. `if JWT_SECRET and not any(path.startswith(p) for p in _AUTH_EXEMPT_PREFIXES):` — calls `verify_hs256_jwt(token, JWT_SECRET, audience=JWT_AUDIENCE, issuer=JWT_ISSUER)`. Missing/invalid token → 401 `UNAUTHORIZED`. Claims forwarded as `X-User-Id`, `X-User-Role`, `X-Tenant-Id` headers (lines 468–471). |
| **Delta** | JWT enforcement was implemented and documented, but the TBD annotation was never resolved. |
| **Remediation** | Resolve TBD in API_CONTRACT.md §3.3. **APPLIED** — see remediation log. |

---

### DELTA-006 — BACKEND_ARCHITECTURE.md: common_service.py marked TBD

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Document** | `docs/01_backend/BACKEND_ARCHITECTURE.md` §2 |
| **Document claim** | "`backend/docker/common_service.py` — TBD – REQUIRES VERIFICATION (not read in full; expected to contain shared service bootstrap helpers based on naming convention)." |
| **Code evidence** | `backend/docker/common_service.py`: A lightweight `BaseHTTPRequestHandler`-based HTTP server (Python stdlib, no uvicorn). Responds to `/health`, `/ready`, `/` with success payloads. Has NO service business logic. It is a minimal stub/fallback server for testing or basic health-check-only deployments — NOT a shared service bootstrap helper. |
| **Delta** | TBD was never resolved. The actual purpose is documented wrong ("expected to contain shared service bootstrap helpers"). |
| **Remediation** | Resolve TBD in BACKEND_ARCHITECTURE.md. **APPLIED** — see remediation log. |

---

### DELTA-007 — API_CONTRACT.md §4: "none of the 21 routes" count stale

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Document** | `docs/01_backend/API_CONTRACT.md` §4 Notes section |
| **Document claim** | "All 21 routes use `Route(expects_versioned_paths=False)`" |
| **Code evidence** | There are now 25 routes. All 25 use `expects_versioned_paths=False` (default). |
| **Delta** | Count stale. |
| **Remediation** | Update "21 routes" → "25 routes" in §4 Notes. **APPLIED** — see remediation log. |

---

### DELTA-008 — API_CONTRACT.md §2: "none of the 21 routes" count stale

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Document** | `docs/01_backend/API_CONTRACT.md` §2 |
| **Document claim** | "the upstream path equals the gateway path_prefix (none of the 21 routes set this)" |
| **Code evidence** | 25 routes; none set `expects_versioned_paths=True`. |
| **Delta** | Count stale. |
| **Remediation** | Update references. **APPLIED** — see remediation log. |

---

### DELTA-009 — API_CONTRACT.md: Missing audit RBAC documentation

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Document** | `docs/01_backend/API_CONTRACT.md` |
| **Document claim** | Lists `/api/v1/payroll`, `/api/v1/hiring`, `/api/v1/reporting` as RBAC-restricted. |
| **Code evidence** | `backend/docker/api_gateway_service.py` lines 66–71: `_ROUTE_ROLE_MAP` also restricts `/api/v1/audit` to `("Admin",)` only. This is NOT documented in API_CONTRACT.md. |
| **Delta** | `/api/v1/audit` route-level RBAC restriction (`Admin` only) is missing from API_CONTRACT.md. |
| **Remediation** | Add audit RBAC row to API_CONTRACT.md. **APPLIED** — see remediation log. |

---

### DELTA-010 — API_CONTRACT.md: Gateway header propagation undocumented

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Document** | `docs/01_backend/API_CONTRACT.md` §3.3 |
| **Document claim** | Describes JWT enforcement but does not describe downstream header propagation. |
| **Code evidence** | `backend/docker/api_gateway_service.py` lines 468–471: After JWT verification, claims are forwarded as `X-User-Id`, `X-User-Role`, `X-Tenant-Id` headers. This is how domain services receive the actor context they use for `actor_role`, `actor_id` parameters. |
| **Delta** | The JWT claim → downstream header propagation mechanism is undocumented but is the foundation for actor context in all service handlers. |
| **Remediation** | Add gateway header propagation to API_CONTRACT.md §3.3. **APPLIED** — see remediation log. |

---

### DELTA-011 — SERVICE_CATALOG: routes.py line reference stale

| Attribute | Detail |
|-----------|--------|
| **Severity** | Low |
| **Document** | `docs/01_backend/SERVICE_CATALOG.md` §Purpose section |
| **Document claim** | "path prefix appears in both `/backend/api-gateway/routes.py` (21 entries, lines 30-52)" |
| **Code evidence** | `routes.py` has 25 entries on lines 31–55. |
| **Delta** | Line numbers and count stale. |
| **Remediation** | Update SERVICE_CATALOG.md purpose section. **APPLIED** — see remediation log. |

---

### DELTA-012 — Dead code: `_employee_domain_departments()` in service_runtime.py

| Attribute | Detail |
|-----------|--------|
| **Severity** | Low |
| **Document** | N/A (code issue) |
| **Code fact** | `backend/docker/service_runtime.py` lines 132–218: `_employee_domain_departments()` is defined but never called after the Python employee-service implementation replaced the old stub. The function parses `domain-seed.ts` and returns fallback departments. The new `EmployeeService()` seeds departments directly from Python. |
| **Delta** | Dead code in service_runtime.py. |
| **Remediation** | **REQUIRES_OWNER_APPROVAL** — removing code from service_runtime.py. See OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md item OA-001. |

---

### DELTA-013 — Legacy product name "Aura HRMS" in api_gateway_service.py

| Attribute | Detail |
|-----------|--------|
| **Severity** | Low |
| **Document** | N/A (code issue) |
| **Code fact** | `backend/docker/api_gateway_service.py` lines 207, 237: OpenAPI spec and Swagger UI use `"Aura HRMS API"` and `"Aura HRMS API Docs"` as the title. Current product name per `docs/00_authority/PROJECT_CHARTER.md` is "Meridian HCM". |
| **Delta** | Legacy product name in code. Not a functional issue but appears in the public `/openapi.json` and `/docs` routes. |
| **Remediation** | **REQUIRES_OWNER_APPROVAL** — code change in api_gateway_service.py. See OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md item OA-002. |

---

## DELTA SUMMARY

| ID | Severity | Type | Status |
|----|----------|------|--------|
| DELTA-001 | Critical | Doc correction | APPLIED |
| DELTA-002 | Critical | Doc correction | APPLIED |
| DELTA-003 | Critical | Doc correction | APPLIED |
| DELTA-004 | High | Doc correction | APPLIED |
| DELTA-005 | High | TBD resolution | APPLIED |
| DELTA-006 | Medium | TBD resolution | APPLIED |
| DELTA-007 | Medium | Doc correction | APPLIED |
| DELTA-008 | Medium | Doc correction | APPLIED |
| DELTA-009 | Medium | Doc addition | APPLIED |
| DELTA-010 | Medium | Doc addition | APPLIED |
| DELTA-011 | Low | Doc correction | APPLIED |
| DELTA-012 | Low | Dead code | OWNER APPROVAL |
| DELTA-013 | Low | Legacy name in code | OWNER APPROVAL |
