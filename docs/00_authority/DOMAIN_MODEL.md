# DOMAIN MODEL

Status: Active
Authority Level: Critical
Last Reviewed: 2026-06-15
Owner: Shared

---

## PURPOSE

This is the authoritative domain entity reference. All service implementations must conform to the entity definitions, relationships, and lifecycle states documented here.

**Primary Evidence Sources:**
- `/backend/docs/canon/domain-model.md`
- `/backend/deployment/migrations/001_core_schema.sql` through `013_travel_domain.sql`
- `/backend/docs/canon/service-map.md`

---

## MULTI-TENANCY INVARIANT

Every primary entity table includes:
- `tenant_id VARCHAR(80) NOT NULL`
- Unique constraint: `(tenant_id, [entity]_id)`
- Foreign keys reference `(tenant_id, [entity]_id)` — never `[entity]_id` alone

This is a system-wide constraint. No exceptions.

**Evidence:** `/backend/deployment/migrations/001_core_schema.sql`, `004_persistence_normalization.sql`

**Migration 014 note:** Migrations 012 (`compensation_domain.sql`) and 013 (`travel_domain.sql`) contained bare single-column FKs that violated this invariant — documented as DG-002 in `docs/08_reports/BACKEND_GAP_REGISTER.md`. Migration `014_schema_integrity_fixes.sql` dropped all bare FKs in those domains and replaced them with compound `(tenant_id, entity_id)` FKs, restoring full compliance with this invariant across all tables.

---

## AGGREGATE ROOTS

### TENANT (Root of All Roots)

**Service Owner:** settings-service / auth-service
**Table:** `tenants`

| Field | Type | Notes |
|-------|------|-------|
| tenant_id | VARCHAR(80) PK | Human-readable slug |
| tenant_name | TEXT | Display name |
| slug | TEXT | URL slug |
| status | ENUM | Provisioning, Active, Suspended, Archived |
| primary_country_code | VARCHAR(10) | Determines compliance layer (e.g., PK) |

**Config Table:** `tenant_configs`
| Field | Type | Notes |
|-------|------|-------|
| feature_flags | JSONB | Per-tenant feature enablement |
| leave_policy_refs | JSONB | References to active leave policies |
| payroll_rule_refs | JSONB | References to active payroll rules |
| enabled_locations | JSONB | Active location set |

**Lifecycle:** Provisioning → Active → Suspended → Archived

---

### EMPLOYEE

**Service Owner:** employee-service (port 8001)
**Table:** `employees`

| Field | Type | Notes |
|-------|------|-------|
| employee_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| hire_date | DATE | |
| employment_type | ENUM | Full-time, Part-time, Contract, Intern |
| status | ENUM | See lifecycle below |
| manager_employee_id | UUID FK | Self-referential hierarchy |
| department_id | UUID FK | |
| cost_allocations | JSONB | Cost center split |

**Lifecycle:** Draft → Active → OnLeave → Suspended → Terminated

**Relationships:**
- belongs-to: Department (many-to-one)
- has-manager: Employee (self-referential)
- has-many: AttendanceRecord, LeaveRequest, PayrollRecord
- has-one: UserAccount (auth-service)

---

### DEPARTMENT

**Service Owner:** employee-service (port 8001)
**Table:** `departments`

| Field | Type | Notes |
|-------|------|-------|
| department_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| name | TEXT | |
| code | VARCHAR(20) | Unique per tenant |
| parent_department_id | UUID FK | Self-referential hierarchy |
| head_employee_id | UUID FK | Department head |

**Lifecycle:** Proposed → Active → Inactive → Archived

---

### ROLE (Job Role / Title)

**Service Owner:** employee-service (port 8001)
**Table:** `roles`

| Field | Type | Notes |
|-------|------|-------|
| role_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| title | TEXT | |
| level | INTEGER | Grade level |
| employment_category | ENUM | |
| permissions | JSONB | Role-specific permissions |
| status | ENUM | Draft, Active, Inactive, Archived |

---

### ORGANIZATIONAL STRUCTURE ENTITIES

**Service Owner:** employee-service

| Entity | Table | Purpose |
|--------|-------|---------|
| BusinessUnit | business_units | High-level org grouping above departments |
| LegalEntity | legal_entities | Legal companies within the tenant group |
| Location | locations | Physical/administrative work locations |
| CostCenter | cost_centers | Finance-facing allocation structures |
| GradeBand | grade_bands | Grade/band framework for compensation |
| JobPosition | job_positions | Position hierarchy and structure |

### GRADE BAND

**Service Owner:** employee-service (port 8001) — org structure domain
**Table:** `grade_bands`

| Field | Type | Notes |
|-------|------|-------|
| grade_band_id | UUID PK | Auto-generated |
| tenant_id | VARCHAR(80) NOT NULL | Row-level tenant isolation |
| name | VARCHAR(150) NOT NULL | Display name (e.g., "Senior Engineer") |
| code | VARCHAR(30) NOT NULL | Short identifier, unique per tenant (e.g., "L5") |
| family | VARCHAR(100) NULL | Optional grouping (e.g., "Engineering", "Sales") |
| level_order | INTEGER NOT NULL | Sort order for band hierarchy; lower = more junior; default 0 |
| status | ENUM NOT NULL | See lifecycle; default Active |
| created_at | TIMESTAMPTZ NOT NULL | |
| updated_at | TIMESTAMPTZ NOT NULL | |

**Lifecycle:** Draft → Active → Inactive → Archived

**Unique Constraints:** `(tenant_id, grade_band_id)`, `(tenant_id, code)`

**Relationships:**
- has-many: CompensationBand (one GradeBand → N CompensationBands with compound FK)

