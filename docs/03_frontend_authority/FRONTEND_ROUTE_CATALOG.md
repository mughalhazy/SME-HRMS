# FRONTEND ROUTE CATALOG

Status: Complete
Created: 2026-06-17
Phase: 3 — Frontend Authority Capture
Source: PRODUCT_DECISION_REGISTER §2.1, API_CONTRACT §4, security-model.md, archetype-system-v1.md

---

## PURPOSE

Authoritative inventory of every frontend route. Each route entry includes its archetype, primary roles, backend API dependency, available primary actions, and blocking conditions (render a 403 or redirect if the condition is false).

**Rule:** No route in this catalog exists without a confirmed backend API. No route exists for a feature outside F-001 to F-016 unless it is an ADD-ON route clearly marked as such.

---

## NOTATION

- **Roles**: Admin (A), PayrollAdmin (PA), Manager (M), Recruiter (R), Employee (E)
- **ADD-ON**: Feature deferred from Phase 3 core; route authority defined, implementation deferred
- **[dynamic]**: Route contains a URL parameter (e.g., `/employees/[id]`)

---

## SECTION 1 — AUTH ROUTES

| # | Route | Archetype | Roles | Backend API | Primary Actions | Blocking Conditions |
|---|-------|-----------|-------|-------------|-----------------|---------------------|
| R-001 | `/login` | Custom | Public | `POST /api/v1/auth/login` | Submit credentials, receive JWT | None (public) |
| R-002 | `/logout` | Redirect | All | `POST /api/v1/auth/logout` | Invalidate token, clear session | Must have active session |
| R-003 | `/auth/refresh` | Programmatic | All | `POST /api/v1/auth/refresh` | Refresh access token silently | Valid refresh token present |

---

## SECTION 2 — DASHBOARD ROUTES

| # | Route | Archetype | Roles | Backend API | Primary Actions | Blocking Conditions |
|---|-------|-----------|-------|-------------|-----------------|---------------------|
| R-010 | `/dashboard` | H01 | All authenticated | `GET /api/v1/employees/summary`, `GET /api/v1/attendance/summary`, `GET /api/v1/leave/balance`, `GET /api/v1/payroll/summary`, `GET /api/v1/hiring/summary`, `GET /api/v1/notifications?unread=true` | Navigate to key sections, view KPIs, trigger quick actions | Valid JWT required; role claim present |

**Note:** `/dashboard` renders one of four H01 variants based on the `role` claim in JWT. The same URL serves all roles with a role-adaptive layout. See FRONTEND_DASHBOARD_CATALOG.md for per-role widget specifications.

---

## SECTION 3 — EMPLOYEE MANAGEMENT ROUTES (F-001)

| # | Route | Archetype | Roles | Backend API | Primary Actions | Blocking Conditions |
|---|-------|-----------|-------|-------------|-----------------|---------------------|
| R-020 | `/employees` | H02 | A, M | `GET /api/v1/employees` | Search, filter, sort, paginate, export, navigate to profile, add employee | CAP-EMP-001 |
| R-021 | `/employees/[id]` | H03 | A, M, E (own) | `GET /api/v1/employees/{id}` | View tabs (Overview/Compensation/Documents/Leave/Performance/History), initiate actions | CAP-EMP-001 (all) or employee viewing own record |
| R-022 | `/employees/new` | H04 | A | `POST /api/v1/employees` | Submit 6-step add-employee form: Personal Info → Employment → Role & Dept → Compensation → Access & Roles → Review | CAP-EMP-002 |
| R-023 | `/employees/[id]/edit` | H04 | A, M (dept-scoped) | `PATCH /api/v1/employees/{id}` | Edit employee fields, save changes, cancel | CAP-EMP-002 |
| R-030 | `/departments` | H02 | A, M | `GET /api/v1/departments` | List, filter, create new, navigate to detail | CAP-EMP-001 |
| R-031 | `/departments/[id]` | H03 | A, M | `GET /api/v1/departments/{id}` | View dept employees, org hierarchy, edit | CAP-EMP-001 |
| R-032 | `/departments/new` | H04 | A | `POST /api/v1/departments` | Create department with name, head, parent | CAP-EMP-002 |
| R-040 | `/organization` | H02/H03 hybrid | A, M | `GET /api/v1/departments`, `GET /api/v1/employees` | View org tree/chart, navigate to dept/employee | CAP-EMP-001 |
| R-050 | `/roles` | H02 | A | `GET /api/v1/roles` | List all roles, create new, view assignments | CAP-AUT-001 (admin-only) |
| R-051 | `/roles/[id]` | H03 | A | `GET /api/v1/roles/{id}` | View role permissions, assigned employees | CAP-AUT-001 |
| R-052 | `/roles/new` | H04 | A | `POST /api/v1/roles` | Create role with permission set | CAP-AUT-001 |

