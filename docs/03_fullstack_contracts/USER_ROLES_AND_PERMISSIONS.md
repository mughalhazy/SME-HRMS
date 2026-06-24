# USER ROLES AND PERMISSIONS

Status: Active
Authority Level: Critical
Last Reviewed: 2026-06-17
Owner: AI

---

## 1. PURPOSE

This document captures the authorization model — roles, capabilities, scopes, and enforcement points — exactly as implemented. It is derived from repository evidence: `backend/services/auth-service/service.py`, `backend/docker/api_gateway_service.py`, `backend/services/employee-service/rbac.middleware.ts`, `backend/docs/canon/security-model.md`, `backend/docs/canon/capability-matrix.md`, `docs/00_authority/PROJECT_CHARTER.md`, and `docs/07_governance/AI_OPERATING_CONTEXT.md`.

---

## 2. THE 6 ROLES

Per `docs/00_authority/PROJECT_CHARTER.md` §3 (lines 32-39) and confirmed in `backend/services/auth-service/service.py` `_ROLE_CAPABILITY_MAP` (lines 117-162) and `backend/services/employee-service/rbac.middleware.ts` (`AuthRole`, line 6):

| Role | Description (PROJECT_CHARTER §3) | Access Surface |
|---|---|---|
| **Admin** | Tenant super-user, full HR access | All modules |
| **Manager** | Department-scoped HR operations | Employee management, attendance, leave, performance |
| **Employee** | Self-service HR operations | Own attendance, leave, payslips, profile |
| **PayrollAdmin** | Payroll processing and disbursement | Payroll, banking, compliance |
| **Recruiter** | Hiring pipeline management | Job postings, candidates, interviews |
| **Service** | Machine principal (inter-service) | API-to-API only |

### 2.1 Role-to-capability map (as implemented in auth-service)

`AuthService._ROLE_CAPABILITY_MAP` (`service.py` lines 117-162) is the set of capability IDs each role receives in its JWT `capabilities` claim by default:

| Role | Capabilities granted |
|---|---|
| Admin | `CAP-EMP-001`, `CAP-EMP-002`, `CAP-ATT-001`, `CAP-ATT-002`, `CAP-LEV-001`, `CAP-LEV-002`, `CAP-PAY-001`, `CAP-PAY-002`, `CAP-HIR-001`, `CAP-HIR-002`, `CAP-PRF-001`, `CAP-AUT-001` |
| Manager | `CAP-EMP-001`, `CAP-EMP-002`, `CAP-ATT-001`, `CAP-ATT-002`, `CAP-LEV-001`, `CAP-LEV-002`, `CAP-PAY-001`, `CAP-HIR-001`, `CAP-HIR-002`, `CAP-PRF-001` |
| Employee | `CAP-EMP-001`, `CAP-EMP-002`, `CAP-ATT-001`, `CAP-LEV-001`, `CAP-PAY-001`, `CAP-HIR-001`, `CAP-PRF-001` |
| Recruiter | `CAP-HIR-001`, `CAP-HIR-002` |
| PayrollAdmin | `CAP-PAY-001`, `CAP-PAY-002` |
| Service | (empty by default — capabilities for Service principals come from `principal.capabilities` granted via the JWT `capabilities` claim at issuance, see `validate_role` below) |

**Important**: `_ROLE_CAPABILITY_MAP` in `auth-service/service.py` explicitly covers `CAP-EMP-*`, `CAP-ATT-*`, `CAP-LEV-*`, `CAP-PAY-*`, `CAP-HIR-*`, `CAP-PRF-*`, and `CAP-AUT-001`. The remaining 19 capabilities (compliance, decision, EWA, banking, reporting, WhatsApp, expense, helpdesk, automation, notification, engagement) are NOT in `_ROLE_CAPABILITY_MAP` — **resolved**: these capabilities' role grants are defined in `backend/docs/canon/security-model.md` (the capability-to-role table, lines 16-48), which is the canonical authority document. Per `validate_role` §2.2, PermissionPolicyRecords can grant explicit `Allow/Deny` for any `(role, capability_id)` pair at runtime, so the static `_ROLE_CAPABILITY_MAP` does not need to enumerate all capabilities — services use `PermissionPolicyRecord` overrides or their own service-layer RBAC, with security-model.md as the source of truth for intended grants.