**All anchor sources consulted:**
| Source | Content |
|--------|---------|
| `backend/docs/canon/domain-model.md` line 142 | GradeBand — owned by employee-service; canonical entity definition |
| `backend/docs/canon/data-architecture.md` line 94–105 | grade_bands column list (pre-multi-tenancy; no tenant_id) |
| `backend/services/employee-service/org.model.ts` | `GradeBand` TypeScript interface + `OrgEntityStatus` type |
| `backend/services/employee-service/domain-seed.ts` | `seedGradeBands()` — dev-only in-memory seed |
| `backend/deployment/migrations/014_schema_integrity_fixes.sql` §1 | SQL table as created (source of truth for deployed schema) |
| `docs/00_authority/DOMAIN_MODEL.md` MULTI-TENANCY INVARIANT | Drove adding `tenant_id` column absent from canon data-architecture.md |

**Schema source reconciliation (resolved):**

| Field | `data-architecture.md` canon | `org.model.ts` | migration 014 (authoritative) | Rationale |
|-------|------------------------------|----------------|-------------------------------|-----------|
| `tenant_id` | Absent (pre-multi-tenancy doc) | Present | Present | MULTI-TENANCY INVARIANT |
| `name` | VARCHAR(80) | VARCHAR(150) implied | VARCHAR(150) | Matches migration 012 peer pattern |
| `family` | VARCHAR(80) | VARCHAR(100) implied | VARCHAR(100) | More generous; no peer conflict |
| `status` | Draft, Active, Inactive, Archived | Active, Inactive, Archived | **Draft, Active, Inactive, Archived** | Migration 012 peers (compensation_bands, benefits_plans, allowances) all include Draft; DB migration pattern takes precedence over TypeScript type definition |

**Discovery note:** This table was absent from migrations 001–013 (DG-001). Migration 014 was created as a documentation-blocking defect fix. See `docs/08_reports/BACKEND_GAP_REGISTER.md` DG-001 for full resolution record.

---

## OPERATIONAL ENTITIES

### ATTENDANCE RECORD

**Service Owner:** attendance-service (port 8002)
**Table:** `attendance_records`

| Field | Type | Notes |
|-------|------|-------|
| attendance_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| employee_id | UUID FK | References employees |
| attendance_date | DATE | Unique per (tenant_id, employee_id, attendance_date) |
| check_in_time | TIMESTAMPTZ | Nullable |
| check_out_time | TIMESTAMPTZ | Nullable |
| total_hours | NUMERIC(5,2) | |
| attendance_status | ENUM | Present, Absent, Late, HalfDay, Holiday |
| source | ENUM | Manual, Biometric, APIImport |

**Evidence:** `002_workflow_schema.sql`

---

### LEAVE REQUEST

**Service Owner:** leave-service (port 8003)
**Table:** `leave_requests`

| Field | Type | Notes |
|-------|------|-------|
| leave_request_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| employee_id | UUID FK | References employees |
| leave_type | ENUM | Annual, Sick, Casual, Unpaid, Other |
| start_date | DATE | |
| end_date | DATE | Must be >= start_date |
| total_days | NUMERIC(4,1) | |
| reason | TEXT | Nullable |
| approver_employee_id | UUID FK | References employees, nullable |
| status | ENUM | See lifecycle |
| submitted_at | TIMESTAMPTZ | Nullable |
| decision_at | TIMESTAMPTZ | Nullable |

**Lifecycle:** Draft → Submitted → Approved | Rejected | Cancelled

**Evidence:** `002_workflow_schema.sql`

---

### PAYROLL RECORD

**Service Owner:** payroll-service (port 8004)
**Table:** `payroll_records`

| Field | Type | Notes |
|-------|------|-------|
| payroll_record_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| employee_id | UUID FK | Unique per (tenant_id, employee_id, pay_period_start, pay_period_end) |
| pay_period_start | DATE | |
| pay_period_end | DATE | Must be >= pay_period_start |
| base_salary | NUMERIC(12,2) | |
| allowances | NUMERIC(12,2) | Default 0.00 |
| deductions | NUMERIC(12,2) | Default 0.00 |
| overtime_pay | NUMERIC(12,2) | Default 0.00 |
| gross_pay | NUMERIC(12,2) | |
| net_pay | NUMERIC(12,2) | |
| currency | CHAR(3) | |
| payment_date | DATE | Nullable |
| status | ENUM | Draft, Processed, Paid, Cancelled |

**Lifecycle:** Draft → Processed → Paid | Cancelled

**Evidence:** `002_workflow_schema.sql`

---

### JOB POSTING

**Service Owner:** hiring-service (port 8005)
**Table:** `job_postings`

| Field | Type | Notes |
|-------|------|-------|
| job_posting_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| title | VARCHAR(200) | |
| department_id | UUID FK | References departments |
| role_id | UUID FK | References roles, nullable |
| employment_type | ENUM | FullTime, PartTime, Contract, Intern |
| location | VARCHAR(200) | Nullable |
| description | TEXT | |
| openings_count | INTEGER | >= 1 |
| posting_date | DATE | |
| closing_date | DATE | Nullable; if set, must be >= posting_date |
| status | ENUM | Draft, Open, OnHold, Closed, Filled |

**Lifecycle:** Draft → Open → OnHold → Closed | Filled

**Evidence:** `002_workflow_schema.sql`

---

### CANDIDATE

**Service Owner:** hiring-service (port 8005)
**Table:** `candidates`