---

## SECTION 4 — ATTENDANCE ROUTES (F-002)

| # | Route | Archetype | Roles | Backend API | Primary Actions | Blocking Conditions |
|---|-------|-----------|-------|-------------|-----------------|---------------------|
| R-060 | `/attendance` | H02 + H06 tab | A, M, E (own) | `GET /api/v1/attendance` | View records list, switch to timeline view, filter by employee/date/status | CAP-ATT-001; Manager gets dept-scoped; Employee gets own records |
| R-061 | `/attendance/timeline` | H06 | A, M | `GET /api/v1/attendance` | View attendance timeline visualization by employee or date range | CAP-ATT-001 |

---

## SECTION 5 — LEAVE ROUTES (F-003)

| # | Route | Archetype | Roles | Backend API | Primary Actions | Blocking Conditions |
|---|-------|-----------|-------|-------------|-----------------|---------------------|
| R-070 | `/leave` | H06 + H02 tab | All | `GET /api/v1/leave`, `GET /api/v1/leave/balance` | View leave calendar, switch to list view, check balances, apply for leave | CAP-LEV-001 |
| R-071 | `/leave/requests` | H02 | A, M | `GET /api/v1/leave?all=true` | Manage all leave requests, filter by status/employee/type | CAP-LEV-001; Manager dept-scoped |
| R-072 | `/leave/requests/[id]` | H03 | A, M, E (own) | `GET /api/v1/leave/{id}` | View leave request detail, approve/reject (Manager/Admin), cancel (own) | CAP-LEV-001 or own record |
| R-073 | `/leave/new` | H04 | A, M, E | `POST /api/v1/leave` | Submit leave request form: type, dates, reason, coverage | CAP-LEV-002 |
| R-074 | `/leave/calendar` | H06 | All | `GET /api/v1/leave?calendar=true` | View team/org leave calendar by month | CAP-LEV-001 |

---

## SECTION 6 — PAYROLL ROUTES (F-004)

| # | Route | Archetype | Roles | Backend API | Primary Actions | Blocking Conditions |
|---|-------|-----------|-------|-------------|-----------------|---------------------|
| R-080 | `/payroll` | H02 | PA, A, M | `GET /api/v1/payroll` | List payroll records, filter by period/status/employee, initiate run, export | CAP-PAY-001; gateway enforces PA/A/M only |
| R-081 | `/payroll/[id]` | H03 | PA, A, E (own) | `GET /api/v1/payroll/{id}` | View payroll record detail, pay components, deductions, disbursement status | CAP-PAY-001; Employee can view own payslip |
| R-082 | `/payroll/run` | H04 (trigger) | PA, A | `POST /api/v1/payroll/run` | Initiate payroll run for a period: select period, validate, confirm | CAP-PAY-002 |

---

## SECTION 7 — HIRING ROUTES (F-005)

| # | Route | Archetype | Roles | Backend API | Primary Actions | Blocking Conditions |
|---|-------|-----------|-------|-------------|-----------------|---------------------|
| R-090 | `/hiring` | H01 (dashboard) | A, M, R | `GET /api/v1/hiring/summary` | View recruitment KPIs, active pipelines, pipeline overview | CAP-HIR-001; gateway enforces A/M/R only |
| R-091 | `/job-postings` | H02 | A, M, R | `GET /api/v1/hiring/postings` | List job postings, filter by status/department, create new | CAP-HIR-001 |
| R-092 | `/job-postings/[id]` | H03 | A, M, R | `GET /api/v1/hiring/postings/{id}` | View posting detail, applicant count, pipeline status, edit, close | CAP-HIR-001 |
| R-093 | `/job-postings/new` | H04 | A, M, R | `POST /api/v1/hiring/postings` | Create job posting: Job Details → Requirements → Pipeline Template → Publish | CAP-HIR-002 |
| R-094 | `/candidates-pipeline` | H13 | A, M, R | `GET /api/v1/hiring/candidates`, `GET /api/v1/hiring/pipeline` | Kanban view of all candidates, drag stages, view candidate cards, schedule interviews | CAP-HIR-001 |
| R-095 | `/candidates-pipeline/[id]` | H03 (slide-over) | A, M, R | `GET /api/v1/hiring/candidates/{id}` | Candidate detail: profile, interview history, notes, stage actions | CAP-HIR-001 |