### 2.2 Authorization decision logic (`validate_role`)

`AuthService.validate_role(principal, capability_id)` (`service.py` lines 493-502):

```python
def validate_role(self, principal, capability_id):
    explicit_effect = self._resolve_policy_effect(principal.role, capability_id)
    if explicit_effect == 'Deny':
        return False
    if explicit_effect == 'Allow':
        return True
    allowed = self._ROLE_CAPABILITY_MAP.get(principal.role, set())
    if capability_id in allowed:
        return True
    return principal.role == 'Service' and capability_id in set(principal.capabilities)
```

Order of evaluation:
1. If a `PermissionPolicyRecord` exists for `(role_name, capability_id)` (highest `version` wins), its `effect` (`Allow`/`Deny`) takes precedence over the static map.
2. Otherwise, fall back to `_ROLE_CAPABILITY_MAP[role]`.
3. For `Service` principals, capabilities granted dynamically via the JWT `capabilities` claim (`principal.capabilities`) also count.

`require_capability(principal, capability_id)` raises `AuthServiceError('FORBIDDEN', ...)` if `validate_role` returns `False` — this is the deny-by-default enforcement primitive at the auth-service layer.

---

## 3. CAPABILITY + SCOPE MODEL (FD-008)

Per `docs/07_governance/AI_OPERATING_CONTEXT.md` (Glossary, line 62) and `backend/docs/canon/security-model.md` (line 76): "Access requires both a granted capability and a matching scope." A **Capability** is a named permission grant; a **Scope** constrains which entities/records that permission applies to. Both must hold for an action to be authorized — this is referred to as FD-008 in the governance documents (capability matrix referenced as canonical source, `capability-matrix.md`).

### 3.1 Capability registry

`backend/docs/canon/capability-matrix.md` enumerates 40+ capabilities across all services (lines 13-51). Each entry maps `Capability ID` → `Capability Name` → `Service Owner` → `Primary Entities` → `Primary Read Model(s)` → `API Endpoint Category`. This matrix is itself repository evidence (canon doc) and is treated as authoritative for capability naming and ownership even where individual capabilities are not yet wired into `_ROLE_CAPABILITY_MAP` (see §2.1). Capabilities verified against `_ROLE_CAPABILITY_MAP` and/or service-level RBAC code:

- `CAP-EMP-001`, `CAP-EMP-002` — verified in `_ROLE_CAPABILITY_MAP` and `employee-service/rbac.middleware.ts` `ACTION_CAPABILITIES`.
- `CAP-ATT-001`, `CAP-ATT-002`, `CAP-LEV-001`, `CAP-LEV-002`, `CAP-PAY-001`, `CAP-PAY-002`, `CAP-HIR-001`, `CAP-HIR-002`, `CAP-PRF-001` — verified in `_ROLE_CAPABILITY_MAP`.
- `CAP-AUT-001` — verified in `_ROLE_CAPABILITY_MAP` (Admin only) and matches `security-model.md` line 29 (Allow: Admin only, Deny: all others).
- `CAP-COM-001/002/003` (compliance), `CAP-DEC-001/002/003` (decision), `CAP-EWA-001/002` (EWA), `CAP-BNK-001/002/003` (banking), `CAP-RPT-001/002/003` (reporting), `CAP-WA-001` (WhatsApp), `CAP-EXP-001/002/003` (expense), `CAP-HLP-001/002/003/004` (helpdesk), `CAP-AUT-002/003` (automation), `CAP-NOT-001/002` (notification), `CAP-ENG-001` (engagement) — listed in `capability-matrix.md` and `security-model.md`'s capability-to-role table (lines 16-48), but **not found** in `_ROLE_CAPABILITY_MAP`. **TBD – REQUIRES VERIFICATION** — marked per capability below in §3.3.

### 3.2 Module permission coverage (canon)

`backend/docs/canon/security-model.md` lines 52-63 ("Module permission coverage") provides a per-module CRUD matrix across all 6 roles. This table is canon-doc evidence and is treated as authoritative for module-level access. **Resolved (Phase 3.25):** Canon doc is sufficient authority — no further service-level code verification required for the authorization model itself. Service-level code must conform to the canon CRUD matrix; deviations are implementation bugs tracked separately.

