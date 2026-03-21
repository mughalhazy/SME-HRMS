# Data Architecture

## Overview
This document maps the canonical domain model to a relational data architecture for SME-HRMS.

- Primary keys use `UUID` unless a provider-specific external identifier is explicitly stored as an attribute.
- Operational timestamps use `TIMESTAMPTZ` in UTC.
- Business dates use `DATE`.
- Monetary values use `NUMERIC(12,2)`.
- Domain enums are modeled with constrained text (`CHECK`) or database enums.
- Cross-service integration uses events and read models rather than cross-service database joins.
- Event publication should be implemented with an outbox table or equivalent transactional mechanism.

## Core workforce tables

### Table: `departments`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| department_id | UUID | No | PK | Primary identifier. |
| name | VARCHAR(150) | No | UQ | Unique department name. |
| code | VARCHAR(30) | No | UQ | Unique short code. |
| description | TEXT | Yes |  | Optional details. |
| head_employee_id | UUID | Yes | FK | References `employees.employee_id`; nullable to avoid circular create dependency. |
| status | VARCHAR(20) | No |  | `Proposed`, `Active`, `Inactive`, `Archived`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

**Indexes**
- `pk_departments (department_id)`
- `uq_departments_name (name)`
- `uq_departments_code (code)`
- `idx_departments_head_employee_id (head_employee_id)`
- `idx_departments_status (status)`


### Table: `business_units`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| business_unit_id | UUID | No | PK | Primary identifier. |
| name | VARCHAR(150) | No | UQ | Unique business-unit name. |
| code | VARCHAR(30) | No | UQ | Unique code. |
| parent_business_unit_id | UUID | Yes | FK | Self-reference for hierarchy. |
| leader_employee_id | UUID | Yes | FK | Optional employee leader. |
| status | VARCHAR(20) | No |  | `Draft`, `Active`, `Inactive`, `Archived`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

### Table: `legal_entities`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| legal_entity_id | UUID | No | PK | Primary identifier. |
| name | VARCHAR(150) | No | UQ | Legal-entity name. |
| code | VARCHAR(30) | No | UQ | Unique code. |
| registration_number | VARCHAR(80) | Yes |  | Registration reference. |
| tax_identifier | VARCHAR(80) | Yes |  | Tax identifier. |
| business_unit_id | UUID | Yes | FK | References `business_units.business_unit_id`. |
| status | VARCHAR(20) | No |  | `Draft`, `Active`, `Inactive`, `Archived`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

### Table: `locations`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| location_id | UUID | No | PK | Primary identifier. |
| name | VARCHAR(150) | No | UQ | Location name. |
| code | VARCHAR(30) | No | UQ | Unique code. |
| country_code | CHAR(2) | No |  | ISO country code. |
| timezone | VARCHAR(80) | No |  | IANA timezone. |
| legal_entity_id | UUID | Yes | FK | References `legal_entities.legal_entity_id`. |
| status | VARCHAR(20) | No |  | `Draft`, `Active`, `Inactive`, `Archived`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

### Table: `cost_centers`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| cost_center_id | UUID | No | PK | Primary identifier. |
| name | VARCHAR(150) | No | UQ | Cost-center name. |
| code | VARCHAR(30) | No | UQ | Unique code. |
| business_unit_id | UUID | Yes | FK | References `business_units.business_unit_id`. |
| department_id | UUID | Yes | FK | References `departments.department_id`. |
| legal_entity_id | UUID | Yes | FK | References `legal_entities.legal_entity_id`. |
| manager_employee_id | UUID | Yes | FK | Optional cost-center owner. |
| status | VARCHAR(20) | No |  | `Draft`, `Active`, `Inactive`, `Archived`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

### Table: `grade_bands`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| grade_band_id | UUID | No | PK | Primary identifier. |
| name | VARCHAR(80) | No | UQ | Display name. |
| code | VARCHAR(30) | No | UQ | Unique code. |
| family | VARCHAR(80) | Yes |  | Optional band family. |
| level_order | INTEGER | No |  | Sort order for ladder progression. |
| status | VARCHAR(20) | No |  | `Draft`, `Active`, `Inactive`, `Archived`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

