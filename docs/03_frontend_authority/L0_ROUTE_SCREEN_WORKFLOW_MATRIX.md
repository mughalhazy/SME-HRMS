# L0 ROUTE-SCREEN-WORKFLOW MATRIX

Phase: 3.5 — L0 Frontend Authority Input Freeze
Status: FROZEN
Created: 2026-06-20
Freeze: L0 FROZEN

---

## PURPOSE

Cross-references every approved route with its screen(s), workflow(s), API dependencies, roles, and archetype. This matrix is the single lookup table for Claude Design and Claude Code to validate traceability.

**Rule:** Every column value must trace to a source in Phase 3 authority documents. No value in this matrix was invented in Phase 3.5.

---

## NOTATION

- A = Admin | PA = PayrollAdmin | M = Manager | R = Recruiter | E = Employee
- ✳ = ADD-ON (implementation deferred)
- ❌ = Excluded (OUT OF SCOPE or PLANNED)
- **NS** = Non-standard envelope: `{status, data, service}` — no `meta` field

---

## PART 1 — CORE ROUTE × SCREEN × WORKFLOW MATRIX

| Route | Screen ID | Screen Name | Archetype | Roles | Workflow(s) | Primary APIs | Feature |
|-------|-----------|-------------|-----------|-------|-------------|-------------|---------|
| `/login` | — (custom) | Login | Custom | Public | — | `POST /api/v1/auth/login` | F-006 |
| `/logout` | — (redirect) | Logout | Redirect | All | — | `POST /api/v1/auth/logout` | F-006 |
| `/auth/refresh` | — (programmatic) | Token Refresh | Programmatic | All | — | `POST /api/v1/auth/refresh` | F-006 |
| `/dashboard` | H01-01 | HR Manager Dashboard | H01 | A, M | WF-001, WF-002, WF-003, WF-004 | Summary + widget APIs | F-001, F-002, F-003, F-004, F-012 |
| `/dashboard` | H01-02 | Employee Self-Service | H01 | E | WF-008 | Leave balance, attendance, payslip, notifications | F-002, F-003, F-009 |
| `/dashboard` | H01-03 | Payroll Admin Dashboard | H01 | PA | WF-003, WF-007 | Payroll status, compliance, decisions | F-004, F-011, F-016 |
| `/dashboard` | H01-04 | Recruitment Dashboard | H01 | R | WF-004 | Hiring postings, candidates, interviews | F-005 |
| `/employees` | H02-01 | Employees List | H02 | A, M | WF-001 | `GET /api/v1/employees` | F-001 |
| `/employees/[id]` | H03-01 | Employee Profile | H03 | A, M, E | WF-001, WF-008 | `GET /api/v1/employees/{id}`, leave, attendance, payroll | F-001 |
| `/employees/new` | H04-01 | Add Employee (6-step) | H04 | A | WF-001 | `POST /api/v1/employees`, roles, depts, settings | F-001 |
| `/employees/[id]/edit` | H04-02 | Edit Employee | H04 | A, M | WF-001 | `GET /api/v1/employees/{id}`, `PATCH /api/v1/employees/{id}` | F-001 |
| `/departments` | H02-02 | Departments List | H02 | A, M | — | `GET /api/v1/departments` | F-001 |
| `/departments/[id]` | H03-02 | Department Detail | H03 | A, M | — | `GET /api/v1/departments/{id}`, `GET /api/v1/employees?dept_id=` | F-001 |
| `/departments/new` | H04-03 | Create Department | H04 | A | — | `POST /api/v1/departments`, depts (parent), employees (head) | F-001 |
| `/organization` | H02/H03 hybrid | Organisation Chart | H02/H03 | A, M | — | `GET /api/v1/departments`, `GET /api/v1/employees` | F-001 |
| `/roles` | H02-03 | Roles List | H02 | A | — | `GET /api/v1/roles` | F-001 |
| `/roles/[id]` | H03-03 | Role Detail | H03 | A | — | `GET /api/v1/roles/{id}` | F-001 |
| `/roles/new` | H04-04 | Create Role | H04 | A | — | `POST /api/v1/roles` | F-001 |
| `/attendance` | H02-09 | Attendance Records | H02 + H06 tab | A, M, E | WF-008 | `GET /api/v1/attendance` | F-002 |
| `/attendance/timeline` | H06-02 | Attendance Timeline | H06 | A, M | — | `GET /api/v1/attendance?timeline=true` | F-002 |
| `/leave` | H06-01 + H02 tab | Leave Calendar | H06 + H02 | All | WF-002, WF-008 | `GET /api/v1/leave`, `GET /api/v1/leave/balance` | F-003 |
| `/leave/requests` | H02-05 | Leave Requests List | H02 | A, M | WF-002 | `GET /api/v1/leave?all=true` | F-003 |
| `/leave/requests/[id]` | H03-05 | Leave Request Detail | H03 | A, M, E | WF-002 | `GET /api/v1/leave/{id}` | F-003 |
| `/leave/new` | H04-06 | Raise Leave Request | H04 | All | WF-002, WF-008 | `POST /api/v1/leave`, `GET /api/v1/leave/balance`, settings | F-003 |
| `/leave/calendar` | H06-01 | Leave Calendar | H06 | All | WF-002 | `GET /api/v1/leave?calendar=true` | F-003 |
| `/payroll` | H02-06 | Payroll Records List | H02 | PA, A, M | WF-003 | `GET /api/v1/payroll` | F-004 |
| `/payroll/[id]` | H03-06 | Payroll Record Detail | H03 | PA, A, M, E | WF-003, WF-008 | `GET /api/v1/payroll/{id}` | F-004 |
| `/payroll/run` | H04 (trigger) | Payroll Run Form | H04 | PA, A | WF-003 | `POST /api/v1/payroll/run` | F-004 |
| `/hiring` | H01 (dashboard) | Hiring Dashboard | H01 | A, M, R | WF-004 | `GET /api/v1/hiring/summary` | F-005 |
| `/job-postings` | H02-04 | Job Postings List | H02 | A, M, R | WF-004 | `GET /api/v1/hiring/postings` | F-005 |
| `/job-postings/[id]` | H03-04 | Job Posting Detail | H03 | A, M, R | WF-004 | `GET /api/v1/hiring/postings/{id}` | F-005 |
| `/job-postings/new` | H04-05 | Create Job Posting (4-step) | H04 | A, M, R | WF-004 | `POST /api/v1/hiring/postings` | F-005 |
| `/candidates-pipeline` | H13-01 | Candidate Pipeline | H13 | A, M, R | WF-004 | `GET /api/v1/hiring/candidates`, `GET /api/v1/hiring/pipeline` | F-005 |
| `/candidates-pipeline/[id]` | H13 slide-over | Candidate Detail | H03 slide-over | A, M, R | WF-004 | `GET /api/v1/hiring/candidates/{id}` | F-005 |
| `/approvals` | H05-01 | Approval Inbox | H05 | A, M | WF-002, WF-003, WF-008 | `GET /api/v1/workflows?status=pending`, `PUT /api/v1/workflows/{id}/steps/{step_id}` | F-007 |
| `/notifications` | H09-01 | Notifications Inbox | H09 | All | All workflows (notification sink) | `GET /api/v1/notifications`, `PATCH /api/v1/notifications/{id}/read` | F-009 |
| `/settings` | H10-01 | Organisation Settings | H10 | A | — | `GET /api/v1/settings`, `PUT /api/v1/settings` | F-010 |
| `/compliance` | H07-05 | Compliance Reports | H07 | A, PA | WF-007 | `GET /api/v1/compliance` **NS** | F-011 |
| `/reporting` | H07-01 | HR Analytics | H07 | A, M | — | `GET /api/v1/reporting/dashboards` | F-012 |
| `/reporting/payroll` | H07-02 | Payroll Reports | H07 tab | PA, A | WF-003 | `GET /api/v1/reporting/payroll` | F-012 |
| `/reporting/attendance` | H07-03 | Attendance Summary | H07 tab | A, M | — | `GET /api/v1/reporting/attendance` | F-012 |
| `/builders/report` | H11-03 | Report Builder | H11 | A | — | `POST /api/v1/reporting/custom` | F-012 |
| `/automations` | H11 | Automations List | H11 | A | — | `GET /api/v1/automations`, `POST /api/v1/automations` | F-013 |
| `/builders/workflow` | H11-01 | Workflow Builder | H11 | A | — | `GET /api/v1/workflows/definitions`, `POST /api/v1/workflows/definitions` | F-007, F-013 |
| `/decisions` | H03 custom | Decision Cards | H03 custom | A, M, PA | — | `GET /api/v1/decisions` **NS** | F-014 |
| `/audit` | H02 | Audit Log | H02 | A | WF-007 | `GET /api/v1/audit` | F-008 |
| `/search` | H08-01 | Global Search | H08 | All | — | `GET /api/v1/search?q=` | F-020 (ADD-ON) |

