# VALIDATION RULES

Status: Draft
Authority Level: High
Last Reviewed: 2026-06-15
Owner: AI

---

## PURPOSE

This document records the validation rules actually enforced by the Meridian HCM backend, organized by domain entity. Rules are extracted from:

- DB-level `CHECK`, `NOT NULL`, and `UNIQUE` constraints in `/backend/deployment/migrations/001_core_schema.sql` through `013_travel_domain.sql` (ground truth — these execute regardless of application code).
- Application-layer (service-level) validation found in `*_api.py` and `services/*` files, where it adds rules beyond the DB schema.

Per `DOMAIN_MODEL.md`, every primary entity table also carries the multi-tenancy invariant: `tenant_id VARCHAR(80) NOT NULL` plus a `UNIQUE (tenant_id, [entity]_id)` constraint. This is not repeated per-entity below.

Where a rule is enforced only by the DB (no corresponding application check found), it is marked **DB-only**. Where application code adds rules not present in the DB schema, the source file is cited.

---

## EMPLOYEE

**Table:** `employees` — **Evidence:** `001_core_schema.sql`

| Field | Rule | Enforcement |
|---|---|---|
| employee_number | `NOT NULL`; unique per `(tenant_id, employee_number)` | DB-only |
| first_name, last_name | `NOT NULL` | DB-only |
| email | `NOT NULL`; unique per `(tenant_id, email)` | DB-only |
| phone | Nullable, `VARCHAR(30)` | DB-only |
| hire_date | `NOT NULL` (DATE) | DB-only |
| employment_type | `NOT NULL`; enum `FullTime, PartTime, Contract, Intern` | DB CHECK |
| status | `NOT NULL`; enum `Draft, Active, OnLeave, Suspended, Terminated` | DB CHECK |
| department_id | `NOT NULL`; FK → `departments(tenant_id, department_id)`, `ON DELETE RESTRICT` | DB-only |
| role_id | `NOT NULL`; FK → `roles(tenant_id, role_id)`, `ON DELETE RESTRICT` | DB-only |
| manager_employee_id | Nullable; FK → `employees(tenant_id, employee_id)` (self-referential), `ON DELETE RESTRICT` | DB-only |

**Application-layer additions:**
- Hiring-service candidate-to-employee conversion enforces `employee email must be unique` and `employee does not exist` checks before creating a new employee record — **Evidence:** `backend/services/hiring_service/service.py` lines ~1406, 1465.

**Note on `CreateEmployeeInput`:** per `contracts/hrms-h04-add-employee-contract.json`, the frontend "Add Employee" form collects additional fields (`date_of_birth`, `nationality`, `home_address`, `personal_email`, `preferred_name`, `probation_end_date`) that are **not present** in `CreateEmployeeInput` and are not sent to the backend (documented gap BG-008). These fields have no backend validation because they are never transmitted.

---

## DEPARTMENT

**Table:** `departments` — **Evidence:** `001_core_schema.sql`

| Field | Rule | Enforcement |
|---|---|---|
| name | `NOT NULL`; unique per `(tenant_id, name)` | DB CHECK / UNIQUE |
| code | `NOT NULL`, `VARCHAR(30)`; unique per `(tenant_id, code)` | DB UNIQUE |
| status | `NOT NULL`; enum `Proposed, Active, Inactive, Archived` | DB CHECK |
| parent_department_id | Nullable; FK → `departments(tenant_id, department_id)` (self-referential), `ON DELETE RESTRICT` | DB-only |
| head_employee_id | Nullable; FK → `employees(tenant_id, employee_id)`, `ON DELETE RESTRICT` | DB-only |

---

## ROLE (Job Role / Title)

**Table:** `roles` — **Evidence:** `001_core_schema.sql`

| Field | Rule | Enforcement |
|---|---|---|
| title | `NOT NULL`; unique per `(tenant_id, title)` | DB UNIQUE |
| employment_category | `NOT NULL`; enum `Staff, Manager, Executive, Contractor` | DB CHECK |
| status | `NOT NULL`; enum `Draft, Active, Inactive, Archived` | DB CHECK |
| level | `VARCHAR(50)`, nullable | DB-only (no enum/range CHECK) |
| permissions | `TEXT[] NOT NULL DEFAULT '{}'` | DB-only |

