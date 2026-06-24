# FRONTEND SCREEN CATALOG

Status: Complete
Created: 2026-06-17
Phase: 3 — Frontend Authority Capture
Source: archetype-system-v1.md (H01–H13), API_CONTRACT.md, security-model.md, PRODUCT_WORKFLOWS.md

---

## PURPOSE

Authoritative catalog of all 48 screens. For each screen: purpose, primary users, required permissions, API dependencies, data dependencies, supported workflows, available actions, and required UI states.

**Wireframes:** Every screen has a built wireframe in `frontend/pages/`. The wireframe is the visual reference; this document is the authority reference. Where they conflict, this document (derived from backend reality) takes precedence.

---

## SCREEN STATES REQUIRED FOR ALL SCREENS

Every screen must implement:
- **Loading:** Skeleton/shimmer matching expected layout
- **Empty:** No-data state with appropriate CTA or explanation
- **Error:** Failed API state with retry option; partial failures must not crash entire screen
- **Success/Data:** Rendered content

---

## H01 — DASHBOARD (4 SCREENS)

### H01-01: HR Manager Dashboard

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h01-hr-manager-dashboard.html` |
| Route | `/dashboard` |
| Roles | Admin (global), Manager (dept-scoped) |
| Feature | F-001, F-002, F-003, F-004, F-012 |
| APIs | `GET /api/v1/employees/summary`, `GET /api/v1/attendance/summary`, `GET /api/v1/leave`, `GET /api/v1/workflows?status=pending`, `GET /api/v1/hiring/summary`, `GET /api/v1/reporting/dashboards` |
| Workflows | WF-001, WF-002, WF-003, WF-004 (entry points from dashboard widgets) |
| Actions | Navigate to sections, quick-add employee (Admin), approve pending items |
| See | FRONTEND_DASHBOARD_CATALOG.md for full widget specification |

---

### H01-02: Employee Self-Service Dashboard

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h01-employee-self-service.html` |
| Route | `/dashboard` |
| Roles | Employee |
| Feature | F-002, F-003, F-009 |
| APIs | `GET /api/v1/leave/balance`, `GET /api/v1/attendance?me=true`, `GET /api/v1/payroll?me=true&latest=true`, `GET /api/v1/notifications?unread=true&limit=5` |
| Workflows | WF-008 |
| Actions | Raise leave request, view payslip, view attendance, view notifications |

---

### H01-03: Payroll Admin Dashboard

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h01-payroll-admin-dashboard.html` |
| Route | `/dashboard` |
| Roles | PayrollAdmin |
| Feature | F-004, F-011, F-016 |
| APIs | `GET /api/v1/payroll/status?period=current`, `GET /api/v1/payroll/summary`, `GET /api/v1/compliance?upcoming=true`, `GET /api/v1/decisions?scope=payroll`, `GET /api/v1/reporting/payroll?widget=cost_trend` |
| Workflows | WF-003, WF-007 |
| Actions | Run payroll, view compliance, trigger disbursement, view decision cards |

---

### H01-04: Recruitment Dashboard

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h01-recruitment-dashboard.html` |
| Route | `/dashboard` |
| Roles | Recruiter |
| Feature | F-005 |
| APIs | `GET /api/v1/hiring/postings?status=open`, `GET /api/v1/hiring/candidates?status=active`, `GET /api/v1/hiring/interviews?this_week=true`, `GET /api/v1/hiring/pipeline/summary` |
| Workflows | WF-004 |
| Actions | Create job posting, view pipeline, review candidates |

---

## H02 — LIST/TABLE (11 SCREENS)

### H02-01: Employees List

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h02-employees.html` |
| Route | `/employees` |
| Roles | Admin, Manager (dept-scoped) |
| Permission | CAP-EMP-001 |
| Feature | F-001 |
| APIs | `GET /api/v1/employees?page=&limit=&dept=&status=&search=` |
| Columns | Name, Employee ID, Department, Role, Status, Start Date, Actions |
| Filters | Status (Active/Draft/On Leave/Suspended/Terminated), Department, Role, Date Range |
| Actions | View profile, Add employee (Admin), Export CSV, Bulk select |
| Empty state | "No employees yet" + Add Employee CTA |

---

### H02-02: Departments List

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h02-departments.html` |
| Route | `/departments` |
| Roles | Admin, Manager |
| Permission | CAP-EMP-001 |
| APIs | `GET /api/v1/departments` |
| Columns | Name, Head, Employee Count, Parent Dept, Actions |
| Actions | View detail, Create department (Admin), Edit (Admin) |

