# Workflow Catalog

This catalog defines deterministic HR workflows and explicitly maps each workflow to canonical services and domain entities.

## Valid service registry
- `employee-service`
- `attendance-service`
- `leave-service`
- `payroll-service`
- `hiring-service`
- `auth-service`
- `notification-service`

## employee_onboarding

### Owning service
- `employee-service`

### Participating services
- `hiring-service` (optional source via `CandidateHired` event)
- `auth-service`
- `notification-service`

### Entities referenced
- `Employee`
- `Department`
- `Role`
- `Candidate` (only when sourced from hiring flow)

### Trigger
- A candidate is marked as **Hired** in recruitment, or HR initiates a direct hire onboarding request.

### Steps
1. Confirm `Department` and `Role` exist and are active for assignment.
2. Create `Employee` in `Draft`.
3. Assign `department_id`, `role_id`, and optional `manager_employee_id`.
4. Validate uniqueness and required fields (`employee_number`, `email`, `hire_date`, `employment_type`).
5. Transition `Employee` from `Draft` to `Active` on hire date.
6. Publish eligibility events to attendance, leave, payroll, and performance consumers.

## attendance_tracking

### Owning service
- `attendance-service`

### Participating services
- `employee-service`
- `auth-service`
- `notification-service`

### Entities referenced
- `AttendanceRecord`
- `Employee`

### Trigger
- Employee check-in/out event (manual, biometric, or API import), or daily sync job.

### Steps
1. Create/update `AttendanceRecord` in `Captured` state.
2. Compute `total_hours` from check-in/check-out timestamps.
3. Classify `attendance_status` (Present, Late, HalfDay, Absent, Holiday).
4. Validate policy and transition to `Validated`.
5. Supervisor/time-admin action transitions to `Approved`.
6. Period close transitions records to `Locked` for payroll safety.

## leave_request

### Owning service
- `leave-service`

### Participating services
- `employee-service`
- `auth-service`
- `notification-service`
- `payroll-service` (consumer of approved leave impact)

### Entities referenced
- `LeaveRequest`
- `Employee`

### Trigger
- Employee submits a leave request from draft.

### Steps
1. Create `LeaveRequest` in `Draft` with leave type, date range, and reason.
2. Calculate `total_days`; validate overlap and policy constraints.
3. Submit request (`status=Submitted`, set `submitted_at`).
4. Notify `approver_employee_id`.
5. Approver sets `Approved` or `Rejected` and stamps `decision_at`.
6. If approved, propagate availability impact to dependent consumers.
7. Allow policy-governed cancellation (`Cancelled`).

## payroll_processing

### Owning service
- `payroll-service`

### Participating services
- `employee-service`
- `attendance-service`
- `leave-service`
- `auth-service`
- `notification-service`

### Entities referenced
- `PayrollRecord`
- `Employee`
- `AttendanceRecord`
- `LeaveRequest`

### Trigger
- Payroll period close date, or payroll admin starts off-cycle run.

### Steps
1. Create `PayrollRecord` in `Draft` for eligible active employees.
2. Pull compensation, attendance summary, and approved leave impacts.
3. Calculate `gross_pay` and `net_pay`; validate currency/period boundaries.
4. Transition validated records to `Processed`.
5. Execute disbursement and stamp `payment_date`.
6. Transition to `Paid` on success or `Cancelled` if reversed/invalid.

## candidate_hiring

### Owning service
- `hiring-service`

### Participating services
- `employee-service` (consumes `CandidateHired`)
- `auth-service`
- `notification-service`

### Entities referenced
- `JobPosting`
- `Candidate`
- `Interview`
- `Department`
- `Role`
- `Employee` (conversion target)

### Trigger
- A `JobPosting` is opened, or a candidate application is received.

### Steps
1. Publish `JobPosting` in `Open` with department/role/vacancy details.
2. Capture `Candidate` in `Applied`.
3. Progress candidate to `Screening`.
4. Schedule and complete `Interview` rounds (`Scheduled` → `Completed`).
5. Move qualified candidate to `Offered`.
6. On acceptance, transition candidate to `Hired`.
7. Emit `CandidateHired` for employee onboarding.

## performance_review

### Owning service
- `employee-service`

### Participating services
- `auth-service`
- `notification-service`

### Entities referenced
- `PerformanceReview`
- `Employee`

### Trigger
- Review cycle start date, or manager initiates ad hoc review.

### Steps
1. Create `PerformanceReview` in `Draft`.
2. Reviewer captures strengths, improvement areas, goals, and optional rating.
3. Submit review (`Submitted`, set `submitted_at`).
4. Employee acknowledges (`Acknowledged`, set `acknowledged_at`).
5. Final closure transitions record to `Finalized`.
6. Persist outcomes for talent and compensation planning.
