# DATA SHAPE REGISTRY

Status: Draft
Authority Level: High
Last Reviewed: 2026-06-15
Owner: AI

---

## PURPOSE

This document registers the API-exposed data shape (`data` payload inside the standard response envelope defined in `backend/api_contract.py`) for each major domain entity, as evidenced by `contracts/hrms-h*.json` frontend page-archetype contracts cross-referenced against `docs/00_authority/DOMAIN_MODEL.md`.

**Standard envelope (Evidence: `backend/api_contract.py`, `backend/docs/canon/api-standards.md`):**
```json
{
  "status": "success | error",
  "data": {},
  "meta": { "request_id": "", "timestamp": "", "pagination": {} },
  "error": null
}
```
For list endpoints, `data` follows the `list_payload` shape from `api_contract.py`: `{"items": [...], ...extra}` (optionally with a `legacy_key` duplicate array for backward compatibility — usage of `legacy_key` per-service is **TBD – REQUIRES VERIFICATION**).

---

## NAMING CONVENTION FINDING

All sampled contracts use **snake_case** for entity field names and query parameters (e.g., `employee_id`, `start_date`, `attendance_status`, `department_id`), consistent with DB column names in the migrations and with `api-standards.md` §1 ("Use snake_case for query-parameter names"). 

The only camelCase strings found in `contracts/hrms-h*.json` are **URL path placeholders** such as `:employeeId`, `:requestId` (e.g., `PATCH /api/v1/employees/:employeeId/department` in `hrms-h03-employee-profile-contract.json`). These are templating placeholders in the contract documents, not actual field names in request/response payloads — the corresponding query parameters and body fields use `employee_id` (snake_case). **No DB-to-API field renaming was found** in the sampled contracts; field names appear to pass through unchanged from DB column name → API payload → frontend field key.

---

## EMPLOYEE

**DB table:** `employees` (`001_core_schema.sql`) | **Service:** employee-service (port 8001)

| DB column | API/contract field | Notes |
|---|---|---|
| employee_id | employee_id | UUID |
| employee_number | employee_number | |
| first_name, last_name | first_name, last_name | Displayed via `avatar_name_id` component |
| email | email | |
| phone | phone | |
| hire_date | hire_date | `format: date_short` |
| employment_type | employment_type | enum ref `api-contracts#Employee.employment_type` |
| status | status | enum ref `api-contracts#Employee.status`, rendered as `chip` |
| department_id | department_id | resolved to `department_name` for display |
| role_id | role_id | resolved to `role_title` for display |
| manager_employee_id | manager_id | Used in `CreateEmployeeInput.manager_id` (h04-add-employee) |

**List endpoint:** `GET /api/v1/employees?status=&department_id=&employment_type=&limit=&offset=` — **Evidence:** `contracts/hrms-h02-employees-contract.json`
**Create endpoint:** `POST /api/v1/employees`, body = `CreateEmployeeInput` — **Evidence:** `contracts/hrms-h04-add-employee-contract.json`

`CreateEmployeeInput` fields confirmed by contract: `first_name, last_name, email, employee_number, hire_date, employment_type, location_name, department_id, role_id, job_title, manager_id`.

**Gap (BG-008):** Frontend form collects `date_of_birth, nationality, home_address, personal_email, preferred_name, probation_end_date` — these are **not part of `CreateEmployeeInput`** and are not transmitted to the backend. They do not appear in the API data shape.

**Delete endpoint:** `DELETE /api/v1/employees/:employeeId` — **Evidence:** `contracts/hrms-h02-employees-contract.json`

---

## DEPARTMENT

**DB table:** `departments` (`001_core_schema.sql`) | **Service:** employee-service (port 8001)

| DB column | API/contract field |
|---|---|
| department_id | department_id |
| name | name |
| code | code |
| parent_department_id | parent_department_id |
| head_employee_id | head_employee_id |
| status | status (enum ref `Department.status`: `Proposed, Active, Inactive, Archived`) |

**List endpoint:** `GET /api/v1/departments` — **Evidence:** `contracts/hrms-h02-departments-contract.json`
**Create endpoint:** `POST /api/v1/departments` — **Evidence:** `contracts/hrms-h02-departments-contract.json`, `contracts/hrms-h04-create-department-contract.json`

---

## ROLE

**DB table:** `roles` (`001_core_schema.sql`) | **Service:** employee-service (port 8001)

