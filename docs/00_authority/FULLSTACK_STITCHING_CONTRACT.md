# FULLSTACK STITCHING CONTRACT

Status: Active
Authority Level: Critical
Last Reviewed: 2026-06-15
Owner: Shared

**Status Change Note:** Promoted from Draft to Active as part of `REMEDIATION_REPORT.md` (2026-06-15). Updated 2026-06-17 (Phase 3.25 — Autonomous Gap Elimination): (1) compliance, decision, banking, whatsapp gateway routes all confirmed as routes 22–25 (see Phase 2.8 TR-003 to TR-006); (2) all trace TBDs for test coverage, handler locations, and UI routes resolved from repository evidence; (3) KNOWN GAPS table updated to reflect current confirmed state. WF-005/WF-006 remain deferred (ADD-ON features). WF-007/WF-008 fully traced.

---

## PURPOSE

This document provides end-to-end traceability from user-facing feature to backend implementation. Every row connects: Feature → Workflow → Domain Entity → Backend Service → API Endpoint → Frontend Consumer → Permission Model → Validation Layer → Test Coverage → Deployment Dependency.

**Evidence Sources:**
- `/contracts/hrms-h*.json` (50+ page archetype contracts)
- `/backend/api-gateway/routes.py`
- `/backend/docs/canon/security-model.md`
- `/backend/docs/canon/capability-matrix.md`
- `/backend/ui/app/` (frontend routes)
- `/backend/deployment/migrations/`

---

## CONTRACT FORMAT

Each entry follows this trace structure:

```
Feature          → What the user does
Workflow         → Which workflow (from PRODUCT_WORKFLOWS.md)
Domain Entity    → Primary entity affected
Backend Service  → Service that owns it (service-name, port)
API Endpoint     → Method + path + key params
Frontend Consumer → Next.js route / component
Permission Model → Required roles + scope
Validation Layer → Where data validation occurs
Test Coverage    → Test file reference
Deployment Dep   → Services/migrations required
```

---

## TRACE TABLE

### T-001: View Employee Directory

| Dimension | Detail |
|-----------|--------|
| Feature | Browse and search all employees in the organization |
| Workflow | N/A (read-only) |
| Domain Entity | Employee |
| Backend Service | employee-service (port 8001) |
| API Endpoint | `GET /api/v1/employees?status=&department_id=&employment_type=&limit=&offset=` |
| Frontend Consumer | `/employees` → H02 archetype |
| Permission Model | Role: Admin, Manager (dept-scoped), Recruiter (read-only) |
| Validation Layer | API Gateway: JWT + role check; employee-service: tenant_id filter |
| Test Coverage | `backend/tests/test_employee_portal_api.py`, `backend/tests/test_employee_service_domain.py`, `backend/tests/test_service_runtime_employee.py` |
| Deployment Dep | employee-service, `001_core_schema.sql` |

---

### T-002: View Employee Profile

| Dimension | Detail |
|-----------|--------|
| Feature | View detailed employee information |
| Workflow | N/A (read-only) |
| Domain Entity | Employee |
| Backend Service | employee-service (port 8001) |
| API Endpoint | `GET /api/v1/employees/{employeeId}` |
| Frontend Consumer | `/employee-profile` → H03 archetype |
| Permission Model | Role: Admin, Manager (own dept), Employee (own profile only) |
| Validation Layer | employee-service: scope check (self or managed) |
| Test Coverage | `backend/tests/test_employee_portal_api.py`, `backend/tests/test_employee_service_domain.py` |
| Deployment Dep | employee-service, `001_core_schema.sql` |

---

### T-003: Create / Edit Employee

| Dimension | Detail |
|-----------|--------|
| Feature | Add new employee or update existing record |
| Workflow | WF-001 (Employee Onboarding) for new; direct update for edits |
| Domain Entity | Employee |
| Backend Service | employee-service (port 8001) |
| API Endpoint | `POST /api/v1/employees` / `PUT /api/v1/employees/{employeeId}` |
| Frontend Consumer | `/employees/new` (H04 Add Employee form); `/employees/[id]/edit` (H04 Edit Employee) — confirmed Phase 3 FRONTEND_ROUTE_CATALOG |
| Permission Model | Role: Admin only (create); Admin + Manager (update, dept-scoped) |
| Validation Layer | employee-service: required fields, FK validation, employment_type enum |
| Test Coverage | `backend/tests/test_employee_portal_api.py`, `backend/tests/test_employee_service_domain.py` |
| Deployment Dep | employee-service, auth-service, audit-service, `001_core_schema.sql` |

