# Read Model Catalog

This catalog defines query-optimized read models used by SME-HRMS for dashboards, directories, and operational reporting.

## 1) `employee_directory_view`

### Purpose
Provide a fast, filterable directory of employees for HR operations and manager self-service.

### Source domain entities
- `Employee`
- `Department`
- `Role`

### Primary key / grain
- **Grain:** One row per employee.
- **Key:** `employee_id`

### Suggested projection fields
- `employee_id`
- `employee_number`
- `full_name` (derived from `first_name` + `last_name`)
- `email`
- `phone`
- `hire_date`
- `employment_type`
- `employee_status` (from `Employee.status`)
- `department_id`
- `department_name`
- `role_id`
- `role_title`
- `manager_employee_id`
- `manager_name` (self-join on employee)
- `updated_at`

### Typical filters and sorts
- Filters: department, role, employment type, status, manager, hire date range
- Sorts: full name, hire date, department name

### Refresh strategy
- Event-driven update on Employee/Department/Role mutations.
- Nightly rebuild for drift correction.

---

## 2) `attendance_dashboard_view`

### Purpose
Support attendance dashboards with daily and period-level metrics for HR/admin users.

### Source domain entities
- `AttendanceRecord`
- `Employee`
- `Department`

### Primary key / grain
- **Grain:** One row per employee per attendance date.
- **Composite key:** `employee_id`, `attendance_date`

### Suggested projection fields
- `employee_id`
- `employee_number`
- `employee_name`
- `department_id`
- `department_name`
- `attendance_date`
- `attendance_status`
- `check_in_time`
- `check_out_time`
- `total_hours`
- `source`
- `record_state` (captured/validated/approved/locked mapping)
- `updated_at`

### Derived dashboard metrics (materialized or computed)
- present_count
- absent_count
- late_count
- half_day_count
- average_hours_per_day
- attendance_rate

### Typical filters and sorts
- Filters: date or period, department, status, source
- Sorts: attendance date, lateness, total hours

### Refresh strategy
- Incremental upsert on attendance changes.
- Period close lock synchronization when state becomes `Locked`.

---

## 3) `leave_requests_view`

### Purpose
Provide a queue and history view of leave requests for employees, managers, and HR approvers.

### Source domain entities
- `LeaveRequest`
- `Employee` (requester)
- `Employee` (approver)
- `Department`

### Primary key / grain
- **Grain:** One row per leave request.
- **Key:** `leave_request_id`

### Suggested projection fields
- `leave_request_id`
- `employee_id`
- `employee_number`
- `employee_name`
- `department_id`
- `department_name`
- `leave_type`
- `start_date`
- `end_date`
- `total_days`
- `reason`
- `approver_employee_id`
- `approver_name`
- `status`
- `submitted_at`
- `decision_at`
- `updated_at`

### Typical filters and sorts
- Filters: status, leave type, employee, approver, department, date range
- Sorts: submitted date, start date, duration

### Refresh strategy
- Event-driven on request submit/approve/reject/cancel transitions.
- SLA-friendly near-real-time updates for manager inboxes.

---

## 4) `payroll_summary_view`

### Purpose
Serve payroll run summaries and employee-level payroll detail lookup for finance/HR.

### Source domain entities
- `PayrollRecord`
- `Employee`
- `Department`

### Primary key / grain
- **Grain:** One row per employee per pay period.
- **Composite key:** `employee_id`, `pay_period_start`, `pay_period_end`

### Suggested projection fields
- `payroll_record_id`
- `employee_id`
- `employee_number`
- `employee_name`
- `department_id`
- `department_name`
- `pay_period_start`
- `pay_period_end`
- `base_salary`
- `allowances`
- `deductions`
- `overtime_pay`
- `gross_pay`
- `net_pay`
- `currency`
- `payment_date`
- `status`
- `updated_at`

### Derived summary metrics (by period/department)
- headcount_paid
- total_gross_pay
- total_net_pay
- total_allowances
- total_deductions
- total_overtime_pay

### Typical filters and sorts
- Filters: pay period, status, department, employee
- Sorts: net pay, gross pay, payment date

### Refresh strategy
- Incremental upsert during payroll processing lifecycle.
- Reconciliation refresh after period transitions to `Paid`.

---

## 5) `candidate_pipeline_view`

### Purpose
Track hiring pipeline progression for each candidate and job posting.

### Source domain entities
- `Candidate`
- `JobPosting`
- `Department`
- `Role` (when linked from job posting)
- `Interview`

### Primary key / grain
- **Grain:** One row per candidate application.
- **Key:** `candidate_id`

### Suggested projection fields
- `candidate_id`
- `candidate_name`
- `candidate_email`
- `job_posting_id`
- `job_title`
- `department_id`
- `department_name`
- `role_id`
- `role_title`
- `application_date`
- `pipeline_stage` (applied/screening/interview/offer/hired/rejected)
- `stage_updated_at`
- `next_interview_at`
- `interview_count`
- `hiring_owner_employee_id`
- `hiring_owner_name`
- `updated_at`

### Derived pipeline metrics
- candidates_by_stage
- time_in_stage
- stage_conversion_rate
- offer_acceptance_rate
- time_to_hire

### Typical filters and sorts
- Filters: job posting, department, stage, application date range
- Sorts: stage age, next interview, application date

### Refresh strategy
- Event-driven updates on candidate stage changes and interview scheduling.
- Daily consistency pass to recalculate stage duration metrics.

---

## Cross-cutting conventions
- Use immutable domain event timestamps where available for deterministic replay.
- Preserve source identifiers (`*_id`) on all views for traceability.
- Keep PII limited to operationally required fields in each view.
- Version view contracts when fields are added/renamed.