### Table: `job_positions`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| job_position_id | UUID | No | PK | Primary identifier. |
| title | VARCHAR(150) | No |  | Position title. |
| code | VARCHAR(30) | No | UQ | Unique code. |
| department_id | UUID | No | FK | References `departments.department_id`. |
| business_unit_id | UUID | Yes | FK | References `business_units.business_unit_id`. |
| legal_entity_id | UUID | Yes | FK | References `legal_entities.legal_entity_id`. |
| location_id | UUID | Yes | FK | References `locations.location_id`. |
| grade_band_id | UUID | Yes | FK | References `grade_bands.grade_band_id`. |
| role_id | UUID | Yes | FK | References `roles.role_id`. |
| reports_to_position_id | UUID | Yes | FK | Self-reference for position hierarchy. |
| default_cost_center_id | UUID | Yes | FK | References `cost_centers.cost_center_id`. |
| status | VARCHAR(20) | No |  | `Draft`, `Active`, `Inactive`, `Archived`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

### Table: `roles`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| role_id | UUID | No | PK | Primary identifier. |
| title | VARCHAR(150) | No |  | Role title. |
| level | VARCHAR(50) | Yes |  | Optional grade/band. |
| description | TEXT | Yes |  | Optional responsibilities summary. |
| employment_category | VARCHAR(20) | No |  | `Staff`, `Manager`, `Executive`, `Contractor`. |
| status | VARCHAR(20) | No |  | `Draft`, `Active`, `Inactive`, `Archived`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

**Indexes**
- `pk_roles (role_id)`
- `idx_roles_title (title)`
- `idx_roles_status (status)`

### Table: `employees`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| employee_id | UUID | No | PK | Primary identifier. |
| employee_number | VARCHAR(40) | No | UQ | Human-readable employee code. |
| first_name | VARCHAR(100) | No |  | Given or preferred name. |
| last_name | VARCHAR(100) | No |  | Family name. |
| email | VARCHAR(255) | No | UQ | Work email. |
| phone | VARCHAR(30) | Yes |  | Optional contact number. |
| hire_date | DATE | No |  | Employment start date. |
| employment_type | VARCHAR(20) | No |  | `FullTime`, `PartTime`, `Contract`, `Intern`. |
| status | VARCHAR(20) | No |  | `Draft`, `Active`, `OnLeave`, `Suspended`, `Terminated`. |
| department_id | UUID | No | FK | References `departments.department_id`. |
| role_id | UUID | No | FK | References `roles.role_id`. |
| manager_employee_id | UUID | Yes | FK | Self-reference to `employees.employee_id`. |
| business_unit_id | UUID | Yes | FK | References `business_units.business_unit_id`. |
| legal_entity_id | UUID | Yes | FK | References `legal_entities.legal_entity_id`. |
| location_id | UUID | Yes | FK | References `locations.location_id`. |
| cost_center_id | UUID | Yes | FK | References `cost_centers.cost_center_id`. |
| job_position_id | UUID | Yes | FK | References `job_positions.job_position_id`. |
| grade_band_id | UUID | Yes | FK | References `grade_bands.grade_band_id`. |
| matrix_manager_employee_ids | JSONB | No |  | Array of matrix manager employee IDs. |
| cost_allocations | JSONB | No |  | Cost-center split allocations that total 100%. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

**Indexes**
- `pk_employees (employee_id)`
- `uq_employees_employee_number (employee_number)`
- `uq_employees_email (email)`
- `idx_employees_department_id (department_id)`
- `idx_employees_role_id (role_id)`
- `idx_employees_manager_employee_id (manager_employee_id)`
- `idx_employees_business_unit_id (business_unit_id)`
- `idx_employees_legal_entity_id (legal_entity_id)`
- `idx_employees_location_id (location_id)`
- `idx_employees_cost_center_id (cost_center_id)`
- `idx_employees_job_position_id (job_position_id)`
- `idx_employees_grade_band_id (grade_band_id)`
- `idx_employees_status (status)`

