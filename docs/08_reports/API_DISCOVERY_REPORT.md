# API DISCOVERY REPORT

Status: Active
Authority Level: High
Last Reviewed: 2026-06-15
Owner: AI

---

## Executive Summary

This report documents the findings of an API discovery pass across the HRMS backend, covering the gateway route registry, service handler files, and UI contracts. The discovery confirmed **164 endpoints** across 17 of 21 gateway-routed prefixes. Four gateway prefixes have no handler source files located. Four additional services have complete handler implementations that are unreachable via the gateway. Several inconsistencies were found between `api-standards.md`, `routes.py`, and actual handler behavior.

---

## 1. Confirmed Endpoint Count per Gateway Prefix

Source files: `D:\SaaS\HRMS\backend\api-gateway\routes.py` (gateway), all `*_api.py` and `attendance_service\api.py` handler files.

| # | Gateway Prefix | Upstream Service | Handler File | Confirmed Endpoints |
|---|---|---|---|---|
| 1 | `/api/v1/auth` | auth-service | `services/auth-service/api.py` | 7 |
| 2 | `/api/v1/attendance` | attendance-service | `attendance_service/api.py` | 18 |
| 3 | `/api/v1/leave` | leave-service | `leave_api.py` | 6 |
| 4 | `/api/v1/payroll` | payroll-service | `payroll_api.py` | 7 |
| 5 | `/api/v1/performance` | performance-service | `performance_api.py` | 19 |
| 6 | `/api/v1/travel` | travel-service | `travel_api.py` | 8 |
| 7 | `/api/v1/projects` | project-service | `project_api.py` | 10 |
| 8 | `/api/v1/hiring` | hiring-service | `services/hiring_service/api.py` | 17 |
| 9 | `/api/v1/workflows` | workflow-service | `workflow_api.py` | 6 |
| 10 | `/api/v1/notifications` | notification-service | `notification_api.py` | 7 |
| 11 | `/api/v1/engagement` | engagement-service | `engagement_api.py` | 10 |
| 12 | `/api/v1/helpdesk` | helpdesk-service | `helpdesk_api.py` | 14 |
| 13 | `/api/v1/reporting` | reporting-analytics-service | `reporting_analytics_api.py` | 13 |
| 14 | `/api/v1/search` | search-service | `search_api.py` | 4 |
| 15 | `/api/v1/expense` | expense-service | `expense_api.py` | 8 |
| 16 | `/api/v1/integrations` | integration-service | `integration_api.py` | 6 |
| 17 | `/api/v1/automations` | automation-service | `automation_api.py` | 4 |
| 18 | `/api/v1/employees` | employee-service | **NOT FOUND** | TBD |
| 19 | `/api/v1/departments` | employee-service | **NOT FOUND** | TBD |
| 20 | `/api/v1/audit` | audit-service | **NOT FOUND** | TBD |
| 21 | `/api/v1/settings` | settings-service | **NOT FOUND** | TBD |

**Total confirmed: 164 endpoints across 17 prefixes**
**TBD: 4 prefixes (employees, departments, audit, settings)**

### Path inference note

The URL path for each confirmed endpoint is inferred from handler function names and cross-referenced with contract files where available (e.g., `contracts/hrms-h04-raise-leave-request-contract.json` confirms `POST /api/v1/leave/requests`). The actual HTTP router wiring was not found in the sampled directories. All paths in `API_CONTRACT.md` marked `(inferred)` should be verified against the router configuration before this document is promoted from Draft.

---

## 2. Contracts in `contracts/*.json` with No Confirmed Handler