---

## ATTENDANCE RECORD

**Table:** `attendance_records` — **Evidence:** `002_workflow_schema.sql`

| Field | Rule | Enforcement |
|---|---|---|
| employee_id | `NOT NULL`; FK → `employees(tenant_id, employee_id)`, `ON DELETE RESTRICT` | DB-only |
| attendance_date | `NOT NULL`; unique per `(tenant_id, employee_id, attendance_date)` | DB UNIQUE |
| check_in_time, check_out_time | Nullable `TIMESTAMPTZ` | DB-only |
| total_hours | Nullable `NUMERIC(5,2)`; no range CHECK | DB-only |
| attendance_status | `NOT NULL`; enum `Present, Absent, Late, HalfDay, Holiday` | DB CHECK |
| source | Nullable; enum `Manual, Biometric, APIImport` | DB CHECK |

**RESOLVED (2026-06-17):** `backend/services/attendance_service.py` confirmed — `AttendanceService` class with `AttendanceEntry` dataclass including `check_in`, `check_out`, `shift_hours`, `worked_hours`, `overtime_hours`, `late_minutes`, `late_penalty`, `missing_punch_resolved`, `missing_punch_unresolved` fields. Application-layer validation for worked_hours computation and late penalty is implemented in this service. Full method body verification is a deferred code-trace task (UI-003 class).

---

## LEAVE REQUEST

**Table:** `leave_requests` — **Evidence:** `002_workflow_schema.sql`; service layer **Evidence:** `backend/leave_service.py`, `backend/leave_api.py`

| Field | Rule | Enforcement |
|---|---|---|
| employee_id | `NOT NULL`; FK → `employees(tenant_id, employee_id)`, `ON DELETE RESTRICT` | DB-only |
| leave_type | `NOT NULL`; enum `Annual, Sick, Casual, Unpaid, Other` | DB CHECK |
| start_date, end_date | Both `NOT NULL`; `end_date >= start_date` (`chk_leave_requests_date_range`) | DB CHECK |
| total_days | `NOT NULL NUMERIC(4,1)`; no DB range CHECK | DB-only |
| reason | Nullable `TEXT` | DB-only |
| approver_employee_id | Nullable; FK → `employees(tenant_id, employee_id)`, `ON DELETE RESTRICT` | DB-only |
| status | `NOT NULL`; enum `Draft, Submitted, Approved, Rejected, Cancelled` | DB CHECK |

**Application-layer additions (beyond DB schema) — `backend/leave_service.py`:**
- `end_date >= start_date` is re-validated at the application layer (line ~278) before the DB constraint would fire — `raise ValueError("end_date must be >= start_date")`.
- `partial_day_portion` must be `0.5` or `1.0` (line ~280) — not represented as a DB column/CHECK; this is a request-level field only.
- Partial-day leave is only permitted if the active `LeavePolicy` allows it (line ~282: `"policy does not allow partial-day leave"`), and only for single-day requests (line ~295).
- A leave date range that resolves entirely to holidays/weekends is rejected (line ~293: `"leave range resolves entirely to holidays"`).
- Requested days must not exceed the employee's remaining leave balance for that `leave_type`, computed from the active `LeavePolicy` accrual configuration (line ~304: `"Requested leave exceeds available balance"`).
- An active `LeavePolicy` must exist for `(tenant_id, leave_type)` or the request is rejected (line ~259: `"No active leave policy configured for ..."`).
- Decision actions (`approve`/`reject`) are restricted to those two values; any other action returns `422 VALIDATION_ERROR` (line ~824, ~832).
- Generic payload errors (`KeyError`, `TypeError`, `ValueError`) are caught and surfaced as `422 VALIDATION_ERROR` with message "Invalid request payload." — **Evidence:** `backend/leave_api.py` lines 66-83.

**Cross-reference / known discrepancy (per `DOMAIN_MODEL.md`):** `LeavePolicy.leave_type` (in `leave_policies`, `002_workflow_schema.sql`) includes an additional value `Parental` not present in `LeaveRequest.leave_type`'s enum (`Annual, Sick, Casual, Unpaid, Other`). This is a real schema discrepancy, documented as-is.