| DB column | API/contract field |
|---|---|
| role_id | role_id |
| title | title |
| level | level |
| employment_category | employment_category (enum `Staff, Manager, Executive, Contractor`) |
| status | status (enum `Draft, Active, Inactive, Archived`) |
| permissions | permissions |

**List endpoint:** `GET /api/v1/roles` — used as a `source` for selects in `contracts/hrms-h04-add-employee-contract.json`, `hrms-h04-create-job-posting-contract.json`.
**Detail/create:** `contracts/hrms-h02-roles-contract.json`, `contracts/hrms-h03-role-detail-contract.json`, `contracts/hrms-h04-create-role-contract.json`.

---

## ATTENDANCE RECORD

**DB table:** `attendance_records` (`002_workflow_schema.sql`) | **Service:** attendance-service (port 8002)

| DB column | API/contract field |
|---|---|
| attendance_id | (row identity — not shown as a column in h02 table) |
| employee_id | employee (rendered as `avatar_name_id`) |
| attendance_date | attendance_date (`format: date_short`) |
| attendance_status | attendance_status (enum ref `Attendance.status`, rendered as `chip`) |
| check_in_time | check_in_time (`format: time`) |
| check_out_time | check_out_time (`format: time`) |
| total_hours | total_hours |
| source | source (enum ref `Attendance.source`) |
| (not in DB schema) | lifecycle_state — **enum ref `Attendance.record_state`; this field is NOT present in the `attendance_records` table DDL (`002_workflow_schema.sql`)**. Source is **TBD – REQUIRES VERIFICATION** — likely a derived/computed field added by the service layer or a contract-only field not yet implemented. |

**List endpoint source:** `attendance_service › AttendanceRecord (paginated)` — **Evidence:** `contracts/hrms-h02-attendance-records-contract.json`

---

## LEAVE REQUEST

**DB table:** `leave_requests` (`002_workflow_schema.sql`) | **Service:** leave-service (port 8003)

| DB column | API/contract field |
|---|---|
| leave_request_id | leave_request_id |
| leave_type | leave_type (enum ref `Leave.type`) |
| start_date | start_date |
| end_date | end_date |
| total_days | total_days (displayed with "days" suffix) |
| reason | reason |
| approver_employee_id | approver_employee_id |
| status | status (enum ref `LEAVE_REQUEST_STATUSES`) |
| submitted_at | submitted_at |
| decision_at | decision_at |

**List endpoint:** `GET /api/v1/leave/requests?status=&employee_id=&leave_type=&limit=&offset=` — **Evidence:** `contracts/hrms-h02-leave-requests-contract.json`
**Detail endpoint:** `GET /api/v1/leave/requests/:requestId` — **Evidence:** `contracts/hrms-h03-leave-request-detail-contract.json`, fields: `leave_request_id, leave_type, start_date, end_date, total_days, reason, approver_employee_id, status, submitted_at, decision_at` (exact 1:1 match with DB columns, minus `tenant_id`/`employee_id` which are implicit context).
**Decision action:** `PATCH /api/v1/leave/requests/:requestId → status=Approved` — **Evidence:** `contracts/hrms-h03-leave-request-detail-contract.json`
**Create endpoint:** `POST /api/v1/leave/requests`, body fields: `leave_type, start_date, end_date, reason, approver_employee_id, partial_day_portion` — **Evidence:** `contracts/hrms-h04-raise-leave-request-contract.json`. Note: `partial_day_portion` is a request-only field (0.5 / 1.0) that does not map to a DB column directly (see `VALIDATION_RULES.md` — LeaveRequest).

---

## PAYROLL RECORD

**DB table:** `payroll_records` (`002_workflow_schema.sql`) | **Service:** payroll-service (port 8004)

| DB column | API/contract field |
|---|---|
| payroll_record_id | (row identity) |
| employee_id | employee |
| pay_period_start, pay_period_end | period (combined display) |
| base_salary, allowances, deductions, overtime_pay | itemized in detail view |
| gross_pay | total_gross (aggregate at list level is BG-001/BG-005 mock only) |
| net_pay | total_net (aggregate at list level is BG-001/BG-005 mock only) |
| currency | currency |
| payment_date | payment_date |
| status | status (enum ref `PayrollRecord.status`: `Draft, Processed, Paid, Cancelled`) |