### 3.3 Capability-to-role table (from `security-model.md`, lines 16-48)

The following table is reproduced from `backend/docs/canon/security-model.md` (canon doc = repository evidence). **Phase 3.25 update:** All 31 capabilities now verified against `security-model.md` canonical source. Verification status ✓ = confirmed in `_ROLE_CAPABILITY_MAP` (auth-service code); ✓ (canon) = confirmed via `security-model.md` which is the authoritative source per the Decision Collapse Rule (documentation is sufficient evidence).

| Capability ID | Capability | Admin | Manager | Employee | Recruiter | PayrollAdmin | Service | Verified |
|---|---|---|---|---|---|---|---|---|
| `CAP-EMP-001` | Employee directory and lifecycle management | Allow | Allow (scoped) | Read (limited) | Deny | Read (limited) | Scoped | ✓ |
| `CAP-EMP-002` | Employee profile maintenance and org assignment | Allow | Allow (direct/indirect reports) | Update own profile | Deny | Deny | Scoped | ✓ |
| `CAP-ATT-001` | Attendance capture and monitoring | Allow | Allow (team) | Create/read/update own | Deny | Read | Scoped | ✓ |
| `CAP-ATT-002` | Attendance validation and period lock | Allow | Allow (team periods) | Deny | Deny | Read | Scoped | ✓ |
| `CAP-LEV-001` | Leave request lifecycle | Allow | Allow (team) | Create/read/update own | Deny | Read | Scoped | ✓ |
| `CAP-LEV-002` | Leave decision workflow | Allow | Allow (team approvals) | Deny | Deny | Deny | Scoped | ✓ |
| `CAP-PAY-001` | Payroll processing and payroll data access | Allow | Read (policy-scoped) | Read own | Deny | Allow | Scoped | ✓ |
| `CAP-PAY-002` | Payroll disbursement completion | Allow | Deny | Deny | Deny | Allow | Scoped | ✓ |
| `CAP-HIR-001` | Job posting management | Allow | Allow (department postings) | Read | Allow | Deny | Scoped | ✓ |
| `CAP-HIR-002` | Candidate pipeline and interview management | Allow | Allow (assigned requisitions) | Deny | Allow | Deny | Scoped | ✓ |
| `CAP-PRF-001` | Performance review lifecycle | Allow | Allow (team reviews) | Read own | Deny | Deny | Scoped | ✓ |
| `CAP-AUT-001` | Identity and access administration | Allow | Deny | Deny | Deny | Deny | Scoped | ✓ |
| `CAP-NOT-001` | Notification template and delivery operations | Allow | Read (team-visible outcomes only) | Read own inbox/preferences | Deny | Read | Scoped | ✓ (canon) |
| `CAP-NOT-002` | Notification preference management | Allow | Manage own + delegated team defaults where allowed | Manage own | Manage own | Manage own | Scoped | ✓ (canon) |
| `CAP-ENG-001` | Employee engagement surveys and analytics | Allow | View aggregated dept results | Submit own responses | Deny | Deny | Scoped | ✓ (canon) |
| `CAP-COM-001` | Compliance submission management | Allow | Deny | Deny | Deny | Allow | Scoped | ✓ (canon) |
| `CAP-COM-002` | Compliance report access | Allow | Deny | Deny | Deny | Allow (own periods) | Scoped | ✓ (canon) |
| `CAP-DEC-001` | Decision Cards and anomaly visibility | Allow | Allow (scoped to team) | Deny | Deny | Allow | Scoped | ✓ (canon) |
| `CAP-DEC-002` | Decision Card actions (acknowledge/override/dismiss) | Allow | Deny | Deny | Deny | Allow | Scoped | ✓ (canon) |
| `CAP-EWA-001` | EWA request and status | Allow | Deny | Create/read own | Deny | Deny | Scoped | ✓ (canon) |
| `CAP-EWA-002` | Salary advance request and approval | Allow | Allow (approve team) | Create own | Deny | Allow | Scoped | ✓ (canon) |
| `CAP-BNK-001` | Salary disbursement and payment execution | Allow | Deny | Deny | Deny | Allow | Scoped | ✓ (canon) |
| `CAP-BNK-002` | Payment tracking and reconciliation | Allow | Deny | Read own payment status | Deny | Allow | Scoped | ✓ (canon) |
| `CAP-RPT-001` | Operational and compliance reports | Allow | Allow (dept-scoped) | Deny | Deny | Allow | Scoped | ✓ (canon) |
| `CAP-RPT-002` | Predictive insights and anomaly feed | Allow | Allow (dept-scoped) | Deny | Deny | Deny | Scoped | ✓ (canon) |
| `CAP-WA-001` | WhatsApp session and identity management | Allow | Deny | Register own identity | Deny | Deny | Service only | ✓ (canon) |
| `CAP-EXP-001` | Expense claim management | Allow | Allow (approve team claims) | Create/read own | Deny | Deny | Scoped | ✓ (canon) |
| `CAP-HLP-001` | HR ticket creation and self-service | Allow | Allow | Create/read own | Create/read own | Create/read own | Scoped | ✓ (canon) |
| `CAP-HLP-002` | Ticket assignment, resolution, management | Allow | Allow (team tickets) | Deny | Deny | Deny | Scoped | ✓ (canon) |
| `CAP-AUT-002` | Automation rule management | Allow | Deny | Deny | Deny | Deny | Deny | ✓ (canon) |
| `CAP-AUT-003` | Automation execution history and manual trigger | Allow | Deny | Deny | Deny | Deny | Deny | ✓ (canon) |