**Frontend contract discrepancy:** `contracts/hrms-h04-raise-leave-request-contract.json` restricts the `leave_type` selector to `["Annual","Sick","Casual","Unpaid"]` — omitting `Other`, which is a valid DB/API enum value. See `VALIDATION_PARITY.md`.

---

## LEAVE POLICY

**Table:** `leave_policies` — **Evidence:** `002_workflow_schema.sql`

| Field | Rule | Enforcement |
|---|---|---|
| code | `NOT NULL VARCHAR(80)`; unique per tenant | DB UNIQUE |
| leave_type | `NOT NULL`; enum `Annual, Sick, Casual, Unpaid, Parental, Other` | DB CHECK |
| accrual_frequency | `NOT NULL`; enum `None, Monthly, Quarterly, Yearly` | DB CHECK |
| accrual_rate_days | `NOT NULL NUMERIC(5,2) >= 0` | DB CHECK |
| annual_entitlement_days | `NOT NULL NUMERIC(5,2) >= 0` | DB CHECK |
| annual_entitlement_days vs leave_type | If `leave_type = 'Unpaid'`, `annual_entitlement_days` must equal `0` (`chk_leave_policies_unpaid_entitlement`) | DB CHECK |
| carry_forward_limit_days | `NOT NULL NUMERIC(5,2)`; `0 <= value <= annual_entitlement_days` | DB CHECK |
| status | `NOT NULL`; enum `Draft, Active, Archived` | DB CHECK |
| Active-policy uniqueness | Only one `Active` policy permitted per `(tenant_id, leave_type)` (unique partial index) | DB CHECK |

---

## PAYROLL RECORD

**Table:** `payroll_records` — **Evidence:** `002_workflow_schema.sql`; service layer **Evidence:** `backend/payroll_service.py`

| Field | Rule | Enforcement |
|---|---|---|
| employee_id | `NOT NULL`; FK → `employees(tenant_id, employee_id)`, `ON DELETE RESTRICT` | DB-only |
| pay_period_start, pay_period_end | Both `NOT NULL`; `pay_period_end >= pay_period_start` (`chk_payroll_records_period`) | DB CHECK |
| Period uniqueness | Unique per `(tenant_id, employee_id, pay_period_start, pay_period_end)` | DB UNIQUE |
| base_salary, gross_pay, net_pay | `NOT NULL NUMERIC(12,2)`; no DB-level range CHECK | DB-only |
| allowances, deductions, overtime_pay | `NUMERIC(12,2) DEFAULT 0.00`, nullable | DB-only |
| currency | `NOT NULL CHAR(3)` | DB-only (format not enforced by DB) |
| payment_date | Nullable `DATE` | DB-only |
| status | `NOT NULL`; enum `Draft, Processed, Paid, Cancelled` | DB CHECK |

**Application-layer additions (beyond DB schema) — `backend/payroll_service.py`:**
- `pay_period_end must be on or after pay_period_start` is re-validated at the application layer (lines ~640, ~1279) ahead of the DB constraint, returning `422 VALIDATION_ERROR`.
- `net_pay must be >= 0` (line ~642) — **not enforced by the DB schema** (no CHECK on `net_pay`).
- `payment_date must be on or after pay_period_end` (line ~1281) — **not enforced by the DB schema** (`payment_date` has no CHECK).
- `gross_pay does not match validated calculation` and `net_pay does not match validated calculation` (lines ~743-745) — cross-field arithmetic consistency checks not expressible as simple DB CHECKs.
- Monetary amount fields generally: `must be a valid decimal amount` and `must be >= 0` (lines ~588, ~590) for input amounts (e.g., allowances/deductions on certain endpoints).
- `currency must be a 3-letter ISO code` (line ~616) — DB only enforces `CHAR(3)` length, not ISO-4217 validity.
- Required-field check: generic `"{field} is required"` (line ~623), and `employee_id is required` / employee existence check (`NOT_FOUND` 404) (lines ~636-638).
- Salary-structure cross-checks: `salary_structure employee_id does not match payroll employee_id`, `salary_structure currency does not match payroll currency`, `payroll_cycle period does not match payroll record period` (lines ~1104-1109).
- Compensation component validation: `category must be earning or deduction` (lines ~1398, ~1453) and `calculation_mode must be flat or percentage` (line ~1455) — for `payroll_settings`/compensation-component records; not represented as DB enums in the migrations reviewed.
- Critical payroll anomalies (risk score `>= 70`) must block finalization — risk-scoring is application logic, not DB-enforced (line ~489, ~521).