| Field | Type | Notes |
|-------|------|-------|
| candidate_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| job_posting_id | UUID FK | References job_postings; unique per (tenant_id, job_posting_id, email) |
| first_name | VARCHAR(100) | |
| last_name | VARCHAR(100) | |
| email | VARCHAR(255) | |
| phone | VARCHAR(30) | Nullable |
| resume_url | TEXT | Nullable |
| source | ENUM | Referral, JobBoard, CareerSite, Agency, LinkedIn, Other; nullable |
| source_candidate_id | VARCHAR(120) | Nullable, external ATS reference |
| source_profile_url | TEXT | Nullable |
| application_date | DATE | |
| status | ENUM | See lifecycle |

**Lifecycle:** Applied → Screening → Interviewing → Offered → Hired | Rejected | Withdrawn

**Evidence:** `002_workflow_schema.sql`

---

### CANDIDATE STAGE TRANSITION

**Service Owner:** hiring-service (port 8005)
**Table:** `candidate_stage_transitions`

| Field | Type | Notes |
|-------|------|-------|
| candidate_stage_transition_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| candidate_id | UUID FK | References candidates (cascade delete) |
| from_status | ENUM | Same value set as Candidate.status; nullable (first transition) |
| to_status | ENUM | Same value set as Candidate.status |
| changed_at | TIMESTAMPTZ | Default now() |
| changed_by | VARCHAR(120) | Nullable, actor identifier |
| reason | TEXT | Nullable |
| notes | TEXT | Nullable |

Records each stage change of a Candidate, providing the audit trail for the hiring pipeline.

**Evidence:** `002_workflow_schema.sql`

---

### INTERVIEW

**Service Owner:** hiring-service (port 8005)
**Table:** `interviews`

| Field | Type | Notes |
|-------|------|-------|
| interview_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| candidate_id | UUID FK | References candidates (cascade delete) |
| interview_type | ENUM | PhoneScreen, Technical, Behavioral, Panel, Final |
| scheduled_start | TIMESTAMPTZ | |
| scheduled_end | TIMESTAMPTZ | Must be > scheduled_start |
| location_or_link | TEXT | Nullable |
| interviewer_employee_ids | UUID[] | Nullable array of employee references |
| feedback_summary | TEXT | Nullable |
| recommendation | ENUM | StrongHire, Hire, NoHire, Undecided; nullable |
| status | ENUM | Scheduled, Completed, Cancelled, NoShow |

**Evidence:** `002_workflow_schema.sql`

---

## IDENTITY & ACCESS ENTITIES

### USER ACCOUNT

**Service Owner:** auth-service (port 8006)
**Table:** `user_accounts`

| Field | Type | Notes |
|-------|------|-------|
| user_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| username | TEXT | Unique per tenant |
| password_hash | TEXT | Hashed, never logged |
| role | ENUM | Admin, Manager, Employee, Recruiter, PayrollAdmin, Service |
| employee_id | UUID FK | Links to employee entity |
| department_id | UUID FK | Dept context |
| active | BOOLEAN | |
| last_login_at | TIMESTAMP | |

---

### SESSION

**Service Owner:** auth-service (port 8006)
**Table:** `sessions`

| Field | Type | Notes |
|-------|------|-------|
| session_id | UUID PK | |
| user_id | UUID FK | |
| access_token_jti | UUID | JWT ID claim |
| refresh_token_hash | TEXT | Hashed opaque token |
| refresh_expires_at | TIMESTAMP | |

---

### REFRESH TOKEN

**Service Owner:** auth-service (port 8006)
**Table:** `refresh_tokens`

| Field | Type | Notes |
|-------|------|-------|
| refresh_token_id | UUID PK | |
| session_id | UUID FK | |
| user_id | UUID FK | |
| token_hash | TEXT | |
| issued_at | TIMESTAMP | |
| expires_at | TIMESTAMP | |
| rotated_from | UUID FK | Previous token (chain) |
| replaced_by | UUID FK | Next token (chain) |

---

### ROLE BINDING

**Service Owner:** auth-service (port 8006)
**Table:** `role_bindings`

| Field | Type | Notes |
|-------|------|-------|
| binding_id | UUID PK | |
| user_id | UUID FK | |
| tenant_id | VARCHAR(80) FK | |
| role_name | TEXT | Admin, Manager, Employee, etc. |
| scope_type | ENUM | Global, Department, Employee, Requisition, Service |
| scope_id | UUID | References scoped entity |

---

## WORKFLOW ENTITIES

### WORKFLOW DEFINITION

**Service Owner:** workflow-service (port 8009)
**Table:** `workflow_definitions`

| Field | Type | Notes |
|-------|------|-------|
| workflow_definition_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| code | VARCHAR(120) | Unique per (tenant_id, code) |
| source_service | VARCHAR(80) | Service that registered this definition |
| subject_type | VARCHAR(80) | Type of entity this workflow acts on |
| description | TEXT | |
| steps | JSONB | Ordered step definitions |

**Known Workflow Types (from `/backend/docs/canon/workflow-catalog.md`):**
- employee_onboarding
- leave_approval
- hiring_pipeline
- payroll_approval
- performance_review_cycle

**Evidence:** `003_centralized_workflow_engine.sql`

---

### WORKFLOW INSTANCE

**Service Owner:** workflow-service (port 8009)
**Table:** `workflow_instances`

| Field | Type | Notes |
|-------|------|-------|
| workflow_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| workflow_definition_id | UUID FK | References workflow_definitions |
| source_service | VARCHAR(80) | |
| subject_type | VARCHAR(80) | |
| subject_id | UUID | Subject of the workflow |
| status | ENUM | `pending`, `completed` — **lowercase only**; see casing note below |
| created_by | VARCHAR(120) | |
| created_by_type | ENUM | user, service, system |
| metadata | JSONB | Default `{}` |

