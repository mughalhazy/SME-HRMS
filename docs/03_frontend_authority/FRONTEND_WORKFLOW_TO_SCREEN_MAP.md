# FRONTEND WORKFLOW TO SCREEN MAP

Status: Complete
Created: 2026-06-17
Phase: 3 — Frontend Authority Capture
Source: PRODUCT_WORKFLOWS.md, DOMAIN_MODEL.md, API_CONTRACT.md, archetype-system-v1.md

---

## PURPOSE

Maps every defined product workflow to the frontend screens and actions that support it. Every workflow step has an identified screen, an API call, and a role.

**Scope:** WF-001 to WF-008. WF-005 and WF-006 are ADD-ON and deferred but their screen mappings are defined here.

---

## WF-001: EMPLOYEE ONBOARDING

**Status:** STABLE
**Feature:** F-001

### Workflow Steps → Screens

| Step | Actor | Screen | Route | API Call | Action |
|------|-------|--------|-------|----------|--------|
| 1. HR initiates onboarding | Admin | Add Employee Form (H04) | `/employees/new` | `POST /api/v1/employees` | Submit 6-step form; employee status = Draft |
| 2. Personal Info | Admin | Step 1 of Add Employee (H04) | `/employees/new` | (Form step) | Enter name, DOB, contact, national ID |
| 3. Employment Details | Admin | Step 2 of Add Employee (H04) | `/employees/new` | (Form step) | Enter start date, employment type, grade band |
| 4. Role & Department | Admin | Step 3 of Add Employee (H04) | `/employees/new` | `GET /api/v1/roles`, `GET /api/v1/departments` | Select role and department |
| 5. Compensation | Admin | Step 4 of Add Employee (H04) | `/employees/new` | (Form step) | Enter base salary, allowances |
| 6. System Access | Admin | Step 5 of Add Employee (H04) | `/employees/new` | (Form step) | Set user account, role binding |
| 7. Review & Confirm | Admin | Step 6 Review (H04) | `/employees/new` | `POST /api/v1/employees` | Review summary, confirm submission |
| 8. Record created | System | Employee Profile (H03) | `/employees/[id]` | `GET /api/v1/employees/{id}` | View new employee record; status = Active |
| 9. (Optional) Document upload | Admin | Employee Profile → Documents tab | `/employees/[id]` | Document upload endpoint | Upload contract, ID documents |

### Workflow States Visible to Frontend

| State | Employee Lifecycle Status | UI Indicator |
|-------|--------------------------|--------------|
| Being created | `draft` | "Draft" status badge |
| Active employee | `active` | "Active" badge (green) |
| On leave | `on_leave` | "On Leave" badge |
| Suspended | `suspended` | "Suspended" badge (orange) |
| Terminated | `terminated` | "Terminated" badge (red) |

---

## WF-002: LEAVE REQUEST AND APPROVAL

**Status:** STABLE
**Feature:** F-003

### Workflow Steps → Screens

| Step | Actor | Screen | Route | API Call | Action |
|------|-------|--------|-------|----------|--------|
| 1. Employee initiates leave | Employee | Raise Leave Request (H04) | `/leave/new` | `GET /api/v1/leave/balance` | View available balance before submitting |
| 2. Submit leave request | Employee | Raise Leave Request (H04) | `/leave/new` | `POST /api/v1/leave` | Enter type, start/end dates, reason; submit |
| 3. Request in pending state | Employee | Leave Calendar (H06) + notifications | `/leave` | `GET /api/v1/leave?me=true` | See own request with "Pending" status in calendar |
| 4. Manager receives notification | Manager | Notifications Inbox (H09) → Approvals (H05) | `/notifications` → `/approvals` | `GET /api/v1/notifications`, `GET /api/v1/workflows?status=pending` | Click notification → routed to approval inbox |
| 5. Manager reviews request | Manager | Approval Inbox split view (H05) | `/approvals` | `GET /api/v1/leave/{id}` | View leave detail in right panel: dates, type, reason, employee balance |
| 6a. Approve | Manager | Approval Inbox (H05) | `/approvals` | `PUT /api/v1/workflows/{id}/steps/{step_id}` body: `{action: "approve"}` | Click "Approve" — inline confirmation; record updates |
| 6b. Reject | Manager | Approval Inbox (H05) | `/approvals` | `PUT /api/v1/workflows/{id}/steps/{step_id}` body: `{action: "reject", reason: "..."}` | Click "Reject" — reason input required |
| 7. Employee notified | Employee | Notifications Inbox (H09) | `/notifications` | `GET /api/v1/notifications` | Receive approved/rejected notification |
| 8. Leave visible in calendar | All | Leave Calendar (H06) | `/leave/calendar` | `GET /api/v1/leave?calendar=true` | Approved leave displayed on team calendar |

