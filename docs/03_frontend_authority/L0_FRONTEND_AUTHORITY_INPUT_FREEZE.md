# L0 FRONTEND AUTHORITY INPUT FREEZE

Phase: 3.5 — L0 Frontend Authority Input Freeze
Status: **FROZEN**
Created: 2026-06-20
Source documents reviewed: 13 (see §0)
Verdict: **L0 FROZEN**

---

## FINAL VERDICT

```
L0 FROZEN
```

**No frontend-impacting gap was found that requires a NO-GO ruling.**

Evidence: FRONTEND_GAP_REGISTER.md — 43 registered gaps, 0 blocking. POST_COLLAPSE_FRONTEND_READINESS.md — GO issued, 7/7 gates PASS. DETERMINISM_CERTIFICATION_REPORT.md — REPOSITORY FULLY DETERMINED. Phase 4 AUTHORIZED.

Claude Design may begin archetype work using this input pack. Claude Code may validate any future design against this pack.

---

## §0 — SOURCE DOCUMENTS REVIEWED

| Document | Location | Phase 3.5 Disposition |
|----------|----------|----------------------|
| FRONTEND_AUTHORITY_MASTER.md | `docs/03_frontend_authority/` | COMPLETE — all inputs confirmed |
| FRONTEND_ROUTE_CATALOG.md | `docs/03_frontend_authority/` | COMPLETE — 55 routes frozen |
| FRONTEND_SCREEN_CATALOG.md | `docs/03_frontend_authority/` | COMPLETE — 49 screens frozen |
| FRONTEND_DASHBOARD_CATALOG.md | `docs/03_frontend_authority/` | COMPLETE — 4 dashboard variants frozen |
| FRONTEND_NAVIGATION_MODEL.md | `docs/03_frontend_authority/` | COMPLETE — 9 navigation sections frozen |
| FRONTEND_ROLE_EXPERIENCE_MATRIX.md | `docs/03_frontend_authority/` | COMPLETE — 5 roles frozen |
| FRONTEND_PERMISSION_MATRIX.md | `docs/03_frontend_authority/` | COMPLETE — 31 capabilities frozen |
| FRONTEND_WORKFLOW_TO_SCREEN_MAP.md | `docs/03_frontend_authority/` | COMPLETE — 8 workflows frozen |
| FRONTEND_API_DEPENDENCY_MAP.md | `docs/03_frontend_authority/` | COMPLETE — 25 gateway routes mapped |
| FRONTEND_GAP_REGISTER.md | `docs/03_frontend_authority/` | COMPLETE — 43 gaps, 0 blocking |
| PRODUCT_DECISION_REGISTER.md | `docs/08_reports/` | COMPLETE — all decisions STABLE |
| POST_COLLAPSE_FRONTEND_READINESS.md | `docs/08_reports/` | COMPLETE — GO, all 7 gates PASS |
| DETERMINISM_CERTIFICATION_REPORT.md | `docs/08_reports/` | COMPLETE — REPOSITORY FULLY DETERMINED |

---

## §1 — APPROVED ROUTES (55 TOTAL)

### Rules
- Do not invent routes beyond this list.
- ADD-ON routes are defined here for authority but MUST NOT be implemented in Phase 4 core sprint unless explicitly activated.
- Routes marked PLANNED are excluded from all Phase 4 work.

### Auth Routes (3)

| ID | Route | Roles | Backend API |
|----|-------|-------|-------------|
| R-001 | `/login` | Public | `POST /api/v1/auth/login` |
| R-002 | `/logout` | All | `POST /api/v1/auth/logout` |
| R-003 | `/auth/refresh` | All | `POST /api/v1/auth/refresh` |

### Dashboard (1)

| ID | Route | Roles | Backend API |
|----|-------|-------|-------------|
| R-010 | `/dashboard` | All (role-adaptive) | Multiple widget APIs (see §4) |

### Employee Management (11)