---

## PART 2 — WORKFLOW × SCREEN FULL TRACE

### WF-001: Employee Onboarding

| Step | Role | Screen | Route | API | Action |
|------|------|--------|-------|-----|--------|
| 1 | Admin | Add Employee (H04) | `/employees/new` | `POST /api/v1/employees` | Submit 6-step form |
| 2 | Admin | Add Employee Step 1 | `/employees/new` | (form step) | Personal Info |
| 3 | Admin | Add Employee Step 2 | `/employees/new` | (form step) | Employment Details |
| 4 | Admin | Add Employee Step 3 | `/employees/new` | `GET /api/v1/roles`, `GET /api/v1/departments` | Role & Department |
| 5 | Admin | Add Employee Step 4 | `/employees/new` | (form step) | Compensation |
| 6 | Admin | Add Employee Step 5 | `/employees/new` | (form step) | System Access |
| 7 | Admin | Add Employee Step 6 | `/employees/new` | `POST /api/v1/employees` | Review & Confirm |
| 8 | System | Employee Profile (H03) | `/employees/[id]` | `GET /api/v1/employees/{id}` | Record created |

**Employee lifecycle states:** `draft` → `active` → `on_leave` / `suspended` / `terminated`

---

### WF-002: Leave Request and Approval

| Step | Role | Screen | Route | API | Action |
|------|------|--------|-------|-----|--------|
| 1 | Employee | Raise Leave (H04) | `/leave/new` | `GET /api/v1/leave/balance` | Check balance |
| 2 | Employee | Raise Leave (H04) | `/leave/new` | `POST /api/v1/leave` | Submit request |
| 3 | Employee | Leave (H06) | `/leave` | `GET /api/v1/leave?me=true` | Pending status visible |
| 4 | Manager | Notifications (H09) → Approvals (H05) | `/notifications` → `/approvals` | `GET /api/v1/workflows?status=pending` | Notification → inbox |
| 5 | Manager | Approval Inbox (H05) | `/approvals` | `GET /api/v1/leave/{id}` | Review detail |
| 6a | Manager | Approval Inbox (H05) | `/approvals` | `PUT /api/v1/workflows/{id}/steps/{step_id}` `{action: "approve"}` | Approve |
| 6b | Manager | Approval Inbox (H05) | `/approvals` | `PUT /api/v1/workflows/{id}/steps/{step_id}` `{action: "reject", reason: "..."}` | Reject |
| 7 | Employee | Notifications (H09) | `/notifications` | `GET /api/v1/notifications` | Receive result |
| 8 | All | Leave Calendar (H06) | `/leave/calendar` | `GET /api/v1/leave?calendar=true` | Approved leave visible |