### Leave Request States

| State | Frontend Indicator |
|-------|-------------------|
| `pending` | "Pending" yellow badge |
| `approved` | "Approved" green badge |
| `rejected` | "Rejected" red badge |
| `cancelled` | "Cancelled" grey badge |

---

## WF-003: PAYROLL RUN

**Status:** STABLE
**Feature:** F-004

**Phase 2.95 Decision:** Payroll approval step (step 8) is OPTIONAL. Default UX: PayrollAdmin reviews and processes in a single flow. Approval step only if PayrollAdmin requires a secondary authorization.

### Workflow Steps → Screens

| Step | Actor | Screen | Route | API Call | Action |
|------|-------|--------|-------|----------|--------|
| 1. PayrollAdmin initiates run | PA / A | Payroll List (H02) | `/payroll` | — | Click "Run Payroll" CTA in header |
| 2. Select period | PA / A | Payroll Run Form (H04) | `/payroll/run` | — | Select pay period (month/year) |
| 3. Validate eligibility | PA / A | Payroll Run Form (H04) | `/payroll/run` | `POST /api/v1/payroll/run` with `validate_only=true` | System validates all employees have attendance/leave data |
| 4. Review validation results | PA / A | Payroll Run Form (H04) | `/payroll/run` | (Response from validate call) | View warnings (missing attendance, pending leave requests) |
| 5. Confirm and submit run | PA / A | Payroll Run Form (H04) | `/payroll/run` | `POST /api/v1/payroll/run` | Confirm submission; payroll run status = Processing |
| 6. Processing state | PA / A | Payroll List (H02) | `/payroll` | `GET /api/v1/payroll?status=processing` | Payroll record shows "Processing" status |
| 7. Run completes | PA / A | Payroll Record Detail (H03) | `/payroll/[id]` | `GET /api/v1/payroll/{id}` | View individual employee payroll details |
| 8. (Optional) Manager/Admin approval | A | Approvals Inbox (H05) | `/approvals` | `PUT /api/v1/workflows/{id}/steps/{step_id}` | Approve payroll run if secondary authorization enabled |
| 9. Trigger disbursement | PA / A | Payroll Record Detail (H03) | `/payroll/[id]` | `POST /api/v1/payroll/{id}/disburse` | Click "Trigger Disbursement"; requires CAP-BNK-002 |
| 10. Disbursement complete | PA / A | Payroll Record Detail (H03) | `/payroll/[id]` | `GET /api/v1/payroll/{id}` | Status = "Disbursed"; banking confirmation shown |
| 11. Employees view payslip | Employee | Employee Dashboard (H01) | `/dashboard` or `/payroll/[id]` (own) | `GET /api/v1/payroll?me=true&latest=true` | Latest payslip visible in dashboard KPI + `/payroll/[id]` |

### Payroll Record States

| State | Frontend Indicator |
|-------|-------------------|
| `draft` | "Draft" grey badge |
| `processing` | "Processing" blue badge + spinner |
| `completed` | "Completed" green badge |
| `pending_disbursement` | "Pending Disbursement" yellow badge |
| `disbursed` | "Disbursed" green badge |
| `failed` | "Failed" red badge + error details |

---

## WF-004: HIRING PIPELINE

**Status:** STABLE
**Feature:** F-005

### Workflow Steps → Screens