| ID | Route | Roles | Permission |
|----|-------|-------|-----------|
| R-020 | `/employees` | A, M | CAP-EMP-001 |
| R-021 | `/employees/[id]` | A, M, E (own) | CAP-EMP-001 or own |
| R-022 | `/employees/new` | A | CAP-EMP-002 |
| R-023 | `/employees/[id]/edit` | A, M (dept-scoped) | CAP-EMP-002 |
| R-030 | `/departments` | A, M | CAP-EMP-001 |
| R-031 | `/departments/[id]` | A, M | CAP-EMP-001 |
| R-032 | `/departments/new` | A | CAP-EMP-002 |
| R-040 | `/organization` | A, M | CAP-EMP-001 |
| R-050 | `/roles` | A | CAP-AUT-001 |
| R-051 | `/roles/[id]` | A | CAP-AUT-001 |
| R-052 | `/roles/new` | A | CAP-AUT-001 |

### Attendance (2)

| ID | Route | Roles | Permission |
|----|-------|-------|-----------|
| R-060 | `/attendance` | A, M, E (own) | CAP-ATT-001 |
| R-061 | `/attendance/timeline` | A, M | CAP-ATT-001 |

### Leave (5)

| ID | Route | Roles | Permission |
|----|-------|-------|-----------|
| R-070 | `/leave` | All | CAP-LEV-001 |
| R-071 | `/leave/requests` | A, M | CAP-LEV-001 |
| R-072 | `/leave/requests/[id]` | A, M, E (own) | CAP-LEV-001 or own |
| R-073 | `/leave/new` | All | CAP-LEV-002 |
| R-074 | `/leave/calendar` | All | CAP-LEV-001 |

### Payroll (3)

| ID | Route | Roles | Permission |
|----|-------|-------|-----------|
| R-080 | `/payroll` | PA, A, M | CAP-PAY-001; gateway enforced |
| R-081 | `/payroll/[id]` | PA, A, E (own) | CAP-PAY-001 or own |
| R-082 | `/payroll/run` | PA, A | CAP-PAY-002 |

### Hiring (6)

| ID | Route | Roles | Permission |
|----|-------|-------|-----------|
| R-090 | `/hiring` | A, M, R | CAP-HIR-001; gateway enforced |
| R-091 | `/job-postings` | A, M, R | CAP-HIR-001 |
| R-092 | `/job-postings/[id]` | A, M, R | CAP-HIR-001 |
| R-093 | `/job-postings/new` | A, M, R | CAP-HIR-002 |
| R-094 | `/candidates-pipeline` | A, M, R | CAP-HIR-001 |
| R-095 | `/candidates-pipeline/[id]` | A, M, R | CAP-HIR-001 |

### Approvals (1)

| ID | Route | Roles | Backend API |
|----|-------|-------|-------------|
| R-100 | `/approvals` | A, M | `GET /api/v1/workflows?status=pending` |

### Notifications (1)

| ID | Route | Roles | Backend API |
|----|-------|-------|-------------|
| R-110 | `/notifications` | All | `GET /api/v1/notifications` |

### Settings (1)

| ID | Route | Roles | Backend API |
|----|-------|-------|-------------|
| R-120 | `/settings` | A | `GET /api/v1/settings`, `PUT /api/v1/settings` |

### Compliance (1)

| ID | Route | Roles | Backend API |
|----|-------|-------|-------------|
| R-130 | `/compliance` | A, PA | `GET /api/v1/compliance` — **non-standard envelope** |

### Reporting (5)

| ID | Route | Roles | Backend API |
|----|-------|-------|-------------|
| R-140 | `/reporting` | A, M | `GET /api/v1/reporting/dashboards` |
| R-141 | `/reporting/payroll` | PA, A | `GET /api/v1/reporting/payroll` |
| R-142 | `/reporting/attendance` | A, M | `GET /api/v1/reporting/attendance` |
| R-143 | `/reporting/engagement` | A, M | ADD-ON — F-018; deferred |
| R-150 | `/builders/report` | A | `POST /api/v1/reporting/custom` |

### Automations (2)

| ID | Route | Roles | Backend API |
|----|-------|-------|-------------|
| R-160 | `/automations` | A | `GET /api/v1/automations` |
| R-161 | `/builders/workflow` | A | `GET /api/v1/workflows/definitions` |

### Decision Cards (1)