---

### H02-03: Roles List

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h02-roles.html` |
| Route | `/roles` |
| Roles | Admin |
| Permission | CAP-AUT-001 |
| APIs | `GET /api/v1/roles` |
| Columns | Role Name, Type, Assigned Count, Permissions, Actions |
| Actions | Create role, Edit role, View assignments |

---

### H02-04: Job Postings List

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h02-job-postings.html` |
| Route | `/job-postings` |
| Roles | Admin, Manager, Recruiter |
| Permission | CAP-HIR-001 |
| APIs | `GET /api/v1/hiring/postings?status=&dept=&search=` |
| Columns | Title, Department, Status (Draft/Open/Closed/Filled), Applicants, Posted Date |
| Filters | Status, Department, Date Range |
| Actions | View detail, Create posting, Close posting |

---

### H02-05: Leave Requests List

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h02-leave-requests.html` |
| Route | `/leave/requests` |
| Roles | Admin (all), Manager (dept-scoped) |
| Permission | CAP-LEV-001 |
| APIs | `GET /api/v1/leave?status=&employee=&type=&from=&to=` |
| Columns | Employee, Type, Start Date, End Date, Days, Status, Actions |
| Filters | Status (Pending/Approved/Rejected/Cancelled), Leave Type, Date Range, Employee |
| Actions | Approve, Reject, View detail |

---

### H02-06: Payroll Records List

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h02-payroll-records.html` |
| Route | `/payroll` |
| Roles | Admin (all), PayrollAdmin (all), Manager (dept-scoped) |
| Permission | CAP-PAY-001 |
| Gateway | Enforced — only PA/A/M can access `/api/v1/payroll` |
| APIs | `GET /api/v1/payroll?period=&status=&employee=` |
| Columns | Period, Employee, Gross Pay, Net Pay, Status, Disbursed Date |
| Filters | Period, Status, Department |
| Actions | View detail, Run Payroll (PA/A), Export |

---

### H02-07: Expense Claims List (ADD-ON)

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h02-expense-claims.html` |
| Route | `/expense-claims` |
| Roles | Admin, Manager (dept), Employee (own) |
| Feature | F-021 ADD-ON |
| APIs | `GET /api/v1/expenses` |
| Status | ADD-ON — implementation deferred |

---

### H02-08: Travel Requests List (ADD-ON — F-023 PLANNED)

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h02-travel-requests.html` |
| Route | (no Phase 3 route — F-023 is PLANNED, not IMPLEMENTED) |
| Status | PLANNED — no backend, no Phase 3 route |

---

### H02-09: Attendance Records List

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h02-attendance-records.html` |
| Route | `/attendance` |
| Roles | Admin, Manager (dept-scoped), Employee (own) |
| Permission | CAP-ATT-001 |
| Feature | F-002 |
| APIs | `GET /api/v1/attendance?employee=&from=&to=&status=` |
| Columns | Employee, Date, Check-In, Check-Out, Duration, Status (Present/Late/Absent/On Leave) |
| Filters | Date Range, Status, Employee, Department |
| Actions | View timeline (toggle to H06), Export, Filter |

---

### H02-10: Performance Reviews List (ADD-ON)

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h02-performance-reviews.html` |
| Route | `/performance/reviews` |
| Roles | Admin, Manager (dept), Employee (own) |
| Feature | F-017 ADD-ON |
| Status | ADD-ON — implementation deferred |

---

### H02-11: Documents List

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h02-documents.html` (exists in archetype as a listed page) |
| Route | (no confirmed Phase 3 route — document management confirmed OUT OF SCOPE) |
| Status | OUT OF SCOPE — wireframe exists but no backend service and no Phase 3 route |

---

## H03 — DETAIL/PROFILE (8 SCREENS)

### H03-01: Employee Profile

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h03-employee-profile.html` |
| Route | `/employees/[id]` |
| Roles | Admin (all), Manager (dept-scoped), Employee (own) |
| Permission | CAP-EMP-001 or own record |
| Feature | F-001 |
| APIs | `GET /api/v1/employees/{id}`, `GET /api/v1/leave/balance?employee_id={id}`, `GET /api/v1/attendance?employee_id={id}&limit=10`, `GET /api/v1/payroll?employee_id={id}` |
| Tabs | Overview, Compensation, Documents, Leave, Performance (ADD-ON), History |
| Actions | Edit (Admin/dept-Manager), Initiate Onboarding, Raise Leave (own), Request Advance (own), Salary Revision (Admin) |
| Related screens | `/employees/[id]/edit` (H04), `/salary-revision` (H04), `/leave/requests/[id]` (H03) |