---

## SECTION 8 — WORKFLOW / APPROVALS ROUTES (F-007)

| # | Route | Archetype | Roles | Backend API | Primary Actions | Blocking Conditions |
|---|-------|-----------|-------|-------------|-----------------|---------------------|
| R-100 | `/approvals` | H05 | A, M | `GET /api/v1/workflows?status=pending`, `PUT /api/v1/workflows/{id}/steps/{step_id}` | View pending approvals split-view, approve, reject, delegate, filter by type | CAP-PRF-001 is not the right cap — WF approval is CAP-LEV-001/002 + CAP-EWA-002 for leave; general workflow approval |

**Note on R-100:** The approval inbox aggregates pending workflow steps from workflow_service. It renders approval tasks from leave requests, expense claims (ADD-ON), and any workflow_service.WorkflowInstance where the current step requires the logged-in user's role action.

---

## SECTION 9 — NOTIFICATIONS ROUTES (F-009)

| # | Route | Archetype | Roles | Backend API | Primary Actions | Blocking Conditions |
|---|-------|-----------|-------|-------------|-----------------|---------------------|
| R-110 | `/notifications` | H09 | All | `GET /api/v1/notifications`, `PATCH /api/v1/notifications/{id}/read` | View notification inbox by folder (All/Approvals/AI Alerts/Leave/Payroll/Hiring/Performance/Starred/Sent/Archive), mark read, filter, star | CAP-NOT-001 |

---

## SECTION 10 — SETTINGS ROUTES (F-010)

| # | Route | Archetype | Roles | Backend API | Primary Actions | Blocking Conditions |
|---|-------|-----------|-------|-------------|-----------------|---------------------|
| R-120 | `/settings` | H10 | A | `GET /api/v1/settings`, `PUT /api/v1/settings` | Manage: Company Details, Leave Policies, Payroll Config, Roles & Permissions, Attendance Rules | Admin only; settings-service volatile (in-memory in dev) |

**Chrome-only settings sections** (no backend persistence): Profile, Security, Notifications, Integrations, AI & Automation — these are future backend scope.

---

## SECTION 11 — COMPLIANCE ROUTE (F-011)

| # | Route | Archetype | Roles | Backend API | Primary Actions | Blocking Conditions |
|---|-------|-----------|-------|-------------|-----------------|---------------------|
| R-130 | `/compliance` | H07 | A, PA | `GET /api/v1/compliance` | View compliance reports, statutory filings, audit trails per period | CAP-COM-001; non-standard envelope: `{status, data, service}` |

---

## SECTION 12 — REPORTING ROUTES (F-012)

| # | Route | Archetype | Roles | Backend API | Primary Actions | Blocking Conditions |
|---|-------|-----------|-------|-------------|-----------------|---------------------|
| R-140 | `/reporting` | H07 | A, M | `GET /api/v1/reporting/dashboards` | View HR analytics, KPIs, headcount trends, attrition | CAP-RPT-001; gateway enforces A/M only |
| R-141 | `/reporting/payroll` | H07 tab | PA, A | `GET /api/v1/reporting/payroll` | View payroll period summaries, cost breakdowns | CAP-RPT-001 + CAP-PAY-001 |
| R-142 | `/reporting/attendance` | H07 tab | A, M | `GET /api/v1/reporting/attendance` | View attendance summary by dept/period | CAP-RPT-001 |
| R-143 | `/reporting/engagement` | H07 tab | A, M | `GET /api/v1/reporting/engagement` (ADD-ON) | Survey results, engagement scores | ADD-ON — F-018; deferred |
| R-150 | `/builders/report` | H11 | A | `POST /api/v1/reporting/custom` | Build custom report: select dimensions, filters, schedule | CAP-RPT-002 |

---

## SECTION 13 — AUTOMATION ROUTES (F-013)