**⚠ STATUS CASING CONVENTION (DG-004 — resolved by documentation):** `workflow_instances.status` and `workflow_steps.status` use **lowercase** values (`pending`, `completed`, `approved`, `rejected`). All other status columns in the system use PascalCase (`Draft`, `Active`, `Approved`, etc.). This is an established DB-level constraint enforced by migration `003_centralized_workflow_engine.sql`. All application code reading or writing workflow status must use lowercase strings. Do not assume PascalCase for workflow status. Evidence: `backend/deployment/migrations/003_centralized_workflow_engine.sql` CHECK constraints.

**Evidence:** `003_centralized_workflow_engine.sql`

---

### WORKFLOW STEP

**Service Owner:** workflow-service (port 8009)
**Table:** `workflow_steps`

| Field | Type | Notes |
|-------|------|-------|
| workflow_step_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| workflow_id | UUID FK | References workflow_instances (cascade delete) |
| step_code | VARCHAR(120) | |
| step_type | ENUM | approval, auto, condition |
| assignee | VARCHAR(120) | |
| status | ENUM | `pending`, `approved`, `rejected` — **lowercase only**; see casing note on WORKFLOW INSTANCE above |
| sla | VARCHAR(32) | |
| metadata | JSONB | Default `{}` |

**Evidence:** `003_centralized_workflow_engine.sql`

---

### WORKFLOW HISTORY

**Service Owner:** workflow-service (port 8009)
**Table:** `workflow_history`

| Field | Type | Notes |
|-------|------|-------|
| workflow_history_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| workflow_id | UUID FK | References workflow_instances (cascade delete) |
| workflow_step_id | UUID FK | References workflow_steps, nullable (set null on step delete) |
| action | VARCHAR(80) | |
| actor_id | VARCHAR(120) | |
| actor_type | ENUM | user, service, system |
| from_status | VARCHAR(20) | Nullable |
| to_status | VARCHAR(20) | |
| details | JSONB | Default `{}` |
| created_at | TIMESTAMPTZ | |

Append-only record of every status transition for a workflow instance/step.

**Evidence:** `003_centralized_workflow_engine.sql`

---

## SETTINGS & POLICY ENTITIES

### ATTENDANCE RULE

**Service Owner:** settings-service (port 8020)
**Table:** `attendance_rules`

| Field | Type | Notes |
|-------|------|-------|
| attendance_rule_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| code | VARCHAR(80) | Unique per tenant |
| name | VARCHAR(160) | |
| timezone | VARCHAR(80) | |
| workdays | VARCHAR(20)[] | |
| standard_work_hours | NUMERIC(4,2) | 0–24 |
| grace_period_minutes | INTEGER | >= 0, default 0 |
| late_after_minutes | INTEGER | >= grace_period_minutes, default 0 |
| auto_clock_out_hours | NUMERIC(4,2) | Nullable, 0–24 |
| require_geo_fencing | BOOLEAN | Default false |
| status | ENUM | Draft, Active, Archived |

**Evidence:** `002_workflow_schema.sql`

---

### LEAVE POLICY

**Service Owner:** settings-service (port 8020)
**Table:** `leave_policies`

| Field | Type | Notes |
|-------|------|-------|
| leave_policy_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| code | VARCHAR(80) | Unique per tenant |
| name | VARCHAR(160) | |
| leave_type | ENUM | Annual, Sick, Casual, Unpaid, Parental, Other |
| accrual_frequency | ENUM | None, Monthly, Quarterly, Yearly |
| accrual_rate_days | NUMERIC(5,2) | >= 0 |
| annual_entitlement_days | NUMERIC(5,2) | >= 0; must be 0 if leave_type = Unpaid |
| carry_forward_limit_days | NUMERIC(5,2) | 0 <= value <= annual_entitlement_days |
| requires_approval | BOOLEAN | Default true |
| allow_negative_balance | BOOLEAN | Default false |
| status | ENUM | Draft, Active, Archived |

Only one `Active` policy per (tenant_id, leave_type) is permitted (unique partial index).

**Note:** `LeavePolicy.leave_type` includes `Parental`, while `LeaveRequest.leave_type` (leave-service) does not — `LeaveRequest` values are `Annual, Sick, Casual, Unpaid, Other`. This is a real schema discrepancy between the two tables, not a documentation error; it is noted here as-is per repository evidence.

**Evidence:** `002_workflow_schema.sql`

---

### PAYROLL SETTINGS

**Service Owner:** settings-service (port 8020)
**Table:** `payroll_settings`

| Field | Type | Notes |
|-------|------|-------|
| payroll_setting_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| pay_schedule | ENUM | Weekly, BiWeekly, SemiMonthly, Monthly |
| pay_day | INTEGER | 1–31 |
| currency | CHAR(3) | |
| overtime_multiplier | NUMERIC(4,2) | >= 1 |
| attendance_cutoff_days | INTEGER | 0–31 |
| leave_deduction_mode | ENUM | None, Prorated, FullDay |
| approval_chain | TEXT[] | |
| status | ENUM | Draft, Active, Archived |

**Evidence:** `002_workflow_schema.sql`

---

## PERFORMANCE ENTITIES (ADD-ON — F-017)

### REVIEW CYCLE

**Service Owner:** performance-service (port 8010)
**Table:** `performance_review_cycles`

| Field | Type | Notes |
|-------|------|-------|
| review_cycle_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| code | VARCHAR(40) | Unique per tenant |
| name | VARCHAR(160) | |
| review_period_start | DATE | |
| review_period_end | DATE | Must be >= review_period_start |
| owner_employee_id | UUID FK | References employees |
| workflow_id | UUID | Nullable, references workflow_instances |
| status | ENUM | Draft, Open, Closed |