| ID | Route | Roles | Backend API |
|----|-------|-------|-------------|
| R-170 | `/decisions` | A, M, PA | `GET /api/v1/decisions` — **non-standard envelope; in-memory** |

### Audit (1)

| ID | Route | Roles | Backend API |
|----|-------|-------|-------------|
| R-180 | `/audit` | A | `GET /api/v1/audit` |

### Search (1)

| ID | Route | Roles | Backend API |
|----|-------|-------|-------------|
| R-190 | `/search` | All | `GET /api/v1/search?q=` |

### ADD-ON Routes — Implementation Deferred (10)

| ID | Route | Feature | Status |
|----|-------|---------|--------|
| R-200 | `/performance` | F-017 | ADD-ON |
| R-201 | `/performance/reviews` | F-017 | ADD-ON |
| R-202 | `/performance/reviews/[id]` | F-017 | ADD-ON |
| R-210 | `/expense-claims` | F-021 | ADD-ON |
| R-211 | `/expense-claims/new` | F-021 | ADD-ON |
| R-212 | `/expense-claims/[id]` | F-021 | ADD-ON |
| R-220 | `/helpdesk` | F-019 | ADD-ON |
| R-230 | `/builders/survey` | F-018 | ADD-ON |
| R-240 | `/salary-revision` | F-022 | ADD-ON |
| R-241 | `/employees/[id]/ewa` | F-015 | ADD-ON |

---

## §2 — APPROVED SCREENS (49 TOTAL)

### Phase 3 Core Screens (36)

| Archetype | Screen ID | Route | Roles | Phase |
|-----------|-----------|-------|-------|-------|
| H01-01 | HR Manager Dashboard | `/dashboard` | A, M | CORE |
| H01-02 | Employee Self-Service Dashboard | `/dashboard` | E | CORE |
| H01-03 | Payroll Admin Dashboard | `/dashboard` | PA | CORE |
| H01-04 | Recruitment Dashboard | `/dashboard` | R | CORE |
| H02-01 | Employees List | `/employees` | A, M | CORE |
| H02-02 | Departments List | `/departments` | A, M | CORE |
| H02-03 | Roles List | `/roles` | A | CORE |
| H02-04 | Job Postings List | `/job-postings` | A, M, R | CORE |
| H02-05 | Leave Requests List | `/leave/requests` | A, M | CORE |
| H02-06 | Payroll Records List | `/payroll` | PA, A, M | CORE |
| H02-09 | Attendance Records List | `/attendance` | A, M, E | CORE |
| H03-01 | Employee Profile | `/employees/[id]` | A, M, E | CORE |
| H03-02 | Department Detail | `/departments/[id]` | A, M | CORE |
| H03-03 | Role Detail | `/roles/[id]` | A | CORE |
| H03-04 | Job Posting Detail | `/job-postings/[id]` | A, M, R | CORE |
| H03-05 | Leave Request Detail | `/leave/requests/[id]` | A, M, E | CORE |
| H03-06 | Payroll Record Detail | `/payroll/[id]` | PA, A, M, E | CORE |
| H04-01 | Add Employee (6-step) | `/employees/new` | A | CORE |
| H04-02 | Edit Employee | `/employees/[id]/edit` | A, M | CORE |
| H04-03 | Create Department | `/departments/new` | A | CORE |
| H04-04 | Create Role | `/roles/new` | A | CORE |
| H04-05 | Create Job Posting (4-step) | `/job-postings/new` | A, M, R | CORE |
| H04-06 | Raise Leave Request | `/leave/new` | All | CORE |
| H04-09 | Salary Revision | `/salary-revision` | A, PA | CORE |
| H05-01 | Approval Inbox | `/approvals` | A, M | CORE |
| H06-01 | Leave Calendar | `/leave/calendar` | All | CORE |
| H06-02 | Attendance Timeline | `/attendance/timeline` | A, M | CORE |
| H07-01 | HR Analytics | `/reporting` | A, M | CORE |
| H07-02 | Payroll Reports | `/reporting/payroll` | PA, A | CORE |
| H07-03 | Attendance Summary | `/reporting/attendance` | A, M | CORE |
| H07-05 | Compliance Reports | `/compliance` | A, PA | CORE |
| H08-01 | Global Search | `/search` | All | CORE |
| H09-01 | Notifications Inbox | `/notifications` | All | CORE |
| H10-01 | Organisation Settings | `/settings` | A | CORE |
| H11-01 | Workflow Builder | `/builders/workflow` | A | CORE |
| H11-03 | Report Builder | `/builders/report` | A | CORE |
| H13-01 | Candidate Pipeline | `/candidates-pipeline` | A, M, R | CORE |

