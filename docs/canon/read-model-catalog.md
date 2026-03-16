# Read Model Catalog

This catalog defines query-optimized projections and validates each read model against canonical source services and entities.

## Cross-cutting conventions
- Source of truth for services: `docs/canon/service-map.md`.
- Source of truth for entities: `docs/canon/domain-model.md`.
- Use immutable event timestamps where available for deterministic replay.
- Preserve source identifiers (`*_id`) for traceability.
- Keep PII limited to operationally required fields.
- Version read-model contracts when fields are added or renamed.

## 1) `employee_directory_view`
- **Source services:** `employee-service`
- **Source entities:** `Employee`, `Department`, `Role`
- **Key/grain:** one row per employee (`employee_id`)
- **Fields:** `employee_id`, `employee_number`, `full_name`, `email`, `phone`, `hire_date`, `employment_type`, `employee_status`, `department_id`, `department_name`, `role_id`, `role_title`, `manager_employee_id`, `manager_name`, `updated_at`

## 2) `attendance_dashboard_view`
- **Source services:** `attendance-service`, `employee-service`
- **Source entities:** `AttendanceRecord`, `Employee`, `Department`
- **Key/grain:** one row per employee per attendance date (`employee_id`, `attendance_date`)
- **Fields:** `employee_id`, `employee_number`, `employee_name`, `department_id`, `department_name`, `attendance_date`, `attendance_status`, `check_in_time`, `check_out_time`, `total_hours`, `source`, `record_state`, `updated_at`

## 3) `leave_requests_view`
- **Source services:** `leave-service`, `employee-service`
- **Source entities:** `LeaveRequest`, `Employee`, `Department`
- **Key/grain:** one row per leave request (`leave_request_id`)
- **Fields:** `leave_request_id`, `employee_id`, `employee_number`, `employee_name`, `department_id`, `department_name`, `leave_type`, `start_date`, `end_date`, `total_days`, `reason`, `approver_employee_id`, `approver_name`, `status`, `submitted_at`, `decision_at`, `updated_at`

## 4) `payroll_summary_view`
- **Source services:** `payroll-service`, `employee-service`
- **Source entities:** `PayrollRecord`, `Employee`, `Department`
- **Key/grain:** one row per employee per period (`employee_id`, `pay_period_start`, `pay_period_end`)
- **Fields:** `payroll_record_id`, `employee_id`, `employee_number`, `employee_name`, `department_id`, `department_name`, `pay_period_start`, `pay_period_end`, `base_salary`, `allowances`, `deductions`, `overtime_pay`, `gross_pay`, `net_pay`, `currency`, `payment_date`, `status`, `updated_at`

## 5) `candidate_pipeline_view`
- **Source services:** `hiring-service`, `employee-service` (interviewer display names)
- **Source entities:** `Candidate`, `JobPosting`, `Department`, `Role`, `Interview`, `Employee`
- **Key/grain:** one row per candidate application (`candidate_id`)
- **Fields:** `candidate_id`, `candidate_name`, `candidate_email`, `job_posting_id`, `job_title`, `department_id`, `department_name`, `role_id`, `role_title`, `application_date`, `pipeline_stage`, `stage_updated_at`, `next_interview_at`, `interview_count`, `hiring_owner_employee_id`, `hiring_owner_name`, `updated_at`

## 6) `performance_review_view`
- **Source services:** `employee-service`
- **Source entities:** `PerformanceReview`, `Employee`, `Department`
- **Key/grain:** one row per performance review (`performance_review_id`)
- **Fields:** `performance_review_id`, `employee_id`, `employee_name`, `reviewer_employee_id`, `reviewer_name`, `department_id`, `department_name`, `review_period_start`, `review_period_end`, `overall_rating`, `status`, `submitted_at`, `acknowledged_at`, `updated_at`