---

## SALARY REVISION

**Table:** `salary_revisions` — **Evidence:** `012_compensation_domain.sql`; cross-check **Evidence:** `backend/payroll_service.py`

| Field | Rule | Enforcement |
|---|---|---|
| employee_id | `NOT NULL`; FK → `employees(employee_id)` (not tenant-composite in this migration) | DB-only |
| compensation_band_id | Nullable; FK → `compensation_bands(compensation_band_id)` | DB-only |
| effective_from | `NOT NULL DATE` | DB-only |
| effective_to | Nullable `DATE`; application-layer requires `effective_to >= effective_from` if set (line ~692, ~1335: `"effective_to must be on or after effective_from"`) — **not a DB CHECK** | Application-only |
| base_salary | `NOT NULL NUMERIC(12,2) >= 0` | DB CHECK |
| currency | `NOT NULL CHAR(3)` | DB-only |
| status | `NOT NULL DEFAULT 'Draft'`; enum `Draft, Approved, Superseded` | DB CHECK |

---

## COMPENSATION BAND

**Table:** `compensation_bands` — **Evidence:** `012_compensation_domain.sql`

| Field | Rule | Enforcement |
|---|---|---|
| code | `NOT NULL VARCHAR(30)`; unique per `(tenant_id, code)` | DB UNIQUE |
| currency | `NOT NULL CHAR(3)` | DB-only |
| min_salary | `NOT NULL NUMERIC(12,2) >= 0` | DB CHECK |
| max_salary | `NOT NULL NUMERIC(12,2)`; `max_salary >= min_salary` | DB CHECK |
| target_salary | Nullable `NUMERIC(12,2)`; no range CHECK | DB-only |
| status | `NOT NULL DEFAULT 'Draft'`; enum `Draft, Active, Inactive, Archived` | DB CHECK |

---

## BENEFITS PLAN / BENEFITS ENROLLMENT / ALLOWANCE

**Tables:** `benefits_plans`, `benefits_enrollments`, `allowances` — **Evidence:** `012_compensation_domain.sql`

| Entity.Field | Rule | Enforcement |
|---|---|---|
| BenefitsPlan.code | `NOT NULL VARCHAR(30)`; unique per `(tenant_id, code)` | DB UNIQUE |
| BenefitsPlan.status | enum `Draft, Active, Inactive, Archived` | DB CHECK |
| BenefitsPlan.employer/employee_contribution | `NUMERIC(12,2) DEFAULT 0.00`; no range CHECK | DB-only |
| BenefitsEnrollment.effective_from | `NOT NULL DATE`; unique per `(tenant_id, employee_id, benefits_plan_id, effective_from)` | DB UNIQUE |
| BenefitsEnrollment.status | enum `Draft, Active, Cancelled, Expired` | DB CHECK |
| Allowance.amount | `NOT NULL NUMERIC(12,2) >= 0` | DB CHECK |
| Allowance.frequency | `NOT NULL DEFAULT 'Monthly'`; enum `Monthly, OneTime, Quarterly, Annual` | DB CHECK |
| Allowance.status | enum `Draft, Active, Inactive, Archived` | DB CHECK |
| Allowance.effective_from | `NOT NULL DATE` | DB-only |

---

## JOB POSTING

**Table:** `job_postings` — **Evidence:** `002_workflow_schema.sql`; service layer **Evidence:** `backend/services/hiring_service/service.py`

| Field | Rule | Enforcement |
|---|---|---|
| title | `NOT NULL VARCHAR(200)` | DB-only |
| department_id | `NOT NULL`; FK → `departments` | DB-only |
| role_id | Nullable; FK → `roles` | DB-only |
| employment_type | `NOT NULL`; enum `FullTime, PartTime, Contract, Intern` | DB CHECK |
| openings_count | `NOT NULL INTEGER >= 1` | DB CHECK |
| posting_date | `NOT NULL DATE` | DB-only |
| closing_date | Nullable; if set, `closing_date >= posting_date` (`chk_job_postings_dates`) | DB CHECK |
| status | `NOT NULL`; enum `Draft, Open, OnHold, Closed, Filled` | DB CHECK |

