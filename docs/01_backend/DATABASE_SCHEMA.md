# DATABASE SCHEMA

Status: Draft
Authority Level: Critical
Last Reviewed: 2026-06-15
Owner: AI

---

## Overview

This document records every table, column, constraint, index, and trigger defined across migration files located at `backend/deployment/migrations/`. All claims are sourced directly from the SQL. Nothing has been inferred or invented; ambiguous cases are marked `TBD – REQUIRES VERIFICATION`.

**Schema state:** Migrations 001–013 (original) + Migration 014 (`014_schema_integrity_fixes.sql`, Phase 2 defect fix). Total tables: **58** (57 from 001–013 + `grade_bands` added by 014).

**Multi-tenancy invariant:** Every primary table carries `tenant_id VARCHAR(80) NOT NULL` and a unique constraint on `(tenant_id, <entity>_id)`. Foreign keys in migrations 001–011 use compound `(tenant_id, <fk_col>)` references against the matching `(tenant_id, <pk_col>)` unique constraint. Migrations 012 and 013 originally deviated from this pattern (DG-002); migration 014 corrected all bare FKs in compensation and travel domains — see `docs/08_reports/DATABASE_DISCOVERY_REPORT.md`.

---

## Migration 001 — `001_core_schema.sql`

**Purpose:** Creates the three foundational domain tables — departments, roles, and employees — and wires their circular FK dependencies via a deferred `DO` block.

---

### Table: `departments`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| department_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| name | VARCHAR(150) | NOT NULL | — | — |
| code | VARCHAR(30) | NOT NULL | — | — |
| description | TEXT | NULL | — | — |
| parent_department_id | UUID | NULL | — | — |
| head_employee_id | UUID | NULL | — | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Proposed','Active','Inactive','Archived')) |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**Status column:** DB-level enum enforced via CHECK constraint. Allowed values: `Proposed`, `Active`, `Inactive`, `Archived`.

**Primary Key:** `department_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_departments_tenant_department | (tenant_id, department_id) |
| uq_departments_tenant_name | (tenant_id, name) |
| uq_departments_tenant_code | (tenant_id, code) |

**Foreign Keys** (added via deferred `DO` block after `employees` table is created):
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_departments_parent_department | (tenant_id, parent_department_id) | departments(tenant_id, department_id) | CASCADE | RESTRICT |
| fk_departments_head_employee | (tenant_id, head_employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_departments_tenant_id | (tenant_id) |
| idx_departments_tenant_parent_department_id | (tenant_id, parent_department_id) |
| idx_departments_tenant_head_employee_id | (tenant_id, head_employee_id) |
| idx_departments_tenant_status | (tenant_id, status) |

---

### Table: `roles`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| role_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| title | VARCHAR(150) | NOT NULL | — | — |
| level | VARCHAR(50) | NULL | — | — |
| description | TEXT | NULL | — | — |
| employment_category | VARCHAR(20) | NOT NULL | — | CHECK (employment_category IN ('Staff','Manager','Executive','Contractor')) |
| permissions | TEXT[] | NOT NULL | '{}' | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Draft','Active','Inactive','Archived')) |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**Status column:** DB-level enum. Allowed values: `Draft`, `Active`, `Inactive`, `Archived`.

**employment_category column:** DB-level enum. Allowed values: `Staff`, `Manager`, `Executive`, `Contractor`.

**Primary Key:** `role_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_roles_tenant_role | (tenant_id, role_id) |
| uq_roles_tenant_title | (tenant_id, title) |

**Foreign Keys:** None defined in this migration.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_roles_tenant_id | (tenant_id) |
| idx_roles_tenant_status | (tenant_id, status) |
| idx_roles_tenant_employment_category | (tenant_id, employment_category) |

---

### Table: `employees`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| employee_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| employee_number | VARCHAR(40) | NOT NULL | — | — |
| first_name | VARCHAR(100) | NOT NULL | — | — |
| last_name | VARCHAR(100) | NOT NULL | — | — |
| email | VARCHAR(255) | NOT NULL | — | — |
| phone | VARCHAR(30) | NULL | — | — |
| hire_date | DATE | NOT NULL | — | — |
| employment_type | VARCHAR(20) | NOT NULL | — | CHECK (employment_type IN ('FullTime','PartTime','Contract','Intern')) |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Draft','Active','OnLeave','Suspended','Terminated')) |
| department_id | UUID | NOT NULL | — | — |
| role_id | UUID | NOT NULL | — | — |
| manager_employee_id | UUID | NULL | — | — |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**Status column:** DB-level enum. Allowed values: `Draft`, `Active`, `OnLeave`, `Suspended`, `Terminated`.

**employment_type column:** DB-level enum. Allowed values: `FullTime`, `PartTime`, `Contract`, `Intern`.