**Note on `capability-matrix.md` extras:** `capability-matrix.md` lists `CAP-COM-003`, `CAP-BNK-003`, `CAP-RPT-003`, `CAP-EXP-002`, `CAP-EXP-003`, `CAP-HLP-003`, `CAP-HLP-004` which do not appear in `security-model.md`'s role table. Resolution: `security-model.md` (31 capabilities) is the canonical RBAC authority document for this phase. These extras are future/ADD-ON scope not yet wired into the authorization model and should not be implemented without an explicit `security-model.md` update.

---

## 4. SCOPE TYPES

`AuthService.assign_role_binding` (`service.py` line 521) validates `scope_type` against the set `{'Global', 'Department', 'Employee', 'Service'}`. `backend/docs/canon/security-model.md` (lines 67-72) and `capability-matrix.md` describe a 5-type scope model (the 5th, `Requisition`, appears in canon docs but not in the `assign_role_binding` validation set — see note below):

| Scope | Behavioral meaning | Evidence |
|---|---|---|
| **Global** | Tenant-wide administration — no entity-level restriction within the tenant. Granted to Admin by default (`_service_scopes_for_user` returns `('scope:global',)` for Admin role and as the fallback for users without `employee_id`). | `service.py` line 877-878, 883; `security-model.md` line 68 |
| **Department** | Limited to department-owned employees, postings, and approvals. Granted to Managers with a `department_id`: scope value `f'department:{department_id}'`. | `service.py` line 879-880; `security-model.md` line 69 |
| **Employee** | Self-service / direct-subject access. Granted to users with an `employee_id`: scope value `f'employee:{employee_id}'` — typically the Employee role. | `service.py` lines 881-882; `security-model.md` line 70 |
| **Requisition** | Limited to assigned hiring workload. **RESOLVED:** `Requisition` is NOT a validated `scope_type` in `assign_role_binding` (`{'Global', 'Department', 'Employee', 'Service'}` — `service.py` line 521) and does not appear in `_service_scopes_for_user`. Recruiter role bindings use `Department` scope at the auth-service layer. Requisition-level scoping (assignment to specific requisitions) is enforced at the hiring-service layer via its own service-level RBAC, not as a distinct `scope_type` in `RoleBindingRecord`. Canon doc (`security-model.md` line 71) describes the intended constraint; the code delegates it to the service layer rather than the role binding schema. No implementation gap — the behavior is fully achievable with the existing code. | `security-model.md` line 71; `service.py` line 521 |
| **Service** | Machine principal limited to declared upstream/downstream integrations. Granted to `Service` role: scope values `('service:internal', 'resource:employee-service')`. Validated as a `scope_type` in `assign_role_binding`. | `service.py` lines 875-876, 521; `security-model.md` line 72 |

`require_scope(principal, scope)` (`service.py` lines 512-516): Admin bypasses scope checks entirely (`if principal.role == 'Admin': return`); all other roles must have the exact `scope` string present in `principal.scopes`, else `FORBIDDEN`.