**Evidence:** `002_workflow_schema.sql`

---

### GOAL

**Service Owner:** performance-service (port 8010)
**Table:** `performance_goals`

| Field | Type | Notes |
|-------|------|-------|
| goal_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| review_cycle_id | UUID FK | References performance_review_cycles |
| employee_id | UUID FK | References employees |
| owner_employee_id | UUID FK | References employees |
| title | VARCHAR(160) | |
| description | TEXT | Default '' |
| metric_name | VARCHAR(120) | |
| target_value | NUMERIC(10,2) | |
| current_value | NUMERIC(10,2) | Default 0 |
| weight | NUMERIC(5,2) | |
| status | ENUM | Draft, Submitted, Approved, Rejected |
| workflow_id | UUID | Nullable |
| approved_at | TIMESTAMPTZ | Nullable |

**Evidence:** `002_workflow_schema.sql`

---

### FEEDBACK

**Service Owner:** performance-service (port 8010)
**Table:** `performance_feedback`

| Field | Type | Notes |
|-------|------|-------|
| feedback_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| employee_id | UUID FK | Feedback subject |
| provider_employee_id | UUID FK | Feedback author |
| review_cycle_id | UUID FK | Nullable, set null on cycle delete |
| feedback_type | ENUM | Manager, Peer, Self, Upward |
| strengths | TEXT | Default '' |
| opportunities | TEXT | Default '' |
| visibility | ENUM | Private, Employee, ManagerAndHR |

**Evidence:** `002_workflow_schema.sql`

---

### CALIBRATION SESSION

**Service Owner:** performance-service (port 8010)
**Table:** `performance_calibrations`

| Field | Type | Notes |
|-------|------|-------|
| calibration_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| review_cycle_id | UUID FK | References performance_review_cycles |
| facilitator_employee_id | UUID FK | References employees |
| department_id | UUID FK | References departments |
| proposed_rating | NUMERIC(2,1) | |
| final_rating | NUMERIC(2,1) | Nullable |
| notes | TEXT | Default '' |
| status | ENUM | Draft, Submitted, Finalized, Rejected |
| workflow_id | UUID | Nullable |
| finalized_at | TIMESTAMPTZ | Nullable |

**Evidence:** `002_workflow_schema.sql`

---

### PIP PLAN

**Service Owner:** performance-service (port 8010)
**Table:** `performance_pip_plans`

| Field | Type | Notes |
|-------|------|-------|
| pip_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| employee_id | UUID FK | References employees |
| manager_employee_id | UUID FK | References employees |
| review_cycle_id | UUID FK | Nullable, set null on cycle delete |
| reason | TEXT | |
| status | ENUM | Draft, Submitted, Active, Completed, Cancelled, Rejected |
| workflow_id | UUID | Nullable |
| started_at | TIMESTAMPTZ | Nullable |
| closed_at | TIMESTAMPTZ | Nullable |

**Evidence:** `002_workflow_schema.sql`

---

### PIP MILESTONE

**Service Owner:** performance-service (port 8010)
**Table:** `performance_pip_milestones`

| Field | Type | Notes |
|-------|------|-------|
| pip_milestone_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| pip_id | UUID FK | References performance_pip_plans (cascade delete) |
| title | VARCHAR(160) | |
| due_date | DATE | |
| success_metric | TEXT | |
| completed | BOOLEAN | Default false |
| completed_at | TIMESTAMPTZ | Nullable |

**Evidence:** `002_workflow_schema.sql`

---

## ENGAGEMENT ENTITIES (ADD-ON — F-018)

### SURVEY

**Service Owner:** engagement-service (port 8011)
**Table:** `engagement_surveys`

| Field | Type | Notes |
|-------|------|-------|
| survey_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| code | VARCHAR(80) | Unique per tenant |
| title | VARCHAR(200) | |
| description | TEXT | Nullable |
| status | ENUM | Draft, Open, Closed |
| owner_employee_id | UUID FK | References employees |
| target_department_id | UUID FK | References departments, nullable |
| published_at | TIMESTAMPTZ | Nullable |
| closed_at | TIMESTAMPTZ | Nullable |

**Evidence:** `010_engagement_service.sql`

---

### SURVEY QUESTION

**Service Owner:** engagement-service (port 8011)
**Table:** `engagement_survey_questions`

| Field | Type | Notes |
|-------|------|-------|
| question_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| survey_id | UUID FK | References engagement_surveys (cascade delete) |
| prompt | TEXT | |
| dimension | ENUM | D1–D5 |
| kind | ENUM | Likert5 (only value currently supported) |
| required | BOOLEAN | Default true |
| scale_min | INTEGER | Default 1 |
| scale_max | INTEGER | Default 5 |

**Evidence:** `010_engagement_service.sql`

---

### SURVEY RESPONSE

**Service Owner:** engagement-service (port 8011)
**Table:** `engagement_survey_responses`

| Field | Type | Notes |
|-------|------|-------|
| response_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| survey_id | UUID FK | References engagement_surveys (cascade delete) |
| employee_id | UUID FK | References employees; unique per (tenant_id, survey_id, employee_id) |
| overall_comment | TEXT | Nullable |
| submitted_at | TIMESTAMPTZ | Default now() |

**Evidence:** `010_engagement_service.sql`

---

### SURVEY ANSWER

**Service Owner:** engagement-service (port 8011)
**Table:** `engagement_survey_answers`