### Table: `performance_reviews`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| performance_review_id | UUID | No | PK | Primary identifier. |
| employee_id | UUID | No | FK | Reviewed employee. |
| reviewer_employee_id | UUID | No | FK | Reviewer employee. |
| review_period_start | DATE | No |  | Review period start. |
| review_period_end | DATE | No |  | `review_period_end >= review_period_start`. |
| overall_rating | NUMERIC(2,1) | Yes |  | Optional score, typically `1.0-5.0`. |
| strengths | TEXT | Yes |  | Strength narrative. |
| improvement_areas | TEXT | Yes |  | Development areas. |
| goals_next_period | TEXT | Yes |  | Goals for next cycle. |
| status | VARCHAR(20) | No |  | `Draft`, `Submitted`, `Finalized`. |
| submitted_at | TIMESTAMPTZ | Yes |  | Reviewer submission time. |
| finalized_at | TIMESTAMPTZ | Yes |  | Review finalization time. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

**Indexes**
- `pk_performance_reviews (performance_review_id)`
- `idx_performance_reviews_employee_id (employee_id)`
- `idx_performance_reviews_reviewer_employee_id (reviewer_employee_id)`
- `uq_performance_reviews_cycle (employee_id, review_period_start, review_period_end)`
- `idx_performance_reviews_status (status)`

## Time, leave, and payroll tables

### Table: `attendance_records`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| attendance_id | UUID | No | PK | Primary identifier. |
| employee_id | UUID | No | FK | References `employees.employee_id`. |
| attendance_date | DATE | No |  | Attendance calendar date. |
| check_in_time | TIMESTAMPTZ | Yes |  | Actual first check-in time. |
| check_out_time | TIMESTAMPTZ | Yes |  | Actual final check-out time. |
| total_hours | NUMERIC(5,2) | Yes |  | Calculated work duration. |
| attendance_status | VARCHAR(20) | No |  | `Present`, `Absent`, `Late`, `HalfDay`, `Holiday`. |
| source | VARCHAR(20) | Yes |  | `Manual`, `Biometric`, `APIImport`. |
| record_state | VARCHAR(20) | No |  | `Captured`, `Validated`, `Approved`, `Locked`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

**Indexes**
- `pk_attendance_records (attendance_id)`
- `idx_attendance_records_employee_id (employee_id)`
- `uq_attendance_records_employee_date (employee_id, attendance_date)`
- `idx_attendance_records_status (attendance_status)`
- `idx_attendance_records_record_state (record_state)`

### Table: `leave_requests`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| leave_request_id | UUID | No | PK | Primary identifier. |
| employee_id | UUID | No | FK | References `employees.employee_id`. |
| leave_type | VARCHAR(20) | No |  | `Annual`, `Sick`, `Casual`, `Unpaid`, `Other`. |
| start_date | DATE | No |  | Requested start date. |
| end_date | DATE | No |  | `end_date >= start_date`. |
| total_days | NUMERIC(4,1) | No |  | Derived duration. |
| reason | TEXT | Yes |  | Optional explanation. |
| approver_employee_id | UUID | Yes | FK | References `employees.employee_id`. |
| status | VARCHAR(20) | No |  | `Draft`, `Submitted`, `Approved`, `Rejected`, `Cancelled`. |
| submitted_at | TIMESTAMPTZ | Yes |  | Submission timestamp. |
| decision_at | TIMESTAMPTZ | Yes |  | Decision timestamp. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

**Indexes**
- `pk_leave_requests (leave_request_id)`
- `idx_leave_requests_employee_id (employee_id)`
- `idx_leave_requests_approver_employee_id (approver_employee_id)`
- `idx_leave_requests_status (status)`
- `idx_leave_requests_date_range (start_date, end_date)`