**Tab detail:**
- **Overview:** Name, ID, role, department, grade band, start date, manager, contact
- **Compensation:** Base salary, allowances, grade band, salary history (SalaryRevision records)
- **Documents:** Uploaded contracts, ID, certificates (Phase 3: list only; upload may be deferred)
- **Leave:** Leave balance by type, recent leave history table
- **Performance:** Review history (ADD-ON — F-017; tab renders but shows ADD-ON notice if not enabled)
- **History:** AuditRecord entries for this employee (immutable log of all changes)

---

### H03-02: Department Detail

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h03-department-detail.html` |
| Route | `/departments/[id]` |
| Roles | Admin, Manager |
| Permission | CAP-EMP-001 |
| APIs | `GET /api/v1/departments/{id}`, `GET /api/v1/employees?dept_id={id}` |
| Content | Department name, head, parent dept, employee list within dept, sub-departments |
| Actions | Edit department (Admin), View employee (navigate), Create sub-department (Admin) |

---

### H03-03: Role Detail

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h03-role-detail.html` |
| Route | `/roles/[id]` |
| Roles | Admin |
| Permission | CAP-AUT-001 |
| APIs | `GET /api/v1/roles/{id}`, `GET /api/v1/employees?role_id={id}` |
| Content | Role name, permission set, assigned employees count, scope type |
| Actions | Edit role, View assigned employees |

---

### H03-04: Job Posting Detail

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h03-job-posting-detail.html` |
| Route | `/job-postings/[id]` |
| Roles | Admin, Manager, Recruiter |
| Permission | CAP-HIR-001 |
| APIs | `GET /api/v1/hiring/postings/{id}`, `GET /api/v1/hiring/candidates?posting_id={id}` |
| Content | Job title, description, requirements, status, applicant count, pipeline link |
| Actions | Edit posting (HIR-002), Close posting, View pipeline |

---

### H03-05: Leave Request Detail

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h03-leave-request-detail.html` |
| Route | `/leave/requests/[id]` |
| Roles | Admin, Manager (dept), Employee (own) |
| Permission | CAP-LEV-001 or own |
| APIs | `GET /api/v1/leave/{id}` |
| Content | Employee, leave type, dates, reason, status, approver, approval notes |
| Actions | Approve/Reject (Admin/Manager), Cancel (own + pending status), Download (if supporting docs) |

---

### H03-06: Payroll Record Detail

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h03-payroll-record-detail.html` |
| Route | `/payroll/[id]` |
| Roles | Admin (all), PayrollAdmin (all), Manager (dept), Employee (own) |
| Permission | CAP-PAY-001 or own |
| APIs | `GET /api/v1/payroll/{id}` |
| Content | Employee, period, gross pay, deductions (tax, insurance, etc.), net pay, disbursement status, bank details (Admin/PA only) |
| Actions | Trigger Disbursement (PA/Admin — CAP-BNK-002), Download payslip (own + PA/Admin), Export |

---

### H03-07: Expense Claim Detail (ADD-ON)

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h03-expense-claim-detail.html` |
| Route | `/expense-claims/[id]` |
| Feature | F-021 ADD-ON |
| Status | ADD-ON — implementation deferred |

---

### H03-08: Performance Review Detail (ADD-ON)

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h03-performance-review-detail.html` |
| Route | `/performance/reviews/[id]` |
| Feature | F-017 ADD-ON |
| Status | ADD-ON — implementation deferred |

---

## H04 — CREATE/EDIT FORM (9 SCREENS)

### H04-01: Add Employee (6-step)

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h04-add-employee.html` |
| Route | `/employees/new` |
| Roles | Admin |
| Permission | CAP-EMP-002 |
| APIs | `POST /api/v1/employees`, `GET /api/v1/roles`, `GET /api/v1/departments`, `GET /api/v1/settings` (grade bands) |
| Steps | 1: Personal Info → 2: Employment → 3: Role & Dept → 4: Compensation → 5: Access & Roles → 6: Review |
| Validation | Required fields per step. Cannot advance step without completing required fields. |
| On submit | Employee created with status `active` (or `draft` if admin selects). Navigate to `/employees/[id]`. |

