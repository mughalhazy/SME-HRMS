# SECURITY DISCOVERY REPORT

Status: Active
Authority Level: High
Last Reviewed: 2026-06-15
Owner: AI

---

## PURPOSE

This report documents the backend security model — authentication, authorization, roles, permissions, tenant isolation, ownership rules, protected operations, administrative access paths, security assumptions, and known security gaps — exactly as implemented, based on direct inspection of:

- `backend/docker/api_gateway_service.py`
- `backend/jwt_utils.py`, `backend/rate_limiting.py`
- `backend/services/auth-service/service.py`, `api.py`
- `backend/middleware/tenant-context.ts`, `audit.ts`
- `backend/services/employee-service/rbac.middleware.ts`
- `backend/deployment/migrations/001_core_schema.sql`, `004_persistence_normalization.sql`, `005_tenant_foundation.sql`
- `backend/deployment/config/gateway-routes.json`, `backend/api-gateway/routes.py`
- `backend/docs/canon/security-model.md`, `capability-matrix.md`
- `docs/00_authority/DOMAIN_MODEL.md`, `PROJECT_CHARTER.md`
- `docs/07_governance/AI_OPERATING_CONTEXT.md`
- `docs/08_reports/GOVERNANCE_CONSISTENCY_AUDIT.md`, `01_backend/SERVICE_CATALOG.md`

Full normative detail lives in `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md` and `docs/03_fullstack_contracts/USER_ROLES_AND_PERMISSIONS.md`. This report summarizes findings and isolates gaps.

---

## 1. AUTHENTICATION MODEL

- **Mechanism**: JWT, HS256, HMAC-SHA256 signature. Tokens are issued by `auth-service` (`backend/services/auth-service/service.py` `_encode_token`) and verified at the API gateway (`backend/jwt_utils.py` `verify_hs256_jwt`) and independently re-verified inside at least one downstream service (`employee-service/rbac.middleware.ts` `validateSignature`).
- **Claims**: `sub`, `sid`, `jti`, `tenant_id`, `role`, `employee_id`, `department_id`, `capabilities`, `scopes`, `subject_type`, `iat`, `nbf`, `exp`, `iss`, `aud`.
- **Token lifetimes**: access token default 900s (15 min), refresh token default 604800s (7 days), bounded by `_validate_ttls` (60-3600s / 300-2,592,000s, refresh > access).
- **Refresh rotation**: each `POST /api/v1/auth/refresh` rotates the refresh token and issues a new `access_token_jti`, invalidating the prior access token (old `jti` no longer matches `session.access_token_jti`).
- **Logout / revocation**: `_revoke_session` sets `revoked=True` on the `SessionRecord`; subsequent `authenticate_token`/`refresh_session` calls reject with `TOKEN_REVOKED`.
- **Password hashing**: PBKDF2-HMAC-SHA256, 390,000 iterations, 16-byte random salt, stored as `salt_hex:key_hex`. Refresh tokens stored as SHA-256 hashes; comparisons use `hmac.compare_digest` (constant-time).
- **Minimum secret length**: 32 characters enforced both in `auth-service` (`AuthService.__init__`) and `employee-service` (`rbac.middleware.ts` module-level throw).
- **Exempt routes (no JWT at gateway)**: `/health`, `/ready`, `/metrics`, `/openapi.json`, `/docs`, `/api/v1/auth/*` (`api_gateway_service.py` line 55). The governance doc (`AI_OPERATING_CONTEXT.md` line 104) lists only `/health`, `/ready`, `/metrics`, `/api/v1/auth/*` — the implementation additionally exempts `/openapi.json` and `/docs` (static spec/docs endpoints).

---

## 2. AUTHORIZATION MODEL

- **Deny-by-default**: confirmed at multiple layers.
  - Gateway: missing/invalid/expired token on a non-exempt path → `401 UNAUTHORIZED` before any routing occurs.
  - Auth-service: `AuthService.require_capability` raises `FORBIDDEN` unless `validate_role` explicitly returns `True` (via explicit `Allow` policy or static `_ROLE_CAPABILITY_MAP` membership).
  - Employee-service: `authorizeEmployeeAction` denies (`403 FORBIDDEN`) unless the role's action list, the capability claim, the service-scope check, and (for Employee role on self-targeted actions) the self-scope check all pass.