### Table: `payroll_records`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| payroll_record_id | UUID | No | PK | Primary identifier. |
| employee_id | UUID | No | FK | References `employees.employee_id`. |
| pay_period_start | DATE | No |  | Period start date. |
| pay_period_end | DATE | No |  | `pay_period_end >= pay_period_start`. |
| base_salary | NUMERIC(12,2) | No |  | Fixed salary. |
| allowances | NUMERIC(12,2) | No |  | Additional earnings; default `0.00`. |
| deductions | NUMERIC(12,2) | No |  | Deductions/taxes; default `0.00`. |
| overtime_pay | NUMERIC(12,2) | No |  | Overtime component; default `0.00`. |
| gross_pay | NUMERIC(12,2) | No |  | Calculated gross pay. |
| net_pay | NUMERIC(12,2) | No |  | Final payout. |
| currency | CHAR(3) | No |  | ISO-4217 currency code. |
| payment_date | DATE | Yes |  | Actual payment date. |
| status | VARCHAR(20) | No |  | `Draft`, `Processed`, `Paid`, `Cancelled`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

**Indexes**
- `pk_payroll_records (payroll_record_id)`
- `idx_payroll_records_employee_id (employee_id)`
- `uq_payroll_records_employee_period (employee_id, pay_period_start, pay_period_end)`
- `idx_payroll_records_status (status)`
- `idx_payroll_records_payment_date (payment_date)`

## Hiring tables

### Table: `job_postings`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| job_posting_id | UUID | No | PK | Primary identifier. |
| title | VARCHAR(200) | No |  | Posting title. |
| department_id | UUID | No | FK | References `departments.department_id`. |
| role_id | UUID | Yes | FK | References `roles.role_id`. |
| employment_type | VARCHAR(20) | No |  | `FullTime`, `PartTime`, `Contract`, `Intern`. |
| location | VARCHAR(200) | Yes |  | Work location. |
| description | TEXT | No |  | Responsibilities and requirements. |
| openings_count | INTEGER | No |  | Must be `>= 1`. |
| posting_date | DATE | No |  | Publication date. |
| closing_date | DATE | Yes |  | Optional close date, must be on/after `posting_date`. |
| status | VARCHAR(20) | No |  | `Draft`, `Open`, `OnHold`, `Closed`, `Filled`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

**Indexes**
- `pk_job_postings (job_posting_id)`
- `idx_job_postings_department_id (department_id)`
- `idx_job_postings_role_id (role_id)`
- `idx_job_postings_status (status)`
- `idx_job_postings_posting_date (posting_date)`

### Table: `candidates`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| candidate_id | UUID | No | PK | Primary identifier. |
| job_posting_id | UUID | No | FK | References `job_postings.job_posting_id`. |
| first_name | VARCHAR(100) | No |  | Candidate first name. |
| last_name | VARCHAR(100) | No |  | Candidate last name. |
| email | VARCHAR(255) | No |  | Candidate email. |
| phone | VARCHAR(30) | Yes |  | Optional contact number. |
| resume_url | TEXT | Yes |  | Link or object-store path. |
| source | VARCHAR(20) | Yes |  | `Referral`, `JobBoard`, `CareerSite`, `Agency`, `LinkedIn`, `Other`. |
| source_candidate_id | VARCHAR(100) | Yes |  | External provider candidate identifier. |
| source_profile_url | TEXT | Yes |  | External profile URL. |
| application_date | DATE | No |  | Application submission date. |
| status | VARCHAR(20) | No |  | `Applied`, `Screening`, `Interviewing`, `Offered`, `Hired`, `Rejected`, `Withdrawn`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

**Indexes**
- `pk_candidates (candidate_id)`
- `idx_candidates_job_posting_id (job_posting_id)`
- `uq_candidates_posting_email (job_posting_id, email)`
- `idx_candidates_status (status)`
- `idx_candidates_application_date (application_date)`
- `idx_candidates_source_candidate_id (source_candidate_id)`

### Table: `interviews`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| interview_id | UUID | No | PK | Primary identifier. |
| candidate_id | UUID | No | FK | References `candidates.candidate_id`. |
| interview_type | VARCHAR(20) | No |  | `PhoneScreen`, `Technical`, `Behavioral`, `Panel`, `Final`. |
| scheduled_start | TIMESTAMPTZ | No |  | Planned start time. |
| scheduled_end | TIMESTAMPTZ | No |  | `scheduled_end > scheduled_start`. |
| location_or_link | TEXT | Yes |  | Meeting location or URL. |
| interviewer_employee_ids | UUID[] | Yes |  | Optional panel members as denormalized array. |
| feedback_summary | TEXT | Yes |  | Consolidated feedback. |
| recommendation | VARCHAR(20) | Yes |  | `StrongHire`, `Hire`, `NoHire`, `Undecided`. |
| google_calendar_event_id | VARCHAR(255) | Yes |  | External Google Calendar event ID. |
| google_calendar_event_link | TEXT | Yes |  | External calendar event URL. |
| status | VARCHAR(20) | No |  | `Scheduled`, `Completed`, `Cancelled`, `NoShow`. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