Note: H13 includes a slide-over detail panel (H13 slide-over = `/candidates-pipeline/[id]`). Total = 37 entries, 36 unique archetypes.

### ADD-ON Screens — Deferred (8)

| Archetype | Screen ID | Route | Feature |
|-----------|-----------|-------|---------|
| H02-07 | Expense Claims List | `/expense-claims` | F-021 |
| H02-10 | Performance Reviews List | `/performance/reviews` | F-017 |
| H03-07 | Expense Claim Detail | `/expense-claims/[id]` | F-021 |
| H03-08 | Performance Review Detail | `/performance/reviews/[id]` | F-017 |
| H04-07 | Raise Expense Claim | `/expense-claims/new` | F-021 |
| H07-04 | Engagement Results | `/reporting/engagement` | F-018 |
| H11-02 | Survey Builder | `/builders/survey` | F-018 |
| H12-01 | Helpdesk | `/helpdesk` | F-019 |

### Out-of-Scope / Planned Screens — DO NOT BUILD (5)

| Screen | Wireframe | Reason |
|--------|-----------|--------|
| Shift Roster (H06-03) | `h06-shift-roster.html` | OUT OF SCOPE — no backend service |
| Documents List (H02-11) | `h02-documents.html` | OUT OF SCOPE — document management excluded |
| Travel Requests List (H02-08) | `h02-travel-requests.html` | PLANNED — F-023, service scaffolded only |
| Raise Travel Request (H04-08) | `h04-raise-travel-request.html` | PLANNED — F-023 |
| Project Management screens | (no wireframe) | PLANNED — F-024 |

---

## §3 — APPROVED DASHBOARDS (4)

One route (`/dashboard`), four variants. JWT role claim selects variant at runtime.

| Variant | Roles | Wireframe |
|---------|-------|-----------|
| HR Manager Dashboard | Admin (global), Manager (dept-scoped) | `h01-hr-manager-dashboard.html` |
| Employee Self-Service Dashboard | Employee | `h01-employee-self-service.html` |
| Payroll Admin Dashboard | PayrollAdmin | `h01-payroll-admin-dashboard.html` |
| Recruitment Dashboard | Recruiter | `h01-recruitment-dashboard.html` |

**Dashboard selection logic:** `role` claim in JWT → select variant. Admin and Manager share the HR Manager variant; data scope differs (global vs. dept-scoped). No separate URL per role.

---

## §4 — APPROVED WORKFLOWS (8)

| ID | Workflow | Status | Primary Screens |
|----|---------|--------|-----------------|
| WF-001 | Employee Onboarding | STABLE | `/employees/new`, `/employees/[id]` |
| WF-002 | Leave Request and Approval | STABLE | `/leave/new`, `/leave`, `/approvals` |
| WF-003 | Payroll Run | STABLE | `/payroll`, `/payroll/run`, `/payroll/[id]` |
| WF-004 | Hiring Pipeline | STABLE | `/job-postings/new`, `/candidates-pipeline`, `/candidates-pipeline/[id]` |
| WF-005 | Performance Review Cycle | ADD-ON | `/performance`, `/performance/reviews/[id]` |
| WF-006 | Expense Claim | ADD-ON | `/expense-claims/new`, `/expense-claims/[id]` |
| WF-007 | Audit and Compliance Reporting | STABLE | `/audit`, `/compliance` |
| WF-008 | Employee Self-Service | STABLE | `/dashboard`, `/leave/new`, `/payroll/[id]`, `/notifications` |

**Phase 4 core workflows:** WF-001, WF-002, WF-003, WF-004, WF-007, WF-008.
**ADD-ON workflows:** WF-005, WF-006 — deferred.

---

