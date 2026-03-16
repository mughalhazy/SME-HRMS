# Data Architecture

## Overview
This document maps the canonical domain model to a relational data architecture for an HRMS system.

- Primary keys use `UUID`.
- Operational timestamps use `TIMESTAMPTZ` (`created_at`, `updated_at`).
- Business dates use `DATE`.
- Monetary values use `NUMERIC(12,2)`.
- Enumerated domain states are modeled using constrained text (`CHECK`) or database enums.

## Table: `departments`

### Purpose
Stores organizational units used for employee assignment, budgeting, and hiring ownership.

### Columns
| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| department_id | UUID | No | PK | Primary identifier. |
| name | VARCHAR(150) | No | UQ | Unique department name. |
| code | VARCHAR(30) | No | UQ | Unique short code. |
| description | TEXT | Yes |  | Optional details. |
| head_employee_id | UUID | Yes | FK | References `employees.employee_id`; nullable to avoid circular create dependency. |
| status | VARCHAR(20) | No |  | One of: `Proposed`, `Active`, `Inactive`, `Archived`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

### Indexes
- `pk_departments (department_id)`
- `uq_departments_name (name)`
- `uq_departments_code (code)`
- `idx_departments_head_employee_id (head_employee_id)`
- `idx_departments_status (status)`

---

## Table: `roles`

### Purpose
Stores standardized job role definitions for assignment and recruitment.

### Columns
| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| role_id | UUID | No | PK | Primary identifier. |
| title | VARCHAR(150) | No |  | Role title. |
| level | VARCHAR(50) | Yes |  | Optional grade/band. |
| description | TEXT | Yes |  | Optional responsibilities summary. |
| employment_category | VARCHAR(20) | No |  | One of: `Staff`, `Manager`, `Executive`, `Contractor`. |
| status | VARCHAR(20) | No |  | One of: `Active`, `Inactive`, `Archived`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

### Indexes
- `pk_roles (role_id)`
- `idx_roles_title (title)`
- `idx_roles_status (status)`

---

## Table: `employees`

### Purpose
Stores core employee identity and employment metadata.

### Columns
| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| employee_id | UUID | No | PK | Primary identifier. |
| employee_number | VARCHAR(40) | No | UQ | Human-readable employee code. |
| first_name | VARCHAR(100) | No |  | Given or preferred name. |
| last_name | VARCHAR(100) | No |  | Family name. |
| email | VARCHAR(255) | No | UQ | Work email. |
| phone | VARCHAR(30) | Yes |  | Optional contact number. |
| hire_date | DATE | No |  | Employment start date. |
| employment_type | VARCHAR(20) | No |  | One of: `FullTime`, `PartTime`, `Contract`, `Intern`. |
| status | VARCHAR(20) | No |  | One of: `Draft`, `Active`, `OnLeave`, `Suspended`, `Terminated`. |
| department_id | UUID | No | FK | References `departments.department_id`. |
| role_id | UUID | No | FK | References `roles.role_id`. |
| manager_employee_id | UUID | Yes | FK | Self-reference to `employees.employee_id`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

### Indexes
- `pk_employees (employee_id)`
- `uq_employees_employee_number (employee_number)`
- `uq_employees_email (email)`
- `idx_employees_department_id (department_id)`
- `idx_employees_role_id (role_id)`
- `idx_employees_manager_employee_id (manager_employee_id)`
- `idx_employees_status (status)`

---

## Table: `attendance_records`

### Purpose
Stores day-level attendance and shift tracking.

### Columns
| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| attendance_id | UUID | No | PK | Primary identifier. |
| employee_id | UUID | No | FK | References `employees.employee_id`. |
| attendance_date | DATE | No |  | Attendance calendar date. |
| check_in_time | TIMESTAMPTZ | Yes |  | Actual check-in time. |
| check_out_time | TIMESTAMPTZ | Yes |  | Actual check-out time. |
| total_hours | NUMERIC(5,2) | Yes |  | Calculated work duration. |
| attendance_status | VARCHAR(20) | No |  | One of: `Present`, `Absent`, `Late`, `HalfDay`, `Holiday`. |
| source | VARCHAR(20) | Yes |  | One of: `Manual`, `Biometric`, `APIImport`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

### Indexes
- `pk_attendance_records (attendance_id)`
- `idx_attendance_records_employee_id (employee_id)`
- `idx_attendance_records_date (attendance_date)`
- `uq_attendance_records_employee_date (employee_id, attendance_date)`
- `idx_attendance_records_status (attendance_status)`

---

## Table: `leave_requests`

### Purpose
Stores employee leave requests and approval workflow outcomes.