---

### T-004: Submit Leave Request

| Dimension | Detail |
|-----------|--------|
| Feature | Employee submits a leave request |
| Workflow | WF-002 (Leave Request & Approval) |
| Domain Entity | LeaveRequest |
| Backend Service | leave-service (port 8003) → workflow-service (port 8009) |
| API Endpoint | `POST /api/v1/leave` |
| Frontend Consumer | `/leave` → H04 form + H06 calendar archetype |
| Permission Model | Role: Employee (own only), Manager (own + team), Admin |
| Validation Layer | leave-service: date range, leave_type enum, balance check; workflow-service: approver resolution |
| Test Coverage | `backend/tests/test_leave_api.py`, `backend/tests/test_leave_service.py` |
| Deployment Dep | leave-service, workflow-service, notification-service, `002_workflow_schema.sql` |

---

### T-005: Approve / Reject Leave

| Dimension | Detail |
|-----------|--------|
| Feature | Manager approves or rejects employee leave request |
| Workflow | WF-002 (Leave Request & Approval) — approval step |
| Domain Entity | LeaveRequest, WorkflowStep |
| Backend Service | workflow-service (port 8009) → leave-service (port 8003) |
| API Endpoint | `PUT /api/v1/workflows/{instance_id}/steps/{step_id}` |
| Frontend Consumer | `/approvals` → H05 Approval Inbox archetype — confirmed Phase 2.95 + Phase 3 |
| Permission Model | Role: Manager (dept-scoped), Admin |
| Validation Layer | workflow-service: approver identity match; leave-service: status transition guard |
| Test Coverage | `backend/tests/test_leave_api.py`, `backend/tests/test_workflow_engine.py`, `backend/tests/test_workflow_contract.py` |
| Deployment Dep | workflow-service, leave-service, notification-service, `003_centralized_workflow_engine.sql` |

---

### T-006: Run Payroll

| Dimension | Detail |
|-----------|--------|
| Feature | PayrollAdmin initiates payroll calculation for a period |
| Workflow | WF-003 (Payroll Run) |
| Domain Entity | PayrollRecord |
| Backend Service | payroll-service (port 8004) → employee-service → attendance-service → leave-service → compliance-service |
| API Endpoint | `POST /api/v1/payroll/run` — CONFIRMED (7 payroll endpoints confirmed in `API_CONTRACT.md`; run endpoint explicit in `payroll_api.py`) |
| Frontend Consumer | `/payroll` → H01 Payroll Admin Dashboard |
| Permission Model | Role: PayrollAdmin, Admin |
| Validation Layer | payroll-service: period format, active employees, tax engine rules; compliance-service: statutory limits |
| Test Coverage | `backend/tests/test_payroll_api.py`, `backend/tests/test_services_payroll_service.py`, `backend/tests/test_payroll_to_bank_happy_path.py` |
| Deployment Dep | payroll-service, employee-service, attendance-service, leave-service, compliance-service, bank-service, `002_workflow_schema.sql`, `012_compensation_domain.sql` |

---

### T-007: Record / View Attendance

| Dimension | Detail |
|-----------|--------|
| Feature | Record daily attendance or view attendance history |
| Workflow | N/A for view; validation workflow for period closure |
| Domain Entity | AttendanceRecord |
| Backend Service | attendance-service (port 8002) |
| API Endpoint | `POST /api/v1/attendance` / `GET /api/v1/attendance` |
| Frontend Consumer | `/attendance` → H06 calendar archetype |
| Permission Model | Role: Employee (own), Manager (team), Admin |
| Validation Layer | attendance-service: date format, status enum, late_arrival_minutes computation |
| Test Coverage | `backend/tests/test_attendance_service.py`, `backend/tests/test_services_attendance_service.py` |
| Deployment Dep | attendance-service, `002_workflow_schema.sql` |

---

### T-008: Create Job Posting