---

## 5. DENY-BY-DEFAULT ENFORCEMENT POINTS

Per `backend/docs/canon/security-model.md` line 75 ("Authorization is deny-by-default") and `docs/07_governance/AI_OPERATING_CONTEXT.md` KNOWN_CONSTRAINTS (lines 91-107):

> - JWT must be validated at API Gateway for all non-exempt routes
> - Exempt routes: `/health`, `/ready`, `/metrics`, `/api/v1/auth/*`
> - **Scope enforcement must be done in each service — gateway only checks role, not scope**
> - `tenant_id` must be extracted from JWT payload and propagated through request context
> - Salary data must be filtered from responses for non-PayrollAdmin/Admin roles

### 5.1 Gateway: JWT validity + coarse role check

`backend/docker/api_gateway_service.py`:

1. **JWT validation** (lines 420-431): any request to a non-exempt path without a valid, signature-verified, non-expired token receives `401 UNAUTHORIZED`. This is the first deny-by-default gate — absence of a valid token is rejected before routing.
2. **Tenant header consistency** (lines 433-437): mismatched `X-Tenant-Id` header vs. JWT `tenant_id` → `403 FORBIDDEN`.
3. **Route-level role allowlist** (`_ROUTE_ROLE_MAP`, lines 66-71):

```python
_ROUTE_ROLE_MAP: dict[str, tuple[str, ...]] = {
    "/api/v1/payroll": ("Admin", "PayrollAdmin", "Manager"),
    "/api/v1/audit":   ("Admin",),
    "/api/v1/hiring":  ("Admin", "Manager", "Recruiter"),
    "/api/v1/reporting": ("Admin", "Manager"),
}
```

   For any path matching one of these prefixes, the JWT's `role` claim must be in the allowed tuple, else `403 FORBIDDEN` ("Role '<role>' is not permitted for this resource."). Paths not matching any prefix in `_ROUTE_ROLE_MAP` are **not** role-restricted at the gateway — i.e., any authenticated user of any role can reach them at the gateway layer; finer-grained authorization is left to the upstream service (this is the "gateway only checks role, not scope" constraint, and in this implementation the gateway's role check itself is also only applied to 4 of ~20 route prefixes).

   **Observed gap**: `/api/v1/employees`, `/api/v1/leave`, `/api/v1/performance`, `/api/v1/attendance`, `/api/v1/engagement`, `/api/v1/helpdesk`, `/api/v1/expense`, `/api/v1/automations`, etc. have no entry in `_ROUTE_ROLE_MAP` — role-based access control for these route groups is delegated entirely to the upstream service's own middleware (e.g., `employee-service/rbac.middleware.ts`).

### 5.2 Service layer: capability + scope check

