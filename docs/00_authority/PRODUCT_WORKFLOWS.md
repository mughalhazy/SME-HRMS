# PRODUCT WORKFLOWS

Status: Active
Authority Level: High
Last Reviewed: 2026-06-15
Owner: Shared

---

## PURPOSE

This document captures the primary end-to-end workflows in the system — how users actually accomplish work across the platform. Each workflow maps user intent through UI → API → services → state changes.

**Primary Evidence Sources:**
- `/backend/docs/canon/workflow-catalog.md`
- `/contracts/hrms-h*.json` (50+ page archetype contracts)
- `/design/hrms-archetype-system-v1.md`
- `/backend/docs/canon/service-map.md`

---

## WORKFLOW CONVENTIONS

- All multi-step approval workflows route through **workflow-service** (port 8009)
- All mutations produce an **audit record** in audit-service
- All approval state changes trigger **notifications** via notification-service
- Workflow instances are created via `POST /api/v1/workflows`
- Step progressions via `PUT /api/v1/workflows/{instance_id}/steps/{step_id}`

---

## WF-001: EMPLOYEE ONBOARDING

**Trigger:** Recruiter initiates hire from candidate pipeline (`POST /api/v1/hiring/candidates/{id}/hire`)
**Primary Actor:** Admin / HR Manager
**Services Involved:** hiring-service → employee-service → auth-service → workflow-service → notification-service → audit-service

### Steps:

1. **Hire Candidate** — hiring-service creates handoff record; status: Hired
2. **Create Employee Record** — employee-service creates Employee entity (status: Draft)
3. **Assign Department & Role** — employee-service links department, role, manager
4. **Create User Account** — auth-service creates UserAccount + RoleBinding
5. **Workflow Instance Created** — workflow-service starts `employee_onboarding` definition
6. **Document Collection** — OUT OF SCOPE. Document management is confirmed OUT OF SCOPE (`FEATURE_SCOPE.md`). This workflow step has no backend service or storage; implementer should omit this step or surface as a UI-only reminder checklist (no API call).
7. **Activate Employee** — employee-service status: Draft → Active
8. **Send Welcome Notification** — notification-service delivers welcome message

**Outcome:** Employee is Active with a UserAccount and can log in

---

## WF-002: LEAVE REQUEST & APPROVAL

**Trigger:** Employee submits leave request via UI (`/leave`)
**Primary Actor:** Employee → Manager → (optionally) HR Admin
**Services Involved:** leave-service → workflow-service → notification-service → audit-service

### Steps:

1. **Submit Leave Request** — `POST /api/v1/leave`; status: Submitted
2. **Workflow Created** — workflow-service starts `leave_approval` definition
3. **Manager Notified** — notification-service delivers approval request to manager
4. **Manager Decision** — Manager approves or rejects via workflow step
   - **Approved:** leave-service status → Approved; employee notified
   - **Rejected:** leave-service status → Rejected; employee notified with reason
5. **Audit Record** — audit-service logs decision
6. **Calendar Updated** — leave-service updates leave record status; attendance-service reads leave status when computing attendance for the covered period. No dedicated "mark days as Leave" event — attendance-service queries leave-service for overlapping approved leaves during period closure.

**Employee Lifecycle Impact:** Employee's leave status `Approved` is surfaced in attendance and calendar views during the leave period. No `OnLeave` employee record status transition — employee status remains `Active`; the calendar/attendance view filters by leave record status.

---

## WF-003: PAYROLL RUN

**Trigger:** PayrollAdmin initiates payroll run for a period
**Primary Actor:** PayrollAdmin
**Services Involved:** payroll-service → employee-service → attendance-service → leave-service → compliance-service → bank-service → audit-service

### Steps:

1. **Initiate Payroll Run** — `POST /api/v1/payroll/run` with period (YYYY-MM)
2. **Employee Data Pull** — payroll-service queries employee-service for active employees
3. **Attendance Data Pull** — payroll-service queries attendance-service for period records
4. **Leave Data Pull** — payroll-service queries leave-service for approved leaves
5. **Gross Calculation** — Apply salary components; country tax engine (`/backend/country/pakistan/tax_engine.py`)
6. **Deductions Calculation** — Tax (FBR), EOBI, PESSI, other deductions
7. **PayrollRecord Created** — status: Draft (one per employee per period)
8. **Review & Approve** — PayrollAdmin reviews records; no mandatory approval workflow step in the current implementation (payroll status transitions directly from Draft to Processed on PayrollAdmin action). A separate approval workflow step is OPTIONAL and not implemented by default.
9. **Status → Processed** — All records marked Processed
10. **Compliance Submission** — compliance-service generates FBR/EOBI/PESSI reports
11. **Disbursement** — bank-service initiates salary transfer (Raast / bank file)
12. **Status → Paid** — Records marked Paid; paid_at timestamp set
13. **Payslip Notification** — notification-service sends payslip to employees

---

## WF-004: HIRING PIPELINE

**Trigger:** Manager/Admin creates job posting
**Primary Actor:** Recruiter / Manager / Admin
**Services Involved:** hiring-service → workflow-service → notification-service → audit-service

### Steps:

1. **Create Job Posting** — `POST /api/v1/hiring` (posting status: Draft)
2. **Publish Posting** — status: Draft → Open
3. **Candidate Applies** — `POST /api/v1/hiring/candidates` (stage: Applied)
4. **Screening** — Recruiter reviews; stage: Applied → ScreeningPass | Rejected
5. **Schedule Interview** — `POST /api/v1/hiring/interviews`; status: Scheduled
6. **Conduct Interview** — Interviewer submits feedback; status: Completed
7. **Interview Loop Repeats** (as needed)
8. **Hire Decision** — stage: InterviewCompleted → Hired | Rejected
9. **Hire Handoff** — `POST /api/v1/hiring/candidates/{id}/hire` triggers WF-001
10. **Close Posting** — status: Open → Closed