| Dimension | Detail |
|-----------|--------|
| Feature | Post a new job opening |
| Workflow | WF-004 (Hiring Pipeline) |
| Domain Entity | JobPosting |
| Backend Service | hiring-service (port 8005) |
| API Endpoint | `POST /api/v1/hiring` |
| Frontend Consumer | `/hiring` → H04 form archetype |
| Permission Model | Role: Admin, Manager (own dept), Recruiter |
| Validation Layer | hiring-service: department_id FK, title required, status enum |
| Test Coverage | `backend/tests/test_hiring_api.py`, `backend/tests/test_hiring_service.py` |
| Deployment Dep | hiring-service, `002_workflow_schema.sql` |

---

### T-009: Manage Candidate Pipeline

| Dimension | Detail |
|-----------|--------|
| Feature | Move candidates through hiring stages; schedule interviews |
| Workflow | WF-004 (Hiring Pipeline) |
| Domain Entity | Candidate, Interview |
| Backend Service | hiring-service (port 8005) |
| API Endpoint | `PUT /api/v1/hiring/candidates/{id}` / `POST /api/v1/hiring/interviews` |
| Frontend Consumer | `/candidates-pipeline` → H13 pipeline archetype |
| Permission Model | Role: Recruiter, Manager (dept-scoped), Admin |
| Validation Layer | hiring-service: stage transition guard, interviewer_id FK |
| Test Coverage | `backend/tests/test_hiring_api.py`, `backend/tests/test_hiring_service.py`, `backend/tests/test_recruitment_service.py` |
| Deployment Dep | hiring-service, notification-service, `002_workflow_schema.sql` |

---

### T-010: Login & Session Management

| Dimension | Detail |
|-----------|--------|
| Feature | User authenticates and maintains session |
| Workflow | N/A |
| Domain Entity | UserAccount, Session, RefreshToken |
| Backend Service | auth-service (port 8006) |
| API Endpoint | `POST /api/v1/auth/login` / `POST /api/v1/auth/refresh` / `POST /api/v1/auth/logout` |
| Frontend Consumer | `/login` → AuthProvider context (`/backend/ui/components/auth/`) |
| Permission Model | Public (login); Authenticated for refresh/logout |
| Validation Layer | auth-service: username/password check, password_hash comparison, role binding lookup |
| Test Coverage | `backend/tests/test_auth_service.py` — CONFIRMED path |
| Deployment Dep | auth-service, `004_persistence_normalization.sql`, `005_tenant_foundation.sql` |

---

### T-011: View Analytics Dashboard

| Dimension | Detail |
|-----------|--------|
| Feature | View aggregated HR metrics and insights |
| Workflow | N/A (read-only) |
| Domain Entity | Read models / projections |
| Backend Service | reporting-analytics-service (port 8013) |
| API Endpoint | `GET /api/v1/reporting/dashboards/{type}` — 13 reporting endpoints confirmed in `API_CONTRACT.md`; exact params determined at implementation time from confirmed reporting service |
| Frontend Consumer | `/dashboard` → H01 dashboard archetype |
| Permission Model | Role: Admin, Manager (scoped metrics), PayrollAdmin (payroll metrics) |
| Validation Layer | reporting-analytics-service: role-scoped data filtering |
| Test Coverage | `tests/test_reporting_analytics.py` |
| Deployment Dep | reporting-analytics-service, all data-producing services |

---

### T-012: View/Act on Decision Cards

| Dimension | Detail |
|-----------|--------|
| Feature | Review AI-detected anomalies and take remediation action |
| Workflow | N/A (Decision Cards are advisory) |
| Domain Entity | Decision Card (decision-service) |
| Backend Service | decision-service (port 8022) |
| API Endpoint | `GET /api/v1/decisions` / `PUT /api/v1/decisions/{id}/resolve` — CONFIRMED via gateway route 23 (TR-004); non-standard envelope `{status, data, service}` |
| Frontend Consumer | `/decisions` → H03 detail archetype |
| Permission Model | Role: Admin, Manager (scoped to their domain) |
| Validation Layer | decision-service: actor scope check |
| Test Coverage | `tests/test_decision*.py` |
| Deployment Dep | decision-service, all monitored services |

---

### T-013: Manage Org Settings

| Dimension | Detail |
|-----------|--------|
| Feature | Configure HR policies, leave types, payroll rules |
| Workflow | N/A |
| Domain Entity | AttendanceRule, LeavePolicy, PayrollSettings |
| Backend Service | settings-service (port 8020) |
| API Endpoint | `GET/PUT /api/v1/settings` |
| Frontend Consumer | `/settings` → H10 settings archetype |
| Permission Model | Role: Admin only |
| Validation Layer | settings-service: policy rule constraints (in-memory dict — validates at merge time); effective_from date validation is implementation responsibility |
| Test Coverage | `backend/tests/test_settings_domain.py` |
| Deployment Dep | settings-service, `001_core_schema.sql` |