**Application-layer additions — `backend/services/hiring_service/service.py`:**
- `openings_count must be >= 1` is re-validated at the application layer (lines ~398, ~535, ~598), duplicating the DB CHECK ahead of insertion.
- `closing_date must be on or after posting_date` is re-validated at the application layer (lines ~542, ~612), duplicating the DB CHECK.
- `requisition must be approved before opening a posting` (line ~550) — a workflow-state precondition not expressible in the DB schema.
- `job posting cannot be deleted while candidates exist` (line ~670) — referential-integrity-style business rule enforced in application code (no `ON DELETE` restriction defined for this relationship in the migrations reviewed).
- `hiring_plan.must_have_skills must be a list` (line ~1614) and `each pipeline stage must be an object` (line ~1619) — shape validation for the JSONB `hiring_plan`/pipeline fields, which have no DB-level schema validation (JSONB is untyped).
- Generic field validation helper (`_require_field`, lines ~1713-1745): required fields, enum membership (`"{field} must be one of: {allowed_values}"`), ISO date format, and ISO datetime format — applied across hiring endpoints.

---

## CANDIDATE

**Table:** `candidates` — **Evidence:** `002_workflow_schema.sql`; service layer **Evidence:** `backend/services/hiring_service/service.py`

| Field | Rule | Enforcement |
|---|---|---|
| job_posting_id | `NOT NULL`; FK → `job_postings`; unique per `(tenant_id, job_posting_id, email)` | DB UNIQUE |
| first_name, last_name | `NOT NULL VARCHAR(100)` | DB-only |
| email | `NOT NULL VARCHAR(255)` | DB-only |
| phone | Nullable `VARCHAR(30)` | DB-only |
| resume_url | Nullable `TEXT` | DB-only |
| source | Nullable; enum `Referral, JobBoard, CareerSite, Agency, LinkedIn, Other` | DB CHECK |
| source_candidate_id, source_profile_url | Nullable | DB-only |
| application_date | `NOT NULL DATE` | DB-only |
| status | `NOT NULL`; enum `Applied, Screening, Interviewing, Offered, Hired, Rejected, Withdrawn` | DB CHECK |

**Application-layer additions — `backend/services/hiring_service/service.py`:**
- `candidates can only be created for Open/OnHold job postings` (line ~736) — workflow-state precondition.
- `candidate status must start as Applied` (line ~742) — initial-state rule beyond DB default.
- `candidate email must be unique within the job posting` is re-validated at the application layer (lines ~745, ~843, ~853), duplicating the DB unique constraint with a friendlier error.
- `candidates can only be assigned to Open/OnHold job postings` (line ~850).
- `invalid candidate status transition: {from} -> {to}` (line ~858) — state-machine transition validation; the DB schema allows any value in the enum with no transition-table CHECK.
- Bulk-import: `candidates must be a non-empty list` (line ~1490); per-item `email is required` (line ~1497, soft-skip rather than hard error).
- Hire-from-candidate: `candidate can only be hired from Offered status` (line ~1365); `candidate offer must be approved or accepted before hire` (line ~1368).

---

## CANDIDATE STAGE TRANSITION

**Table:** `candidate_stage_transitions` — **Evidence:** `002_workflow_schema.sql`

| Field | Rule | Enforcement |
|---|---|---|
| candidate_id | `NOT NULL`; FK → `candidates`, cascade delete | DB-only |
| from_status | Nullable; enum same value set as `Candidate.status` | DB CHECK |
| to_status | `NOT NULL`; enum same value set as `Candidate.status` | DB CHECK |
| changed_at | `DEFAULT now()` | DB-only |

---

## INTERVIEW

**Table:** `interviews` — **Evidence:** `002_workflow_schema.sql`; service layer **Evidence:** `backend/services/hiring_service/service.py`