**Indexes**
- `pk_interviews (interview_id)`
- `idx_interviews_candidate_id (candidate_id)`
- `idx_interviews_schedule (scheduled_start, scheduled_end)`
- `idx_interviews_status (status)`
- `idx_interviews_google_calendar_event_id (google_calendar_event_id)`

## Access-control tables

### Table: `user_accounts`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| user_id | UUID | No | PK | Primary identifier. |
| employee_id | UUID | Yes | FK | References `employees.employee_id`; nullable for non-workforce/service users. |
| username | VARCHAR(120) | No | UQ | Unique login name. |
| email | VARCHAR(255) | No | UQ | Unique identity email. |
| password_hash | TEXT | No |  | Credential hash or external subject reference. |
| identity_provider | VARCHAR(20) | No |  | `Local`, `SSO`, `OAuth`. |
| status | VARCHAR(20) | No |  | `Invited`, `Active`, `Locked`, `Disabled`. |
| last_login_at | TIMESTAMPTZ | Yes |  | Most recent successful login. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

**Indexes**
- `pk_user_accounts (user_id)`
- `uq_user_accounts_username (username)`
- `uq_user_accounts_email (email)`
- `idx_user_accounts_employee_id (employee_id)`
- `idx_user_accounts_status (status)`

### Table: `role_bindings`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| binding_id | UUID | No | PK | Primary identifier. |
| user_id | UUID | No | FK | References `user_accounts.user_id`. |
| role_name | VARCHAR(50) | No |  | Canonical role name. |
| scope_type | VARCHAR(20) | No |  | `Global`, `Department`, `Employee`, `Service`, `Requisition`. |
| scope_id | VARCHAR(100) | Yes |  | Scoped object identifier. |
| effective_from | TIMESTAMPTZ | No |  | Binding start timestamp. |
| effective_to | TIMESTAMPTZ | Yes |  | Optional expiry. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

**Indexes**
- `pk_role_bindings (binding_id)`
- `idx_role_bindings_user_id (user_id)`
- `idx_role_bindings_scope (scope_type, scope_id)`
- `idx_role_bindings_role_name (role_name)`

### Table: `permission_policies`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| policy_id | UUID | No | PK | Primary identifier. |
| capability_id | VARCHAR(30) | No |  | Stable capability identifier. |
| role_name | VARCHAR(50) | No |  | Role this rule applies to. |
| resource_type | VARCHAR(80) | No |  | Protected resource family. |
| scope_rule | TEXT | No |  | Scope evaluation rule/expression. |
| effect | VARCHAR(10) | No |  | `Allow`, `Deny`. |
| version | INTEGER | No |  | Monotonic policy version. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

**Indexes**
- `pk_permission_policies (policy_id)`
- `idx_permission_policies_capability_id (capability_id)`
- `idx_permission_policies_role_name (role_name)`
- `uq_permission_policies_versioned_rule (capability_id, role_name, version)`

### Table: `sessions`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| session_id | UUID | No | PK | Primary identifier. |
| user_id | UUID | No | FK | References `user_accounts.user_id`. |
| access_token_jti | VARCHAR(255) | No | UQ | Token identifier. |
| client_type | VARCHAR(20) | No |  | `Web`, `Mobile`, `Service`. |
| ip_address | VARCHAR(64) | Yes |  | Source IP. |
| user_agent | TEXT | Yes |  | Client user agent. |
| started_at | TIMESTAMPTZ | No |  | Session start. |
| expires_at | TIMESTAMPTZ | No |  | Session expiry. |
| revoked_at | TIMESTAMPTZ | Yes |  | Revocation timestamp. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