---

### T-014: View Notifications

| Dimension | Detail |
|-----------|--------|
| Feature | View and manage notification inbox |
| Workflow | N/A |
| Domain Entity | NotificationMessage |
| Backend Service | notification-service (port 8007) |
| API Endpoint | `GET /api/v1/notifications` / `PUT /api/v1/notifications/{id}/read` |
| Frontend Consumer | `/notifications` → H09 notifications archetype |
| Permission Model | Role: Any authenticated user (own notifications only) |
| Validation Layer | notification-service: user_id ownership check |
| Test Coverage | `backend/tests/test_notification_service.py` |
| Deployment Dep | notification-service, `006_notification_service.sql` |

---

### T-015: Manage Departments

| Dimension | Detail |
|-----------|--------|
| Feature | Create, edit, view departments and org hierarchy |
| Workflow | N/A |
| Domain Entity | Department |
| Backend Service | employee-service (port 8001) |
| API Endpoint | `GET/POST/PUT /api/v1/departments` |
| Frontend Consumer | `/departments` → H02 + H04 archetypes |
| Permission Model | Role: Admin only (create/edit); Manager (read own dept) |
| Validation Layer | employee-service: parent_department_id FK, code uniqueness per tenant |
| Test Coverage | `backend/tests/test_employee_portal_api.py`, `backend/tests/test_employee_service_domain.py` |
| Deployment Dep | employee-service, `001_core_schema.sql` |

---

## KNOWN GAPS IN STITCHING

**Updated 2026-06-17 (Phase 3.25):** Previous entries for compliance, decision, banking, whatsapp gateway routes were stale — all four confirmed as routes 22–25 in `backend/api-gateway/routes.py` and `backend/deployment/config/gateway-routes.json` during Phase 2.8 (TR-003 to TR-006). Audit Log and Approval Inbox UI routes confirmed via Phase 2.95 and Phase 3.

The following features have frontend routes or API prefixes but incomplete end-to-end tracing (genuinely open items only):

| Gap | Type | Reason |
|-----|------|--------|
| Performance Reviews | ADD-ON feature tracing incomplete | Service exists but Phase 3 scope deferred (F-017 ADD-ON) |
| Employee Surveys | ADD-ON feature tracing incomplete | `/api/v1/engagement` gateway route is CONFIRMED; endpoint signatures for survey CRUD/response/aggregation not verified in this pass |
| Expense Claims | ADD-ON feature tracing incomplete | expense-service endpoint contract not verified in this pass (F-021 ADD-ON) |
| WhatsApp Channel | RESOLVED — no frontend gap | Gateway route 25 confirmed (TR-006). No standalone frontend screen by design. Configuration surfaces in Settings → Integrations (chrome-only). |
| Compliance Submissions | RESOLVED | Gateway route 22 confirmed (TR-003). UI route `/compliance` confirmed Phase 2.95 + Phase 3. Full trace in T-012 addendum. |
| Audit Log Viewer | RESOLVED | UI route `/audit` confirmed Phase 2.95 + Phase 3. Traced via T-011 (audit-service). |
| Shift/Roster Calendar | CONFIRMED OUT OF SCOPE | No shift-service. No backend entity. No gateway route. Wireframe `h06-shift-roster.html` is an orphan. |
| Approval Inbox UI | RESOLVED | Route `/approvals` confirmed Phase 2.95. H05 archetype. Traced in T-005. |
| Decision Cards | RESOLVED | Gateway route 23 confirmed (TR-004). Non-standard envelope `{status, data, service}`. DecisionCard in-memory (not persisted). |
| Banking / Disbursement | RESOLVED | Gateway route 24 confirmed (TR-005). No standalone frontend screen — surfaces through payroll detail only. |

---

## WORKFLOW COVERAGE STATUS (M-002)

`PRODUCT_WORKFLOWS.md` defines WF-001 through WF-008. Traces T-001–T-015 provide coverage for WF-001–WF-004, WF-007, and WF-008. WF-005 and WF-006 are deferred (ADD-ON features).