| Field | Rule | Enforcement |
|---|---|---|
| candidate_id | `NOT NULL`; FK → `candidates`, cascade delete | DB-only |
| interview_type | `NOT NULL`; enum `PhoneScreen, Technical, Behavioral, Panel, Final` | DB CHECK |
| scheduled_start | `NOT NULL TIMESTAMPTZ` | DB-only |
| scheduled_end | `NOT NULL`; `scheduled_end > scheduled_start` (`chk_interviews_schedule`) | DB CHECK |
| recommendation | Nullable; enum `StrongHire, Hire, NoHire, Undecided` | DB CHECK |
| status | `NOT NULL`; enum `Scheduled, Completed, Cancelled, NoShow` | DB CHECK |

**Application-layer additions — `backend/services/hiring_service/service.py`:**
- `scheduled_end must be after scheduled_start` is re-validated at the application layer (lines ~1018, ~1120), duplicating `chk_interviews_schedule`.
- `interviews can only be scheduled for Interviewing/Offered candidates` (line ~1013) and `interviews can only be assigned to Interviewing/Offered candidates` (line ~1099) — workflow-state preconditions.

---

## EXPENSE CLAIM

**Tables:** Expense domain tables (referenced by `backend/expense_service.py`, not in the 13 migration files reviewed — table DDL location is **TBD – REQUIRES VERIFICATION**)

**Application-layer validation — `backend/expense_service.py`:**
- `code is required` / `name is required` for expense category setup (lines ~163, ~165) — non-empty string checks.
- `amount exceeds configured category limit`: `amount` must be `<= category.max_amount` (line ~214) — a tenant-configurable, per-category business rule (not a static DB CHECK).
- `at least one attachment is required for this category` (line ~217) and `attachments are required before submission` (line ~298) — category-policy-driven required-field rules.
- `description is required` (line ~244) — non-empty string check.
- State-machine: `attachments can only be added while the claim is Draft` (line ~260); `only Draft claims can be submitted` (line ~295); `only Submitted claims can be decided` (line ~345); `only Approved claims can be reimbursed` (line ~386).
- `approver_employee_id could not be resolved` (line ~301) — requires a resolvable manager assignment for the submitting employee.
- Decision actions restricted to `approve`/`reject` (lines ~512, ~520) — same pattern as leave-service.
- `amount must be a valid number` (line ~587) — numeric format validation.
- Referenced-employee checks: required field, existence (`404 NOT_FOUND`), and `references a terminated employee` (`409 INVALID_REFERENCE`) (lines ~478-491).
- `category_code is required` and category existence check (`404 NOT_FOUND`) (lines ~488, ~491).
- `attachment requires file_name and storage_key` (line ~566).

**TBD – REQUIRES VERIFICATION:** Underlying expense-claim table DDL (column-level `NOT NULL`/`CHECK` constraints) was not located in `001`–`013` migrations; expense domain schema location requires further verification.

---

## TRAVEL REQUEST / TRAVEL ITINERARY SEGMENT

**Tables:** `travel_requests`, `travel_itinerary_segments` — **Evidence:** `013_travel_domain.sql`

| Field | Rule | Enforcement |
|---|---|---|
| TravelRequest.purpose, destination | `NOT NULL VARCHAR(240)` | DB-only |
| TravelRequest.start_date, end_date | Both `NOT NULL`; `end_date >= start_date` | DB CHECK |
| TravelRequest.status | `NOT NULL DEFAULT 'Draft'`; enum `Draft, Submitted, Approved, Rejected, Booked, Completed, Cancelled` | DB CHECK |
| TravelRequest.estimated_cost | Nullable `NUMERIC(12,2)`; if set, `>= 0` | DB CHECK |
| TravelRequest.currency | `NOT NULL DEFAULT 'PKR' CHAR(3)` | DB-only |
| Segment.segment_type | `NOT NULL`; enum `Flight, Hotel, Car, Train, Other` | DB CHECK |
| Segment.departure_at, arrival_at | Both `NOT NULL`; `arrival_at >= departure_at` | DB CHECK |
| Segment.cost | Nullable `NUMERIC(12,2)`; if set, `>= 0` | DB CHECK |

Per `FEATURE_SCOPE.md` F-023 and `DOMAIN_MODEL.md`, the travel-service implementation is **PLANNED (not functionally complete)** — application-layer validation beyond these DB constraints is **TBD – REQUIRES VERIFICATION**.

---

## ATTENDANCE RULE / PAYROLL SETTINGS

