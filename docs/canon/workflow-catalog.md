# Workflow Catalog

This catalog defines core HRMS workflows based on the canonical domain model entities and lifecycle states.

## employee_onboarding

### Trigger
- A candidate is marked as **Hired** in recruitment, or HR initiates a direct hire onboarding request.

### Steps
1. Create or confirm **Department** and **Role** assignment for the incoming employee.
2. Create **Employee** record in **Draft** state with required identity, contact, and employment metadata.
3. Assign manager (`manager_employee_id`) and organizational placement (`department_id`, `role_id`).
4. Validate mandatory onboarding fields (employee number, email uniqueness, hire date, employment type).
5. Activate employee by transitioning **Employee** from **Draft** to **Active** on hire date.
6. Initialize downstream eligibility for attendance, leave, payroll, and performance workflows.

## attendance_tracking

### Trigger
- An employee checks in/out (manual, biometric, or API import), or a daily attendance batch process runs.

### Steps
1. Capture attendance event and create/update **AttendanceRecord** in **Captured** state.
2. Resolve attendance date and compute `total_hours` from check-in/check-out timestamps when available.
3. Apply attendance rules to classify `attendance_status` (Present, Late, HalfDay, Absent, Holiday).
4. Validate record against policy and move to **Validated** state.
5. Route for supervisor/time-admin confirmation and mark as **Approved**.
6. Lock period records to **Locked** state for payroll and reporting integrity.

## leave_request

### Trigger
- An employee submits a leave request from draft.

### Steps
1. Employee creates **LeaveRequest** in **Draft** with leave type, date range, and reason.
2. System calculates `total_days` and validates date overlap/policy constraints.
3. Submit request and transition status to **Submitted** with `submitted_at` timestamp.
4. Notify approver (`approver_employee_id`) for decision.
5. Approver reviews and sets status to **Approved** or **Rejected**, recording `decision_at`.
6. If approved, update employee availability/status context for the leave period (e.g., **OnLeave** as applicable).
7. Allow cancellation path to **Cancelled** when initiated by employee/admin under policy.

## payroll_processing

### Trigger
- Payroll cycle reaches period close date, or payroll admin starts an off-cycle payroll run.

### Steps
1. Create **PayrollRecord** entries in **Draft** for all eligible active employees in the pay period.
2. Pull period inputs (base salary, allowances, deductions, overtime) from configured sources.
3. Calculate `gross_pay` and `net_pay` per employee and validate currency/period boundaries.
4. Review and transition records to **Processed** after payroll validation checks.
5. Execute payment disbursement and stamp `payment_date`.
6. Update records to **Paid** on successful payout, or **Cancelled** for reversed/invalid runs.

## candidate_hiring

### Trigger
- A **JobPosting** is opened, or a new candidate application is submitted.

### Steps
1. Publish **JobPosting** in **Open** state with department, role profile, and vacancy details.
2. Capture **Candidate** application in **Applied** state.
3. Progress candidate to **Screening** after recruiter review.
4. Schedule and conduct **Interview** rounds (`Scheduled` → `Completed`) and capture recommendations.
5. Move qualified candidate to **Offered** and complete offer decision.
6. On acceptance, transition candidate to **Hired** and close or update related job posting status.
7. Convert hired candidate into **Employee** onboarding flow.

## performance_review

### Trigger
- Review cycle start date is reached, or manager initiates an ad hoc review.

### Steps
1. Create **PerformanceReview** in **Draft** for target employee and assigned reviewer.
2. Reviewer records assessment inputs (strengths, improvement areas, goals, optional rating).
3. Submit review and transition to **Submitted** with `submitted_at`.
4. Employee reads and acknowledges review, setting status to **Acknowledged** with `acknowledged_at`.
5. Final HR/manager closure transitions review to **Finalized**.
6. Store finalized outcomes for promotion, compensation, and development planning.