| Field | Type | Notes |
|-------|------|-------|
| answer_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| response_id | UUID FK | References engagement_survey_responses (cascade delete) |
| question_id | UUID FK | References engagement_survey_questions (cascade delete); unique per (tenant_id, response_id, question_id) |
| score | INTEGER | 1–5 |
| comment | TEXT | Nullable |

**Evidence:** `010_engagement_service.sql`

---

### SURVEY AGGREGATE

**Service Owner:** engagement-service (port 8011)
**Table:** `engagement_survey_aggregates`

| Field | Type | Notes |
|-------|------|-------|
| survey_id | UUID PK | References engagement_surveys (cascade delete) |
| tenant_id | VARCHAR(80) FK | |
| response_count | INTEGER | Default 0 |
| participant_count | INTEGER | Default 0 |
| target_population | INTEGER | Default 0 |
| participation_rate | NUMERIC(6,4) | Default 0 |
| overall_average_score | NUMERIC(6,2) | Default 0 |
| favorable_ratio | NUMERIC(6,4) | Default 0 |
| question_scores | JSONB | |
| dimension_scores | JSONB | |
| score_distribution | JSONB | |
| generated_at | TIMESTAMPTZ | Default now() |

A precomputed read-model/projection over Survey responses and answers (see `AI_OPERATING_CONTEXT.md` Glossary — "Read Model / Projection").

**Evidence:** `010_engagement_service.sql`

---

## COMPENSATION ENTITIES (F-004 / Payroll extension)

### COMPENSATION BAND

**Service Owner:** payroll-service (port 8004) — compensation domain
**Table:** `compensation_bands`

| Field | Type | Notes |
|-------|------|-------|
| compensation_band_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| grade_band_id | UUID FK | References grade_bands |
| name | VARCHAR(150) | |
| code | VARCHAR(30) | Unique per tenant |
| currency | CHAR(3) | |
| min_salary | NUMERIC(12,2) | >= 0 |
| max_salary | NUMERIC(12,2) | >= min_salary |
| target_salary | NUMERIC(12,2) | Nullable |
| status | ENUM | Draft, Active, Inactive, Archived |

**Evidence:** `012_compensation_domain.sql`

---

### SALARY REVISION

**Service Owner:** payroll-service (port 8004) — compensation domain
**Table:** `salary_revisions`

| Field | Type | Notes |
|-------|------|-------|
| salary_revision_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| employee_id | UUID FK | References employees |
| compensation_band_id | UUID FK | References compensation_bands, nullable |
| effective_from | DATE | |
| effective_to | DATE | Nullable |
| base_salary | NUMERIC(12,2) | >= 0 |
| currency | CHAR(3) | |
| reason | TEXT | Nullable |
| status | ENUM | Draft, Approved, Superseded |

Effective-dated base-pay decisions per employee; master input for PayrollRecord.base_salary.

**Evidence:** `012_compensation_domain.sql`

---

### BENEFITS PLAN

**Service Owner:** payroll-service (port 8004) — compensation domain
**Table:** `benefits_plans`

| Field | Type | Notes |
|-------|------|-------|
| benefits_plan_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| code | VARCHAR(30) | Unique per tenant |
| name | VARCHAR(150) | |
| plan_type | VARCHAR(50) | |
| employer_contribution | NUMERIC(12,2) | Default 0.00 |
| employee_contribution | NUMERIC(12,2) | Default 0.00 |
| currency | CHAR(3) | Default PKR |
| status | ENUM | Draft, Active, Inactive, Archived |

**Evidence:** `012_compensation_domain.sql`

---

### BENEFITS ENROLLMENT

**Service Owner:** payroll-service (port 8004) — compensation domain
**Table:** `benefits_enrollments`

| Field | Type | Notes |
|-------|------|-------|
| benefits_enrollment_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| employee_id | UUID FK | References employees |
| benefits_plan_id | UUID FK | References benefits_plans |
| employee_contribution | NUMERIC(12,2) | Default 0.00 |
| employer_contribution | NUMERIC(12,2) | Default 0.00 |
| effective_from | DATE | Unique per (tenant_id, employee_id, benefits_plan_id, effective_from) |
| effective_to | DATE | Nullable |
| status | ENUM | Draft, Active, Cancelled, Expired |

**Evidence:** `012_compensation_domain.sql`

---

### ALLOWANCE

**Service Owner:** payroll-service (port 8004) — compensation domain
**Table:** `allowances`

| Field | Type | Notes |
|-------|------|-------|
| allowance_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| employee_id | UUID FK | References employees |
| code | VARCHAR(60) | |
| amount | NUMERIC(12,2) | >= 0 |
| currency | CHAR(3) | Default PKR |
| frequency | ENUM | Monthly, OneTime, Quarterly, Annual |
| effective_from | DATE | |
| effective_to | DATE | Nullable |
| status | ENUM | Draft, Active, Inactive, Archived |

Recurring or one-time compensation additions aggregated into PayrollRecord.allowances.

**Evidence:** `012_compensation_domain.sql`

---

## TRAVEL ENTITIES (PLANNED — F-023)

These tables exist in the schema; per `FEATURE_SCOPE.md` F-023 the travel-service implementation is PLANNED (not functionally complete), though the gateway route `/api/v1/travel` is confirmed.

### TRAVEL REQUEST

**Service Owner:** travel-service (port 8018)
**Table:** `travel_requests`