**Leave request states:** `pending` → `approved` / `rejected` / `cancelled`

---

### WF-003: Payroll Run

| Step | Role | Screen | Route | API | Action |
|------|------|--------|-------|-----|--------|
| 1 | PA/A | Payroll List (H02) | `/payroll` | — | Click "Run Payroll" |
| 2 | PA/A | Payroll Run Form (H04) | `/payroll/run` | — | Select pay period |
| 3 | PA/A | Payroll Run Form | `/payroll/run` | `POST /api/v1/payroll/run` `{validate_only: true}` | Validate |
| 4 | PA/A | Payroll Run Form | `/payroll/run` | (response) | Review warnings |
| 5 | PA/A | Payroll Run Form | `/payroll/run` | `POST /api/v1/payroll/run` | Confirm submit |
| 6 | PA/A | Payroll List (H02) | `/payroll` | `GET /api/v1/payroll?status=processing` | Processing status |
| 7 | PA/A | Payroll Record Detail (H03) | `/payroll/[id]` | `GET /api/v1/payroll/{id}` | View results |
| 8 (optional) | A | Approvals (H05) | `/approvals` | `PUT /api/v1/workflows/{id}/steps/{step_id}` | Secondary approval |
| 9 | PA/A | Payroll Record Detail (H03) | `/payroll/[id]` | `POST /api/v1/payroll/{id}/disburse` | Trigger disbursement |
| 10 | PA/A | Payroll Record Detail (H03) | `/payroll/[id]` | `GET /api/v1/payroll/{id}` | Disbursed status |
| 11 | E | Dashboard (H01) or `/payroll/[id]` | `/dashboard` | `GET /api/v1/payroll?me=true&latest=true` | View payslip |