- **Capability + Scope model (FD-008)**: an action is authorized only if the principal holds the required capability AND the applicable scope. Scope types: `Global`, `Department`, `Employee`, `Requisition` (canon-documented, not found validated in code), `Service`.
- **Policy override layer**: `PermissionPolicyRecord` (table `permission_policies`) allows explicit per-role-per-capability `Allow`/`Deny` overrides, versioned, taking precedence over the static `_ROLE_CAPABILITY_MAP`.
- **Gateway role gate (`_ROUTE_ROLE_MAP`)**: only 4 of ~20 gateway route prefixes carry a role allowlist:
  - `/api/v1/payroll` → `Admin`, `PayrollAdmin`, `Manager`
  - `/api/v1/audit` → `Admin`
  - `/api/v1/hiring` → `Admin`, `Manager`, `Recruiter`
  - `/api/v1/reporting` → `Admin`, `Manager`
  All other route prefixes (employees, departments, performance, attendance, leave, travel, projects, workflows, notifications, engagement, helpdesk, search, expense, integrations, automations, settings) have no gateway-level role restriction — any authenticated user of any role can reach them at the gateway; per-action authorization is delegated entirely to the upstream service.

---

## 3. ROLES

Six roles, per `docs/00_authority/PROJECT_CHARTER.md` §3 and confirmed in `auth-service/service.py` `_ROLE_CAPABILITY_MAP` and `employee-service/rbac.middleware.ts` `AuthRole`:

| Role | Summary |
|---|---|
| Admin | Tenant super-user, full HR access, all modules, bypasses scope checks |
| Manager | Department-scoped HR operations (employee mgmt, attendance, leave, performance) |
| Employee | Self-service (own attendance, leave, payslips, profile) |
| PayrollAdmin | Payroll processing/disbursement, banking, compliance |
| Recruiter | Hiring pipeline (job postings, candidates, interviews) |
| Service | Machine principal, API-to-API only, scopes declared at token issuance |

---

## 4. PERMISSIONS

- The static role→capability map (`_ROLE_CAPABILITY_MAP`) covers `CAP-EMP-001/002`, `CAP-ATT-001/002`, `CAP-LEV-001/002`, `CAP-PAY-001/002`, `CAP-HIR-001/002`, `CAP-PRF-001`, `CAP-AUT-001` — 12 of the 40+ capabilities enumerated in `backend/docs/canon/capability-matrix.md`.
- The remaining ~30 capabilities (`CAP-NOT-*`, `CAP-ENG-001`, `CAP-COM-*`, `CAP-DEC-*`, `CAP-EWA-*`, `CAP-BNK-*`, `CAP-RPT-*`, `CAP-WA-001`, `CAP-EXP-*`, `CAP-HLP-*`, `CAP-AUT-002/003`) are documented in canon (`capability-matrix.md`, `security-model.md`) but have **no confirmed role-binding mechanism** in the inspected code. They are marked `TBD – REQUIRES VERIFICATION` in `USER_ROLES_AND_PERMISSIONS.md` §3.3, capability-by-capability.
- `employee-service/rbac.middleware.ts` maintains its own local `ROLE_ACTIONS` / `ACTION_CAPABILITIES` tables — a second, service-local source of truth for that service's actions, layered on top of the JWT `capabilities` claim. This is a confirmed working pattern but its presence in other services is unverified.

---

## 5. TENANT ISOLATION

- **Schema-level invariant** (`docs/00_authority/DOMAIN_MODEL.md` lines 21-28, "MULTI-TENANCY INVARIANT"): every primary entity table has `tenant_id VARCHAR(80) NOT NULL`, a `UNIQUE (tenant_id, entity_id)` constraint, and all foreign keys are composite `(tenant_id, ref_id)`. Verified directly against `001_core_schema.sql` (departments, roles, employees) and `004_persistence_normalization.sql` (user_accounts, role_bindings, permission_policies, sessions, refresh_tokens).
- **JWT-to-request propagation**: gateway extracts `tenant_id` from the verified JWT, compares it against any client-supplied `X-Tenant-Id` header (mismatch → `403 FORBIDDEN`), and forwards `X-Tenant-Id` (and `X-User-Id`, `X-User-Role`) derived from the JWT to upstream services.
- **Service-level double-check**: `employee-service/rbac.middleware.ts` `ensureTenantConsistency` independently re-derives `tenant_id` from its own JWT decode and throws `TENANT_SCOPE_VIOLATION` (→ 403) on mismatch with the request's tenant header — a second, independent enforcement point beyond the gateway.
- **Default tenant**: `tenant-default` (`DEFAULT_TENANT_ID`), used when no tenant context is resolvable.

---

## 6. OWNERSHIP RULES