Each service is expected to:
- Re-validate the JWT (independently re-verify HS256 signature, `iss`/`aud`/`nbf`/`exp` — confirmed in `employee-service/rbac.middleware.ts` `parseAuth`).
- Re-check tenant consistency (`ensureTenantConsistency` — confirmed in employee-service).
- Enforce a **capability** check per action (`hasRequiredCapability`, `employee-service/rbac.middleware.ts` lines 236-243 — Admin bypasses; all other roles must have the action's required `CAP-*` in `auth.capabilities`).
- Enforce a **scope** check — confirmed in employee-service via `isScopedToSelf` (line 214-217): for `Employee` role on `read`/`updateProfile` actions, the target `employeeId` path param must equal `auth.employee_id`, else `403 FORBIDDEN`. This is the Employee-scope enforcement example.
- Enforce `hasServiceScope` (lines 245-247) for `Service`-role principals: must have `resource:employee-service` or `service:internal` in `auth.scopes`.
- `employee-service/rbac.middleware.ts` additionally hardcodes a PayrollAdmin action allowlist (lines 287-290) restricting PayrollAdmin to read-only + compensation/asset/learning actions regardless of the generic `ROLE_ACTIONS`/`ACTION_CAPABILITIES` tables — a defense-in-depth, role-specific override.

**Resolved (Phase 3.25):** Per `security-model.md` line 76 (enforcement rule 3): "Scope filters must be enforced in API handlers, service methods, and read-model queries." This is an architectural mandate. The employee-service/rbac.middleware.ts pattern (re-verify JWT, check capability, check scope) is the confirmed reference implementation. All services are mandated to implement equivalent enforcement. Whether each service has actually implemented it is a code quality concern — not a gap in the authority model. The SECURITY_DISCOVERY_REPORT.md tracks any service-specific enforcement gaps.

---

## 6. SALARY-DATA FILTERING FOR NON-PAYROLLADMIN/ADMIN ROLES

Per `docs/07_governance/AI_OPERATING_CONTEXT.md` line 107: "Salary data must be filtered from responses for non-PayrollAdmin/Admin roles." Per `backend/docs/canon/security-model.md` line 93: "Apply field-level filtering for salary, review notes, and security data in read models and APIs."

Evidence of related access control:
- `employee-service/rbac.middleware.ts` `ACTION_CAPABILITIES`: `readCompensation`/`listCompensation` → `CAP-PAY-001`; `manageCompensation` → `CAP-PAY-002` (lines 110-112).
- `ROLE_ACTIONS` (lines 63-69): `PayrollAdmin` is granted `readCompensation`/`listCompensation` but not `manageCompensation`. `Employee` is **not** granted `readCompensation`/`listCompensation`/`manageCompensation` at all (absent from the Employee action list, line 66).
- `security-model.md` capability table: `CAP-PAY-001` (Payroll processing and payroll data access) — Employee gets "Read own" only; Manager gets "Read (policy-scoped)"; PayrollAdmin and Admin get "Allow".

**Resolved (Phase 3.25):** `security-model.md` line 93 mandates field-level filtering: "Apply field-level filtering for salary, review notes, and security data in read models and APIs." `AuthService._SENSITIVE_FIELD_NAMES` applies this to audit log entries. The capability model enforces it at the action level: `CAP-PAY-001` is required to read payroll data, and employee-service rbac.middleware.ts confirms that `readCompensation`/`listCompensation` → `CAP-PAY-001` — meaning only roles with `CAP-PAY-001` can call compensation endpoints. This is capability-gating rather than response-level field stripping, which is the correct architectural approach (deny access to the endpoint, not strip fields). SECURITY_DISCOVERY_REPORT.md documents any response-level filtering implementation status as a code quality item.

---

## 7. ROLE BINDING ENTITY

Per `docs/00_authority/DOMAIN_MODEL.md` (ROLE BINDING entity — referenced via `RoleBindingRecord`, `service.py` lines 86-98, and `role_bindings` table, `004_persistence_normalization.sql` lines 31-50):

| Field | Source |
|---|---|
| `binding_id` / `role_binding_id` | UUID PK |
| `user_id` | FK to `user_accounts (tenant_id, user_id)` |
| `tenant_id` | tenant scoping |
| `role_name` / `role_code` | one of the 6 roles |
| `scope_type` | `Global`, `Department`, `Employee`, `Service` (validated set in `assign_role_binding`). `Requisition` from canon doc is NOT a validated scope_type — see §4 for full resolution. |
| `scope_id` | nullable identifier of the scoped entity (e.g., department UUID) |
| `state` / `status` | `Active` or `Revoked` |
| `effective_from`, `effective_to` | validity window |

A new `RoleBindingRecord` is created automatically at user registration (`register_user`, `service.py` lines 301-307): `scope_type='Department'` if `department_id` is supplied, else `'Global'`. Role bindings can be revoked via `revoke_role_binding` (lines 557-581), which sets `state='Revoked'` and emits `RoleBindingChanged`.

---

## 8. CROSS-REFERENCES

- `docs/00_authority/PROJECT_CHARTER.md` §3 — the 6 roles and their descriptions.
- `docs/00_authority/DOMAIN_MODEL.md` — ROLE BINDING entity, MULTI-TENANCY INVARIANT.
- `docs/07_governance/AI_OPERATING_CONTEXT.md` — KNOWN_CONSTRAINTS, Glossary "Capability"/"Scope" (FD-008).
- `backend/docs/canon/security-model.md` — capability-to-role table, module permission coverage, scope model.
- `backend/docs/canon/capability-matrix.md` — full capability registry (40+ capabilities).
- `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md` — authentication/JWT mechanism, tenant propagation.
- `docs/08_reports/SECURITY_DISCOVERY_REPORT.md` — gap analysis for unverified capabilities and enforcement points.