**Indexes**
- `pk_sessions (session_id)`
- `uq_sessions_access_token_jti (access_token_jti)`
- `idx_sessions_user_id (user_id)`
- `idx_sessions_expires_at (expires_at)`
- `idx_sessions_revoked_at (revoked_at)`

### Table: `refresh_tokens`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| refresh_token_id | UUID | No | PK | Primary identifier. |
| session_id | UUID | No | FK | References `sessions.session_id`. |
| user_id | UUID | No | FK | References `user_accounts.user_id`. |
| token_hash | TEXT | No |  | Stored refresh token hash. |
| issued_at | TIMESTAMPTZ | No |  | Issue timestamp. |
| expires_at | TIMESTAMPTZ | No |  | Expiry timestamp. |
| rotated_from_token_id | UUID | Yes | FK | Self-reference to previous refresh token in chain. |
| revoked_at | TIMESTAMPTZ | Yes |  | Revocation timestamp. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

**Indexes**
- `pk_refresh_tokens (refresh_token_id)`
- `idx_refresh_tokens_session_id (session_id)`
- `idx_refresh_tokens_user_id (user_id)`
- `idx_refresh_tokens_expires_at (expires_at)`

## Notification tables

### Table: `notification_templates`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| template_id | UUID | No | PK | Primary identifier. |
| code | VARCHAR(100) | No | UQ | Stable template code. |
| channel | VARCHAR(20) | No |  | `Email`, `SMS`, `Push`, `InApp`. |
| subject_template | TEXT | Yes |  | Subject-capable channels only. |
| body_template | TEXT | No |  | Message body template. |
| locale | VARCHAR(10) | No |  | Locale code such as `en-US`. |
| is_active | BOOLEAN | No |  | Whether template is usable. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

**Indexes**
- `pk_notification_templates (template_id)`
- `uq_notification_templates_code (code)`
- `idx_notification_templates_channel (channel)`
- `idx_notification_templates_active (is_active)`

### Table: `notification_messages`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| message_id | UUID | No | PK | Primary identifier. |
| template_id | UUID | Yes | FK | References `notification_templates.template_id`. |
| subject_type | VARCHAR(40) | No |  | `Employee`, `Candidate`, `UserAccount`, `Service`. |
| subject_id | VARCHAR(100) | No |  | Subject identifier. |
| channel | VARCHAR(20) | No |  | `Email`, `SMS`, `Push`, `InApp`. |
| destination | TEXT | No |  | Rendered destination. |
| payload | JSONB | No |  | Resolved data payload. |
| status | VARCHAR(20) | No |  | `Queued`, `Sent`, `Failed`, `Suppressed`. |
| queued_at | TIMESTAMPTZ | No |  | Queue timestamp. |
| sent_at | TIMESTAMPTZ | Yes |  | Delivery completion timestamp. |
| failure_reason | TEXT | Yes |  | Failure or suppression summary. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

**Indexes**
- `pk_notification_messages (message_id)`
- `idx_notification_messages_subject (subject_type, subject_id)`
- `idx_notification_messages_status (status)`
- `idx_notification_messages_channel (channel)`
- `idx_notification_messages_template_id (template_id)`

### Table: `delivery_attempts`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| delivery_attempt_id | UUID | No | PK | Primary identifier. |
| message_id | UUID | No | FK | References `notification_messages.message_id`. |
| provider_name | VARCHAR(100) | No |  | Delivery provider. |
| provider_message_id | VARCHAR(255) | Yes |  | Provider-assigned identifier. |
| attempt_number | INTEGER | No |  | Sequential retry number starting at `1`. |
| attempted_at | TIMESTAMPTZ | No |  | Attempt timestamp. |
| outcome | VARCHAR(20) | No |  | `Sent`, `Failed`, `Deferred`. |
| response_code | VARCHAR(50) | Yes |  | Provider response code. |
| response_message | TEXT | Yes |  | Provider response detail. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |

**Indexes**
- `pk_delivery_attempts (delivery_attempt_id)`
- `idx_delivery_attempts_message_id (message_id)`
- `uq_delivery_attempts_message_attempt (message_id, attempt_number)`
- `idx_delivery_attempts_outcome (outcome)`