---

### H04-02: Edit Employee

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h04-edit-employee.html` |
| Route | `/employees/[id]/edit` |
| Roles | Admin (all fields), Manager (dept-scoped, limited fields) |
| Permission | CAP-EMP-002 |
| APIs | `GET /api/v1/employees/{id}`, `PATCH /api/v1/employees/{id}` |
| Manager field restrictions | Cannot edit compensation, role assignment, or system access |

---

### H04-03: Create Department

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h04-create-department.html` |
| Route | `/departments/new` |
| Roles | Admin |
| Permission | CAP-EMP-002 |
| APIs | `POST /api/v1/departments`, `GET /api/v1/departments` (parent dept dropdown), `GET /api/v1/employees` (head dropdown) |
| Fields | Name, Description, Head (employee select), Parent Department (optional), Cost Center |

---

### H04-04: Create Role

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h04-create-role.html` |
| Route | `/roles/new` |
| Roles | Admin |
| Permission | CAP-AUT-001 |
| APIs | `POST /api/v1/roles` |
| Fields | Role name, scope type (Global/Department/Employee), permission set (multi-select from capability list) |

---

### H04-05: Create Job Posting (4-step)

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h04-create-job-posting.html` |
| Route | `/job-postings/new` |
| Roles | Admin, Manager, Recruiter |
| Permission | CAP-HIR-002 |
| APIs | `POST /api/v1/hiring/postings`, `GET /api/v1/departments` |
| Steps | 1: Job Details → 2: Requirements → 3: Pipeline Template → 4: Publish |
| On submit | Posting created. Navigate to `/job-postings/[id]`. |

---

### H04-06: Raise Leave Request

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h04-raise-leave-request.html` |
| Route | `/leave/new` |
| Roles | All authenticated |
| Permission | CAP-LEV-002 |
| APIs | `POST /api/v1/leave`, `GET /api/v1/leave/balance`, `GET /api/v1/settings` (leave types) |
| Fields | Leave type (from settings), Start date, End date (calendar picker), Reason (required), Coverage notes |
| Validation | Cannot select past dates (configurable). Cannot exceed leave balance (show warning). |
| On submit | Leave request created with status `pending`. Navigate to `/leave` with confirmation. |

---

### H04-07: Raise Expense Claim (ADD-ON)

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h04-raise-expense-claim.html` |
| Route | `/expense-claims/new` |
| Feature | F-021 ADD-ON |
| Status | ADD-ON — implementation deferred |

---

### H04-08: Raise Travel Request (PLANNED)

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h04-raise-travel-request.html` |
| Route | (no Phase 3 route — F-023 PLANNED) |
| Status | PLANNED — no backend, no Phase 3 route |

---

### H04-09: Salary Revision

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h04-salary-revision.html` |
| Route | `/salary-revision` |
| Roles | Admin, PayrollAdmin |
| Permission | CAP-PAY-002 |
| APIs | `POST /api/v1/employees/{id}/salary` |
| Fields | Employee (select), New base salary, Effective date, Reason, Notes |
| Access point | Initiated from Employee Profile (H03) → Actions dropdown |

---

## H05 — WORKFLOW/APPROVAL (1 SCREEN)

### H05-01: Approval Inbox

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h05-approval-inbox.html` |
| Route | `/approvals` |
| Roles | Admin, Manager |
| Feature | F-007 |
| APIs | `GET /api/v1/workflows?status=pending`, `PUT /api/v1/workflows/{id}/steps/{step_id}`, `GET /api/v1/leave/{id}` (for leave detail) |
| Layout | H05 split-view: 340px fixed list panel + flex detail panel |
| List panel | Pending items sorted by created_at DESC; each card shows: type, employee name, description, time pending |
| Detail panel | Full request details from the relevant service (leave/expense/EWA/payroll); Approve + Reject action buttons |
| Approval types | Leave requests (WF-002), EWA (WF-008/F-015), Expense claims ADD-ON (WF-006), Payroll approval optional (WF-003) |
| Actions | Approve (with optional comment), Reject (reason required), Delegate (future scope) |
| On approve/reject | Item removed from list; detail panel shows next item or empty state |
| Empty state | "No pending approvals" with illustration |

---

## H06 — CALENDAR/TIMELINE (3 SCREENS)

### H06-01: Leave Calendar

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h06-leave-calendar.html` |
| Route | `/leave/calendar` (or `/leave` with calendar tab active) |
| Roles | All authenticated |
| Feature | F-003 |
| APIs | `GET /api/v1/leave?calendar=true&month=&year=` |
| Content | Monthly calendar view. Approved leave events shown as colored blocks by employee. Employee filter. |
| Actions | Navigate months, filter by department/employee, click event to view leave detail, "Raise Leave Request" CTA |