## §5 — APPROVED ROLES (5)

| Role | JWT Claim | Scope | Dashboard Variant |
|------|-----------|-------|-------------------|
| Admin | `Admin` | Global | HR Manager Dashboard |
| PayrollAdmin | `PayrollAdmin` | Global (payroll/compliance) | Payroll Admin Dashboard |
| Manager | `Manager` | Department-scoped | HR Manager Dashboard (dept-scoped) |
| Recruiter | `Recruiter` | Global (hiring) | Recruitment Dashboard |
| Employee | `Employee` | Own records | Employee Self-Service Dashboard |

**Rule:** No new roles may be introduced without a new ADR and REQUIRES_APPROVAL change to `api_gateway_service.py` and `security-model.md`.

---

## §6 — APPROVED PERMISSIONS (31 CAPABILITIES)

| Capability | Description | Roles |
|-----------|-------------|-------|
| CAP-EMP-001 | View Employee Records | A (global), PA (read), M (dept), E (own) |
| CAP-EMP-002 | Create/Edit Employee Records | A (global), M (dept, limited fields) |
| CAP-ATT-001 | View Attendance Records | A (global), M (dept), E (own) |
| CAP-ATT-002 | Manage Attendance Rules | A |
| CAP-LEV-001 | View Leave Requests | A (global), M (dept), E (own), PA (read), R (own) |
| CAP-LEV-002 | Submit Leave Requests | All |
| CAP-PAY-001 | View Payroll Records | A (global), PA (global), M (dept), E (own) |
| CAP-PAY-002 | Process Payroll (Run) | A, PA |
| CAP-HIR-001 | View Hiring Data | A, M, R |
| CAP-HIR-002 | Manage Hiring | A, M, R |
| CAP-PRF-001 | View Performance Data (ADD-ON) | A, M (dept), E (own) |
| CAP-AUT-001 | Manage Roles | A |
| CAP-AUT-002 | Manage Automation Rules | A |
| CAP-AUT-003 | Token & Session Management | A (full), All (own session) |
| CAP-NOT-001 | Receive Notifications | All |
| CAP-NOT-002 | Send Notifications | A |
| CAP-ENG-001 | View Engagement Data (ADD-ON) | A, M (team) |
| CAP-COM-001 | View Compliance Reports | A, PA |
| CAP-COM-002 | Manage Compliance | A |
| CAP-DEC-001 | View Decision Cards | A (global), PA (payroll scope), M (dept scope) |
| CAP-DEC-002 | Resolve Decision Cards | A |
| CAP-EWA-001 | Request EWA | E |
| CAP-EWA-002 | Approve EWA | A, PA, M |
| CAP-BNK-001 | View Banking/Disbursement Details | A, PA |
| CAP-BNK-002 | Trigger Disbursement | A, PA |
| CAP-RPT-001 | View Reports | A (all tabs), M (HR + attendance, dept-scoped), PA (payroll tab) |
| CAP-RPT-002 | Build Custom Reports | A |
| CAP-WA-001 | WhatsApp Integration Config | A |
| CAP-EXP-001 | Manage Expenses (ADD-ON) | A, M (dept), E (own) |
| CAP-HLP-001 | Submit Helpdesk Tickets (ADD-ON) | All |
| CAP-HLP-002 | Manage Helpdesk Tickets (ADD-ON) | A |

---

## §7 — APPROVED API DEPENDENCIES (25 GATEWAY ROUTES)