**List endpoint:** `GET /api/v1/payroll/records?status=&period_start=&period_end=&department_id=&limit=&offset=` — **Evidence:** `contracts/hrms-h02-payroll-records-contract.json`
**Run payroll:** `POST /api/v1/payroll/run` — **Evidence:** `contracts/hrms-h02-payroll-records-contract.json`
**Detail:** `contracts/hrms-h03-payroll-record-detail-contract.json`

**Gap (BG-001/BG-005):** No aggregate-totals endpoint exists; `total_gross`/`total_net`/`anomalies` stats are mock/client-aggregated, not part of the confirmed API data shape.

---

## SALARY REVISION

**DB table:** `salary_revisions` (`012_compensation_domain.sql`) | **Service:** payroll-service (compensation controller, employee-service routed)

| DB column | API/contract field |
|---|---|
| employee_id | employee_id |
| base_salary | base_salary |
| currency | currency |
| effective_from | effective_from |
| effective_to | effective_to |
| reason | reason (free-text in DB; frontend constrains to a pill-selector enum: `Annual Review, Promotion, Market Adjustment, Performance Bonus, Retention, Other`) |
| compensation_band_id | compensation_band_id |
| status | status (DB default `Draft`; frontend submission defaults to `Approved`) |

**Create endpoint:** `POST /api/v1/compensation/employees/:employeeId/salary-revisions` — **Evidence:** `contracts/hrms-h04-salary-revision-contract.json`
**History endpoint:** `GET /api/v1/compensation/employees/:employeeId/salary-revisions` — same contract.

**Naming/type note:** The contract types `base_salary` as `"string (required)"` in the request body even though the DB column is `NUMERIC(12,2)`. This may reflect JSON-transport-as-string for decimals — **TBD – REQUIRES VERIFICATION** whether the API actually accepts a string or a JSON number for `base_salary`.

---

## JOB POSTING

**DB table:** `job_postings` (`002_workflow_schema.sql`) | **Service:** hiring-service (port 8005)

| DB column | API/contract field |
|---|---|
| job_posting_id | job_posting_id |
| title | title |
| department_id | department_id |
| role_id | role_id |
| employment_type | employment_type (enum ref `employee.model.EMPLOYMENT_TYPES`) |
| location | location |
| description | description |
| openings_count | openings_count |
| posting_date | posting_date |
| closing_date | closing_date |
| status | status (enum `Draft, Open, OnHold, Closed, Filled`) |
| (not in DB schema) | hiring_manager_id, recruiter_ids — **contract-level fields, not present as columns in `job_postings` (`002_workflow_schema.sql`)**. Likely stored inside the `hiring_plan` JSONB or a related table — **TBD – REQUIRES VERIFICATION**. |
| (not in DB schema) | hiring_plan (dict: `required_skills`, `min_experience`, `education_level`, `salary_range.{min,max,currency}`, `salary_visibility`, `pipeline_template_id`) — JSONB field, not individually enumerated in migration DDL; shape is contract-defined only. |

**List endpoint:** `GET /api/v1/job-postings` (implied by `contracts/hrms-h02-job-postings-contract.json`)
**Create endpoint:** `POST /api/v1/job-postings` — **Evidence:** `contracts/hrms-h04-create-job-posting-contract.json`
**Detail:** `contracts/hrms-h03-job-posting-detail-contract.json`

---

## CANDIDATE

**DB table:** `candidates` (`002_workflow_schema.sql`) | **Service:** hiring-service (port 8005)

| DB column | API/contract field |
|---|---|
| candidate_id | candidate_id |
| job_posting_id | job_posting_id |
| first_name, last_name | first_name, last_name |
| email | email |
| phone | phone |
| resume_url | resume_url |
| source | source (enum `Referral, JobBoard, CareerSite, Agency, LinkedIn, Other`) |
| source_candidate_id, source_profile_url | source_candidate_id, source_profile_url |
| application_date | application_date |
| status | status (enum ref `Hiring.pipeline.stage`; lifecycle `Applied → Screening → Interviewing → Offered → Hired \| Rejected \| Withdrawn`) |

**Pipeline (kanban) endpoint:** `GET /api/v1/hiring/pipeline?pipeline_stage=&department_id=&job_posting_id=`, response shape `{"candidates": "Candidate[]", "total": "int"}` — **Evidence:** `contracts/hrms-h13-candidate-pipeline-contract.json`. Note: this response shape (`candidates` + `total` directly under `data`) differs from the generic `{"items": [...]}` `list_payload` convention in `api_contract.py` — **TBD – REQUIRES VERIFICATION** whether `candidates`/`total` are top-level `data` keys or nested under `items`.