---

### H06-02: Attendance Timeline

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h06-attendance-timeline.html` |
| Route | `/attendance/timeline` (or `/attendance` with timeline tab) |
| Roles | Admin, Manager |
| Feature | F-002 |
| APIs | `GET /api/v1/attendance?timeline=true&from=&to=&dept=` |
| Content | Gantt-style timeline. Each row = one employee. Blocks = attendance periods. Color-coded by status. |
| Actions | Date range picker, department filter, employee filter, click to view day detail |

---

### H06-03: Shift Roster

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h06-shift-roster.html` |
| Route | (no Phase 3 route — Shift/Roster confirmed OUT OF SCOPE) |
| Status | OUT OF SCOPE — wireframe exists but no backend service and no Phase 3 route |

---

## H07 — ANALYTICS/REPORTS (5 SCREENS)

### H07-01: HR Analytics

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h07-hr-analytics.html` |
| Route | `/reporting` |
| Roles | Admin (global), Manager (dept-scoped) |
| Permission | CAP-RPT-001 |
| Feature | F-012 |
| APIs | `GET /api/v1/reporting/dashboards`, `GET /api/v1/reporting/dashboards?widget=headcount`, `GET /api/v1/reporting/dashboards?widget=attrition` |
| Content | Headcount trends, attrition rate, department breakdown, hiring funnel summary |
| Actions | Date range filter, department filter, export report |

---

### H07-02: Payroll Reports

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h07-payroll-reports.html` |
| Route | `/reporting/payroll` |
| Roles | Admin, PayrollAdmin |
| Permission | CAP-RPT-001 + CAP-PAY-001 |
| APIs | `GET /api/v1/reporting/payroll` |
| Content | Period-by-period cost, cost by department, salary distribution, disbursement summary |
| Actions | Period selector, export |

---

### H07-03: Attendance Summary

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h07-attendance-summary.html` |
| Route | `/reporting/attendance` |
| Roles | Admin, Manager (dept-scoped) |
| Permission | CAP-RPT-001 |
| APIs | `GET /api/v1/reporting/attendance` |
| Content | Attendance rate by dept/period, late arrival trends, absence heatmap |

---

### H07-04: Engagement Results (ADD-ON)

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h07-engagement-results.html` |
| Route | `/reporting/engagement` |
| Feature | F-018 ADD-ON |
| Status | ADD-ON — implementation deferred |

---

### H07-05: Compliance Reports

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h07-compliance-reports.html` |
| Route | `/compliance` |
| Roles | Admin, PayrollAdmin |
| Permission | CAP-COM-001 |
| Feature | F-011 |
| APIs | `GET /api/v1/compliance` — **non-standard envelope: `{status, data, service}`** — no `meta` field |
| Content | Statutory filing status by period, upcoming deadlines, generated compliance reports |
| Actions | Generate report for period, download, filter by filing type |
| Error handling | Must handle missing `meta` in API response |

---

## H08 — SEARCH (1 SCREEN)

### H08-01: Global Search

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h08-global-search.html` |
| Route | `/search` |
| Roles | All authenticated |
| Feature | F-020 ADD-ON |
| APIs | `GET /api/v1/search?q=&type=` |
| Entity types | Employee, Candidate, Document |
| Content | Search input, entity type filter tabs, results list with contextual links |
| Actions | Enter search term, filter by entity type, click result → navigate to relevant screen |

---

## H09 — INBOX/FEED (1 SCREEN)