| Gateway Prefix | Service | Phase 4 Status | Envelope |
|---------------|---------|---------------|---------|
| `/api/v1/employees` | employee-service | CORE | Standard `{status, data, meta, error}` |
| `/api/v1/departments` | employee-service | CORE | Standard |
| `/api/v1/roles` | employee-service (C-004) | CORE | Standard |
| `/api/v1/auth` | auth-service | CORE | Standard |
| `/api/v1/attendance` | attendance-service | CORE | Standard |
| `/api/v1/leave` | leave-service | CORE | Standard |
| `/api/v1/payroll` | payroll-service | CORE | Standard |
| `/api/v1/hiring` | hiring-service | CORE | Standard |
| `/api/v1/workflows` | workflow-service | CORE | Standard |
| `/api/v1/settings` | settings-service | CORE (volatile) | Standard |
| `/api/v1/notifications` | notification-service | CORE | Standard |
| `/api/v1/reporting` | reporting-analytics | CORE | Standard |
| `/api/v1/compliance` | compliance-service | CORE | **Non-standard `{status, data, service}`** |
| `/api/v1/decisions` | decision-engine | CORE | **Non-standard `{status, data, service}`** |
| `/api/v1/banking` | banking-service | CORE (backend only) | **Non-standard `{status, data, service}`** |
| `/api/v1/whatsapp` | whatsapp-service | CORE (backend only) | **Non-standard `{status, data, service}`** |
| `/api/v1/search` | search-service | CORE | Standard |
| `/api/v1/ewa` | ewa-service | CORE | Standard |
| `/api/v1/audit` | audit-service | CORE | Standard |
| `/api/v1/automations` | automations-service | CORE | Standard |
| `/api/v1/performance` | performance-service | ADD-ON | Standard |
| `/api/v1/engagement` | engagement-service | ADD-ON | Standard |
| `/api/v1/expenses` | expense-service | ADD-ON | Standard |
| `/api/v1/helpdesk` | helpdesk-service | ADD-ON | Standard |
| `/api/v1/integrations` | integration-service | Chrome-only | Standard |

**All API calls go through gateway at `localhost:8000`. Never call services directly.**

---

## §8 — APPROVED FRONTEND STATES

Every screen and every widget MUST implement all 4 states:

| State | Behavior |
|-------|---------|
| Loading | Skeleton / shimmer placeholder matching expected layout size |
| Empty | No-data state with appropriate CTA or explanation — not just an empty page |
| Error | Failed API state with retry option; partial failures must not crash the whole screen |
| Success/Data | Rendered content |

**Dashboard partial-failure rule:** A single widget API failure MUST NOT prevent the dashboard from rendering. Each widget fetches independently via TanStack React Query. Widget failures render their own error state; other widgets continue.

---

## §9 — APPROVED NAVIGATION GROUPS (9 SECTIONS)

| Section | Label | Routes | Roles |
|---------|-------|--------|-------|
| A: Core | Dashboard, Notifications | `/dashboard`, `/notifications` | All |
| B: People & Org | Employees, Departments, Organisation, Roles | `/employees`, `/departments`, `/organization`, `/roles` | A, M (no Roles for M) |
| C: Attendance & Leave | Attendance, Leave | `/attendance`, `/leave` | A, M, E (Attendance: not PA, R); Leave: All |
| D: Payroll | Payroll | `/payroll` | PA, A, M |
| E: Hiring | Hiring, Job Postings, Pipeline | `/hiring`, `/job-postings`, `/candidates-pipeline` | A, M, R |
| F: Approvals | Approvals | `/approvals` | A, M |
| G: Analytics & Compliance | Reporting, Compliance, Audit Log, Decision Cards | `/reporting`, `/compliance`, `/audit`, `/decisions` | A, M (no Audit, Compliance), PA (Compliance, Decisions) |
| H: Automation | Automations, Workflow Builder, Report Builder | `/automations`, `/builders/workflow`, `/builders/report` | A |
| I: Settings | Settings | `/settings` | A |
| ADD-ON | Performance, Expense Claims, Helpdesk, Engagement, Survey Builder | ADD-ON routes | Render only when feature enabled |

**Empty section rule:** If a role has no items in a section, omit the section heading entirely. Never render an empty section heading.

---

## §10 — APPROVED BLOCKED / EXCLUDED ITEMS

These items are EXCLUDED from all Phase 4 work. Do not design, prototype, or build any of the following:

### Screens — DO NOT BUILD

| Item | Reason |
|------|--------|
| Shift Roster | OUT OF SCOPE — no backend service |
| Documents List / Management | OUT OF SCOPE — no backend service |
| Travel Requests List (H02-08) | PLANNED — F-023 service scaffolded only |
| Raise Travel Request (H04-08) | PLANNED — F-023 |
| Project Management screens | PLANNED — F-024 no wireframes |
| Biometric enrollment screen | ADD-ON — no backend implementation |
| Succession planning screen | ADD-ON — excluded |
| Benefits enrollment screen | ADD-ON — excluded |
| Standalone WhatsApp management screen | OUT OF SCOPE by design — backend integration only |
| Standalone Banking management screen | OUT OF SCOPE by design — surfaces through payroll detail |