| Step | Actor | Screen | Route | API Call | Action |
|------|-------|--------|-------|----------|--------|
| 1. Create job posting | A/M/R | Create Job Posting (H04) | `/job-postings/new` | `POST /api/v1/hiring/postings` | 4-step form: Job Details → Requirements → Pipeline Template → Publish |
| 2. Publish posting | A/M/R | Job Posting Detail (H03) | `/job-postings/[id]` | `PATCH /api/v1/hiring/postings/{id}` `{status: "published"}` | Publish button → status changes to "Open" |
| 3. Candidates enter pipeline | A/M/R | Candidate Pipeline (H13) | `/candidates-pipeline` | `GET /api/v1/hiring/candidates` | Candidates appear in "Applied" column |
| 4. Screening | A/M/R | Candidate Pipeline (H13) | `/candidates-pipeline` | `PATCH /api/v1/hiring/candidates/{id}` `{stage: "Screening"}` | Drag card from Applied → Screening; or use stage dropdown in candidate detail |
| 5. Interview scheduling | A/M/R | Candidate Detail slide-over | `/candidates-pipeline/[id]` | `POST /api/v1/hiring/interviews` | Schedule interview: date, type, interviewers |
| 6. Interview stage | A/M/R | Candidate Pipeline (H13) | `/candidates-pipeline` | `PATCH /api/v1/hiring/candidates/{id}` `{stage: "Interviewing"}` | Stage advances to Interviewing |
| 7. Final round | A/M/R | Candidate Pipeline (H13) | `/candidates-pipeline` | (UI-only stage) | "Final Round" is UI-only stage; backend stage = `Interviewing` until offer |
| 8. Extend offer | A/M/R | Candidate Detail slide-over | `/candidates-pipeline/[id]` | `PATCH /api/v1/hiring/candidates/{id}` `{stage: "Offered"}` | "Extend Offer" action in candidate detail |
| 9. Offer accepted → Hire | A/M/R | Candidate Detail | `/candidates-pipeline/[id]` | `PATCH /api/v1/hiring/candidates/{id}` `{stage: "Hired"}` | "Mark as Hired" → triggers employee onboarding (WF-001) |
| 10. Reject candidate | A/M/R | Candidate Detail | `/candidates-pipeline/[id]` | `PATCH /api/v1/hiring/candidates/{id}` `{stage: "Rejected"}` | "Reject" with reason; candidate moved to rejected column |

### Candidate Pipeline Kanban Stage Mapping

| Frontend Stage (H13) | Backend Stage (Candidate entity) | Notes |
|---------------------|----------------------------------|-------|
| Applied | `Applied` | Backend and frontend match |
| Screening | `Screening` | Backend and frontend match |
| Interview | `Interviewing` | Backend and frontend match |
| Final Round | `Interviewing` | Frontend-only stage; no separate backend value |
| Offer Sent | `Offered` | Backend uses "Offered"; frontend shows "Offer Sent" |
| (Hired) | `Hired` | Removed from active kanban; moved to "Hired" summary |
| (Rejected) | `Rejected` | Removed from active kanban; viewable in rejected filter |

---

## WF-005: PERFORMANCE REVIEW CYCLE (ADD-ON)

**Status:** ADD-ON — Deferred. F-017. Screen map defined for authority but implementation deferred.

### Workflow Steps → Screens (Authority Only)

| Step | Actor | Screen | Route |
|------|-------|--------|-------|
| 1. Admin creates review cycle | Admin | Review Cycle setup | `/performance` |
| 2. Self-assessment (Employee) | Employee | Performance Review Form | `/performance/reviews/[id]` |
| 3. Manager review | Manager | Performance Review Detail | `/performance/reviews/[id]` |
| 4. Calibration (Admin) | Admin | Calibration interface | `/performance` |
| 5. Employee views final review | Employee | Performance Review Detail | `/performance/reviews/[id]` |

---

## WF-006: EXPENSE CLAIM (ADD-ON)

**Status:** ADD-ON — Deferred. F-021. Screen map defined for authority but implementation deferred.

### Workflow Steps → Screens (Authority Only)

| Step | Actor | Screen | Route |
|------|-------|--------|-------|
| 1. Employee raises claim | Employee | Raise Expense Claim (H04) | `/expense-claims/new` |
| 2. Manager approval | Manager | Approval Inbox (H05) | `/approvals` |
| 3. Finance/Admin processing | Admin | Expense Claim Detail (H03) | `/expense-claims/[id]` |
| 4. Employee notified | Employee | Notifications (H09) | `/notifications` |

---

## WF-007: AUDIT AND COMPLIANCE REPORTING

**Status:** STABLE
**Feature:** F-008, F-011

### Workflow Steps → Screens

| Step | Actor | Screen | Route | API Call | Action |
|------|-------|--------|-------|----------|--------|
| 1. Admin views audit log | Admin | Audit Log List (H02) | `/audit` | `GET /api/v1/audit` | Filter by user, action type, entity, date range |
| 2. Drill into specific event | Admin | Audit Log Detail | `/audit` (inline expand) | `GET /api/v1/audit/{id}` | Expand row to see full before/after state |
| 3. Export audit log | Admin | Audit Log (H02) | `/audit` | `GET /api/v1/audit?export=csv` | Download CSV |
| 4. PayrollAdmin views compliance reports | PA / A | Compliance Reports (H07) | `/compliance` | `GET /api/v1/compliance` | View statutory filings by period |
| 5. Admin generates compliance filing | A | Compliance Reports (H07) | `/compliance` | `POST /api/v1/compliance/generate` | Trigger report generation for a period |
| 6. Export compliance report | A / PA | Compliance Reports (H07) | `/compliance` | `GET /api/v1/compliance/{id}/export` | Download for submission |