Source: `D:\SaaS\HRMS\contracts\` directory (46 JSON files).

| Contract File | Referenced Endpoint | Handler Found? | Gap |
|---|---|---|---|
| `hrms-h02-employees-contract.json` | `GET /api/v1/employees/summary` | No | BG-005 — aggregate not built |
| `hrms-h04-raise-leave-request-contract.json` | `GET /api/v1/leave/employees/:id/balances` | No | BG-006 — balance endpoint not built |
| `hrms-h01-hr-manager-dashboard-contract.json` | TBD — REQUIRES VERIFICATION | TBD | Dashboard-specific aggregates not confirmed |
| `hrms-h01-payroll-admin-dashboard-contract.json` | TBD — REQUIRES VERIFICATION | TBD | Payroll admin aggregates not confirmed |
| `hrms-h02-attendance-records-contract.json` | TBD — REQUIRES VERIFICATION | TBD | Path mapping to `attendance_service/api.py` not confirmed |
| `hrms-h07-hr-analytics-contract.json` | TBD — REQUIRES VERIFICATION | TBD | Uncertain mapping; `reporting` or dedicated analytics endpoint unclear |
| `hrms-h10-org-settings-contract.json` | TBD — REQUIRES VERIFICATION | TBD | `settings-service` has no handler file found |
| `hrms-h02-documents-contract.json` | TBD — REQUIRES VERIFICATION | TBD | No documents handler found in any service |
| `hrms-h02-roles-contract.json` | TBD — REQUIRES VERIFICATION | TBD | No roles/org gateway route; `api-standards.md` mentions `/api/v1/roles` and `/api/v1/org` |

**Confirmed gaps from contract notes:**
- **BG-005**: `GET /api/v1/employees/summary` — referenced in `hrms-h02-employees-contract.json` as explicitly not built ("BG-005 mock").
- **BG-006**: `GET /api/v1/leave/employees/:id/balances` — referenced in `hrms-h04-raise-leave-request-contract.json` as "no endpoint" (balance data served from mock).

---

## 3. Backend Handlers NOT Reachable via a Confirmed Gateway Route

Four services have complete API handler files but are not registered in `routes.py`. Five additional endpoints exist in `background_jobs_api.py` with no corresponding gateway route.

| Service | Handler File | Endpoint Count | Gateway Route |
|---|---|---|---|
| compliance-service | `compliance_api.py` | 9 | None |
| bank-service | `banking_api.py` | 11 | None |
| whatsapp-service | `whatsapp_api.py` | 8 | None |
| decision-service | `decision_api.py` | 9 public + 2 internal utilities | None |
| background-jobs-service | `background_jobs_api.py` | 5 | None |

**Total unreachable-via-gateway endpoints: 42 (9+11+8+9+5)**

Additionally, `api-standards.md` lists these path prefixes that have no corresponding `routes.py` entry and no discoverable handler:

| Path in api-standards.md | Route in routes.py | Handler Found |
|---|---|---|
| `/api/v1/compliance` | No | `compliance_api.py` (internal only) |
| `/api/v1/decisions` | No | `decision_api.py` (internal only) |
| `/api/v1/financial-wellness` | No | No |
| `/api/v1/banking` | No | `banking_api.py` (internal only) |
| `/api/v1/analytics` | No | Partially mapped to `/api/v1/reporting` |
| `/api/v1/whatsapp` | No | `whatsapp_api.py` (internal only) |
| `/api/v1/roles` | No | No handler found |
| `/api/v1/org` | No | No handler found |

---

## 4. Inconsistencies Between `api-standards.md` and Actual Implementation

Source: `D:\SaaS\HRMS\backend\docs\canon\api-standards.md` vs. `routes.py` and `*_api.py` handler files.

### 4.1 Path Naming: `/expense` vs. `/expenses`

**Inconsistency**: `api-standards.md` (§1) lists the path as `/api/v1/expenses` (plural). The gateway `routes.py` registers the prefix as `/expense` (singular, line 48). The handler file is `expense_api.py` and its `SERVICE_NAME = 'expense-service'`. The actual accessible public path is `/api/v1/expense/...`.

**Impact**: Any client following `api-standards.md` and using `/api/v1/expenses/...` will receive a gateway 404.

### 4.2 `meta.service` Field Not Documented

**Inconsistency**: `api_contract.py` — `meta_payload()` conditionally adds `meta['service']` when `context.service is not None`. This field is emitted by every conforming `*_api.py` handler (all set their `SERVICE_NAME`). However, `api-standards.md` (§3) does not list `meta.service` in the response envelope spec.

**Impact**: Clients relying solely on `api-standards.md` would not know to expect this field in `meta`.

### 4.3 `error.details` Type Ambiguity

**Inconsistency**: `api-standards.md` (§3 Error rules) shows `"details": {}` (object). `api_contract.py` (`error_payload()` signature line 145) accepts `details: dict[str, Any] | list[dict[str, Any]] | None`. In practice, field-level validation errors use a list form: `[{"field": "...", "reason": "..."}]`. The standard only documents the dict form.

**Impact**: Client error parsers expecting `details` to always be a dict will fail when a list is returned.

### 4.4 Non-Conforming Error Envelope in 4 Services

**Inconsistency**: `compliance_api.py`, `banking_api.py`, `whatsapp_api.py`, and `decision_api.py` use custom `_ok()` / `_err()` helpers that **do not** use `api_contract.py`. Their responses are missing the required `meta` block entirely. This directly violates the SCS mandate in `api-standards.md` (§6 QC: "no_raw_json_responses", "error_format_consistent", "meta_fields_present").

**Impact**: These 4 services cannot pass the QC gates defined in `api-standards.md` §6. Their responses cannot be consumed by any client expecting the standard envelope.

### 4.5 `api-standards.md` Lists Paths Not in `routes.py`

`api-standards.md` §1 lists 26 route namespaces. Of these, only 21 are registered in `routes.py`. The 5 unregistered paths in the standard are:

| Path in api-standards.md | Status |
|---|---|
| `/api/v1/compliance` | Handler exists (`compliance_api.py`); no gateway route |
| `/api/v1/decisions` | Handler exists (`decision_api.py`); no gateway route |
| `/api/v1/financial-wellness` | No handler found; no gateway route |
| `/api/v1/banking` | Handler exists (`banking_api.py`); no gateway route |
| `/api/v1/whatsapp` | Handler exists (`whatsapp_api.py`); no gateway route |

Additionally, `api-standards.md` lists `/api/v1/analytics` and `/api/v1/roles` / `/api/v1/org` which have no gateway entries and no confirmed handler files.

### 4.6 Legacy Bare-Prefix Paths Not Mentioned in `api-standards.md`

`routes.py` supports legacy bare-prefix paths (e.g. `/employees` without `/api/v1`). The `is_legacy_route()` function marks them. `api-standards.md` does not document this behavior, which could lead callers to believe only `/api/v1/...` paths are valid.

---

## 5. Gap / TBD Summary Table

| # | Gap | Severity | Source Evidence | Recommended Action |
|---|---|---|---|---|
| G1 | 4 services (compliance, banking, whatsapp, decision) have full handler implementations but no gateway route — 37 public endpoints unreachable via standard gateway | Critical | `routes.py` vs. `compliance_api.py`, `banking_api.py`, `whatsapp_api.py`, `decision_api.py` | Register these services in `routes.py` or document the intended access mechanism |
| G2 | 4 gateway routes (employees, departments, audit, settings) have no handler source file located — 0 confirmed endpoints | High | `routes.py` routes 1, 2, 12, 21; no `*_api.py` or service `api.py` found | Locate handler files or confirm these are placeholder routes |
| G3 | `/expense` (gateway) vs. `/expenses` (api-standards.md) naming mismatch | High | `routes.py` line 48; `api-standards.md` §1 | Align `api-standards.md` or rename gateway prefix |
| G4 | 4 services (compliance, banking, whatsapp, decision) use non-standard response envelopes — missing `meta` block | High | `compliance_api.py`, `banking_api.py`, `whatsapp_api.py`, `decision_api.py` `_ok()` / `_err()` helpers | Migrate to `api_contract.py` `success_response()` / `error_response()` |
| G5 | BG-005: `GET /api/v1/employees/summary` not built — frontend uses mock data | Medium | `hrms-h02-employees-contract.json` field `gap_ref: BG-005` | Build aggregate endpoint in employee-service |
| G6 | BG-006: `GET /api/v1/leave/employees/{id}/balances` not built — frontend uses mock data | Medium | `hrms-h04-raise-leave-request-contract.json` note `BG-006` | Build balance endpoint in leave-service |
| G7 | `meta.service` field emitted by all handlers but not documented in `api-standards.md` | Low | `api_contract.py` `meta_payload()` lines 98-99; `api-standards.md` §3 | Add `meta.service` to the standard |
| G8 | `error.details` type is `dict | list[dict]` in code but only `{}` (dict) documented in standard | Medium | `api_contract.py` line 145; `api-standards.md` §3 | Update standard to document both forms |
| G9 | `background_jobs_api.py` has 5 endpoint handlers with no gateway route — internal mechanism not documented | Medium | `background_jobs_api.py`; `routes.py` (no `jobs` entry) | Document access mechanism or add gateway route |
| G10 | `api-standards.md` lists 8 path prefixes not in `routes.py` (`/compliance`, `/decisions`, `/financial-wellness`, `/banking`, `/analytics`, `/whatsapp`, `/roles`, `/org`) | Medium | `api-standards.md` §1 vs. `routes.py` | Reconcile the standards doc with actual gateway config |
| G11 | URL path-to-handler wiring not located — all 164 endpoint paths are inferred, not verified from router | High | No router config file found in sampled paths | Locate the HTTP router file (Flask/FastAPI/etc.) and cross-check all paths |
| G12 | JWT-to-actor extraction mechanism at the gateway level not confirmed — services receive pre-extracted `actor_role` / `actor_employee_id` but the middleware is not located | Medium | `leave_api.py`, `engagement_api.py`, etc. receive actor params directly | Locate and document gateway auth middleware |
| G13 | Legacy bare-prefix path support (`/employees` without `/api/v1`) not documented in `api-standards.md` | Low | `routes.py` `is_legacy_route()` function; `api-standards.md` §1 | Document or deprecate legacy paths |
| G14 | No handler found for `documents` resource despite `hrms-h02-documents-contract.json` existing | Medium | `hrms-h02-documents-contract.json`; no documents `*_api.py` found | Confirm if documents are served via employee-service or a separate service |
| G15 | `decision_api.py` `get_compliance_readiness` path comment shows `/decisions/compliance-readiness` (missing `/api/v1/`) | Low | `decision_api.py` line 510 comment | Correct path comment |

---

## 6. Services Summary

| Category | Count | Services |
|---|---|---|
| Gateway-routed with confirmed handler | 17 | auth, attendance, leave, payroll, performance, travel, projects, hiring, workflows, notifications, engagement, helpdesk, reporting, search, expense, integrations, automations |
| Gateway-routed, handler NOT found | 4 | employees/departments (employee-service), audit, settings |
| Handler found, NO gateway route | 5 | compliance, banking, whatsapp, decision, background-jobs |
| Listed in api-standards.md only | 3 | financial-wellness, roles, org |