---

## CANDIDATE STAGE TRANSITION / INTERVIEW

**DB tables:** `candidate_stage_transitions`, `interviews` (`002_workflow_schema.sql`) | **Service:** hiring-service (port 8005)

Field shapes for these entities were not directly sampled from a dedicated list/detail contract in this pass. DB columns (per `DOMAIN_MODEL.md`): 
- CandidateStageTransition: `candidate_stage_transition_id, candidate_id, from_status, to_status, changed_at, changed_by, reason, notes`
- Interview: `interview_id, candidate_id, interview_type, scheduled_start, scheduled_end, location_or_link, interviewer_employee_ids, feedback_summary, recommendation, status`

API exposure shape — **TBD – REQUIRES VERIFICATION** (likely surfaced via candidate-detail panel in `hrms-h13-candidate-pipeline-contract.json`, not fully read in this pass).

---

## TRAVEL REQUEST

**DB table:** `travel_requests` (`013_travel_domain.sql`) | **Service:** travel-service (port 8018, PLANNED per F-023)

| DB column | API/contract field |
|---|---|
| travel_request_id | travel_request_id |
| employee_id | employee_id |
| manager_employee_id | manager_employee_id |
| purpose | purpose |
| destination | destination |
| start_date, end_date | start_date, end_date |
| status | status (enum `Draft, Submitted, Approved, Rejected, Booked, Completed, Cancelled`) |
| estimated_cost | estimated_cost |
| currency | currency |

**Contracts:** `contracts/hrms-h02-travel-requests-contract.json` (list), `contracts/hrms-h04-raise-travel-request-contract.json` (create). Field-level mapping not individually verified in this pass beyond DB column names — **TBD – REQUIRES VERIFICATION** for any additional contract-only fields (analogous to `hiring_manager_id`/`recruiter_ids` pattern seen in JobPosting).

---

## EXPENSE CLAIM

**DB table:** Not located in `001`–`013` migrations (table DDL **TBD – REQUIRES VERIFICATION**) | **Service:** expense-service (port 8015)

**Contracts:** `contracts/hrms-h02-expense-claims-contract.json` (list), `contracts/hrms-h03-expense-claim-detail-contract.json` (detail), `contracts/hrms-h04-raise-expense-claim-contract.json` (create).

Based on `backend/expense_service.py` validation logic (see `VALIDATION_RULES.md`), the entity carries at minimum: `employee_id`, `category_code`, `amount`, `description`, `attachments[]`, `approver_employee_id`, `status` (Draft/Submitted/Approved/Rejected/Reimbursed — exact enum **TBD – REQUIRES VERIFICATION**, not confirmed against a CHECK constraint).

---

## PERFORMANCE REVIEW (Review Cycle / Goal / Feedback / Calibration / PIP)

**DB tables:** `performance_review_cycles`, `performance_goals`, `performance_feedback`, `performance_calibrations`, `performance_pip_plans`, `performance_pip_milestones` (`002_workflow_schema.sql`) | **Service:** performance-service (port 8010)

**Contracts:** `contracts/hrms-h02-performance-reviews-contract.json` (list), `contracts/hrms-h03-performance-review-detail-contract.json` (detail). Field names not individually re-verified against the DB column list in this pass beyond what's in `DOMAIN_MODEL.md`; assumed snake_case 1:1 pass-through consistent with the pattern observed for Employee/Leave/Department.

---

## SUMMARY: PAGINATION SHAPE

Per `backend/api_contract.py` (`pagination_payload`), `meta.pagination` carries `{limit, cursor, next_cursor, count, ...extra}`. Frontend contracts (e.g., `hrms-h02-employees-contract.json`) reference `limit`/`offset`-style query params (`?limit=&offset=`) in several list endpoints, which is **offset-based**, while `api-standards.md` §5 states cursor pagination is the default with `limit`/`cursor`/`next_cursor`/`count`. This is a discrepancy between the documented pagination standard and the `offset=` query parameters shown in multiple `hrms-h02-*` list contracts (employees, leave-requests, payroll-records, attendance-records). Flagged here as observed; not resolved — **TBD – REQUIRES VERIFICATION** which pagination style each service actually implements.