### Table: `notification_preferences`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| preference_id | UUID | No | PK | Primary identifier. |
| subject_type | VARCHAR(40) | No |  | `Employee`, `Candidate`, `UserAccount`, `Service`. |
| subject_id | VARCHAR(100) | No |  | Preference owner identifier. |
| topic_code | VARCHAR(100) | No |  | Notification topic key. |
| email_enabled | BOOLEAN | No |  | Email channel preference. |
| sms_enabled | BOOLEAN | No |  | SMS channel preference. |
| push_enabled | BOOLEAN | No |  | Push channel preference. |
| in_app_enabled | BOOLEAN | No |  | In-app preference. |
| quiet_hours | JSONB | Yes |  | Optional quiet-hours object. |
| created_at | TIMESTAMPTZ | No |  | Creation timestamp. |
| updated_at | TIMESTAMPTZ | No |  | Last update timestamp. |

**Indexes**
- `pk_notification_preferences (preference_id)`
- `uq_notification_preferences_subject_topic (subject_type, subject_id, topic_code)`
- `idx_notification_preferences_subject (subject_type, subject_id)`

## Integration and eventing tables

### Table: `event_outbox`

| Column | Type | Null | Key | Constraints / Notes |
|---|---|---:|---|---|
| event_id | UUID | No | PK | Primary identifier. |
| aggregate_type | VARCHAR(80) | No |  | Aggregate/table family. |
| aggregate_id | VARCHAR(100) | No |  | Aggregate identifier. |
| event_name | VARCHAR(120) | No |  | Canonical event name. |
| payload | JSONB | No |  | Event payload. |
| trace_id | VARCHAR(64) | No |  | Correlation identifier. |
| occurred_at | TIMESTAMPTZ | No |  | Business occurrence time. |
| published_at | TIMESTAMPTZ | Yes |  | Broker publish time. |
| failed_attempts | INTEGER | No |  | Default `0`. |
| created_at | TIMESTAMPTZ | No |  | Row creation timestamp. |

**Indexes**
- `pk_event_outbox (event_id)`
- `idx_event_outbox_unpublished (published_at)`
- `idx_event_outbox_aggregate (aggregate_type, aggregate_id)`
- `idx_event_outbox_event_name (event_name)`

## Referential graph summary

- `employees.department_id -> departments.department_id`
- `employees.role_id -> roles.role_id`
- `employees.manager_employee_id -> employees.employee_id`
- `departments.head_employee_id -> employees.employee_id`
- `performance_reviews.employee_id -> employees.employee_id`
- `performance_reviews.reviewer_employee_id -> employees.employee_id`
- `attendance_records.employee_id -> employees.employee_id`
- `leave_requests.employee_id -> employees.employee_id`
- `leave_requests.approver_employee_id -> employees.employee_id`
- `payroll_records.employee_id -> employees.employee_id`
- `job_postings.department_id -> departments.department_id`
- `job_postings.role_id -> roles.role_id`
- `candidates.job_posting_id -> job_postings.job_posting_id`
- `interviews.candidate_id -> candidates.candidate_id`
- `user_accounts.employee_id -> employees.employee_id`
- `role_bindings.user_id -> user_accounts.user_id`
- `sessions.user_id -> user_accounts.user_id`
- `refresh_tokens.session_id -> sessions.session_id`
- `refresh_tokens.user_id -> user_accounts.user_id`
- `refresh_tokens.rotated_from_token_id -> refresh_tokens.refresh_token_id`
- `notification_messages.template_id -> notification_templates.template_id`
- `delivery_attempts.message_id -> notification_messages.message_id`

## Implementation notes
- Apply `ON UPDATE CASCADE` for foreign keys.
- Prefer `ON DELETE RESTRICT` for master entities and `ON DELETE CASCADE` only for strictly dependent operational records where retention policy allows it.
- Maintain all `updated_at` fields through application logic or update triggers.
- Use service-owned schemas or databases in deployment; the model above is canonical logical architecture, not a mandate for a single physical database.