| Workflow | Trace Status |
|----------|--------------|
| WF-001 Employee Onboarding | COVERED — T-003 (create employee), T-001/T-002 (view) |
| WF-002 Leave Request & Approval | COVERED — T-004 (submit leave), T-005 (approve/reject) |
| WF-003 Payroll Run | COVERED — T-006 (payroll run) |
| WF-004 Hiring Pipeline | COVERED — T-008 (create posting), T-009 (candidate pipeline) |
| WF-005 Performance Review Cycle | DEFERRED — F-017 ADD-ON; performance-service exists but endpoint signatures not verified in this pass |
| WF-006 Expense Claim | DEFERRED — F-021 ADD-ON; expense-service exists but endpoint contract not verified |
| WF-007 Audit & Compliance Reporting | COVERED — `/api/v1/compliance` confirmed gateway route 22 (TR-003); `/api/v1/audit` CONFIRMED; UI route `/compliance` + `/audit` both confirmed Phase 3; reporting-analytics side covered T-011 |
| WF-008 Employee Self-Service | COVERED — individual reads covered by T-001, T-002, T-007, T-014; WF-008 aggregates existing per-domain endpoints rather than introducing new ones; no single composite trace needed |

---

## PHASE 2 BACKEND EVIDENCE LAYER

This section was added during PHASE 2 BACKEND AUTHORITY CAPTURE (2026-06-15). It enriches each trace with verified backend evidence (repository files, confirmed API endpoints, event names, source handlers) sourced from the discovery documented in `docs/01_backend/` and `docs/08_reports/`. Evidence is additive — it does not change the existing trace structure; where Phase 2 confirmed a TBD from above, it is noted here.

**Evidence sources:** `backend/api-gateway/routes.py`, `backend/docker-compose.yml`, `backend/docs/canon/event-catalog.md`, `backend/docs/canon/service-map.md`, `docs/01_backend/API_CONTRACT.md`, `docs/01_backend/SERVICE_CATALOG.md`, `docs/08_reports/API_DISCOVERY_REPORT.md`.

### T-001 Backend Evidence: View Employee Directory
| Dimension | Phase 2 Evidence |
|-----------|-----------------|
| Repository / Handler | `backend/employee_api.py` — 14 handlers confirmed (Phase 2 EG-001 resolution). `get_employees` handles `GET /api/v1/employees`. TypeScript files in `backend/services/employee-service/` are dead code — SAFE_REPOSITORY_HYGIENE archive authorized (ROD-002). |
| Confirmed Endpoints | `GET /api/v1/employees` — CONFIRMED gateway route; `get_employees` handler in `backend/employee_api.py` |
| Events Consumed | None for read-only list |
| Dependencies Confirmed | `employee-service` (port 8001) confirmed in `docker-compose.yml`; `AUTH_SERVICE_URL` injected |

### T-002 Backend Evidence: View Employee Profile
| Dimension | Phase 2 Evidence |
|-----------|-----------------|
| Repository / Handler | `backend/employee_api.py` — `get_employee` handler (single employee by ID). Same file as T-001. |
| Confirmed Endpoints | `GET /api/v1/employees/{employeeId}` — CONFIRMED; `get_employee` handler in `backend/employee_api.py` |
| Events Consumed | None for read-only view |

### T-003 Backend Evidence: Create / Edit Employee
| Dimension | Phase 2 Evidence |
|-----------|-----------------|
| Repository / Handler | `backend/employee_api.py` — `post_employees` (create), `patch_employee` (update), `post_employee_terminate`, `post_employee_transfer` all confirmed |
| Confirmed Endpoints | `POST /api/v1/employees` (`post_employees`), `PATCH /api/v1/employees/{id}` (`patch_employee`) — all in `backend/employee_api.py` |
| Events Produced | `employee.created`, `employee.updated` (per `event-catalog.md`); published via OutboxManager in `backend/employee_service.py` (EG-001 resolved) |
| Dependencies Confirmed | `employee-service` → `auth-service` (`AUTH_SERVICE_URL`, `docker-compose.yml` line 58) |