**Payroll record states:** `draft` / `processing` / `completed` / `pending_disbursement` / `disbursed` / `failed`

---

### WF-004: Hiring Pipeline

| Step | Role | Screen | Route | API | Action |
|------|------|--------|-------|-----|--------|
| 1 | A/M/R | Create Job Posting (H04) | `/job-postings/new` | `POST /api/v1/hiring/postings` | 4-step form |
| 2 | A/M/R | Job Posting Detail (H03) | `/job-postings/[id]` | `PATCH /api/v1/hiring/postings/{id}` `{status: "published"}` | Publish |
| 3 | A/M/R | Pipeline (H13) | `/candidates-pipeline` | `GET /api/v1/hiring/candidates` | Candidates in Applied |
| 4 | A/M/R | Pipeline (H13) | `/candidates-pipeline` | `PATCH /api/v1/hiring/candidates/{id}` `{stage: "Screening"}` | Advance stage |
| 5 | A/M/R | Candidate slide-over | `/candidates-pipeline/[id]` | `POST /api/v1/hiring/interviews` | Schedule interview |
| 6 | A/M/R | Pipeline (H13) | `/candidates-pipeline` | `PATCH /api/v1/hiring/candidates/{id}` `{stage: "Interviewing"}` | Interview stage |
| 7 | A/M/R | Pipeline (H13) | `/candidates-pipeline` | (UI-only — backend stage = `Interviewing`) | Final Round UI stage |
| 8 | A/M/R | Candidate slide-over | `/candidates-pipeline/[id]` | `PATCH /api/v1/hiring/candidates/{id}` `{stage: "Offered"}` | Extend offer |
| 9 | A/M/R | Candidate slide-over | `/candidates-pipeline/[id]` | `PATCH /api/v1/hiring/candidates/{id}` `{stage: "Hired"}` | Mark hired → WF-001 |
| 10 | A/M/R | Candidate slide-over | `/candidates-pipeline/[id]` | `PATCH /api/v1/hiring/candidates/{id}` `{stage: "Rejected"}` | Reject |

**Kanban stage mapping:**

| Frontend Column | Backend Stage Value |
|----------------|---------------------|
| Applied | `Applied` |
| Screening | `Screening` |
| Interview | `Interviewing` |
| Final Round | `Interviewing` (UI-only) |
| Offer Sent | `Offered` |
| (Hired) | `Hired` — removed from kanban |
| (Rejected) | `Rejected` — filtered view |