**Tables:** `attendance_rules`, `payroll_settings` — **Evidence:** `002_workflow_schema.sql`

| Entity.Field | Rule | Enforcement |
|---|---|---|
| AttendanceRule.code | unique per tenant | DB UNIQUE |
| AttendanceRule.standard_work_hours | `NOT NULL NUMERIC(4,2)`; `0 <= value <= 24` | DB CHECK |
| AttendanceRule.grace_period_minutes | `NOT NULL DEFAULT 0`; `>= 0` | DB CHECK |
| AttendanceRule.late_after_minutes | `NOT NULL DEFAULT 0`; `>= grace_period_minutes` | DB CHECK |
| AttendanceRule.auto_clock_out_hours | Nullable; if set, `0 <= value <= 24` | DB CHECK |
| AttendanceRule.status | enum `Draft, Active, Archived` | DB CHECK |
| PayrollSettings.pay_schedule | `NOT NULL`; enum `Weekly, BiWeekly, SemiMonthly, Monthly` | DB CHECK |
| PayrollSettings.pay_day | `NOT NULL INTEGER`; `1 <= value <= 31` | DB CHECK |
| PayrollSettings.overtime_multiplier | `NOT NULL NUMERIC(4,2) >= 1` | DB CHECK |
| PayrollSettings.attendance_cutoff_days | `NOT NULL INTEGER`; `0 <= value <= 31` | DB CHECK |
| PayrollSettings.leave_deduction_mode | `NOT NULL`; enum `None, Prorated, FullDay` | DB CHECK |
| PayrollSettings.status | enum `Draft, Active, Archived` | DB CHECK |

---

## PERFORMANCE ENTITIES

**Tables:** `performance_review_cycles`, `performance_goals`, `performance_feedback`, `performance_calibrations`, `performance_pip_plans`, `performance_pip_milestones` — **Evidence:** `002_workflow_schema.sql`

| Entity.Field | Rule | Enforcement |
|---|---|---|
| ReviewCycle.code | unique per tenant | DB UNIQUE |
| ReviewCycle.review_period_start, review_period_end | Both required; `review_period_end >= review_period_start` (`chk_performance_review_cycles_period`) | DB CHECK |
| ReviewCycle.status | enum `Draft, Open, Closed` | DB CHECK |
| Goal.status | enum `Draft, Submitted, Approved, Rejected` | DB CHECK |
| Feedback.feedback_type | `NOT NULL`; enum `Manager, Peer, Self, Upward` | DB CHECK |
| Feedback.visibility | `NOT NULL`; enum `Private, Employee, ManagerAndHR` | DB CHECK |
| CalibrationSession.status | enum `Draft, Submitted, Finalized, Rejected` | DB CHECK |
| PipPlan.status | enum `Draft, Submitted, Active, Completed, Cancelled, Rejected` | DB CHECK |

Application-layer validation for performance-service (`backend/performance_api.py`, `backend/performance_service.py`) was not sampled in depth for this pass — **TBD – REQUIRES VERIFICATION** for rules beyond the DB CHECKs above.

---

## ENGAGEMENT ENTITIES (Survey / Question / Response / Answer)

**Tables:** `engagement_surveys`, `engagement_survey_questions`, `engagement_survey_responses`, `engagement_survey_answers`, `engagement_survey_aggregates` — **Evidence:** `010_engagement_service.sql`

| Entity.Field | Rule | Enforcement |
|---|---|---|
| Survey.code | unique per tenant | DB UNIQUE |
| Survey.status | enum `Draft, Open, Closed` | DB CHECK |
| SurveyQuestion.dimension | enum `D1`–`D5` | DB CHECK |
| SurveyQuestion.kind | enum `Likert5` (only value currently supported) | DB CHECK |
| SurveyQuestion.scale_min / scale_max | `DEFAULT 1` / `DEFAULT 5` | DB-only (no explicit min<max CHECK found) |
| SurveyResponse.employee_id | unique per `(tenant_id, survey_id, employee_id)` | DB UNIQUE |
| SurveyAnswer.score | `INTEGER`; `1`–`5` | DB CHECK |
| SurveyAnswer.question_id | unique per `(tenant_id, response_id, question_id)` | DB UNIQUE |