- **Self-scope ("Employee" scope)**: confirmed in `employee-service/rbac.middleware.ts` `isScopedToSelf` — for `Employee` role, `read`/`updateProfile` actions require `req.params.employeeId === auth.employee_id`.
- **Department scope ("Manager")**: Manager principals receive `scopes = [f'department:{department_id}']`. `require_scope` enforces exact scope-string membership for non-Admin roles. The behavioral extent of "department-scoped" filtering inside list/query endpoints (e.g., whether employee-service filters `SELECT` results by `department_id` for Managers) was **not directly observed** in the inspected files — `TBD – REQUIRES VERIFICATION`.
- **Service scope**: `Service` principals must carry `resource:<service-name>` or `service:internal` in `scopes`; `hasServiceScope` enforces this in employee-service.
- **Admin bypass**: `require_scope` short-circuits `True` for Admin; `hasRequiredCapability` short-circuits `True` for Admin; `ROLE_ACTIONS.Admin` includes all defined actions.

---

## 7. PROTECTED OPERATIONS

- **Identity & access administration** (`CAP-AUT-001`, `/api/v1/auth/users`, `/api/v1/auth/sessions`, `/api/v1/auth/policies`, `/api/v1/auth/access`): Admin-only per `_ROLE_CAPABILITY_MAP` and `security-model.md` line 29 (Deny for all other roles, including Service).
- **Payroll disbursement** (`CAP-PAY-002`): Admin and PayrollAdmin only (per `_ROLE_CAPABILITY_MAP`: `CAP-PAY-002` present only for Admin; per `security-model.md`, PayrollAdmin also `Allow`).
- **Audit log access** (`/api/v1/audit`): gateway-enforced Admin-only (`_ROUTE_ROLE_MAP`).
- **Compensation management** (`manageCompensation` → `CAP-PAY-002`): in employee-service, only Admin/Service can manage compensation per `ROLE_ACTIONS`; PayrollAdmin is read-only (`readCompensation`/`listCompensation` only, confirmed by the explicit PayrollAdmin allowlist at `rbac.middleware.ts` lines 287-290).
- **Session revocation** (`POST /api/v1/auth/sessions/{id}/revoke`): exposed via auth-service `api.py`, but **no explicit role/capability check was found in the auth-service handler itself** — see Gap G-1 below.

---

## 8. ADMINISTRATIVE ACCESS PATHS

- `Admin` role: full bypass of scope checks (`require_scope`), full `_ROLE_CAPABILITY_MAP` coverage including `CAP-AUT-001` (identity/access admin), gateway role allowlists all include `Admin` where present.
- `PermissionPolicyRecord` upsert (`upsert_permission_policy`, `service.py` lines 583-623): allows runtime override of any role's capability effect (`Allow`/`Deny`), versioned. **No caller-side authorization check was found inside `upsert_permission_policy` itself** — it is presumably gated by the `CAP-AUT-001` capability at the API/gateway layer for whichever endpoint invokes it (`/api/v1/auth/policies` per `capability-matrix.md`), but this was not directly traced to a handler in `auth-service/api.py` (`api.py` does not appear to expose a `post_auth_policies` handler in the inspected file). — `TBD – REQUIRES VERIFICATION` (see Gap G-2).
- `assign_role_binding` / `revoke_role_binding` (`service.py` lines 518-581): similarly, no in-function authorization check; presumed gated externally via `CAP-AUT-001`.

---

## 9. SECURITY ASSUMPTIONS

1. `JWT_SECRET` is non-empty in all deployed environments. If empty, the gateway **disables JWT enforcement entirely** for all routes (`if JWT_SECRET and not any(...)`, `api_gateway_service.py` line 421) — this is an environment-configuration assumption, not a verified runtime guarantee.
2. The in-process `SlidingWindowRateLimiter` (200 req/min/IP) assumes either a single gateway instance or per-instance rate limiting is acceptable — state is not shared across replicas (`rate_limiting.py` `_buckets: dict[str, deque[float]]`, in-memory).
3. Client IP for rate limiting trusts `X-Forwarded-For`/`X-Real-Ip` headers — assumes these are set by a trusted reverse proxy/load balancer in front of the gateway and cannot be spoofed by the client directly. No evidence of an allowlist of trusted proxy IPs was found.
4. Tenant consistency checks (gateway and employee-service) assume the JWT `tenant_id` claim is trustworthy because the JWT signature has been verified — this holds as long as `JWT_SECRET` is kept confidential and tokens are only issued by `auth-service`.
5. Service-to-service calls rely on the `Service` role + `scopes` claim (`service:internal`, `resource:<service-name>`) issued by auth-service at token issuance; no mTLS or network-level service identity was observed in the inspected files (`TBD – REQUIRES VERIFICATION` for service mesh / network policy enforcement).
6. Audit log sanitization (`_SENSITIVE_FIELD_NAMES` in auth-service) redacts known-sensitive field names from audit `before`/`after` payloads — this assumes all sensitive field names are enumerated in that fixed set; new sensitive fields added elsewhere would not be auto-redacted unless added to this list.