| Field | Type | Notes |
|-------|------|-------|
| travel_request_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| employee_id | UUID FK | References employees |
| manager_employee_id | UUID FK | References employees, nullable |
| purpose | VARCHAR(240) | |
| destination | VARCHAR(240) | |
| start_date | DATE | |
| end_date | DATE | Must be >= start_date |
| status | ENUM | See lifecycle, default Draft |
| workflow_id | UUID | Nullable |
| estimated_cost | NUMERIC(12,2) | Nullable, >= 0 |
| currency | CHAR(3) | Default PKR |

**Lifecycle:** Draft → Submitted → Approved | Rejected; Approved → Booked → Completed; Draft/Submitted/Approved/Booked → Cancelled

**Evidence:** `013_travel_domain.sql`

---

### TRAVEL ITINERARY SEGMENT

**Service Owner:** travel-service (port 8018)
**Table:** `travel_itinerary_segments`

| Field | Type | Notes |
|-------|------|-------|
| segment_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| travel_request_id | UUID FK | References travel_requests (cascade delete) |
| segment_type | ENUM | Flight, Hotel, Car, Train, Other |
| departure_city | VARCHAR(120) | |
| arrival_city | VARCHAR(120) | |
| departure_at | TIMESTAMPTZ | |
| arrival_at | TIMESTAMPTZ | Must be >= departure_at |
| provider_name | VARCHAR(120) | Nullable |
| booking_reference | VARCHAR(80) | Nullable |
| cost | NUMERIC(12,2) | Nullable, >= 0 |

Individual travel legs attached to a TravelRequest; created/updated after the request is Approved.

**Evidence:** `013_travel_domain.sql`

---

## ADD-ON DOMAIN ENTITIES (Helpdesk F-019, Workforce Intelligence)

### HELPDESK TICKET

**Service Owner:** helpdesk-service (port 8012)
**Table:** `helpdesk_tickets`

| Field | Type | Notes |
|-------|------|-------|
| ticket_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| requester_employee_id | UUID | References employees |
| subject | VARCHAR(240) | |
| category_code | VARCHAR(60) | |
| priority | VARCHAR(20) | Enum: `Low`, `Medium`, `High`, `Urgent` — confirmed from `backend/helpdesk_service.py` line 128: `PRIORITIES = {'Low', 'Medium', 'High', 'Urgent'}` |
| status | VARCHAR(20) | Enum: `Draft`, `Open`, `InProgress`, `Resolved`, `Closed` — confirmed from `backend/helpdesk_service.py` line 127: `TICKET_STATUSES = {'Draft', 'Open', 'InProgress', 'Resolved', 'Closed'}` |

**Evidence:** `011_addon_domains.sql`, `backend/helpdesk_service.py` lines 127–128

---

### HELPDESK TICKET SLA EVENT

**Service Owner:** helpdesk-service (port 8012)
**Table:** `helpdesk_ticket_sla_events`

| Field | Type | Notes |
|-------|------|-------|
| event_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| ticket_id | UUID FK | References helpdesk_tickets (cascade delete) |
| escalation_stage | VARCHAR(30) | |
| triggered_at | TIMESTAMPTZ | Default now() |
| metadata | JSONB | Default `{}` |

**Evidence:** `011_addon_domains.sql`

---

### WORKFORCE INTELLIGENCE SNAPSHOT

**Service Owner:** reporting-analytics-service (port 8013)
**Table:** `workforce_intelligence_snapshots`

| Field | Type | Notes |
|-------|------|-------|
| snapshot_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| snapshot_type | VARCHAR(80) | |
| dimension_key | VARCHAR(80) | |
| dimension_value | VARCHAR(160) | |
| metrics | JSONB | Default `{}` |
| captured_at | TIMESTAMPTZ | Default now() |

A read-model/projection capturing point-in-time workforce metrics (see Glossary in `AI_OPERATING_CONTEXT.md`).

**Evidence:** `011_addon_domains.sql`

---

### LEARNING PATH

**Service Owner:** NONE — CONFIRMED OUT OF SCOPE. `FEATURE_SCOPE.md` explicitly lists LMS as out of scope. No LMS service in docker-compose.yml. Table exists in schema as a forward migration artifact — do not treat as implemented. Schema presence without a service = planned/speculative definition only.
**Table:** `learning_paths`

| Field | Type | Notes |
|-------|------|-------|
| learning_path_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| code | VARCHAR(100) | Unique per tenant |
| title | VARCHAR(200) | |
| description | TEXT | Default '' |
| status | VARCHAR(20) | Default 'Active' |

**Note:** This table exists in the schema, but `FEATURE_SCOPE.md` "OUT OF SCOPE" section lists LMS as not in the codebase. The table's existence without an associated service is logged as a discrepancy — do not assume an LMS feature exists based on this table alone.

**Evidence:** `011_addon_domains.sql`

---

### WORKFORCE COST PLAN

**Service Owner:** reporting-analytics-service (port 8013)
**Table:** `workforce_cost_plans`

| Field | Type | Notes |
|-------|------|-------|
| plan_id | UUID PK | |
| tenant_id | VARCHAR(80) FK | |
| fiscal_year | SMALLINT | |
| period_code | VARCHAR(20) | Unique per (tenant_id, fiscal_year, period_code) |
| headcount_target | INTEGER | >= 0 |
| salary_forecast | NUMERIC(14,2) | Default 0 |
| budget_limit | NUMERIC(14,2) | Default 0 |
| forecast_currency | CHAR(3) | Default USD |
| notes | TEXT | Default '' |

**Evidence:** `011_addon_domains.sql`

---

## DECISION CARD (F-014)

**Service Owner:** decision-service (port 8022)
**Representation:** In-memory/runtime dataclass — **not a persisted database table**. No `decision_cards` table exists in any migration file (verified by search of `/backend/deployment/migrations/`).

`DecisionCard` (`services/decision_engine.py`):