---

### WF-007: Audit and Compliance Reporting

| Step | Role | Screen | Route | API | Action |
|------|------|--------|-------|-----|--------|
| 1 | A | Audit Log (H02) | `/audit` | `GET /api/v1/audit` | Filter log |
| 2 | A | Audit Log (H02) | `/audit` | `GET /api/v1/audit/{id}` | Expand row detail |
| 3 | A | Audit Log (H02) | `/audit` | `GET /api/v1/audit?export=csv` | Export CSV |
| 4 | PA/A | Compliance Reports (H07) | `/compliance` | `GET /api/v1/compliance` **NS** | View statutory filings |
| 5 | A | Compliance Reports (H07) | `/compliance` | `POST /api/v1/compliance/generate` | Generate report |
| 6 | PA/A | Compliance Reports (H07) | `/compliance` | `GET /api/v1/compliance/{id}/export` | Download |

---

### WF-008: Employee Self-Service

| Step | Role | Screen | Route | API | Action |
|------|------|--------|-------|-----|--------|
| 1 | E | Login | `/login` | `POST /api/v1/auth/login` | Authenticate |
| 2 | E | Employee Dashboard (H01) | `/dashboard` | Widget APIs | View KPIs |
| 3 | E | Attendance (H02) | `/attendance` | `GET /api/v1/attendance?me=true` | Own history |
| 4 | E | Raise Leave (H04) | `/leave/new` | `POST /api/v1/leave` | Submit leave → WF-002 |
| 5 | E | Payroll Detail (H03) | `/payroll/[id]` (own) | `GET /api/v1/payroll/{id}` | View payslip |
| 6 | E | Notifications (H09) | `/notifications` | `GET /api/v1/notifications?me=true` | Read results |
| 7 | E | EWA Request | `/employees/[id]/ewa` | `POST /api/v1/ewa/request` | Request advance |
| 8 | E | Employee Profile (H03) | `/employees/[id]` (own) | `GET /api/v1/employees/{id}` | View own profile |

---

## PART 3 — SCREEN UNIVERSAL REQUIREMENTS

### All Screens

Every screen in this matrix MUST implement:

| Requirement | Rule |
|-------------|------|
| 4 UI states | Loading (skeleton), Empty (CTA), Error (retry), Data (content) |
| Permission check | Render UI elements only if the role's capability permits — never rely solely on nav hiding |
| Scope enforcement | Dept-scoped: pass dept context; Own-scoped: pass X-User-Id; never pass cross-scope IDs |
| Non-standard envelope | `/compliance`, `/decisions`, `/banking`, `/whatsapp` — no `meta` field; handle `service` field |
| Token propagation | JWT Bearer header on every non-exempt request; X-User-Id, X-User-Role, X-Tenant-Id forwarded |
| Error on 403 | Render "Not Authorized" — do not crash screen or leak data |

### Form Screens (H04)

| Requirement | Rule |
|-------------|------|
| Multi-step forms | Cannot advance step without completing required fields |
| Validation | Client-side validation matches backend rules (from VALIDATION_RULES.md) |
| On submit | Navigate to the created/updated resource detail screen |

### Dashboard Screens (H01)

| Requirement | Rule |
|-------------|------|
| Widget isolation | Each widget fetches independently; one failure must not break other widgets |
| Empty dashboard | Show onboarding checklist if key data source returns zero records (new tenant) |
| Role-adaptive | Same URL `/dashboard`, variant selected from JWT role claim |

---

## PART 4 — API CONSUMER COMPLETENESS

All 25 gateway routes have Phase 4 consumers. Zero orphan APIs. Zero orphan screens.

| Status | Count |
|--------|-------|
| Phase 4 Core consumers confirmed | 20 routes |
| ADD-ON (deferred) | 4 routes |
| Chrome-only (Phase 3) | 1 route (integrations) |
| **Total** | **25** |