---

## 10. KNOWN SECURITY GAPS

### G-1: Session administration endpoints lack a visible explicit role check
`GET /api/v1/auth/sessions` (list all sessions, optionally filtered by `user_id`/`tenant_id`) and `POST /api/v1/auth/sessions/{id}/revoke` (`auth-service/api.py` `get_auth_sessions`, `post_auth_session_revoke`) are exposed under `/api/v1/auth/*`, which is **exempt from gateway JWT enforcement** and from `_ROUTE_ROLE_MAP`. The handlers in `api.py` do not call `require_capability`/`validate_role`/role-check logic before executing `list_sessions`/`revoke_session`. Per `capability-matrix.md` (`CAP-AUT-001`) and `security-model.md` (Identity and access administration: Allow Admin only, Deny all others), this should be Admin-only. **As implemented, the enforcement point for this restriction was not located** — it is either (a) enforced by a wrapper/router not present in the inspected files, or (b) a gap where any caller who can reach the auth-service directly (bypassing gateway role checks, since `/api/v1/auth/*` skips them) could list/revoke arbitrary sessions. Severity: High if (b). **TBD – REQUIRES VERIFICATION.**

### G-2: Permission-policy and role-binding mutation endpoints lack a visible authorization check
`AuthService.upsert_permission_policy`, `assign_role_binding`, `revoke_role_binding` (`service.py`) contain no internal capability/role check. These are the most privileged mutations in the system (they can grant/deny any capability to any role, or rebind any user's role/scope). If the HTTP handlers that call these methods (not found in the inspected `api.py`) do not gate on `CAP-AUT-001` + Admin role, this is a privilege-escalation path. **TBD – REQUIRES VERIFICATION** — requires locating the handler(s) for `/api/v1/auth/policies` and `/api/v1/auth/access` (per `capability-matrix.md` route categories for `CAP-AUT-001`), which were not present in `backend/services/auth-service/api.py` as inspected.

### G-3: Gateway role allowlist covers only 4 of ~20 route groups
`_ROUTE_ROLE_MAP` in `api_gateway_service.py` only restricts `/api/v1/payroll`, `/api/v1/audit`, `/api/v1/hiring`, `/api/v1/reporting`. All other route groups (employees, performance, attendance, leave, travel, projects, workflows, notifications, engagement, helpdesk, expense, integrations, automations, settings, search) have no gateway-level role restriction. This is consistent with the documented design ("gateway only checks role, not scope" — scope/role enforcement pushed to services), but means a misconfigured or unprotected downstream service for any of these route groups would have **no gateway-level role backstop**. Confirmed defense-in-depth exists for employee-service (`rbac.middleware.ts`); unverified for the others.

### G-4: 4 services with unconfirmed/absent gateway routes — direct-reachability risk
Per `backend/api-gateway/routes.py` and `backend/deployment/config/gateway-routes.json`, the following services have **no route registered at the gateway** (confirmed in `docs/01_backend/SERVICE_CATALOG.md` §21-24, each marked "GATEWAY ROUTE: TBD"):

| # | Service | Port | Capabilities owned | Gateway route status |
|---|---|---|---|---|
| 21 | `compliance-service` | 8021 | `CAP-COM-001/002/003` | Not in `routes.py`/`gateway-routes.json`. `/api/v1/compliance` absent. |
| 22 | `decision-service` | 8022 | `CAP-DEC-001/002/003` | Not in `routes.py`/`gateway-routes.json`. `/api/v1/decisions` absent. |
| 23 | `bank-service` | 8023 | `CAP-BNK-001/002/003` | Not in `routes.py`/`gateway-routes.json`. `/api/v1/banking` absent. |
| 24 | `whatsapp-service` | 8024 | `CAP-WA-001` | Not in `routes.py`/`gateway-routes.json`. `/api/v1/whatsapp` absent. |

(`ewa-financial-service` / `CAP-EWA-001/002` is additionally noted in `SERVICE_CATALOG.md` as not present as a docker-compose service at all — a 5th capability owner with no confirmed deployment, separate from the 4 above.)

**Security implication**: Because `resolve_route()` in `backend/api-gateway/routes.py` raises `RouteNotFoundError` (→ `404 ROUTE_NOT_FOUND`) for any path not matching a registered route prefix, requests to `/api/v1/compliance/*`, `/api/v1/decisions/*`, `/api/v1/banking/*`, `/api/v1/whatsapp/*` **cannot currently be proxied through the gateway at all** — the gateway's JWT validation, tenant-consistency check, and rate limiting would all execute (since these checks happen before route resolution at lines 421-448), but the request would then 404 rather than reach the service.

This means: **if these 4 services are also directly network-reachable** (e.g., their container ports 8021-8024 are exposed on a network the gateway's clients can also reach, bypassing the gateway entirely), then **all of the gateway's protections — JWT validation, tenant-header consistency, rate limiting, `_ROUTE_ROLE_MAP` — would be bypassed** for those services. Their security posture would then depend entirely on whatever authentication/authorization those services implement internally (unverified — not inspected in this pass, `TBD – REQUIRES VERIFICATION`). If these services are *not* directly network-reachable (e.g., isolated on an internal Docker network with no exposed ports to clients), they are effectively unreachable in their current configuration (neither directly nor via gateway), which is a functional gap but not a security exposure. **Network topology / port exposure was not verified in this pass** — this is the single highest-priority follow-up item for security posture of these 4 services.

### G-5: Salary/compensation field-level response filtering not located
`AI_OPERATING_CONTEXT.md` (KNOWN_CONSTRAINTS) and `security-model.md` both require salary/compensation data to be filtered from API responses for non-PayrollAdmin/Admin roles. The inspected code confirms **capability-level** gating (Employee role lacks `readCompensation`/`listCompensation`/`manageCompensation` actions in `employee-service/rbac.middleware.ts`), which prevents Employee from calling compensation-specific endpoints. However, no **field-level response filter** (e.g., stripping `base_salary` from a general employee-profile response returned to a Manager or Employee viewing another employee's record) was located. `AuthService._SENSITIVE_FIELD_NAMES` only governs audit-log redaction, not API response shaping. `TBD – REQUIRES VERIFICATION`.

### G-6: Capability coverage gap — ~30 of 40+ capabilities have no confirmed role binding
`_ROLE_CAPABILITY_MAP` in `auth-service/service.py` only defines grants for 12 capability IDs. The remaining capabilities listed in `backend/docs/canon/capability-matrix.md` (notification, engagement, compliance, decision, EWA, banking, reporting, WhatsApp, expense, helpdesk, automation) have no confirmed mechanism granting them to any role's JWT `capabilities` claim. If a service checks `principal.capabilities` (the JWT claim) for one of these capability IDs, and the JWT issuance code never populates that capability for any role, **the corresponding feature would be unreachable for all roles including Admin** (deny-by-default would deny everyone) — unless that service instead relies on its own local role-action table (as employee-service does) rather than the JWT `capabilities` claim. Each of these capabilities is individually marked `TBD – REQUIRES VERIFICATION` in `USER_ROLES_AND_PERMISSIONS.md` §3.3.

### G-7: Rate limiter state is per-process/in-memory
`SlidingWindowRateLimiter` stores buckets in a process-local `dict`. In a horizontally-scaled gateway deployment (multiple replicas), each replica enforces its own 200 req/min/IP limit independently, effectively multiplying the aggregate allowed rate by the replica count. Not a vulnerability per se, but a deviation from the documented "200 req/min per IP" if read as a global guarantee. `TBD – REQUIRES VERIFICATION` (deployment topology / replica count not in scope of this capture).

---

## 11. CROSS-REFERENCES

- `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md`
- `docs/03_fullstack_contracts/USER_ROLES_AND_PERMISSIONS.md`
- `backend/docs/canon/security-model.md`
- `backend/docs/canon/capability-matrix.md`
- `docs/01_backend/SERVICE_CATALOG.md` (§21-24, gateway route status for compliance/decision/bank/whatsapp services)
- `docs/07_governance/AI_OPERATING_CONTEXT.md` (KNOWN_CONSTRAINTS)
- `docs/00_authority/DOMAIN_MODEL.md` (MULTI-TENANCY INVARIANT, ROLE BINDING)
- `docs/08_reports/GOVERNANCE_CONSISTENCY_AUDIT.md`