**Pipeline View:** `/candidates-pipeline` (H13 archetype)

---

## WF-005: PERFORMANCE REVIEW CYCLE

**Trigger:** HR Admin creates a review cycle
**Primary Actor:** HR Admin → Managers → Employees
**Services Involved:** performance-service → workflow-service → notification-service → audit-service
**Status:** ADD-ON feature

### Steps:

1. **Create Review Cycle** — `POST /api/v1/performance/cycles` (status: Draft)
2. **Configure Participants** — Assign employee-manager review pairs
3. **Launch Cycle** — status: Draft → Open; notifications sent
4. **Self-Assessment** — Employee submits self-review (Goal progress, feedback)
5. **Manager Assessment** — Manager submits rating and feedback
6. **Calibration** — HR Admin runs calibration session; adjustments made
7. **Close Cycle** — status: Open → Closed; results locked
8. **PIP Initiation** (conditional) — If below threshold, PipPlan created: Draft → Active

---

## WF-006: EXPENSE CLAIM

**Trigger:** Employee submits expense claim
**Primary Actor:** Employee → Manager → Finance
**Services Involved:** expense-service → workflow-service → notification-service → audit-service
**Status:** ADD-ON feature

### Steps:

1. **Submit Claim** — `POST /api/v1/expense` (confirmed gateway route; expense-service in routes.py line 48); receipts as attachment
2. **Manager Approval** — Workflow routes to manager; approved/rejected
3. **Finance Review** — ADD-ON deferred: whether a 2nd approval step exists is an implementation detail for the add-on; the expense-service contract will define it
4. **Accounting Export** — Approved claims exported to accounting system
5. **Reimbursement** — ADD-ON deferred: whether bank-service is involved depends on expense-service integration scope; not confirmed in current codebase

---

## WF-007: AUDIT & COMPLIANCE REPORTING

**Trigger:** Admin/PayrollAdmin requests compliance report
**Primary Actor:** Admin / PayrollAdmin / Compliance Officer
**Services Involved:** compliance-service → reporting-analytics-service → audit-service

### Steps:

1. **Generate Report** — `GET /api/v1/compliance/{report_type}?period=`
2. **Data Aggregation** — reporting-analytics-service aggregates from projections
3. **Compliance Formatting** — compliance-service formats to FBR/EOBI/PESSI schema
4. **Review** — Admin reviews generated report
5. **Submit** — compliance-service submits to regulatory body via adapter
6. **Status Tracking** — Filing status tracked and stored

---

## WF-008: EMPLOYEE SELF-SERVICE

**Trigger:** Employee logs in
**Primary Actor:** Employee
**Services Involved:** auth-service, attendance-service, leave-service, payroll-service, notification-service

### Self-Service Capabilities:

| Action | Route | API |
|--------|-------|-----|
| View own attendance | `/attendance` | `GET /api/v1/attendance?employee_id=self` |
| Submit leave request | `/leave` | `POST /api/v1/leave` |
| View leave balance | `/leave` | `GET /api/v1/leave/balance` |
| View payslip | `/payroll` | `GET /api/v1/payroll?employee_id=self` |
| View notifications | `/notifications` | `GET /api/v1/notifications` |
| Update profile (limited) | `/employee-profile` | `PUT /api/v1/employees/{id}` (scoped fields) |

---

## WORKFLOW ORCHESTRATION PATTERNS

### Synchronous Operations (immediate response)
- Read operations (GET requests)
- Simple creates with no approval chain

### Asynchronous via Workflow Engine
- All multi-step approvals (leave, payroll, performance, hiring decisions)
- Any operation requiring audit trail before completion

### Background Jobs
- Bulk payroll calculation (long-running)
- Compliance report generation
- Notification batch delivery
- Data integrity validation

**Evidence:** `/backend/background_jobs.py`, `008_background_jobs_schema.sql`

---

## CROSS-CUTTING CONCERNS (ALL WORKFLOWS)

1. **Request Tracing:** All requests carry X-Trace-Id propagated end-to-end
2. **Idempotency:** All state-changing operations accept Idempotency-Key header
3. **Audit:** Every mutation produces AuditRecord before response is returned
4. **Notifications:** State transitions trigger notification-service events
5. **Rate Limiting:** 200 req/min per IP enforced at API Gateway

---

## REMAINING OPEN ITEMS (Phase 3.25 assessment)

| Item | Classification | Resolution |
|------|---------------|------------|
| Exact approval chain in multi-manager leave scenarios | IMPLEMENTATION DETAIL | workflow-service approver resolution handles routing; multi-manager chain is a configuration detail, not a new workflow |
| Expense reimbursement ↔ bank-service integration | ADD-ON DEFERRED | Not confirmed in current codebase; expense-service is ADD-ON; resolve when implementing F-021 |
| Shift/roster management workflow | CONFIRMED OUT OF SCOPE | No shift-service in codebase. `FEATURE_SCOPE.md` confirms OUT OF SCOPE. |
| Employee offboarding checklist | FUTURE SCOPE | No offboarding workflow defined in the current implementation. Can be added as WF-009 in a future phase. |
| Survey distribution workflow | ADD-ON DEFERRED | engagement-service exists; workflow details deferred with F-018 ADD-ON scope |