**Primary Key:** `employee_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_employees_tenant_employee | (tenant_id, employee_id) |
| uq_employees_tenant_employee_number | (tenant_id, employee_number) |
| uq_employees_tenant_email | (tenant_id, email) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_employees_department | (tenant_id, department_id) | departments(tenant_id, department_id) | CASCADE | RESTRICT |
| fk_employees_role | (tenant_id, role_id) | roles(tenant_id, role_id) | CASCADE | RESTRICT |
| fk_employees_manager | (tenant_id, manager_employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_employees_tenant_id | (tenant_id) |
| idx_employees_tenant_department_id | (tenant_id, department_id) |
| idx_employees_tenant_role_id | (tenant_id, role_id) |
| idx_employees_tenant_manager_employee_id | (tenant_id, manager_employee_id) |
| idx_employees_tenant_status | (tenant_id, status) |

---

## Migration 002 — `002_workflow_schema.sql`

**Purpose:** Creates the bulk of the domain tables — attendance, leave, payroll, hiring, performance management, and HR settings. Despite the filename suggesting workflow content, this migration contains all core domain entity tables. Workflow tables are defined separately in migration 003.

---

### Table: `attendance_records`

> Note: This table is modified by migration 004, which adds `record_state` and `correction_note` columns. The complete column list including those additions is shown here.

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| attendance_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| employee_id | UUID | NOT NULL | — | — |
| attendance_date | DATE | NOT NULL | — | — |
| check_in_time | TIMESTAMPTZ | NULL | — | — |
| check_out_time | TIMESTAMPTZ | NULL | — | — |
| total_hours | NUMERIC(5,2) | NULL | — | — |
| attendance_status | VARCHAR(20) | NOT NULL | — | CHECK (attendance_status IN ('Present','Absent','Late','HalfDay','Holiday')) |
| source | VARCHAR(20) | NULL | — | CHECK (source IN ('Manual','Biometric','APIImport')) |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |
| record_state | VARCHAR(20) | NOT NULL | 'Captured' | CHECK (record_state IN ('Captured','Validated','Approved','Locked')) — *added in migration 004* |
| correction_note | TEXT | NULL | — | — — *added in migration 004* |

**attendance_status column:** DB-level enum. Allowed values: `Present`, `Absent`, `Late`, `HalfDay`, `Holiday`.

**source column:** DB-level enum (nullable). Allowed values: `Manual`, `Biometric`, `APIImport`.

**record_state column:** DB-level enum (added by 004). Allowed values: `Captured`, `Validated`, `Approved`, `Locked`.

**Primary Key:** `attendance_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_attendance_records_tenant_attendance | (tenant_id, attendance_id) |
| uq_attendance_records_employee_date | (tenant_id, employee_id, attendance_date) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_attendance_records_employee | (tenant_id, employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_attendance_records_tenant_id | (tenant_id) |
| idx_attendance_records_tenant_employee_id | (tenant_id, employee_id) |
| idx_attendance_records_tenant_date | (tenant_id, attendance_date) |
| idx_attendance_records_tenant_status | (tenant_id, attendance_status) |
| idx_attendance_records_tenant_record_state | (tenant_id, record_state) — *added in migration 004* |

---

### Table: `leave_requests`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| leave_request_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| employee_id | UUID | NOT NULL | — | — |
| leave_type | VARCHAR(20) | NOT NULL | — | CHECK (leave_type IN ('Annual','Sick','Casual','Unpaid','Other')) |
| start_date | DATE | NOT NULL | — | — |
| end_date | DATE | NOT NULL | — | — |
| total_days | NUMERIC(4,1) | NOT NULL | — | — |
| reason | TEXT | NULL | — | — |
| approver_employee_id | UUID | NULL | — | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Draft','Submitted','Approved','Rejected','Cancelled')) |
| submitted_at | TIMESTAMPTZ | NULL | — | — |
| decision_at | TIMESTAMPTZ | NULL | — | — |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**leave_type column:** DB-level enum. Allowed values: `Annual`, `Sick`, `Casual`, `Unpaid`, `Other`. Note: `Parental` is absent here but present in `leave_policies.leave_type` — see Discovery Report.

**status column:** DB-level enum. Allowed values: `Draft`, `Submitted`, `Approved`, `Rejected`, `Cancelled`.

**Primary Key:** `leave_request_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_leave_requests_tenant_request | (tenant_id, leave_request_id) |

**Check Constraints:**
| Constraint Name | Expression |
|----------------|-----------|
| chk_leave_requests_date_range | end_date >= start_date |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_leave_requests_employee | (tenant_id, employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT |
| fk_leave_requests_approver | (tenant_id, approver_employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_leave_requests_tenant_id | (tenant_id) |
| idx_leave_requests_tenant_employee_id | (tenant_id, employee_id) |
| idx_leave_requests_tenant_approver_employee_id | (tenant_id, approver_employee_id) |
| idx_leave_requests_tenant_status | (tenant_id, status) |
| idx_leave_requests_tenant_date_range | (tenant_id, start_date, end_date) |

---

### Table: `payroll_records`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| payroll_record_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| employee_id | UUID | NOT NULL | — | — |
| pay_period_start | DATE | NOT NULL | — | — |
| pay_period_end | DATE | NOT NULL | — | — |
| base_salary | NUMERIC(12,2) | NOT NULL | — | — |
| allowances | NUMERIC(12,2) | NULL | 0.00 | — |
| deductions | NUMERIC(12,2) | NULL | 0.00 | — |
| overtime_pay | NUMERIC(12,2) | NULL | 0.00 | — |
| gross_pay | NUMERIC(12,2) | NOT NULL | — | — |
| net_pay | NUMERIC(12,2) | NOT NULL | — | — |
| currency | CHAR(3) | NOT NULL | — | — |
| payment_date | DATE | NULL | — | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Draft','Processed','Paid','Cancelled')) |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**status column:** DB-level enum. Allowed values: `Draft`, `Processed`, `Paid`, `Cancelled`.

**Primary Key:** `payroll_record_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_payroll_records_tenant_record | (tenant_id, payroll_record_id) |
| uq_payroll_records_employee_period | (tenant_id, employee_id, pay_period_start, pay_period_end) |

**Check Constraints:**
| Constraint Name | Expression |
|----------------|-----------|
| chk_payroll_records_period | pay_period_end >= pay_period_start |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_payroll_records_employee | (tenant_id, employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_payroll_records_tenant_id | (tenant_id) |
| idx_payroll_records_tenant_employee_id | (tenant_id, employee_id) |
| idx_payroll_records_tenant_status | (tenant_id, status) |
| idx_payroll_records_tenant_payment_date | (tenant_id, payment_date) |

---

### Table: `job_postings`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| job_posting_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| title | VARCHAR(200) | NOT NULL | — | — |
| department_id | UUID | NOT NULL | — | — |
| role_id | UUID | NULL | — | — |
| employment_type | VARCHAR(20) | NOT NULL | — | CHECK (employment_type IN ('FullTime','PartTime','Contract','Intern')) |
| location | VARCHAR(200) | NULL | — | — |
| description | TEXT | NOT NULL | — | — |
| openings_count | INTEGER | NOT NULL | — | CHECK (openings_count >= 1) |
| posting_date | DATE | NOT NULL | — | — |
| closing_date | DATE | NULL | — | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Draft','Open','OnHold','Closed','Filled')) |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**status column:** DB-level enum. Allowed values: `Draft`, `Open`, `OnHold`, `Closed`, `Filled`.

**Primary Key:** `job_posting_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_job_postings_tenant_posting | (tenant_id, job_posting_id) |

**Check Constraints:**
| Constraint Name | Expression |
|----------------|-----------|
| chk_job_postings_dates | closing_date IS NULL OR closing_date >= posting_date |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_job_postings_department | (tenant_id, department_id) | departments(tenant_id, department_id) | CASCADE | RESTRICT |
| fk_job_postings_role | (tenant_id, role_id) | roles(tenant_id, role_id) | CASCADE | RESTRICT |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_job_postings_tenant_id | (tenant_id) |
| idx_job_postings_tenant_department_id | (tenant_id, department_id) |
| idx_job_postings_tenant_role_id | (tenant_id, role_id) |
| idx_job_postings_tenant_status | (tenant_id, status) |
| idx_job_postings_tenant_posting_date | (tenant_id, posting_date) |

---

### Table: `candidates`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| candidate_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| job_posting_id | UUID | NOT NULL | — | — |
| first_name | VARCHAR(100) | NOT NULL | — | — |
| last_name | VARCHAR(100) | NOT NULL | — | — |
| email | VARCHAR(255) | NOT NULL | — | — |
| phone | VARCHAR(30) | NULL | — | — |
| resume_url | TEXT | NULL | — | — |
| source | VARCHAR(20) | NULL | — | CHECK (source IN ('Referral','JobBoard','CareerSite','Agency','LinkedIn','Other')) |
| source_candidate_id | VARCHAR(120) | NULL | — | — |
| source_profile_url | TEXT | NULL | — | — |
| application_date | DATE | NOT NULL | — | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Applied','Screening','Interviewing','Offered','Hired','Rejected','Withdrawn')) |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**status column:** DB-level enum. Allowed values: `Applied`, `Screening`, `Interviewing`, `Offered`, `Hired`, `Rejected`, `Withdrawn`.

**Primary Key:** `candidate_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_candidates_tenant_candidate | (tenant_id, candidate_id) |
| uq_candidates_posting_email | (tenant_id, job_posting_id, email) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_candidates_job_posting | (tenant_id, job_posting_id) | job_postings(tenant_id, job_posting_id) | CASCADE | CASCADE |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_candidates_tenant_id | (tenant_id) |
| idx_candidates_tenant_job_posting_id | (tenant_id, job_posting_id) |
| idx_candidates_tenant_status | (tenant_id, status) |
| idx_candidates_tenant_application_date | (tenant_id, application_date) |
| idx_candidates_tenant_source_candidate_id | (tenant_id, source_candidate_id) |

---

### Table: `candidate_stage_transitions`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| candidate_stage_transition_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| candidate_id | UUID | NOT NULL | — | — |
| from_status | VARCHAR(20) | NULL | — | CHECK (from_status IN ('Applied','Screening','Interviewing','Offered','Hired','Rejected','Withdrawn')) |
| to_status | VARCHAR(20) | NOT NULL | — | CHECK (to_status IN ('Applied','Screening','Interviewing','Offered','Hired','Rejected','Withdrawn')) |
| changed_at | TIMESTAMPTZ | NOT NULL | now() | — |
| changed_by | VARCHAR(120) | NULL | — | — |
| reason | TEXT | NULL | — | — |
| notes | TEXT | NULL | — | — |

**from_status / to_status columns:** DB-level enum matching `candidates.status`. Allowed values: `Applied`, `Screening`, `Interviewing`, `Offered`, `Hired`, `Rejected`, `Withdrawn`.

**Primary Key:** `candidate_stage_transition_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_candidate_stage_transitions_tenant_transition | (tenant_id, candidate_stage_transition_id) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_candidate_stage_transitions_candidate | (tenant_id, candidate_id) | candidates(tenant_id, candidate_id) | CASCADE | CASCADE |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_candidate_stage_transitions_tenant_id | (tenant_id) |
| idx_candidate_stage_transitions_tenant_candidate_id | (tenant_id, candidate_id) |
| idx_candidate_stage_transitions_tenant_changed_at | (tenant_id, changed_at) |
| idx_candidate_stage_transitions_tenant_to_status | (tenant_id, to_status) |

---

### Table: `interviews`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| interview_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| candidate_id | UUID | NOT NULL | — | — |
| interview_type | VARCHAR(20) | NOT NULL | — | CHECK (interview_type IN ('PhoneScreen','Technical','Behavioral','Panel','Final')) |
| scheduled_start | TIMESTAMPTZ | NOT NULL | — | — |
| scheduled_end | TIMESTAMPTZ | NOT NULL | — | — |
| location_or_link | TEXT | NULL | — | — |
| interviewer_employee_ids | UUID[] | NULL | — | — |
| feedback_summary | TEXT | NULL | — | — |
| recommendation | VARCHAR(20) | NULL | — | CHECK (recommendation IN ('StrongHire','Hire','NoHire','Undecided')) |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Scheduled','Completed','Cancelled','NoShow')) |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**interview_type column:** DB-level enum. Allowed values: `PhoneScreen`, `Technical`, `Behavioral`, `Panel`, `Final`.

**recommendation column:** DB-level enum (nullable). Allowed values: `StrongHire`, `Hire`, `NoHire`, `Undecided`.

**status column:** DB-level enum. Allowed values: `Scheduled`, `Completed`, `Cancelled`, `NoShow`.

**Note:** `interviewer_employee_ids UUID[]` stores multiple employee IDs as a PostgreSQL array. No FK enforcement on individual array elements.

**Primary Key:** `interview_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_interviews_tenant_interview | (tenant_id, interview_id) |

**Check Constraints:**
| Constraint Name | Expression |
|----------------|-----------|
| chk_interviews_schedule | scheduled_end > scheduled_start |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_interviews_candidate | (tenant_id, candidate_id) | candidates(tenant_id, candidate_id) | CASCADE | CASCADE |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_interviews_tenant_id | (tenant_id) |
| idx_interviews_tenant_candidate_id | (tenant_id, candidate_id) |
| idx_interviews_tenant_schedule | (tenant_id, scheduled_start, scheduled_end) |
| idx_interviews_tenant_status | (tenant_id, status) |

---

### Table: `attendance_rules`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| attendance_rule_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| code | VARCHAR(80) | NOT NULL | — | — |
| name | VARCHAR(160) | NOT NULL | — | — |
| timezone | VARCHAR(80) | NOT NULL | — | — |
| workdays | VARCHAR(20)[] | NOT NULL | — | — |
| standard_work_hours | NUMERIC(4,2) | NOT NULL | — | CHECK (standard_work_hours >= 0 AND standard_work_hours <= 24) |
| grace_period_minutes | INTEGER | NOT NULL | 0 | CHECK (grace_period_minutes >= 0) |
| late_after_minutes | INTEGER | NOT NULL | 0 | CHECK (late_after_minutes >= grace_period_minutes) |
| auto_clock_out_hours | NUMERIC(4,2) | NULL | — | CHECK (auto_clock_out_hours IS NULL OR (auto_clock_out_hours >= 0 AND auto_clock_out_hours <= 24)) |
| require_geo_fencing | BOOLEAN | NOT NULL | FALSE | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Draft','Active','Archived')) |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**status column:** DB-level enum. Allowed values: `Draft`, `Active`, `Archived`.

**workdays column:** PostgreSQL array of VARCHAR(20). Values are not CHECK-constrained at the DB level — TBD – REQUIRES VERIFICATION for application-level enforcement.

**Primary Key:** `attendance_rule_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_attendance_rules_tenant_rule | (tenant_id, attendance_rule_id) |
| uq_attendance_rules_code | (tenant_id, code) |

**Foreign Keys:** None.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_attendance_rules_tenant_id | (tenant_id) |
| idx_attendance_rules_tenant_status | (tenant_id, status) |

---

### Table: `leave_policies`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| leave_policy_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| code | VARCHAR(80) | NOT NULL | — | — |
| name | VARCHAR(160) | NOT NULL | — | — |
| leave_type | VARCHAR(20) | NOT NULL | — | CHECK (leave_type IN ('Annual','Sick','Casual','Unpaid','Parental','Other')) |
| accrual_frequency | VARCHAR(20) | NOT NULL | — | CHECK (accrual_frequency IN ('None','Monthly','Quarterly','Yearly')) |
| accrual_rate_days | NUMERIC(5,2) | NOT NULL | — | CHECK (accrual_rate_days >= 0) |
| annual_entitlement_days | NUMERIC(5,2) | NOT NULL | — | CHECK (annual_entitlement_days >= 0) |
| carry_forward_limit_days | NUMERIC(5,2) | NOT NULL | — | CHECK (carry_forward_limit_days >= 0 AND carry_forward_limit_days <= annual_entitlement_days) |
| requires_approval | BOOLEAN | NOT NULL | TRUE | — |
| allow_negative_balance | BOOLEAN | NOT NULL | FALSE | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Draft','Active','Archived')) |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**leave_type column:** DB-level enum. Allowed values: `Annual`, `Sick`, `Casual`, `Unpaid`, `Parental`, `Other`. Note: includes `Parental` which is absent from `leave_requests.leave_type` — see Discovery Report.

**status column:** DB-level enum. Allowed values: `Draft`, `Active`, `Archived`.

**Primary Key:** `leave_policy_id`

**Unique Constraints:**
| Constraint Name | Columns | Condition |
|----------------|---------|-----------|
| uq_leave_policies_tenant_policy | (tenant_id, leave_policy_id) | — |
| uq_leave_policies_code | (tenant_id, code) | — |
| uq_leave_policies_active_type *(partial index)* | (tenant_id, leave_type) | WHERE status = 'Active' |

**Check Constraints:**
| Constraint Name | Expression |
|----------------|-----------|
| chk_leave_policies_unpaid_entitlement | leave_type <> 'Unpaid' OR annual_entitlement_days = 0 |

**Foreign Keys:** None.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_leave_policies_tenant_id | (tenant_id) |
| idx_leave_policies_tenant_status | (tenant_id, status) |
| idx_leave_policies_tenant_type_status | (tenant_id, leave_type, status) |
| uq_leave_policies_active_type *(partial unique)* | (tenant_id, leave_type) WHERE status = 'Active' |

---

### Table: `payroll_settings`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| payroll_setting_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| pay_schedule | VARCHAR(20) | NOT NULL | — | CHECK (pay_schedule IN ('Weekly','BiWeekly','SemiMonthly','Monthly')) |
| pay_day | INTEGER | NOT NULL | — | CHECK (pay_day >= 1 AND pay_day <= 31) |
| currency | CHAR(3) | NOT NULL | — | — |
| overtime_multiplier | NUMERIC(4,2) | NOT NULL | — | CHECK (overtime_multiplier >= 1) |
| attendance_cutoff_days | INTEGER | NOT NULL | — | CHECK (attendance_cutoff_days >= 0 AND attendance_cutoff_days <= 31) |
| leave_deduction_mode | VARCHAR(20) | NOT NULL | — | CHECK (leave_deduction_mode IN ('None','Prorated','FullDay')) |
| approval_chain | TEXT[] | NOT NULL | — | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Draft','Active','Archived')) |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**status column:** DB-level enum. Allowed values: `Draft`, `Active`, `Archived`.

**Primary Key:** `payroll_setting_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_payroll_settings_tenant_setting | (tenant_id, payroll_setting_id) |

**Foreign Keys:** None.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_payroll_settings_tenant_id | (tenant_id) |
| idx_payroll_settings_tenant_status | (tenant_id, status) |

---

### Table: `performance_review_cycles`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| review_cycle_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| code | VARCHAR(40) | NOT NULL | — | — |
| name | VARCHAR(160) | NOT NULL | — | — |
| review_period_start | DATE | NOT NULL | — | — |
| review_period_end | DATE | NOT NULL | — | — |
| owner_employee_id | UUID | NOT NULL | — | — |
| workflow_id | UUID | NULL | — | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Draft','Open','Closed')) |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**status column:** DB-level enum. Allowed values: `Draft`, `Open`, `Closed`.

**Primary Key:** `review_cycle_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_performance_review_cycles_tenant_review | (tenant_id, review_cycle_id) |
| uq_performance_review_cycles_tenant_code | (tenant_id, code) |

**Check Constraints:**
| Constraint Name | Expression |
|----------------|-----------|
| chk_performance_review_cycles_period | review_period_end >= review_period_start |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_performance_review_cycles_owner | (tenant_id, owner_employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_performance_review_cycles_tenant_id | (tenant_id) |
| idx_performance_review_cycles_tenant_status | (tenant_id, status) |

---

### Table: `performance_goals`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| goal_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| review_cycle_id | UUID | NOT NULL | — | — |
| employee_id | UUID | NOT NULL | — | — |
| owner_employee_id | UUID | NOT NULL | — | — |
| title | VARCHAR(160) | NOT NULL | — | — |
| description | TEXT | NOT NULL | '' | — |
| metric_name | VARCHAR(120) | NOT NULL | — | — |
| target_value | NUMERIC(10,2) | NOT NULL | — | — |
| current_value | NUMERIC(10,2) | NOT NULL | 0 | — |
| weight | NUMERIC(5,2) | NOT NULL | — | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Draft','Submitted','Approved','Rejected')) |
| workflow_id | UUID | NULL | — | — |
| approved_at | TIMESTAMPTZ | NULL | — | — |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**status column:** DB-level enum. Allowed values: `Draft`, `Submitted`, `Approved`, `Rejected`.

**Primary Key:** `goal_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_performance_goals_tenant_goal | (tenant_id, goal_id) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_performance_goals_cycle | (tenant_id, review_cycle_id) | performance_review_cycles(tenant_id, review_cycle_id) | CASCADE | RESTRICT |
| fk_performance_goals_employee | (tenant_id, employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT |
| fk_performance_goals_owner | (tenant_id, owner_employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_performance_goals_tenant_employee | (tenant_id, employee_id) |
| idx_performance_goals_tenant_status | (tenant_id, status) |

---

### Table: `performance_feedback`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| feedback_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| employee_id | UUID | NOT NULL | — | — |
| provider_employee_id | UUID | NOT NULL | — | — |
| review_cycle_id | UUID | NULL | — | — |
| feedback_type | VARCHAR(20) | NOT NULL | — | CHECK (feedback_type IN ('Manager','Peer','Self','Upward')) |
| strengths | TEXT | NOT NULL | '' | — |
| opportunities | TEXT | NOT NULL | '' | — |
| visibility | VARCHAR(20) | NOT NULL | — | CHECK (visibility IN ('Private','Employee','ManagerAndHR')) |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**feedback_type column:** DB-level enum. Allowed values: `Manager`, `Peer`, `Self`, `Upward`.

**visibility column:** DB-level enum. Allowed values: `Private`, `Employee`, `ManagerAndHR`.

**Primary Key:** `feedback_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_performance_feedback_tenant_feedback | (tenant_id, feedback_id) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_performance_feedback_employee | (tenant_id, employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT |
| fk_performance_feedback_provider | (tenant_id, provider_employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT |
| fk_performance_feedback_cycle | (tenant_id, review_cycle_id) | performance_review_cycles(tenant_id, review_cycle_id) | CASCADE | SET NULL |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_performance_feedback_tenant_employee | (tenant_id, employee_id, created_at DESC) |

---

### Table: `performance_calibrations`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| calibration_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| review_cycle_id | UUID | NOT NULL | — | — |
| facilitator_employee_id | UUID | NOT NULL | — | — |
| department_id | UUID | NOT NULL | — | — |
| proposed_rating | NUMERIC(2,1) | NOT NULL | — | — |
| final_rating | NUMERIC(2,1) | NULL | — | — |
| notes | TEXT | NOT NULL | '' | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Draft','Submitted','Finalized','Rejected')) |
| workflow_id | UUID | NULL | — | — |
| finalized_at | TIMESTAMPTZ | NULL | — | — |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**status column:** DB-level enum. Allowed values: `Draft`, `Submitted`, `Finalized`, `Rejected`.

**Primary Key:** `calibration_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_performance_calibrations_tenant_calibration | (tenant_id, calibration_id) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_performance_calibrations_cycle | (tenant_id, review_cycle_id) | performance_review_cycles(tenant_id, review_cycle_id) | CASCADE | RESTRICT |
| fk_performance_calibrations_facilitator | (tenant_id, facilitator_employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT |
| fk_performance_calibrations_department | (tenant_id, department_id) | departments(tenant_id, department_id) | CASCADE | RESTRICT |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_performance_calibrations_tenant_cycle | (tenant_id, review_cycle_id, status) |

---

### Table: `performance_pip_plans`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| pip_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| employee_id | UUID | NOT NULL | — | — |
| manager_employee_id | UUID | NOT NULL | — | — |
| review_cycle_id | UUID | NULL | — | — |
| reason | TEXT | NOT NULL | — | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Draft','Submitted','Active','Completed','Cancelled','Rejected')) |
| workflow_id | UUID | NULL | — | — |
| started_at | TIMESTAMPTZ | NULL | — | — |
| closed_at | TIMESTAMPTZ | NULL | — | — |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**status column:** DB-level enum. Allowed values: `Draft`, `Submitted`, `Active`, `Completed`, `Cancelled`, `Rejected`.

**Primary Key:** `pip_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_performance_pip_plans_tenant_pip | (tenant_id, pip_id) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_performance_pip_plans_employee | (tenant_id, employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT |
| fk_performance_pip_plans_manager | (tenant_id, manager_employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT |
| fk_performance_pip_plans_cycle | (tenant_id, review_cycle_id) | performance_review_cycles(tenant_id, review_cycle_id) | CASCADE | SET NULL |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_performance_pip_plans_tenant_employee | (tenant_id, employee_id, status) |

---

### Table: `performance_pip_milestones`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| pip_milestone_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| pip_id | UUID | NOT NULL | — | — |
| title | VARCHAR(160) | NOT NULL | — | — |
| due_date | DATE | NOT NULL | — | — |
| success_metric | TEXT | NOT NULL | — | — |
| completed | BOOLEAN | NOT NULL | FALSE | — |
| completed_at | TIMESTAMPTZ | NULL | — | — |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**Primary Key:** `pip_milestone_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_performance_pip_milestones_tenant_milestone | (tenant_id, pip_milestone_id) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_performance_pip_milestones_pip | (tenant_id, pip_id) | performance_pip_plans(tenant_id, pip_id) | CASCADE | CASCADE |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_performance_pip_milestones_tenant_pip | (tenant_id, pip_id) |

---

## Migration 003 — `003_centralized_workflow_engine.sql`

**Purpose:** Creates the centralized workflow engine tables — definitions, instances, steps, and audit history.

---

### Table: `workflow_definitions`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| workflow_definition_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| code | VARCHAR(120) | NOT NULL | — | — |
| source_service | VARCHAR(80) | NOT NULL | — | — |
| subject_type | VARCHAR(80) | NOT NULL | — | — |
| description | TEXT | NOT NULL | — | — |
| steps | JSONB | NOT NULL | — | — |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**Primary Key:** `workflow_definition_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_workflow_definitions_tenant_code | (tenant_id, code) |

**Note:** No `(tenant_id, workflow_definition_id)` unique constraint — deviates from the multi-tenant invariant.

**Foreign Keys:** None.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_workflow_definitions_tenant_id | (tenant_id) |

---

### Table: `workflow_instances`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| workflow_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| workflow_definition_id | UUID | NOT NULL | — | — |
| source_service | VARCHAR(80) | NOT NULL | — | — |
| subject_type | VARCHAR(80) | NOT NULL | — | — |
| subject_id | UUID | NOT NULL | — | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('pending','completed')) |
| created_by | VARCHAR(120) | NOT NULL | — | — |
| created_by_type | VARCHAR(20) | NOT NULL | — | CHECK (created_by_type IN ('user','service','system')) |
| metadata | JSONB | NOT NULL | '{}'::jsonb | — |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**status column:** DB-level enum. Allowed values: `pending`, `completed` (lowercase).

**created_by_type column:** DB-level enum. Allowed values: `user`, `service`, `system`.

**Primary Key:** `workflow_id`

**Unique Constraints:** None (no `(tenant_id, workflow_id)` unique — deviates from multi-tenant invariant).

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_workflow_instances_definition | (workflow_definition_id) | workflow_definitions(workflow_definition_id) | CASCADE | RESTRICT |

**Note:** FK not tenant-scoped — references `workflow_definition_id` alone.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_workflow_instances_tenant_status | (tenant_id, status) |
| idx_workflow_instances_subject | (tenant_id, subject_type, subject_id) |

---

### Table: `workflow_steps`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| workflow_step_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| workflow_id | UUID | NOT NULL | — | — |
| step_code | VARCHAR(120) | NOT NULL | — | — |
| step_type | VARCHAR(20) | NOT NULL | — | CHECK (step_type IN ('approval','auto','condition')) |
| assignee | VARCHAR(120) | NOT NULL | — | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('pending','approved','rejected')) |
| sla | VARCHAR(32) | NOT NULL | — | — |
| metadata | JSONB | NOT NULL | '{}'::jsonb | — |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**step_type column:** DB-level enum. Allowed values: `approval`, `auto`, `condition`.

**status column:** DB-level enum. Allowed values: `pending`, `approved`, `rejected` (lowercase).

**Primary Key:** `workflow_step_id`

**Unique Constraints:** None (no `(tenant_id, workflow_step_id)` unique — deviates from multi-tenant invariant).

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_workflow_steps_instance | (workflow_id) | workflow_instances(workflow_id) | CASCADE | CASCADE |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_workflow_steps_tenant_assignee | (tenant_id, assignee, status) |
| idx_workflow_steps_tenant_workflow | (tenant_id, workflow_id) |

---

### Table: `workflow_history`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| workflow_history_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| workflow_id | UUID | NOT NULL | — | — |
| workflow_step_id | UUID | NULL | — | — |
| action | VARCHAR(80) | NOT NULL | — | — |
| actor_id | VARCHAR(120) | NOT NULL | — | — |
| actor_type | VARCHAR(20) | NOT NULL | — | CHECK (actor_type IN ('user','service','system')) |
| from_status | VARCHAR(20) | NULL | — | — |
| to_status | VARCHAR(20) | NOT NULL | — | — |
| details | JSONB | NOT NULL | '{}'::jsonb | — |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |

**actor_type column:** DB-level enum. Allowed values: `user`, `service`, `system`.

**Primary Key:** `workflow_history_id`

**Unique Constraints:** None.

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_workflow_history_instance | (workflow_id) | workflow_instances(workflow_id) | CASCADE | CASCADE |
| fk_workflow_history_step | (workflow_step_id) | workflow_steps(workflow_step_id) | CASCADE | SET NULL |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_workflow_history_tenant_workflow | (tenant_id, workflow_id, created_at) |

---

## Migration 004 — `004_persistence_normalization.sql`

**Purpose:** Adds persistence normalization columns to `attendance_records` and creates the authentication and authorization tables.

**Alterations to existing tables:**
- `attendance_records`: adds `record_state VARCHAR(20) NOT NULL DEFAULT 'Captured'` with CHECK and `correction_note TEXT` (reflected in migration 002 section above).

---

### Table: `user_accounts`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| user_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| employee_id | UUID | NULL | — | — |
| username | VARCHAR(150) | NOT NULL | — | — |
| email | VARCHAR(255) | NULL | — | — |
| password_hash | TEXT | NOT NULL | — | — |
| identity_provider | VARCHAR(40) | NOT NULL | 'local' | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Invited','Active','Locked','Disabled')) |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |
| last_login_at | TIMESTAMPTZ | NULL | — | — |

**status column:** DB-level enum. Allowed values: `Invited`, `Active`, `Locked`, `Disabled`.

**Primary Key:** `user_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_user_accounts_tenant_user | (tenant_id, user_id) |
| uq_user_accounts_tenant_username | (tenant_id, username) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_user_accounts_employee | (tenant_id, employee_id) | employees(tenant_id, employee_id) | CASCADE | SET NULL |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_user_accounts_tenant_employee_id | (tenant_id, employee_id) |
| idx_user_accounts_tenant_status | (tenant_id, status) |

---

### Table: `role_bindings`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| role_binding_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| user_id | UUID | NOT NULL | — | — |
| role_code | VARCHAR(80) | NOT NULL | — | — |
| scope_type | VARCHAR(40) | NOT NULL | — | — |
| scope_id | VARCHAR(120) | NULL | — | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Active','Revoked')) |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**status column:** DB-level enum. Allowed values: `Active`, `Revoked`.

**Primary Key:** `role_binding_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_role_bindings_tenant_binding | (tenant_id, role_binding_id) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_role_bindings_user | (tenant_id, user_id) | user_accounts(tenant_id, user_id) | CASCADE | CASCADE |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_role_bindings_tenant_user_id | (tenant_id, user_id) |
| idx_role_bindings_tenant_status | (tenant_id, status) |

---

### Table: `permission_policies`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| permission_policy_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| policy_code | VARCHAR(100) | NOT NULL | — | — |
| subject_type | VARCHAR(40) | NOT NULL | — | — |
| subject_id | VARCHAR(120) | NOT NULL | — | — |
| capability_code | VARCHAR(80) | NOT NULL | — | — |
| scope_type | VARCHAR(40) | NOT NULL | — | — |
| scope_id | VARCHAR(120) | NULL | — | — |
| effect | VARCHAR(10) | NOT NULL | — | CHECK (effect IN ('Allow','Deny')) |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**effect column:** DB-level enum. Allowed values: `Allow`, `Deny`.

**Primary Key:** `permission_policy_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_permission_policies_tenant_policy | (tenant_id, permission_policy_id) |
| uq_permission_policies_tenant_policy_code | (tenant_id, policy_code) |

**Foreign Keys:** None.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_permission_policies_tenant_subject | (tenant_id, subject_type, subject_id) |
| idx_permission_policies_tenant_capability | (tenant_id, capability_code) |

---

### Table: `sessions`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| session_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| user_id | UUID | NOT NULL | — | — |
| access_token_jti | VARCHAR(120) | NOT NULL | — | — |
| client_type | VARCHAR(40) | NOT NULL | 'api' | — |
| started_at | TIMESTAMPTZ | NOT NULL | now() | — |
| expires_at | TIMESTAMPTZ | NOT NULL | — | — |
| last_rotated_at | TIMESTAMPTZ | NOT NULL | now() | — |
| revoked_at | TIMESTAMPTZ | NULL | — | — |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**Primary Key:** `session_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_sessions_tenant_session | (tenant_id, session_id) |
| uq_sessions_access_token_jti | (tenant_id, access_token_jti) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_sessions_user | (tenant_id, user_id) | user_accounts(tenant_id, user_id) | CASCADE | CASCADE |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_sessions_tenant_user_id | (tenant_id, user_id) |
| idx_sessions_tenant_expires_at | (tenant_id, expires_at) |
| idx_sessions_tenant_revoked_at | (tenant_id, revoked_at) |

---

### Table: `refresh_tokens`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| refresh_token_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| session_id | UUID | NOT NULL | — | — |
| user_id | UUID | NOT NULL | — | — |
| token_hash | TEXT | NOT NULL | — | — |
| rotated_from_token_id | UUID | NULL | — | — |
| expires_at | TIMESTAMPTZ | NOT NULL | — | — |
| revoked_at | TIMESTAMPTZ | NULL | — | — |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**Primary Key:** `refresh_token_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_refresh_tokens_tenant_token | (tenant_id, refresh_token_id) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_refresh_tokens_session | (tenant_id, session_id) | sessions(tenant_id, session_id) | CASCADE | CASCADE |
| fk_refresh_tokens_user | (tenant_id, user_id) | user_accounts(tenant_id, user_id) | CASCADE | CASCADE |
| fk_refresh_tokens_rotated_from | (tenant_id, rotated_from_token_id) | refresh_tokens(tenant_id, refresh_token_id) | CASCADE | SET NULL |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_refresh_tokens_tenant_session_id | (tenant_id, session_id) |
| idx_refresh_tokens_tenant_user_id | (tenant_id, user_id) |
| idx_refresh_tokens_tenant_expires_at | (tenant_id, expires_at) |

---

## Migration 005 — `005_tenant_foundation.sql`

**Purpose:** Creates the tenant registry and per-tenant configuration table. These are referenced by FK from notification and audit tables in later migrations.

---

### Table: `tenants`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | PRIMARY KEY |
| tenant_name | VARCHAR(200) | NOT NULL | — | — |
| slug | VARCHAR(120) | NOT NULL | — | UNIQUE |
| status | VARCHAR(20) | NOT NULL | 'Active' | CHECK (status IN ('Provisioning','Active','Suspended','Archived')) |
| default_locale | VARCHAR(20) | NOT NULL | 'en-US' | — |
| legal_entity_name | VARCHAR(200) | NULL | — | — |
| primary_country_code | CHAR(2) | NULL | — | — |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**status column:** DB-level enum. Allowed values: `Provisioning`, `Active`, `Suspended`, `Archived`.

**Note:** `tenant_id` is VARCHAR(80) and serves directly as the PRIMARY KEY (not a UUID). The `slug` column has a global unique constraint (not tenant-scoped, since this is the tenant root table).

**Primary Key:** `tenant_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| *(inline)* | slug |

**Foreign Keys:** None.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_tenants_status | (status) |

---

### Table: `tenant_configs`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_config_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| feature_flags | JSONB | NOT NULL | '{}'::jsonb | — |
| leave_policy_refs | JSONB | NOT NULL | '[]'::jsonb | — |
| payroll_rule_refs | JSONB | NOT NULL | '[]'::jsonb | — |
| locale | VARCHAR(20) | NOT NULL | 'en-US' | — |
| legal_entity | JSONB | NOT NULL | '{}'::jsonb | — |
| enabled_locations | JSONB | NOT NULL | '[]'::jsonb | — |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**Primary Key:** `tenant_config_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_tenant_configs_tenant | (tenant_id) |

**Note:** `UNIQUE (tenant_id)` enforces one config record per tenant.

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_tenant_configs_tenant | (tenant_id) | tenants(tenant_id) | CASCADE | CASCADE |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_tenant_configs_tenant_id | (tenant_id) |

---

## Migration 006 — `006_notification_service.sql`

**Purpose:** Creates all notification service tables — templates, messages, delivery attempts, and user preferences.

---

### Table: `notification_templates`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| template_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| code | VARCHAR(100) | NOT NULL | — | — |
| channel | VARCHAR(20) | NOT NULL | — | CHECK (channel IN ('Email','SMS','Push','InApp')) |
| topic_code | VARCHAR(100) | NOT NULL | — | — |
| subject_template | TEXT | NULL | — | — |
| body_template | TEXT | NOT NULL | — | — |
| locale | VARCHAR(10) | NOT NULL | 'en-US' | — |
| status | VARCHAR(20) | NOT NULL | 'Active' | CHECK (status IN ('Draft','Active','Retired')) |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**channel column:** DB-level enum. Allowed values: `Email`, `SMS`, `Push`, `InApp`.

**status column:** DB-level enum. Allowed values: `Draft`, `Active`, `Retired`.

**Primary Key:** `template_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_notification_templates_code | (tenant_id, code, channel) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_notification_templates_tenant | (tenant_id) | tenants(tenant_id) | CASCADE | CASCADE |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_notification_templates_channel | (tenant_id, channel) |
| idx_notification_templates_active | (tenant_id, status) |

---

### Table: `notification_messages`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| message_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| template_id | UUID | NULL | — | — |
| event_name | VARCHAR(120) | NULL | — | — |
| event_type | VARCHAR(160) | NULL | — | — |
| recipient | VARCHAR(100) | NOT NULL | — | — |
| subject_type | VARCHAR(40) | NOT NULL | — | — |
| subject_id | VARCHAR(100) | NOT NULL | — | — |
| topic_code | VARCHAR(100) | NOT NULL | — | — |
| channel | VARCHAR(20) | NOT NULL | — | CHECK (channel IN ('Email','SMS','Push','InApp')) |
| destination | TEXT | NOT NULL | — | — |
| payload | JSONB | NOT NULL | '{}'::jsonb | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Queued','Sent','Failed','Suppressed')) |
| queued_at | TIMESTAMPTZ | NOT NULL | now() | — |
| sent_at | TIMESTAMPTZ | NULL | — | — |
| delivered_at | TIMESTAMPTZ | NULL | — | — |
| failed_at | TIMESTAMPTZ | NULL | — | — |
| failure_reason | TEXT | NULL | — | — |
| read_at | TIMESTAMPTZ | NULL | — | — |
| retry_count | INTEGER | NOT NULL | 0 | — |
| last_attempt_at | TIMESTAMPTZ | NULL | — | — |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**status column:** DB-level enum. Allowed values: `Queued`, `Sent`, `Failed`, `Suppressed`.

**Primary Key:** `message_id`

**Unique Constraints:** None at table level.

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_notification_messages_tenant | (tenant_id) | tenants(tenant_id) | CASCADE | CASCADE |
| fk_notification_messages_template | (template_id) | notification_templates(template_id) | CASCADE | SET NULL |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_notification_messages_subject | (tenant_id, subject_type, subject_id) |
| idx_notification_messages_status | (tenant_id, status) |
| idx_notification_messages_channel | (tenant_id, channel) |
| idx_notification_messages_template_id | (template_id) |

---

### Table: `delivery_attempts`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| delivery_attempt_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| message_id | UUID | NOT NULL | — | — |
| provider_name | VARCHAR(100) | NOT NULL | — | — |
| provider_message_id | VARCHAR(255) | NULL | — | — |
| attempt_number | INTEGER | NOT NULL | — | CHECK (attempt_number >= 1) |
| attempted_at | TIMESTAMPTZ | NOT NULL | now() | — |
| outcome | VARCHAR(20) | NOT NULL | — | CHECK (outcome IN ('Sent','Failed','Deferred','Suppressed')) |
| response_code | VARCHAR(50) | NULL | — | — |
| response_message | TEXT | NULL | — | — |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |

**outcome column:** DB-level enum. Allowed values: `Sent`, `Failed`, `Deferred`, `Suppressed`.

**Primary Key:** `delivery_attempt_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_delivery_attempts_message_attempt | (message_id, attempt_number) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_delivery_attempts_tenant | (tenant_id) | tenants(tenant_id) | CASCADE | CASCADE |
| fk_delivery_attempts_message | (message_id) | notification_messages(message_id) | CASCADE | CASCADE |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_delivery_attempts_message_id | (tenant_id, message_id) |
| idx_delivery_attempts_outcome | (tenant_id, outcome) |

---

### Table: `notification_preferences`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| preference_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| subject_type | VARCHAR(40) | NOT NULL | — | — |
| subject_id | VARCHAR(100) | NOT NULL | — | — |
| topic_code | VARCHAR(100) | NOT NULL | — | — |
| email_enabled | BOOLEAN | NOT NULL | TRUE | — |
| sms_enabled | BOOLEAN | NOT NULL | FALSE | — |
| push_enabled | BOOLEAN | NOT NULL | TRUE | — |
| in_app_enabled | BOOLEAN | NOT NULL | TRUE | — |
| quiet_hours | JSONB | NULL | — | — |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**Primary Key:** `preference_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_notification_preferences_subject_topic | (tenant_id, subject_type, subject_id, topic_code) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_notification_preferences_tenant | (tenant_id) | tenants(tenant_id) | CASCADE | CASCADE |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_notification_preferences_subject | (tenant_id, subject_type, subject_id) |

---

## Migration 007 — `007_event_outbox.sql`

**Purpose:** Creates the service-level outbox and idempotency tables for reliable event dispatch. Note: Despite the filename `event_outbox.sql`, this migration creates `service_outbox` and `processed_events`; the table named `event_outbox` is in migration 008.

---

### Table: `service_outbox`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| outbox_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| source_service | VARCHAR(80) | NOT NULL | — | — |
| event_id | UUID | NOT NULL | — | — |
| event_type | VARCHAR(160) | NOT NULL | — | — |
| event_payload | JSONB | NOT NULL | — | — |
| status | VARCHAR(20) | NOT NULL | 'Pending' | CHECK (status IN ('Pending','Dispatched','Failed')) |
| attempt_count | INTEGER | NOT NULL | 0 | — |
| last_error | TEXT | NULL | — | — |
| dispatched_at | TIMESTAMPTZ | NULL | — | — |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**status column:** DB-level enum. Allowed values: `Pending`, `Dispatched`, `Failed`.

**Primary Key:** `outbox_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_service_outbox_event | (tenant_id, source_service, event_id) |

**Foreign Keys:** None.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_service_outbox_dispatch | (tenant_id, source_service, status, created_at) |
| idx_service_outbox_event_type | (tenant_id, event_type, created_at) |

---

### Table: `processed_events`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| processed_event_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| consumer_name | VARCHAR(120) | NOT NULL | — | — |
| event_id | UUID | NOT NULL | — | — |
| event_type | VARCHAR(160) | NOT NULL | — | — |
| processed_at | TIMESTAMPTZ | NOT NULL | now() | — |
| metadata | JSONB | NOT NULL | '{}'::jsonb | — |

**Purpose:** Idempotency deduplication table — prevents reprocessing the same event by the same consumer.

**Primary Key:** `processed_event_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_processed_events_consumer | (tenant_id, consumer_name, event_id) |

**Foreign Keys:** None.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_processed_events_lookup | (tenant_id, consumer_name, processed_at DESC) |

---

## Migration 008 — `008_background_jobs_schema.sql`

**Purpose:** Creates the aggregate-level event outbox and background job scheduling tables. Note: The file is named `background_jobs_schema.sql` but also contains the `event_outbox` table.

---

### Table: `event_outbox`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| event_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| aggregate_type | VARCHAR(80) | NOT NULL | — | — |
| aggregate_id | VARCHAR(100) | NOT NULL | — | — |
| event_name | VARCHAR(120) | NOT NULL | — | — |
| payload | JSONB | NOT NULL | — | — |
| trace_id | VARCHAR(64) | NOT NULL | — | — |
| occurred_at | TIMESTAMPTZ | NOT NULL | — | — |
| published_at | TIMESTAMPTZ | NULL | — | — |
| failed_attempts | INTEGER | NOT NULL | 0 | — |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |

**Primary Key:** `event_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_event_outbox_tenant_event | (tenant_id, event_id) |

**Foreign Keys:** None.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_event_outbox_unpublished | (tenant_id, published_at) |
| idx_event_outbox_aggregate | (tenant_id, aggregate_type, aggregate_id) |
| idx_event_outbox_event_name | (tenant_id, event_name) |

---

### Table: `background_jobs`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| job_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| job_type | VARCHAR(120) | NOT NULL | — | — |
| payload | JSONB | NOT NULL | — | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Scheduled','Running','Succeeded','Failed','DeadLettered','Cancelled')) |
| attempts | INTEGER | NOT NULL | 0 | — |
| scheduled_at | TIMESTAMPTZ | NOT NULL | — | — |
| started_at | TIMESTAMPTZ | NULL | — | — |
| finished_at | TIMESTAMPTZ | NULL | — | — |
| failure_reason | TEXT | NULL | — | — |
| idempotency_key | VARCHAR(160) | NULL | — | — |
| created_at | TIMESTAMPTZ | NOT NULL | now() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | — |

**status column:** DB-level enum. Allowed values: `Scheduled`, `Running`, `Succeeded`, `Failed`, `DeadLettered`, `Cancelled`.

**Primary Key:** `job_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_background_jobs_tenant_job | (tenant_id, job_id) |

**Foreign Keys:** None.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_background_jobs_schedulable | (tenant_id, status, scheduled_at) |
| idx_background_jobs_type | (tenant_id, job_type) |
| idx_background_jobs_idempotency | (tenant_id, idempotency_key) |

---

### Table: `background_job_failures`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| background_job_failure_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| job_id | UUID | NOT NULL | — | — |
| attempt_number | INTEGER | NOT NULL | — | CHECK (attempt_number >= 1) |
| failure_reason | TEXT | NOT NULL | — | — |
| retryable | BOOLEAN | NOT NULL | TRUE | — |
| occurred_at | TIMESTAMPTZ | NOT NULL | now() | — |
| recovered_at | TIMESTAMPTZ | NULL | — | — |

**Primary Key:** `background_job_failure_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_background_job_failures_tenant_failure | (tenant_id, background_job_failure_id) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_background_job_failures_job | (tenant_id, job_id) | background_jobs(tenant_id, job_id) | CASCADE | CASCADE |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_background_job_failures_job | (tenant_id, job_id, occurred_at) |

---

## Migration 009 — `009_audit_service.sql`

**Purpose:** Creates the immutable audit log table with DB-level triggers that prevent any UPDATE or DELETE.

---

### Table: `audit_records`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| audit_log_row_id | BIGSERIAL | NOT NULL | auto-increment | PRIMARY KEY |
| audit_id | UUID | NOT NULL | uuid_generate_v4() | — |
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| actor | JSONB | NOT NULL | — | — |
| action | VARCHAR(120) | NOT NULL | — | — |
| entity | VARCHAR(120) | NOT NULL | — | — |
| entity_id | VARCHAR(120) | NOT NULL | — | — |
| before | JSONB | NOT NULL | '{}'::jsonb | — |
| after | JSONB | NOT NULL | '{}'::jsonb | — |
| timestamp | TIMESTAMPTZ | NOT NULL | NOW() | — |
| trace_id | VARCHAR(120) | NOT NULL | — | — |
| source | JSONB | NOT NULL | '{}'::jsonb | — |

**APPEND-ONLY TABLE:** Database triggers `trg_audit_records_prevent_update` and `trg_audit_records_prevent_delete` (BEFORE UPDATE / BEFORE DELETE FOR EACH ROW) call `prevent_audit_record_mutation()` which raises an exception. No UPDATE or DELETE is permitted on this table at the database level.

**Primary Key:** `audit_log_row_id` (BIGSERIAL — sequential integer, not UUID)

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_audit_records_audit_id | (audit_id) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_audit_records_tenant | (tenant_id) | tenants(tenant_id) | CASCADE | RESTRICT |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_audit_records_tenant_timestamp | (tenant_id, timestamp DESC) |
| idx_audit_records_tenant_actor | (tenant_id, (actor->>'id'), (actor->>'type')) — expression index on JSONB fields |
| idx_audit_records_tenant_entity | (tenant_id, entity, entity_id, timestamp DESC) |
| idx_audit_records_tenant_action | (tenant_id, action, timestamp DESC) |

---

## Migration 010 — `010_engagement_service.sql`

**Purpose:** Creates the employee engagement survey tables — surveys, questions, responses, individual answers, and aggregate statistics.

---

### Table: `engagement_surveys`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| survey_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| code | VARCHAR(80) | NOT NULL | — | — |
| title | VARCHAR(200) | NOT NULL | — | — |
| description | TEXT | NULL | — | — |
| status | VARCHAR(20) | NOT NULL | — | CHECK (status IN ('Draft','Open','Closed')) |
| owner_employee_id | UUID | NOT NULL | — | — |
| target_department_id | UUID | NULL | — | — |
| published_at | TIMESTAMPTZ | NULL | — | — |
| closed_at | TIMESTAMPTZ | NULL | — | — |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**status column:** DB-level enum. Allowed values: `Draft`, `Open`, `Closed`.

**Primary Key:** `survey_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_engagement_surveys_tenant_code | (tenant_id, code) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_engagement_surveys_owner | (tenant_id, owner_employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT (default) |
| fk_engagement_surveys_department | (tenant_id, target_department_id) | departments(tenant_id, department_id) | CASCADE | RESTRICT (default) |

**Note:** Neither FK specifies ON DELETE — PostgreSQL default is RESTRICT.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_engagement_surveys_tenant_status | (tenant_id, status, updated_at DESC) |

---

### Table: `engagement_survey_questions`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| question_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| survey_id | UUID | NOT NULL | — | — |
| prompt | TEXT | NOT NULL | — | — |
| dimension | VARCHAR(2) | NOT NULL | — | CHECK (dimension IN ('D1','D2','D3','D4','D5')) |
| kind | VARCHAR(20) | NOT NULL | — | CHECK (kind IN ('Likert5')) |
| required | BOOLEAN | NOT NULL | TRUE | — |
| scale_min | INTEGER | NOT NULL | 1 | — |
| scale_max | INTEGER | NOT NULL | 5 | — |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**dimension column:** DB-level enum. Allowed values: `D1`, `D2`, `D3`, `D4`, `D5`. Semantic meaning of dimensions is TBD – REQUIRES VERIFICATION (not documented in the SQL).

**kind column:** DB-level enum. Allowed values: `Likert5` only.

**Primary Key:** `question_id`

**Unique Constraints:** None (no `(tenant_id, question_id)` unique constraint).

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_engagement_questions_survey | (tenant_id, survey_id) | engagement_surveys(tenant_id, survey_id) | CASCADE | CASCADE |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_engagement_questions_survey | (tenant_id, survey_id) |

---

### Table: `engagement_survey_responses`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| response_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| survey_id | UUID | NOT NULL | — | — |
| employee_id | UUID | NOT NULL | — | — |
| overall_comment | TEXT | NULL | — | — |
| submitted_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**Primary Key:** `response_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_engagement_responses_tenant_survey_employee | (tenant_id, survey_id, employee_id) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_engagement_responses_survey | (tenant_id, survey_id) | engagement_surveys(tenant_id, survey_id) | CASCADE | CASCADE |
| fk_engagement_responses_employee | (tenant_id, employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT (default) |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_engagement_responses_survey | (tenant_id, survey_id, submitted_at DESC) |

---

### Table: `engagement_survey_answers`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| answer_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY |
| response_id | UUID | NOT NULL | — | — |
| question_id | UUID | NOT NULL | — | — |
| score | INTEGER | NOT NULL | — | CHECK (score BETWEEN 1 AND 5) |
| comment | TEXT | NULL | — | — |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**score column:** CHECK constraint enforces 1–5 range.

**Primary Key:** `answer_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_engagement_answers_response_question | (tenant_id, response_id, question_id) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_engagement_answers_response | (tenant_id, response_id) | engagement_survey_responses(tenant_id, response_id) | CASCADE | CASCADE |
| fk_engagement_answers_question | (tenant_id, question_id) | engagement_survey_questions(tenant_id, question_id) | CASCADE | CASCADE |

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_engagement_answers_response | (tenant_id, response_id) |

---

### Table: `engagement_survey_aggregates`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| survey_id | UUID | NOT NULL | — | PRIMARY KEY |
| response_count | INTEGER | NOT NULL | 0 | — |
| participant_count | INTEGER | NOT NULL | 0 | — |
| target_population | INTEGER | NOT NULL | 0 | — |
| participation_rate | NUMERIC(6,4) | NOT NULL | 0 | — |
| overall_average_score | NUMERIC(6,2) | NOT NULL | 0 | — |
| favorable_ratio | NUMERIC(6,4) | NOT NULL | 0 | — |
| question_scores | JSONB | NOT NULL | — | — |
| dimension_scores | JSONB | NOT NULL | — | — |
| score_distribution | JSONB | NOT NULL | — | — |
| generated_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**Note:** `survey_id` is both the PRIMARY KEY and the FK target — one aggregate row per survey. This is a 1:1 relationship with `engagement_surveys`.

**Primary Key:** `survey_id`

**Unique Constraints:** None beyond the PK.

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_engagement_aggregates_survey | (tenant_id, survey_id) | engagement_surveys(tenant_id, survey_id) | CASCADE | CASCADE |

**Indexes:** None defined.

---

## Migration 011 — `011_addon_domains.sql`

**Purpose:** Creates tables for add-on and miscellaneous domain features — helpdesk, workforce analytics, learning paths, and workforce cost planning. Wrapped in `BEGIN`/`COMMIT` transaction. Note: `learning_paths` references LMS functionality which is listed as OUT OF SCOPE in `FEATURE_SCOPE.md`.

---

### Table: `helpdesk_tickets`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| ticket_id | UUID | NOT NULL | — | PRIMARY KEY |
| requester_employee_id | UUID | NOT NULL | — | — |
| subject | VARCHAR(240) | NOT NULL | — | — |
| category_code | VARCHAR(60) | NOT NULL | — | — |
| priority | VARCHAR(20) | NOT NULL | — | No CHECK constraint — application enforces: `Low`, `Medium`, `High`, `Urgent` (`helpdesk_service.py` line 128) |
| status | VARCHAR(20) | NOT NULL | — | No CHECK constraint — application enforces: `Draft`, `Open`, `InProgress`, `Resolved`, `Closed` (`helpdesk_service.py` line 127) |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**Note:** `ticket_id` has no `DEFAULT uuid_generate_v4()` — the application must supply the UUID. `priority` and `status` columns have no DB-level CHECK constraints; application-enforced allowed values confirmed from `helpdesk_service.py` lines 127–128 (Phase 3.25 DC-011).

**No `(tenant_id, ticket_id)` unique constraint** — deviates from the multi-tenant invariant.

**No FK** to `employees` for `requester_employee_id`.

**Primary Key:** `ticket_id`

**Unique Constraints:** None.

**Foreign Keys:** None.

**Indexes:** None defined.

---

### Table: `helpdesk_ticket_sla_events`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| event_id | UUID | NOT NULL | — | PRIMARY KEY |
| ticket_id | UUID | NOT NULL | — | — |
| escalation_stage | VARCHAR(30) | NOT NULL | — | — |
| triggered_at | TIMESTAMPTZ | NOT NULL | NOW() | — |
| metadata | JSONB | NOT NULL | '{}'::jsonb | — |

**Note:** `event_id` has no `DEFAULT uuid_generate_v4()`. No `(tenant_id, event_id)` unique constraint.

**Primary Key:** `event_id`

**Unique Constraints:** None.

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_helpdesk_sla_ticket | (ticket_id) | helpdesk_tickets(ticket_id) | RESTRICT (default) | CASCADE |

**Note:** FK is not tenant-scoped (single column, not compound).

**Indexes:** None defined.

---

### Table: `workforce_intelligence_snapshots`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| snapshot_id | UUID | NOT NULL | — | PRIMARY KEY |
| snapshot_type | VARCHAR(80) | NOT NULL | — | — |
| dimension_key | VARCHAR(80) | NOT NULL | — | — |
| dimension_value | VARCHAR(160) | NOT NULL | — | — |
| metrics | JSONB | NOT NULL | '{}'::jsonb | — |
| captured_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**Note:** `snapshot_id` has no `DEFAULT uuid_generate_v4()`. No `(tenant_id, snapshot_id)` unique constraint. No FK to `tenants`. No indexes.

**Primary Key:** `snapshot_id`

**Unique Constraints:** None.

**Foreign Keys:** None.

**Indexes:** None defined.

---

### Table: `learning_paths`

> **OUT OF SCOPE:** LMS is explicitly listed as "OUT OF SCOPE" in `docs/00_authority/FEATURE_SCOPE.md`. This table exists in the migration but has no corresponding service implementation.

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| learning_path_id | UUID | NOT NULL | — | PRIMARY KEY |
| code | VARCHAR(100) | NOT NULL | — | — |
| title | VARCHAR(200) | NOT NULL | — | — |
| description | TEXT | NOT NULL | '' | — |
| status | VARCHAR(20) | NOT NULL | 'Active' | No CHECK constraint — TBD – REQUIRES VERIFICATION |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**Note:** `learning_path_id` has no `DEFAULT uuid_generate_v4()`. `status` has no CHECK constraint (allowed values TBD). No FK to `tenants`.

**Primary Key:** `learning_path_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_learning_paths_tenant_code | (tenant_id, code) |

**Foreign Keys:** None.

**Indexes:** None defined.

---

### Table: `workforce_cost_plans`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| plan_id | UUID | NOT NULL | — | PRIMARY KEY |
| fiscal_year | SMALLINT | NOT NULL | — | — |
| period_code | VARCHAR(20) | NOT NULL | — | — |
| headcount_target | INTEGER | NOT NULL | — | CHECK (headcount_target >= 0) |
| salary_forecast | NUMERIC(14,2) | NOT NULL | 0 | — |
| budget_limit | NUMERIC(14,2) | NOT NULL | 0 | — |
| forecast_currency | CHAR(3) | NOT NULL | 'USD' | — |
| notes | TEXT | NOT NULL | '' | — |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**Note:** `plan_id` has no `DEFAULT uuid_generate_v4()`. No FK to `tenants`. `forecast_currency` defaults to `'USD'` whereas most other currency columns default to `'PKR'` or have no default — TBD – REQUIRES VERIFICATION.

**Primary Key:** `plan_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_workforce_cost_plan | (tenant_id, fiscal_year, period_code) |

**Foreign Keys:** None.

**Indexes:** None defined.

---

## Migration 012 — `012_compensation_domain.sql`

**Purpose:** Creates compensation management tables — bands, salary revisions, benefits plans, enrollments, and allowances. Wrapped in `BEGIN`/`COMMIT`. Note: FKs in this migration use single-column references to `employees` and `compensation_bands`, breaking the compound `(tenant_id, <id>)` pattern used in migrations 001–010.

---

### Table: `compensation_bands`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| compensation_band_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY (pk_compensation_bands) |
| grade_band_id | UUID | NOT NULL | — | — |
| name | VARCHAR(150) | NOT NULL | — | — |
| code | VARCHAR(30) | NOT NULL | — | — |
| currency | CHAR(3) | NOT NULL | — | — |
| min_salary | NUMERIC(12,2) | NOT NULL | — | CHECK (min_salary >= 0) |
| max_salary | NUMERIC(12,2) | NOT NULL | — | CHECK (max_salary >= min_salary) |
| target_salary | NUMERIC(12,2) | NULL | — | — |
| status | VARCHAR(20) | NOT NULL | 'Draft' | CHECK (status IN ('Draft','Active','Inactive','Archived')) |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**status column:** DB-level enum. Allowed values: `Draft`, `Active`, `Inactive`, `Archived`.

**DG-001 RESOLVED:** FK `fk_compensation_bands_grade_band` originally referenced a `grade_bands` table not defined in migrations 001–013. Migration `014_schema_integrity_fixes.sql` §1 adds the `grade_bands` table and §3 replaces the bare FK with a compound `(tenant_id, grade_band_id)` FK. See `docs/08_reports/BACKEND_GAP_REGISTER.md` DG-001.

**Primary Key:** `compensation_band_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_compensation_bands_tenant_code | (tenant_id, code) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_compensation_bands_grade_band | (tenant_id, grade_band_id) | grade_bands(tenant_id, grade_band_id) | CASCADE | RESTRICT |

**Note (migration 014):** FK upgraded from bare `(grade_band_id)` to compound `(tenant_id, grade_band_id)` — DG-002 fix. `grade_bands` table added by migration 014 §1 — DG-001 fix.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_compensation_bands_tenant_id | (tenant_id) |
| idx_compensation_bands_grade_band_id | (grade_band_id) |
| idx_compensation_bands_tenant_status | (tenant_id, status) |

---

### Table: `salary_revisions`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| salary_revision_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY (pk_salary_revisions) |
| employee_id | UUID | NOT NULL | — | — |
| compensation_band_id | UUID | NULL | — | — |
| effective_from | DATE | NOT NULL | — | — |
| effective_to | DATE | NULL | — | — |
| base_salary | NUMERIC(12,2) | NOT NULL | — | CHECK (base_salary >= 0) |
| currency | CHAR(3) | NOT NULL | — | — |
| reason | TEXT | NULL | — | — |
| status | VARCHAR(20) | NOT NULL | 'Draft' | CHECK (status IN ('Draft','Approved','Superseded')) |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**status column:** DB-level enum. Allowed values: `Draft`, `Approved`, `Superseded`.

**Primary Key:** `salary_revision_id`

**Unique Constraints:** None (no `(tenant_id, salary_revision_id)` unique constraint).

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_salary_revisions_employee | (tenant_id, employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT |
| fk_salary_revisions_band | (tenant_id, compensation_band_id) | compensation_bands(tenant_id, compensation_band_id) | CASCADE | RESTRICT |

**Note (migration 014):** Both FKs upgraded from bare single-column to compound `(tenant_id, entity_id)` — DG-002 fix.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_salary_revisions_tenant_id | (tenant_id) |
| idx_salary_revisions_employee_id | (employee_id) |
| idx_salary_revisions_tenant_status | (tenant_id, status) |
| idx_salary_revisions_effective_from | (employee_id, effective_from DESC) |

---

### Table: `benefits_plans`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| benefits_plan_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY (pk_benefits_plans) |
| code | VARCHAR(30) | NOT NULL | — | — |
| name | VARCHAR(150) | NOT NULL | — | — |
| plan_type | VARCHAR(50) | NOT NULL | — | No CHECK constraint — TBD – REQUIRES VERIFICATION |
| employer_contribution | NUMERIC(12,2) | NOT NULL | 0.00 | — |
| employee_contribution | NUMERIC(12,2) | NOT NULL | 0.00 | — |
| currency | CHAR(3) | NOT NULL | 'PKR' | — |
| status | VARCHAR(20) | NOT NULL | 'Draft' | CHECK (status IN ('Draft','Active','Inactive','Archived')) |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**status column:** DB-level enum. Allowed values: `Draft`, `Active`, `Inactive`, `Archived`.

**plan_type:** No CHECK constraint — allowed values are TBD – REQUIRES VERIFICATION.

**Primary Key:** `benefits_plan_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_benefits_plans_tenant_code | (tenant_id, code) |

**Foreign Keys:** None.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_benefits_plans_tenant_id | (tenant_id) |
| idx_benefits_plans_tenant_status | (tenant_id, status) |

---

### Table: `benefits_enrollments`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| benefits_enrollment_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY (pk_benefits_enrollments) |
| employee_id | UUID | NOT NULL | — | — |
| benefits_plan_id | UUID | NOT NULL | — | — |
| employee_contribution | NUMERIC(12,2) | NOT NULL | 0.00 | — |
| employer_contribution | NUMERIC(12,2) | NOT NULL | 0.00 | — |
| effective_from | DATE | NOT NULL | — | — |
| effective_to | DATE | NULL | — | — |
| status | VARCHAR(20) | NOT NULL | 'Draft' | CHECK (status IN ('Draft','Active','Cancelled','Expired')) |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**status column:** DB-level enum. Allowed values: `Draft`, `Active`, `Cancelled`, `Expired`.

**Primary Key:** `benefits_enrollment_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_benefits_enrollments_active | (tenant_id, employee_id, benefits_plan_id, effective_from) |

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_benefits_enrollments_employee | (tenant_id, employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT |
| fk_benefits_enrollments_plan | (tenant_id, benefits_plan_id) | benefits_plans(tenant_id, benefits_plan_id) | CASCADE | RESTRICT |

**Note (migration 014):** Both FKs upgraded from bare single-column to compound `(tenant_id, entity_id)` — DG-002 fix.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_benefits_enrollments_tenant_id | (tenant_id) |
| idx_benefits_enrollments_employee_id | (employee_id) |
| idx_benefits_enrollments_plan_id | (benefits_plan_id) |
| idx_benefits_enrollments_tenant_status | (tenant_id, status) |

---

### Table: `allowances`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| allowance_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY (pk_allowances) |
| employee_id | UUID | NOT NULL | — | — |
| code | VARCHAR(60) | NOT NULL | — | — |
| amount | NUMERIC(12,2) | NOT NULL | — | CHECK (amount >= 0) |
| currency | CHAR(3) | NOT NULL | 'PKR' | — |
| frequency | VARCHAR(20) | NOT NULL | 'Monthly' | CHECK (frequency IN ('Monthly','OneTime','Quarterly','Annual')) |
| effective_from | DATE | NOT NULL | — | — |
| effective_to | DATE | NULL | — | — |
| status | VARCHAR(20) | NOT NULL | 'Draft' | CHECK (status IN ('Draft','Active','Inactive','Archived')) |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**frequency column:** DB-level enum. Allowed values: `Monthly`, `OneTime`, `Quarterly`, `Annual`.

**status column:** DB-level enum. Allowed values: `Draft`, `Active`, `Inactive`, `Archived`.

**Primary Key:** `allowance_id`

**Unique Constraints:** None (no `(tenant_id, allowance_id)` unique constraint).

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_allowances_employee | (tenant_id, employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT |

**Note (migration 014):** FK upgraded from bare `(employee_id)` to compound `(tenant_id, employee_id)` — DG-002 fix.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_allowances_tenant_id | (tenant_id) |
| idx_allowances_employee_id | (employee_id) |
| idx_allowances_tenant_status | (tenant_id, status) |
| idx_allowances_employee_effective | (employee_id, effective_from DESC) |

---

## Migration 013 — `013_travel_domain.sql`

**Purpose:** Creates the travel domain tables for employee travel requests and itinerary segments. Feature status is PLANNED per `FEATURE_SCOPE.md`. Wrapped in `BEGIN`/`COMMIT`. FKs follow the same non-scoped single-column pattern as migration 012.

---

### Table: `travel_requests`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| travel_request_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY (pk_travel_requests) |
| employee_id | UUID | NOT NULL | — | — |
| manager_employee_id | UUID | NULL | — | — |
| purpose | VARCHAR(240) | NOT NULL | — | — |
| destination | VARCHAR(240) | NOT NULL | — | — |
| start_date | DATE | NOT NULL | — | — |
| end_date | DATE | NOT NULL | — | CHECK (end_date >= start_date) |
| status | VARCHAR(20) | NOT NULL | 'Draft' | CHECK (status IN ('Draft','Submitted','Approved','Rejected','Booked','Completed','Cancelled')) |
| workflow_id | UUID | NULL | — | — |
| estimated_cost | NUMERIC(12,2) | NULL | — | CHECK (estimated_cost >= 0) |
| currency | CHAR(3) | NOT NULL | 'PKR' | — |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**status column:** DB-level enum. Allowed values: `Draft`, `Submitted`, `Approved`, `Rejected`, `Booked`, `Completed`, `Cancelled`. State machine documented in migration comments: Draft → Submitted → Approved/Rejected; Approved → Booked → Completed; Draft/Submitted/Approved/Booked → Cancelled.

**Primary Key:** `travel_request_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_travel_requests_tenant_id | (tenant_id, travel_request_id) |

**Note (migration 014):** `uq_travel_requests_tenant_id` added by migration 014 §2 so that downstream compound FKs can reference `(tenant_id, travel_request_id)`.

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_travel_requests_employee | (tenant_id, employee_id) | employees(tenant_id, employee_id) | CASCADE | RESTRICT |
| fk_travel_requests_manager | (tenant_id, manager_employee_id) | employees(tenant_id, employee_id) | CASCADE | SET NULL |

**Note (migration 014):** Both FKs upgraded from bare single-column to compound `(tenant_id, entity_id)` — DG-002 fix.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_travel_requests_tenant_id | (tenant_id) |
| idx_travel_requests_employee_id | (employee_id) |
| idx_travel_requests_manager_id | (manager_employee_id) |
| idx_travel_requests_tenant_status | (tenant_id, status) |
| idx_travel_requests_start_date | (tenant_id, start_date) |

---

### Table: `travel_itinerary_segments`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| segment_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY (pk_travel_itinerary_segments) |
| travel_request_id | UUID | NOT NULL | — | — |
| segment_type | VARCHAR(30) | NOT NULL | — | CHECK (segment_type IN ('Flight','Hotel','Car','Train','Other')) |
| departure_city | VARCHAR(120) | NOT NULL | — | — |
| arrival_city | VARCHAR(120) | NOT NULL | — | — |
| departure_at | TIMESTAMPTZ | NOT NULL | — | — |
| arrival_at | TIMESTAMPTZ | NOT NULL | — | CHECK (arrival_at >= departure_at) |
| provider_name | VARCHAR(120) | NULL | — | — |
| booking_reference | VARCHAR(80) | NULL | — | — |
| cost | NUMERIC(12,2) | NULL | — | CHECK (cost >= 0) |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**segment_type column:** DB-level enum. Allowed values: `Flight`, `Hotel`, `Car`, `Train`, `Other`.

**Primary Key:** `segment_id`

**Unique Constraints:** None (no `(tenant_id, segment_id)` unique constraint).

**Foreign Keys:**
| Constraint Name | Columns | References | On Update | On Delete |
|----------------|---------|-----------|-----------|-----------|
| fk_travel_segments_request | (tenant_id, travel_request_id) | travel_requests(tenant_id, travel_request_id) | — | CASCADE |

**Note (migration 014):** FK upgraded from bare `(travel_request_id)` to compound `(tenant_id, travel_request_id)` — DG-002 fix.

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_travel_segments_tenant_id | (tenant_id) |
| idx_travel_segments_request_id | (travel_request_id) |
| idx_travel_segments_departure_at | (travel_request_id, departure_at) |

---

## Migration 014 — `014_schema_integrity_fixes.sql`

**Purpose:** Fixes two CRITICAL gaps discovered during Phase 2 Backend Authority Capture: DG-001 (missing `grade_bands` table) and DG-002 (bare single-column FKs in compensation and travel domains that violated the MULTI-TENANCY INVARIANT). This migration is idempotent — all operations use `IF NOT EXISTS` / `IF EXISTS` guards.

**Evidence source for grade_bands schema:** `backend/docs/canon/data-architecture.md` line 94–105 (primary canon), `backend/docs/canon/domain-model.md` line 142 (entity/owner), `backend/services/employee-service/org.model.ts` (GradeBand interface), `backend/services/employee-service/domain-seed.ts` (seedGradeBands). Status values follow migration 012 peer pattern (Draft included) over org.model.ts OrgEntityStatus (Draft absent).

---

### Table: `grade_bands`

| Column | Type | Nullable | Default | Inline Constraint |
|--------|------|----------|---------|-------------------|
| tenant_id | VARCHAR(80) | NOT NULL | — | — |
| grade_band_id | UUID | NOT NULL | uuid_generate_v4() | PRIMARY KEY (pk_grade_bands) |
| name | VARCHAR(150) | NOT NULL | — | — |
| code | VARCHAR(30) | NOT NULL | — | — |
| family | VARCHAR(100) | NULL | — | — |
| level_order | INTEGER | NOT NULL | 0 | — |
| status | VARCHAR(20) | NOT NULL | 'Active' | CHECK (status IN ('Draft','Active','Inactive','Archived')) |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | — |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | — |

**status column:** DB-level enum. Allowed values: `Draft`, `Active`, `Inactive`, `Archived`. Anchored by migration 012 peer pattern (compensation_bands, benefits_plans, allowances all include Draft) and `backend/docs/canon/data-architecture.md` line 103. `org.model.ts` OrgEntityStatus omits Draft — DB migration pattern takes precedence.

**Primary Key:** `grade_band_id`

**Unique Constraints:**
| Constraint Name | Columns |
|----------------|---------|
| uq_grade_bands_tenant_id | (tenant_id, grade_band_id) |
| uq_grade_bands_tenant_code | (tenant_id, code) |

**Foreign Keys:** None (root reference table).

**Indexes:**
| Index Name | Columns |
|-----------|---------|
| idx_grade_bands_tenant_id | (tenant_id) |
| idx_grade_bands_tenant_status | (tenant_id, status) |

**Gap resolution:** DG-001 — table was missing from migrations 001–013 despite being FK-referenced by `compensation_bands`. Added here as a new migration per the "documentation-blocking defect" exception in `PHASE 2 – BACKEND AUTHORITY CAPTURE.md`.