### Features — DO NOT BUILD

| Item | Reason |
|------|--------|
| Performance Management (F-017) | ADD-ON — deferred |
| Employee Engagement Surveys (F-018) | ADD-ON — deferred |
| Helpdesk (F-019) | ADD-ON — deferred |
| Expense Management (F-021) | ADD-ON — deferred |
| Integration Hub (F-022) | ADD-ON — deferred |
| Travel Management (F-023) | PLANNED — no backend |
| Project Management (F-024) | PLANNED — no backend |
| LMS | OUT OF SCOPE — confirmed absent |
| Shift/Roster Scheduling | OUT OF SCOPE — confirmed absent |
| Video interview integration | OUT OF SCOPE |
| Native mobile app | FUTURE SCOPE |
| Multi-country modules (India, UAE, etc.) | OUT OF SCOPE for Phase 4 |

---

## §11 — APPROVED SAFE DEFAULTS

### Phase 4 Conditions (C-001 to C-004) — MANDATORY

| Condition | Rule | Impact |
|-----------|------|--------|
| C-001 | 4 services (compliance, decision, banking, whatsapp) return `{status, data, service}` — NO `meta` field | Frontend API client must normalize both envelope shapes; never assume `meta` for these 4 services |
| C-002 | Settings-service uses in-memory dict stub — resets on restart | Frontend must not cache settings aggressively; treat settings as volatile |
| C-003 | Frontend is at `backend/ui/` — NOT repo root `frontend/` | All Phase 4 work targets `backend/ui/`; no frontend relocation during Phase 4 |
| C-004 | `/api/v1/roles` and `/api/v1/departments` are served by employee-service (no separate gateway prefix) | Route all role/dept calls through `/api/v1/roles` and `/api/v1/departments` at the gateway |

### Technical Defaults

| Default | Value |
|---------|-------|
| API base URL (dev) | `http://localhost:8000` |
| Frontend port (dev) | 3000 |
| Auth token type | JWT HS256, Bearer |
| Auth-exempt routes | `/api/v1/auth/*`, `/health`, `/ready`, `/metrics` |
| JWT claims forwarded | X-User-Id, X-User-Role, X-Tenant-Id |
| Rate limit | 200 req/min per IP |
| State management (server state) | TanStack React Query |
| Workflow status values | lowercase: `pending`, `completed`, `approved`, `rejected` |
| Employee lifecycle statuses | `draft`, `active`, `on_leave`, `suspended`, `terminated` |
| Frontend sidebar collapsed | 54px |
| Frontend sidebar expanded | 216px |
| Frontend topbar height | 52px |
| Primary font | Inter |
| Monospace font | JetBrains Mono (numbers, IDs) |
| Content background | `#F5F7FA` |

---

## §12 — REMAINING OWNER CONFIRMATIONS (NON-BLOCKING)

These items are OPEN but do NOT block Phase 4 frontend implementation.

| ID | Item | Impact on Phase 4 |
|----|------|------------------|
| OD-001 | Commercial launch date | None — determines sprint urgency, not implementation |
| OD-002 | Scaling strategy (Docker Compose vs Kubernetes) | None — rate limiter SD-033 default applies for single-replica |
| OD-003 | Data residency for multi-country expansion | None — Pakistan launch; `backend/country/pakistan/` is the only active country |

---

## §13 — FREEZE GOVERNANCE

**Frozen inputs may NOT be altered without:**
1. Owner authorization for scope changes (new routes, new screens, new roles)
2. REQUIRES_APPROVAL for API changes (`api_gateway_service.py`, `routes.py`)
3. New ADR for architectural decisions (new frameworks, new patterns, role additions)

**Freeze date:** 2026-06-20
**Freeze authority:** Phase 3 authority layer (all 13 source documents confirmed COMPLETE)
**Implementation phase:** Phase 4 — Frontend Implementation