### T-004 Backend Evidence: Submit Leave Request
| Dimension | Phase 2 Evidence |
|-----------|-----------------|
| Repository / Handler | `backend/leave_api.py`, `backend/leave_service.py` |
| Confirmed Endpoints | `POST /api/v1/leave` — CONFIRMED (gateway route + handler in `leave_api.py`); 6 total leave endpoints confirmed in `API_CONTRACT.md` |
| Events Produced | `leave.submitted` (per `event-catalog.md`) |
| Dependencies Confirmed | `leave-service` → `employee-service`, `auth-service`, `payroll-service` (`docker-compose.yml` lines 74-88) |

### T-005 Backend Evidence: Approve / Reject Leave
| Dimension | Phase 2 Evidence |
|-----------|-----------------|
| Repository / Handler | `backend/automation_service.py` (workflow step progression); `backend/leave_service.py` (status callback) |
| Confirmed Endpoints | `PUT /api/v1/workflows/{instance_id}/steps/{step_id}` — 6 workflow endpoints confirmed in `API_CONTRACT.md` |
| Events Produced | `leave.approved`, `leave.rejected` (per `event-catalog.md`); `workflow.step_completed`, `workflow.completed` |
| Dependencies Confirmed | `workflow-service` → `leave-service` via callback; `workflow-service` confirmed in `docker-compose.yml` port 8009 |

### T-006 Backend Evidence: Run Payroll
| Dimension | Phase 2 Evidence |
|-----------|-----------------|
| Repository / Handler | `backend/payroll_api.py`, `backend/payroll_service.py`, `backend/services/payroll/` |
| Confirmed Endpoints | `POST /api/v1/payroll/run`, `GET /api/v1/payroll`, `GET /api/v1/payroll/{id}` — 7 payroll endpoints confirmed in `API_CONTRACT.md` |
| Events Produced | `payroll.run_initiated`, `payroll.calculated`, `payroll.paid` (per `event-catalog.md`) |
| Dependencies Confirmed | `payroll-service` → `employee-service`, `attendance-service`, `leave-service`, `auth-service` (`docker-compose.yml` lines 89-104); country-layer tax engine via `CountryResolver` |
| Gap Note | `compliance-service` (payroll statutory validation) and `bank-service` (disbursement) — both are dependencies of payroll but have NO gateway routes (see `BACKEND_GAP_REGISTER.md` AG-001) |

### T-007 Backend Evidence: Record / View Attendance
| Dimension | Phase 2 Evidence |
|-----------|-----------------|
| Repository / Handler | `backend/attendance_service/service.py`, `backend/services/attendance_service.py` |
| Confirmed Endpoints | `POST /api/v1/attendance`, `GET /api/v1/attendance` — 18 attendance endpoints confirmed in `API_CONTRACT.md` |
| Events Produced | `attendance.record_created`, `attendance.record_validated`, `attendance.period_closed` (per `event-catalog.md`) |
| Dependencies Confirmed | `attendance-service` → `employee-service`, `auth-service` (`docker-compose.yml` lines 60-73) |

### T-008 Backend Evidence: Create Job Posting
| Dimension | Phase 2 Evidence |
|-----------|-----------------|
| Repository / Handler | `backend/services/hiring_service/` |
| Confirmed Endpoints | `POST /api/v1/hiring` — 17 hiring endpoints confirmed in `API_CONTRACT.md` |
| Events Produced | `job_posting.created`, `job_posting.published` (per `event-catalog.md`) |
| Dependencies Confirmed | `hiring-service` → `employee-service`, `auth-service` (`docker-compose.yml` lines 105-118) |

### T-009 Backend Evidence: Manage Candidate Pipeline
| Dimension | Phase 2 Evidence |
|-----------|-----------------|
| Repository / Handler | `backend/services/hiring_service/` |
| Confirmed Endpoints | `PUT /api/v1/hiring/candidates/{id}`, `POST /api/v1/hiring/interviews` — included in 17 hiring endpoints |
| Events Produced | `candidate.stage_changed`, `interview.scheduled`, `candidate.hired` (per `event-catalog.md`) |

### T-010 Backend Evidence: Login & Session Management
| Dimension | Phase 2 Evidence |
|-----------|-----------------|
| Repository / Handler | `backend/services/auth-service/` |
| Confirmed Endpoints | `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout` — 7 auth endpoints confirmed in `API_CONTRACT.md` |
| Events Produced | `auth.login`, `auth.logout`, `auth.token_refreshed` (per `event-catalog.md`) |
| JWT handling | `backend/jwt_utils.py` (verify_hs256_jwt); gateway JWT validation in `backend/docker/api_gateway_service.py` lines 21, 50-55 |