### Columns
| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| leave_request_id | UUID | No | PK | Primary identifier. |
| employee_id | UUID | No | FK | References `employees.employee_id`. |
| leave_type | VARCHAR(20) | No |  | One of: `Annual`, `Sick`, `Casual`, `Unpaid`, `Other`. |
| start_date | DATE | No |  | Requested start date. |
| end_date | DATE | No |  | Requested end date (`end_date >= start_date`). |
| total_days | NUMERIC(4,1) | No |  | Derived duration. |
| reason | TEXT | Yes |  | Optional explanation. |
| approver_employee_id | UUID | Yes | FK | References `employees.employee_id`. |
| status | VARCHAR(20) | No |  | One of: `Draft`, `Submitted`, `Approved`, `Rejected`, `Cancelled`. |
| submitted_at | TIMESTAMPTZ | Yes |  | Submission timestamp. |
| decision_at | TIMESTAMPTZ | Yes |  | Decision timestamp. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

### Indexes
- `pk_leave_requests (leave_request_id)`
- `idx_leave_requests_employee_id (employee_id)`
- `idx_leave_requests_approver_employee_id (approver_employee_id)`
- `idx_leave_requests_status (status)`
- `idx_leave_requests_date_range (start_date, end_date)`

---

## Table: `payroll_records`

### Purpose
Stores payroll computation and payout information by pay period.

### Columns
| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| payroll_record_id | UUID | No | PK | Primary identifier. |
| employee_id | UUID | No | FK | References `employees.employee_id`. |
| pay_period_start | DATE | No |  | Period start date. |
| pay_period_end | DATE | No |  | Period end date (`pay_period_end >= pay_period_start`). |
| base_salary | NUMERIC(12,2) | No |  | Fixed salary. |
| allowances | NUMERIC(12,2) | Yes |  | Additional earnings; default `0.00`. |
| deductions | NUMERIC(12,2) | Yes |  | Deductions/taxes; default `0.00`. |
| overtime_pay | NUMERIC(12,2) | Yes |  | Overtime component; default `0.00`. |
| gross_pay | NUMERIC(12,2) | No |  | Calculated gross pay. |
| net_pay | NUMERIC(12,2) | No |  | Final payout. |
| currency | CHAR(3) | No |  | ISO-4217 currency code. |
| payment_date | DATE | Yes |  | Actual payment date. |
| status | VARCHAR(20) | No |  | One of: `Draft`, `Processed`, `Paid`, `Cancelled`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

### Indexes
- `pk_payroll_records (payroll_record_id)`
- `idx_payroll_records_employee_id (employee_id)`
- `uq_payroll_records_employee_period (employee_id, pay_period_start, pay_period_end)`
- `idx_payroll_records_status (status)`
- `idx_payroll_records_payment_date (payment_date)`

---

## Table: `job_postings`

### Purpose
Stores open/planned roles for recruitment campaigns.

### Columns
| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| job_posting_id | UUID | No | PK | Primary identifier. |
| title | VARCHAR(200) | No |  | Posting title. |
| department_id | UUID | No | FK | References `departments.department_id`. |
| role_id | UUID | Yes | FK | References `roles.role_id`. |
| employment_type | VARCHAR(20) | No |  | One of: `FullTime`, `PartTime`, `Contract`, `Intern`. |
| location | VARCHAR(200) | Yes |  | Work location. |
| description | TEXT | No |  | Responsibilities and requirements. |
| openings_count | INTEGER | No |  | Must be `>= 1`. |
| posting_date | DATE | No |  | Publication date. |
| closing_date | DATE | Yes |  | Optional close date (`closing_date >= posting_date`). |
| status | VARCHAR(20) | No |  | One of: `Draft`, `Open`, `OnHold`, `Closed`, `Filled`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

### Indexes
- `pk_job_postings (job_posting_id)`
- `idx_job_postings_department_id (department_id)`
- `idx_job_postings_role_id (role_id)`
- `idx_job_postings_status (status)`
- `idx_job_postings_posting_date (posting_date)`

---

## Table: `candidates`

### Purpose
Stores applicants linked to job postings and their recruitment progression.

### Columns
| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| candidate_id | UUID | No | PK | Primary identifier. |
| job_posting_id | UUID | No | FK | References `job_postings.job_posting_id`. |
| first_name | VARCHAR(100) | No |  | Candidate first name. |
| last_name | VARCHAR(100) | No |  | Candidate last name. |
| email | VARCHAR(255) | No |  | Candidate email. |
| phone | VARCHAR(30) | Yes |  | Optional contact number. |
| resume_url | TEXT | Yes |  | Link or object-store path. |
| source | VARCHAR(20) | Yes |  | One of: `Referral`, `JobBoard`, `CareerSite`, `Agency`, `Other`. |
| application_date | DATE | No |  | Application submission date. |
| status | VARCHAR(20) | No |  | One of: `Applied`, `Screening`, `Interviewing`, `Offered`, `Hired`, `Rejected`, `Withdrawn`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