| Field | Type | Notes |
|-------|------|-------|
| trigger | str | What triggered the card |
| impact | str | |
| confidence | float | |
| recommended_action | str | Aliased as `action` in `to_dict()` for backward compatibility |
| reversibility | str | |
| expires_at | str (ISO timestamp) | |
| source_domain | str | Default "system" — domain that triggered the card (e.g., payroll, attendance, compliance, ai) |
| severity | ENUM (`DecisionSeverity`) | critical, notify, passive — default "notify" |
| resolved_at | str \| None | ISO timestamp when resolved |
| actor | str \| None | Who resolved the decision |
| status | str | Default "active" |
| lifecycle_state | str | Default "create" |
| override_tracking | list[dict] | Default `[]` |
| created_at | str (ISO timestamp) | Auto-generated |
| updated_at | str (ISO timestamp) | Auto-generated |
| audit_history | list[dict] | Default `[]` |

**Severity semantics (`DecisionSeverity`):**
- `critical` → blocks the related action / requires mandatory approval
- `notify` → visible action required, non-blocking unless escalated
- `passive` → logged / surfaced in decision stream only

**Note on gateway access:** `/api/v1/decisions` is CONFIRMED as gateway route 23 (`routes.py` line 53, `gateway-routes.json` line 26 — Phase 2.8 TR-004). ADR-001 §2 note was stale; this has been resolved. Non-standard envelope `{status, data, service}` — no `meta` field.

**Evidence:** `services/decision_engine.py`, `services/governance/service.py`, `decision_api.py`

---

## SYSTEM / INFRASTRUCTURE ENTITIES

### AUDIT RECORD

**Service Owner:** audit-service (port 8008)
**Table:** `audit_records`

| Field | Type | Notes |
|-------|------|-------|
| audit_id | UUID PK | |
| entity_type | TEXT | Domain entity name |
| entity_id | UUID | Subject entity |
| actor_id | UUID | User who performed action |
| action | TEXT | create, update, delete, etc. |
| before | JSONB | State before mutation |
| after | JSONB | State after mutation |
| timestamp | TIMESTAMP | |

**Protection Level:** PROHIBITED from deletion or modification. See `DECISION_ESCALATION_MATRIX.md`.

---

### EVENT OUTBOX

**Service Owner:** Cross-cutting (infrastructure)
**Tables:** `service_outbox`, `processed_events`, `event_outbox`

All cross-service events must be written to the outbox table atomically with the triggering mutation. The outbox processor publishes events asynchronously.

**Evidence:** `/backend/event_outbox.py`, `/backend/outbox_system.py`, `007_event_outbox.sql`, `008_background_jobs_schema.sql`

---

### BACKGROUND JOB

**Service Owner:** Cross-cutting (infrastructure)
**Tables:** `background_jobs`, `background_job_failures`

Async job queue for deferred processing. All long-running operations (payroll runs, bulk exports, compliance submissions) should use background jobs.

**Evidence:** `/backend/background_jobs.py`

---

## DOMAIN EVENT CATALOG SUMMARY

143 domain events are defined across all services. Full catalog: `/backend/docs/canon/event-catalog.md`

**Event Envelope:**
```json
{
  "event_id": "uuid",
  "event_name": "string",
  "occurred_at": "ISO8601",
  "producer_service": "string",
  "trace_id": "uuid",
  "payload": {}
}
```

**Sample Events by Domain:**
- `employee.hired`, `employee.terminated`, `employee.transferred`
- `attendance.record_validated`, `attendance.period_closed`
- `leave.submitted`, `leave.approved`, `leave.rejected`
- `payroll.run_initiated`, `payroll.paid`
- `candidate.hired`, `interview.completed`
- `workflow.step_completed`, `workflow.completed`

---

## ENTITY RELATIONSHIP SUMMARY

```
Tenant (1) ──── (N) Employee
Employee (N) ──── (1) Department
Employee (N) ──── (1) Employee (manager self-ref)
Employee (1) ──── (1) UserAccount
Employee (1) ──── (N) AttendanceRecord
Employee (1) ──── (N) LeaveRequest
Employee (1) ──── (N) PayrollRecord
Employee (1) ──── (N) SalaryRevision
Employee (1) ──── (N) Allowance
Employee (1) ──── (N) BenefitsEnrollment
Employee (1) ──── (N) TravelRequest
Department (N) ──── (1) Department (parent self-ref)
JobPosting (1) ──── (N) Candidate
Candidate (1) ──── (N) Interview
Candidate (1) ──── (N) CandidateStageTransition
WorkflowDefinition (1) ──── (N) WorkflowInstance
WorkflowInstance (1) ──── (N) WorkflowStep
WorkflowInstance (1) ──── (N) WorkflowHistory
WorkflowStep (1) ──── (N) WorkflowHistory
GradeBand (1) ──── (N) CompensationBand
TravelRequest (1) ──── (N) TravelItinerarySegment
ReviewCycle (1) ──── (N) Goal
ReviewCycle (1) ──── (N) Feedback
ReviewCycle (1) ──── (N) CalibrationSession
ReviewCycle (1) ──── (N) PipPlan
PipPlan (1) ──── (N) PipMilestone
Survey (1) ──── (N) SurveyQuestion
Survey (1) ──── (N) SurveyResponse
SurveyResponse (1) ──── (N) SurveyAnswer
SurveyQuestion (1) ──── (N) SurveyAnswer
Survey (1) ──── (1) SurveyAggregate
HelpdeskTicket (1) ──── (N) HelpdeskTicketSlaEvent
Any Entity mutation ──── (1) AuditRecord
```