### H09-01: Notifications Inbox

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h09-notifications-inbox.html` |
| Route | `/notifications` |
| Roles | All authenticated |
| Permission | CAP-NOT-001 |
| Feature | F-009 |
| APIs | `GET /api/v1/notifications`, `PATCH /api/v1/notifications/{id}/read`, `DELETE /api/v1/notifications/{id}` (if supported) |
| Folder navigation | All / Approvals / AI Alerts / Leave / Payroll / Hiring / Performance / Starred / Sent / Archive |
| Content | Notification list sorted by created_at DESC. Each item: icon, title, body preview, timestamp, read/unread indicator |
| Actions | Mark read, Mark unread, Star, Archive, Delete, Filter by folder |

---

## H10 — SETTINGS (1 SCREEN)

### H10-01: Organisation Settings

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h10-org-settings.html` |
| Route | `/settings` |
| Roles | Admin |
| Feature | F-010 |
| APIs | `GET /api/v1/settings`, `PUT /api/v1/settings` |
| Sections (backend-persistent) | Company Details, Leave Policies, Payroll Config, Roles & Permissions, Attendance Rules |
| Sections (chrome-only) | Profile, Security, Notifications, Integrations, AI & Automation |
| Warning | Settings-service uses in-memory dict stub — settings reset on service restart in dev. Frontend must treat settings as volatile; do not cache aggressively. |
| Actions | Edit section, Save changes, Cancel (discard changes) |

---

## H11 — BUILDER (3 SCREENS)

### H11-01: Workflow Builder

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h11-workflow-builder.html` |
| Route | `/builders/workflow` |
| Roles | Admin |
| Permission | CAP-AUT-002 |
| Feature | F-007, F-013 |
| APIs | `GET /api/v1/workflows/definitions`, `POST /api/v1/workflows/definitions` |
| Content | Visual workflow designer: drag-and-drop steps, conditions, approver assignment |

---

### H11-02: Survey Builder (ADD-ON)

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h11-survey-builder.html` |
| Route | `/builders/survey` |
| Feature | F-018 ADD-ON |
| Status | ADD-ON — Likert5 scale surveys only. Implementation deferred. |

---

### H11-03: Report Builder

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h11-report-builder.html` |
| Route | `/builders/report` |
| Roles | Admin |
| Permission | CAP-RPT-002 |
| Feature | F-012 |
| APIs | `POST /api/v1/reporting/custom` |
| Content | Select data source, dimensions, filters, schedule — build and save custom report |

---

## H12 — SUPPORT/TICKET (1 SCREEN) (ADD-ON)

### H12-01: Helpdesk

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h12-helpdesk.html` |
| Route | `/helpdesk` |
| Feature | F-019 ADD-ON |
| Status | ADD-ON — priority/reassign/merge are chrome-only in wireframe (BG-032). Implementation deferred. |

---

## H13 — CANDIDATE PIPELINE (1 SCREEN)

### H13-01: Candidate Pipeline

| Field | Value |
|-------|-------|
| Wireframe | `frontend/pages/h13-candidate-pipeline.html` |
| Route | `/candidates-pipeline` |
| Roles | Admin, Manager, Recruiter |
| Permission | CAP-HIR-001 |
| Feature | F-005 |
| APIs | `GET /api/v1/hiring/candidates`, `PATCH /api/v1/hiring/candidates/{id}`, `GET /api/v1/hiring/pipeline` |
| Layout | Kanban board. One column per stage. |
| Stages (frontend) | Applied / Screening / Interview / Final Round (UI-only) / Offer Sent |
| Stages (backend) | Applied / Screening / Interviewing / Offered / Hired / Rejected |
| Card content | Candidate name, posting title, days in stage, key action (schedule interview, extend offer) |
| Actions | Drag card to advance stage, open candidate detail (slide-over), add note, schedule interview, reject |
| Slide-over detail | Candidate profile, interview history, notes, stage action buttons |

---

## SCREEN COUNT SUMMARY

| Archetype | Total | Phase 3 Core | ADD-ON | Out of Scope/Planned |
|-----------|-------|--------------|--------|----------------------|
| H01 Dashboard | 4 | 4 | 0 | 0 |
| H02 List/Table | 11 | 7 | 2 | 2 |
| H03 Detail/Profile | 8 | 6 | 2 | 0 |
| H04 Create/Edit | 9 | 6 | 1 | 2 |
| H05 Approval | 1 | 1 | 0 | 0 |
| H06 Calendar | 3 | 2 | 0 | 1 |
| H07 Analytics | 5 | 4 | 1 | 0 |
| H08 Search | 1 | 1 | 0 | 0 |
| H09 Inbox | 1 | 1 | 0 | 0 |
| H10 Settings | 1 | 1 | 0 | 0 |
| H11 Builder | 3 | 2 | 1 | 0 |
| H12 Support | 1 | 0 | 1 | 0 |
| H13 Pipeline | 1 | 1 | 0 | 0 |
| **Total** | **49** | **36** | **8** | **5** |

Note: 49 entries because H13 Candidate slide-over detail counts as a screen entry; archetype system counts 48 pages.