### Indexes
- `pk_candidates (candidate_id)`
- `idx_candidates_job_posting_id (job_posting_id)`
- `uq_candidates_posting_email (job_posting_id, email)`
- `idx_candidates_status (status)`
- `idx_candidates_application_date (application_date)`

---

## Table: `interviews`

### Purpose
Stores interview schedule events, panel feedback, and recommendations.

### Columns
| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| interview_id | UUID | No | PK | Primary identifier. |
| candidate_id | UUID | No | FK | References `candidates.candidate_id`. |
| interview_type | VARCHAR(20) | No |  | One of: `PhoneScreen`, `Technical`, `Behavioral`, `Panel`, `Final`. |
| scheduled_start | TIMESTAMPTZ | No |  | Planned start time. |
| scheduled_end | TIMESTAMPTZ | No |  | Planned end time (`scheduled_end > scheduled_start`). |
| location_or_link | TEXT | Yes |  | Meeting location or URL. |
| interviewer_employee_ids | UUID[] | Yes |  | Optional panel members as denormalized array. |
| feedback_summary | TEXT | Yes |  | Consolidated feedback. |
| recommendation | VARCHAR(20) | Yes |  | One of: `StrongHire`, `Hire`, `NoHire`, `Undecided`. |
| status | VARCHAR(20) | No |  | One of: `Scheduled`, `Completed`, `Cancelled`, `NoShow`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

### Indexes
- `pk_interviews (interview_id)`
- `idx_interviews_candidate_id (candidate_id)`
- `idx_interviews_schedule (scheduled_start, scheduled_end)`
- `idx_interviews_status (status)`

---

## Table: `performance_reviews`

### Purpose
Stores structured performance assessments for review cycles.

### Columns
| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| performance_review_id | UUID | No | PK | Primary identifier. |
| employee_id | UUID | No | FK | Reviewed employee; references `employees.employee_id`. |
| reviewer_employee_id | UUID | No | FK | Reviewer; references `employees.employee_id`. |
| review_period_start | DATE | No |  | Review period start. |
| review_period_end | DATE | No |  | Review period end (`review_period_end >= review_period_start`). |
| overall_rating | NUMERIC(2,1) | Yes |  | Optional score, typically 1.0-5.0. |
| strengths | TEXT | Yes |  | Strength narrative. |
| improvement_areas | TEXT | Yes |  | Development areas. |
| goals_next_period | TEXT | Yes |  | Goals for next cycle. |
| status | VARCHAR(20) | No |  | One of: `Draft`, `Submitted`, `Acknowledged`, `Finalized`. |
| submitted_at | TIMESTAMPTZ | Yes |  | Reviewer submission time. |
| acknowledged_at | TIMESTAMPTZ | Yes |  | Employee acknowledgement time. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

### Indexes
- `pk_performance_reviews (performance_review_id)`
- `idx_performance_reviews_employee_id (employee_id)`
- `idx_performance_reviews_reviewer_employee_id (reviewer_employee_id)`
- `uq_performance_reviews_cycle (employee_id, review_period_start, review_period_end)`
- `idx_performance_reviews_status (status)`

---

## Referential Graph Summary

- `employees.department_id -> departments.department_id`
- `employees.role_id -> roles.role_id`
- `employees.manager_employee_id -> employees.employee_id`
- `departments.head_employee_id -> employees.employee_id`
- `attendance_records.employee_id -> employees.employee_id`
- `leave_requests.employee_id -> employees.employee_id`
- `leave_requests.approver_employee_id -> employees.employee_id`
- `payroll_records.employee_id -> employees.employee_id`
- `job_postings.department_id -> departments.department_id`
- `job_postings.role_id -> roles.role_id`
- `candidates.job_posting_id -> job_postings.job_posting_id`
- `interviews.candidate_id -> candidates.candidate_id`
- `performance_reviews.employee_id -> employees.employee_id`
- `performance_reviews.reviewer_employee_id -> employees.employee_id`

## Implementation Notes
- Apply `ON UPDATE CASCADE` for all foreign keys.
- Prefer `ON DELETE RESTRICT` for master entities (`employees`, `departments`, `roles`) and `ON DELETE CASCADE` for strictly dependent records where retention policy permits.
- Enforce domain enums with either DB enum types or `CHECK` constraints.
- Ensure all `updated_at` fields are maintained by application logic or update triggers.