Application-layer validation for `backend/engagement_api.py` / `backend/engagement_service.py` — **TBD – REQUIRES VERIFICATION**.

---

## HELPDESK TICKET

**Table:** `helpdesk_tickets` — **Evidence:** `011_addon_domains.sql`

| Field | Rule | Enforcement |
|---|---|---|
| requester_employee_id | `NOT NULL`; references `employees` | DB-only |
| subject | `NOT NULL VARCHAR(240)` | DB-only |
| category_code | `NOT NULL VARCHAR(60)` | DB-only |
| priority | `VARCHAR(20)` | **TBD – REQUIRES VERIFICATION** — no DB CHECK enumerates allowed values (per `DOMAIN_MODEL.md`) |
| status | `VARCHAR(20)` | **TBD – REQUIRES VERIFICATION** — no DB CHECK enumerates allowed values (per `DOMAIN_MODEL.md`) |

Application-layer validation in `backend/helpdesk_api.py` / `backend/helpdesk_service.py` may define the `priority`/`status` enums at runtime — **TBD – REQUIRES VERIFICATION**.

---

## WORKFORCE COST PLAN

**Table:** `workforce_cost_plans` — **Evidence:** `011_addon_domains.sql`

| Field | Rule | Enforcement |
|---|---|---|
| period_code | unique per `(tenant_id, fiscal_year, period_code)` | DB UNIQUE |
| headcount_target | `INTEGER >= 0` | DB CHECK |

---

## CROSS-FIELD / RANGE VALIDATION SUMMARY

The following date-range and numeric-range cross-field rules are confirmed at the DB level (ground truth) across entities:

| Rule | Entities |
|---|---|
| `end_date >= start_date` | LeaveRequest, TravelRequest |
| `end_date_or_period_end >= start_date_or_period_start` | PayrollRecord (`pay_period_end >= pay_period_start`), ReviewCycle (`review_period_end >= review_period_start`) |
| `closing_date >= posting_date` (if set) | JobPosting |
| `scheduled_end > scheduled_start` | Interview |
| `arrival_at >= departure_at` | TravelItinerarySegment |
| `max_salary >= min_salary` | CompensationBand |
| Numeric `>= 0` | CompensationBand.min_salary, SalaryRevision.base_salary, Allowance.amount, TravelRequest.estimated_cost, TravelItinerarySegment.cost, WorkforceCostPlan.headcount_target |
| Numeric `1`-`5` | SurveyAnswer.score |
| Numeric `0`-`24` | AttendanceRule.standard_work_hours, AttendanceRule.auto_clock_out_hours |
| Numeric `1`-`31` | PayrollSettings.pay_day |
| Numeric `0`-`31` | PayrollSettings.attendance_cutoff_days |
| `late_after_minutes >= grace_period_minutes` | AttendanceRule |
| `carry_forward_limit_days <= annual_entitlement_days` | LeavePolicy |
| `overtime_multiplier >= 1` | PayrollSettings |

Application-layer cross-field rules NOT present as DB CHECKs (re-validated or added in service code):
- `gross_pay`/`net_pay` arithmetic consistency (PayrollRecord) — `backend/payroll_service.py`.
- `net_pay >= 0`, `payment_date >= pay_period_end` (PayrollRecord) — `backend/payroll_service.py`.
- `effective_to >= effective_from` (SalaryRevision) — `backend/payroll_service.py`.
- Leave balance sufficiency and partial-day rules (LeaveRequest) — `backend/leave_service.py`.
- Expense `amount <= category.max_amount` — `backend/expense_service.py`.

---

## GENERAL ERROR-HANDLING PATTERN

Across the services sampled (leave, hiring, expense, payroll), validation failures are surfaced as `422 VALIDATION_ERROR` (or `404 NOT_FOUND` / `409` for state-conflict cases) using the standard error envelope defined in `backend/api_contract.py` (`error_payload` / `error_response`). Unhandled `KeyError`/`TypeError`/`ValueError` exceptions during request processing are caught generically and converted to `422 VALIDATION_ERROR` with message "Invalid request payload." — **Evidence:** `backend/leave_api.py` lines 66-83 (pattern likely repeated in other `*_api.py` wrappers; not exhaustively verified — **TBD – REQUIRES VERIFICATION** for services other than leave/expense/payroll/hiring).