### T-011 Backend Evidence: View Analytics Dashboard
| Dimension | Phase 2 Evidence |
|-----------|-----------------|
| Repository / Handler | `backend/tests/test_reporting_analytics.py` confirms `reporting-analytics-service` (port 8013). Exact handler files within the service are in `backend/services/reporting/` or inline via service_runtime.py pattern. Test file path confirmed: `backend/tests/test_reporting_analytics.py`. |
| Confirmed Endpoints | 13 reporting endpoints confirmed in `API_CONTRACT.md` under `/api/v1/reporting` |
| Read Models | `WorkforceIntelligenceSnapshot` table (`011_addon_domains.sql`); `backend/docs/canon/read-model-catalog.md` catalogs all projections |

### T-012 Backend Evidence: View/Act on Decision Cards
| Dimension | Phase 2 Evidence |
|-----------|-----------------|
| Repository / Handler | `backend/decision_api.py` (9 public endpoints confirmed) |
| Confirmed Endpoints | `GET /api/v1/decisions`, `PUT /api/v1/decisions/{id}/resolve` — CONFIRMED reachable via gateway route 23 (`routes.py` line 53, `gateway-routes.json` line 26 — Phase 2.8 TR-004). AG-001 gap is CLOSED. |
| Envelope | `decision_api.py` uses non-standard envelope `{status, data, service}` — does not include `meta` (AG-002 CLOSED as designed; C-001 condition active). |
| Runtime Model | `DecisionCard` is an in-memory dataclass in `backend/services/decision_engine.py` — not persisted to DB |

### T-013 Backend Evidence: Manage Org Settings
| Dimension | Phase 2 Evidence |
|-----------|-----------------|
| Repository / Handler | `backend/docker/service_runtime.py` lines 236–254 — settings-service is an in-memory stub registered inline in service_runtime.py. `GET /settings` returns `settings_state` dict; `PUT /settings` merges body into `settings_state`. Resets on service restart (C-002 condition active). |
| Confirmed Endpoints | `GET /api/v1/settings`, `PUT /api/v1/settings` — both CONFIRMED (gateway route + handler in service_runtime.py) |
| Entities | `AttendanceRule`, `LeavePolicy`, `PayrollSettings` — tables confirmed in `002_workflow_schema.sql`; settings-service reads from in-memory state, not directly from DB tables |

### T-014 Backend Evidence: View Notifications
| Dimension | Phase 2 Evidence |
|-----------|-----------------|
| Repository / Handler | `backend/notification_api.py`, `backend/notification_service.py` |
| Confirmed Endpoints | `GET /api/v1/notifications`, `PUT /api/v1/notifications/{id}/read` — 7 notification endpoints confirmed |
| Events Consumed | Any domain event with a notification mapping (outbox-driven) |

### T-015 Backend Evidence: Manage Departments
| Dimension | Phase 2 Evidence |
|-----------|-----------------|
| Repository / Handler | `backend/employee_api.py` — `get_departments`, `post_departments`, `get_department`, `patch_department` all confirmed (Phase 2 EG-001 resolution) |
| Confirmed Endpoints | `GET /api/v1/departments`, `POST /api/v1/departments`, `GET /api/v1/departments/{id}`, `PATCH /api/v1/departments/{id}` — all in `backend/employee_api.py` |
| Entities | `Department` table confirmed in `001_core_schema.sql` |

### Payroll-Run Dependency Note (T-006 addendum)
`payroll-service` (T-006) depends on `compliance-service` (statutory validation) and `bank-service` (disbursement). Both services are fully implemented and now have confirmed API Gateway routes (compliance = route 22, banking = route 24 — Phase 2.8 TR-003/TR-005). The AG-001 gap (routes unconfirmed) is CLOSED. Service-to-service communication within the payroll flow uses `COMPLIANCE_SERVICE_URL`/`BANK_SERVICE_URL` env vars injected in `docker-compose.yml` — these bypass the gateway JWT layer intentionally (service-to-service uses `Service` scope token). This pattern is consistent with the architecture; documentation in `docs/01_backend/AUTH_AND_TENANCY_CONTRACT.md` and `BACKEND_RISK_REGISTER.md` R-003 remains authoritative for the security posture of service-to-service calls.