**Non-standard envelope note:** `/api/v1/compliance` returns `{status, data, service}` — frontend must handle missing `meta` field.

---

## WF-008: EMPLOYEE SELF-SERVICE

**Status:** STABLE
**Feature:** F-003, F-009, F-015

### Workflow Steps → Screens

| Step | Actor | Screen | Route | API Call | Action |
|------|-------|--------|-------|----------|--------|
| 1. Employee logs in | Employee | Login | `/login` | `POST /api/v1/auth/login` | Enter credentials, receive JWT |
| 2. View dashboard | Employee | Employee Dashboard (H01) | `/dashboard` | Multiple widget APIs | See own KPIs, leave balance, next payday, notifications |
| 3. Check attendance | Employee | Attendance records (H02) | `/attendance` | `GET /api/v1/attendance?me=true` | View own attendance history |
| 4. Submit leave request | Employee | Raise Leave Request (H04) | `/leave/new` | `POST /api/v1/leave` | Select type, dates, reason (→ WF-002) |
| 5. View payslip | Employee | Payroll Record Detail (H03) | `/payroll/[id]` (own) | `GET /api/v1/payroll/{id}` | View net pay, deductions, breakdown |
| 6. View notifications | Employee | Notifications Inbox (H09) | `/notifications` | `GET /api/v1/notifications?me=true` | Read approval results, payroll notifications |
| 7. Request salary advance (EWA) | Employee | EWA Request (H04) | `/employees/[id]/ewa` | `POST /api/v1/ewa/request` | Submit advance request; requires CAP-EWA-001 |
| 8. View own profile | Employee | Employee Profile (H03) | `/employees/[id]` (own) | `GET /api/v1/employees/{id}` | View personal details, leave history |

---

## WORKFLOW ↔ SCREEN CROSS-REFERENCE SUMMARY

| Workflow | Primary Screens | Approval Screen Used |
|----------|----------------|----------------------|
| WF-001 Employee Onboarding | `/employees/new` (H04), `/employees/[id]` (H03) | — |
| WF-002 Leave Approval | `/leave/new` (H04), `/leave` (H06), `/approvals` (H05) | ✅ `/approvals` |
| WF-003 Payroll Run | `/payroll` (H02), `/payroll/run` (H04), `/payroll/[id]` (H03) | Optional `/approvals` |
| WF-004 Hiring Pipeline | `/job-postings/new` (H04), `/candidates-pipeline` (H13), `/candidates-pipeline/[id]` | — |
| WF-005 Performance (ADD-ON) | `/performance`, `/performance/reviews/[id]` | ✅ via workflow |
| WF-006 Expense Claim (ADD-ON) | `/expense-claims/new` (H04), `/expense-claims/[id]` (H03) | ✅ `/approvals` |
| WF-007 Audit & Compliance | `/audit` (H02), `/compliance` (H07) | — |
| WF-008 Employee Self-Service | `/dashboard` (H01), `/leave/new` (H04), `/payroll/[id]` (H03), `/notifications` (H09) | — |

---

## APPROVAL INBOX (H05) AGGREGATE VIEW

The `/approvals` screen is an aggregation point for all pending workflow steps where the logged-in user (Admin or Manager) is an approver. It draws from:

| Source | API | Approval Types |
|--------|-----|----------------|
| Leave requests | `GET /api/v1/workflows?status=pending&type=leave_approval` | WF-002 |
| Payroll runs (optional) | `GET /api/v1/workflows?status=pending&type=payroll_approval` | WF-003 |
| EWA requests | `GET /api/v1/workflows?status=pending&type=ewa_approval` | WF-008 (F-015) |
| Expense claims (ADD-ON) | `GET /api/v1/workflows?status=pending&type=expense_approval` | WF-006 |

The approval inbox uses the WorkflowInstance entity. WorkflowInstance.status is lowercase (`pending`, `completed`). Each pending step in the WorkflowInstance is displayed as an approval card in the H05 split-view layout (340px list + flex detail panel).