| # | Route | Archetype | Roles | Backend API | Primary Actions | Blocking Conditions |
|---|-------|-----------|-------|-------------|-----------------|---------------------|
| R-160 | `/automations` | H11 | A | `GET /api/v1/automations`, `POST /api/v1/automations` | View automation rules, create/edit rules, enable/disable | CAP-AUT-002; Admin only |
| R-161 | `/builders/workflow` | H11 | A | `GET /api/v1/workflows/definitions`, `POST /api/v1/workflows/definitions` | Build workflow definitions: steps, conditions, approvers | CAP-AUT-002 |

---

## SECTION 14 — DECISION CARDS ROUTE (F-014)

| # | Route | Archetype | Roles | Backend API | Primary Actions | Blocking Conditions |
|---|-------|-----------|-------|-------------|-----------------|---------------------|
| R-170 | `/decisions` | H03 custom | A, M, PA | `GET /api/v1/decisions` | View AI-generated decision cards, filter by severity/domain, mark resolved | CAP-DEC-001; non-standard envelope: `{status, data, service}`; in-memory — may be empty after restart |

---

## SECTION 15 — AUDIT ROUTE (F-008)

| # | Route | Archetype | Roles | Backend API | Primary Actions | Blocking Conditions |
|---|-------|-----------|-------|-------------|-----------------|---------------------|
| R-180 | `/audit` | H02 | A | `GET /api/v1/audit` | View immutable audit log: filter by user/action/entity/date, export | Admin only; AuditRecord is PROHIBITED from modification |

---

## SECTION 16 — SEARCH ROUTE (F-020 ADD-ON)

| # | Route | Archetype | Roles | Backend API | Primary Actions | Blocking Conditions |
|---|-------|-----------|-------|-------------|-----------------|---------------------|
| R-190 | `/search` | H08 | All | `GET /api/v1/search?q=` | Full-text search across Employees, Candidates, Documents; navigate to result | CAP-ENG-001 |

---

## SECTION 17 — ADD-ON ROUTES (F-017 to F-022)

ADD-ON routes are authorized for Phase 3 authority but implementation is deferred.

| # | Route | Archetype | Feature | Roles | Backend API |
|---|-------|-----------|---------|-------|-------------|
| R-200 | `/performance` | H01 tab | F-017 | A, M | `GET /api/v1/performance/summary` (ADD-ON) |
| R-201 | `/performance/reviews` | H02 | F-017 | A, M, E | `GET /api/v1/performance/reviews` (ADD-ON) |
| R-202 | `/performance/reviews/[id]` | H03 | F-017 | A, M, E | `GET /api/v1/performance/reviews/{id}` (ADD-ON) |
| R-210 | `/expense-claims` | H02 | F-021 | A, M, E | `GET /api/v1/expenses` (ADD-ON) |
| R-211 | `/expense-claims/new` | H04 | F-021 | A, M, E | `POST /api/v1/expenses` (ADD-ON) |
| R-212 | `/expense-claims/[id]` | H03 | F-021 | A, M, E | `GET /api/v1/expenses/{id}` (ADD-ON) |
| R-220 | `/helpdesk` | H12 | F-019 | All | `GET /api/v1/helpdesk` (ADD-ON) |
| R-230 | `/builders/survey` | H11 | F-018 | A | `POST /api/v1/engagement/surveys` (ADD-ON) |
| R-240 | `/salary-revision` | H04 | F-022 | A, PA | `POST /api/v1/employees/{id}/salary` |
| R-241 | `/employees/[id]/ewa` | H04 | F-015 | E, M, PA, A | `POST /api/v1/ewa/request` |

---

## ROUTE COUNT SUMMARY

| Category | Routes |
|----------|--------|
| Auth | 3 |
| Dashboard | 1 |
| Employee Management | 11 |
| Attendance | 2 |
| Leave | 5 |
| Payroll | 3 |
| Hiring | 6 |
| Approvals | 1 |
| Notifications | 1 |
| Settings | 1 |
| Compliance | 1 |
| Reporting + Report Builder | 5 |
| Automations + Workflow Builder | 2 |
| Decision Cards | 1 |
| Audit | 1 |
| Search | 1 |
| ADD-ON (deferred) | 10 |
| **Total** | **55** |

**Phase 3 Core Routes (excluding ADD-ON and auth/redirect):** 44
**ADD-ON Routes (implementation deferred):** 10
**Auth/System Routes:** 3
