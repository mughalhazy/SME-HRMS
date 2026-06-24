# VALIDATION PARITY

Status: Draft
Authority Level: Medium
Last Reviewed: 2026-06-15
Owner: AI

---

## PURPOSE

This document compares frontend-declared validation (as encoded in `contracts/hrms-h*.json` form definitions) against backend/DB validation rules documented in `docs/01_backend/VALIDATION_RULES.md`. For each entity, the parity status is one of:

- **DB only** — constraint enforced at the database layer; no corresponding frontend rule found in sampled contracts.
- **API only (application-layer)** — enforced in service code beyond the DB schema; no corresponding frontend rule found.
- **Both (parity)** — the same rule appears in both the frontend contract (as a `required`, `enum_ref`, `values`, or `min`/format constraint) and the backend/DB.
- **Frontend only** — a rule appears in the frontend contract with no confirmed backend enforcement (potential gap).
- **TBD** — insufficient evidence to classify.

## IMPORTANT CAVEAT

The `contracts/hrms-h*.json` files are **page-archetype/UI rendering contracts**, not formal API schema definitions. Most encode only:
- `required: true/false` per form field
- `enum_ref` / `values` for dropdowns and radio groups
- `type` (text, number, date, email, etc.) — a UI input-type hint, not a backend format validator
- Occasional `min` (e.g., `openings_count.min: 1`)

They generally do **not** encode range checks, cross-field rules, uniqueness constraints, or business-rule validation (balance checks, state-transition rules, etc.). Therefore, for most entities, "frontend validation" below is limited to required-field and enum-membership checks visible in form field definitions — absence of a contract-side rule does not imply the frontend performs no client-side validation; it means the contract document does not specify one.

---

## EMPLOYEE

**Source:** `contracts/hrms-h04-add-employee-contract.json` vs `docs/01_backend/VALIDATION_RULES.md` (Employee)

| Rule | Frontend (contract) | Backend/DB | Parity |
|---|---|---|---|
| first_name, last_name required | `required: true` | `NOT NULL` | **Both (parity)** |
| email (work_email) required | `required: true`, `type: email` | `NOT NULL`, unique per tenant | **Both (parity)** for required; uniqueness is **DB only** (not visible in contract) |
| employee_number required | `required: true` | `NOT NULL`, unique per tenant | **Both (parity)** for required; uniqueness **DB only** |
| hire_date required | `required: true`, `type: date` | `NOT NULL` | **Both (parity)** |
| employment_type enum | `required: true`, `values: [FullTime,PartTime,Contract,Intern]` | DB CHECK same enum | **Both (parity)** — values match exactly |
| department_id, role_id required | `required: true` | `NOT NULL` + FK | **Both (parity)** for required; FK referential integrity is **DB only** |
| status lifecycle (`Draft→Active→OnLeave→Suspended→Terminated`) | Not present in create-form contract | DB CHECK enum | **DB only** |
| date_of_birth, nationality, home_address, personal_email, preferred_name, probation_end_date | Present in form, `required: false` | **Not in `CreateEmployeeInput`** — no backend field exists | **Frontend only** (and a documented gap, BG-008) — these fields are collected by the UI but have no backend counterpart to validate against |

---

## DEPARTMENT

**Source:** `contracts/hrms-h02-departments-contract.json`, `contracts/hrms-h04-create-department-contract.json` vs VALIDATION_RULES.md (Department)

| Rule | Frontend | Backend/DB | Parity |
|---|---|---|---|
| name, code required | Not verified in detail in this pass (h04-create-department-contract.json not opened) | `NOT NULL`, unique per tenant | **TBD** |
| status enum (`Proposed, Active, Inactive, Archived`) | Filter tabs reference `status=Active`/`status=Proposed` (list contract) | DB CHECK | Filter usage confirms enum awareness on read side; create-form parity **TBD** |

---

## LEAVE REQUEST

**Source:** `contracts/hrms-h04-raise-leave-request-contract.json` vs VALIDATION_RULES.md (Leave Request)

| Rule | Frontend (contract) | Backend/DB | Parity |
|---|---|---|---|
| leave_type required | `required: true`, `values: [Annual,Sick,Casual,Unpaid]` | `NOT NULL`, DB CHECK enum `Annual,Sick,Casual,Unpaid,Other` | **Mismatch** — frontend enum is a **subset** of the backend enum: `Other` is a valid backend value but is not offered by the frontend selector. Not a validation-gap in the sense of allowing invalid data, but a **frontend restriction narrower than backend allows**. |
| start_date, end_date required | `required: true`, `type: date` for both | `NOT NULL`; `end_date >= start_date` DB CHECK + app-level re-check | **Partial parity** — required-ness matches; the `end_date >= start_date` range rule is **not encoded in the contract** (no `min`/cross-field rule visible) — **Backend only** for the range check |
| total_days | Computed client-side ("calculated client-side from start_date/end_date excluding weekends") | `NOT NULL NUMERIC(4,1)`, no DB range CHECK; leave balance sufficiency checked in `leave_service.py` | **Frontend computes, backend re-validates balance** — the balance-sufficiency check (`Requested leave exceeds available balance`) has **no frontend-visible equivalent** in the contract (balances shown are BG-006 mock data) — **Backend only** |
| reason | `required: false` | Nullable `TEXT` | **Both (parity)** |
| approver_employee_id | `required: false` | Nullable FK | **Both (parity)** for optionality; backend additionally requires a resolvable approver in some flows (expense-service pattern) — for leave specifically, approver resolution rules are **TBD – REQUIRES VERIFICATION** |
| partial_day_portion (0.5/1.0) | `half_day` toggle maps to `partial_day_portion (0.5 if true, 1.0 if false)` | App-level: must be `0.5` or `1.0`; only valid if policy allows partial-day and request is single-day | **Both (parity)** for the binary toggle representation; the **policy-dependent eligibility check** (partial-day allowed only if `LeavePolicy.allows...` and single-day) is **Backend only** — not encoded in the frontend contract |

---

## PAYROLL RECORD / SALARY REVISION

**Source:** `contracts/hrms-h04-salary-revision-contract.json`, `contracts/hrms-h02-payroll-records-contract.json` vs VALIDATION_RULES.md (Payroll Record, Salary Revision)

| Rule | Frontend | Backend/DB | Parity |
|---|---|---|---|
| base_salary required | `required: true`, `type: number` | DB CHECK `base_salary >= 0` (salary_revisions) | **Partial parity** — required-ness matches; the `>= 0` range constraint is **not visible in the contract** (no `min` specified) — **Backend (DB) only** for the range |
| currency required | `required: true`, `type: select` | `NOT NULL CHAR(3)`; app-level `must be a 3-letter ISO code` | **Both (parity)** for required; ISO-code format validation is **Backend (application) only** |
| effective_from required | `required: true`, `type: date` | `NOT NULL DATE` | **Both (parity)** |
| effective_to optional | `required: false` | Nullable; app-level `effective_to >= effective_from` if set | **Partial parity** — optionality matches; the cross-field date-order rule is **Backend (application) only** |
| reason (revision_reason) | `required: true`, `values: [Annual Review, Promotion, Market Adjustment, Performance Bonus, Retention, Other]` | DB: `reason TEXT` nullable, no enum CHECK | **Mismatch** — frontend imposes a **closed enum** that the backend schema does **not** enforce (DB column is free-text `TEXT`). Frontend is *more* restrictive than backend here — **Frontend only** for the enum constraint |
| pay_period_end >= pay_period_start | Not present in any sampled payroll contract field definition | DB CHECK `chk_payroll_records_period` + app-level re-check | **Backend only** |
| net_pay >= 0 | Not present in contract | App-level only (`backend/payroll_service.py`); **no DB CHECK** | **Backend (application) only** |

---

## JOB POSTING

**Source:** `contracts/hrms-h04-create-job-posting-contract.json` vs VALIDATION_RULES.md (Job Posting)

| Rule | Frontend | Backend/DB | Parity |
|---|---|---|---|
| title required | `required: true` | `NOT NULL VARCHAR(200)` | **Both (parity)** |
| department_id required | `required: true` | `NOT NULL` + FK | **Both (parity)** |
| employment_type enum | `required: true`, `values: [FullTime,PartTime,Contract,Intern]` | DB CHECK same enum | **Both (parity)** — exact match |
| openings_count >= 1 | `required: true`, `min: 1` | DB CHECK `openings_count >= 1` + app-level re-check | **Both (parity)** — exact match, including the numeric bound |
| posting_date required | `required: true` | `NOT NULL DATE` | **Both (parity)** |
| closing_date optional, >= posting_date | `required: false` (no cross-field rule shown) | DB CHECK `chk_job_postings_dates` + app-level re-check | **Partial parity** — optionality matches; `>= posting_date` rule **not encoded in contract** — **Backend only** |
| status initial values | `values: [Open, Draft]`, default `Open` | DB CHECK enum `Draft, Open, OnHold, Closed, Filled` (full set) | **Partial parity** — frontend restricts the *creatable* initial states to a safe subset of the full backend enum; this is consistent (not a violation) since `OnHold/Closed/Filled` are reached via later transitions, not creation |
| hiring_plan shape (salary_range, required_skills, pipeline_template_id, etc.) | Present as individual form fields, all `required: false` | JSONB field with **no DB-level schema validation**; app-level only checks `must_have_skills must be a list` and `each pipeline stage must be an object` | **Frontend collects more structured detail than backend validates** — backend validation of `hiring_plan` substructure is shallow (type-only checks) — **Backend (application) partial; mostly unvalidated** |

---

## CANDIDATE / HIRING PIPELINE

**Source:** `contracts/hrms-h13-candidate-pipeline-contract.json` vs VALIDATION_RULES.md (Candidate)

The sampled pipeline contract is a **read-only Kanban view** (`GET /api/v1/hiring/pipeline`) and does not define a create/edit form with validation rules. Candidate creation/transition rules (status-transition state machine, email-uniqueness-per-job-posting, `candidates can only be created for Open/OnHold job postings`) are **application-layer only** (`backend/services/hiring_service/service.py`) with **no frontend-contract equivalent found** in this pass.

| Rule | Frontend | Backend | Parity |
|---|---|---|---|
| status transition validity | Kanban drag-and-drop implies transitions but contract does not enumerate a transition table | App-level `invalid candidate status transition: {from} -> {to}` | **Backend only** |
| email uniqueness per job posting | Not in pipeline contract | DB UNIQUE `(tenant_id, job_posting_id, email)` + app-level re-check | **Backend (DB + application)** — **TBD** whether candidate-creation contract (not sampled) encodes this |

---

## ATTENDANCE RECORD

**Source:** `contracts/hrms-h02-attendance-records-contract.json` vs VALIDATION_RULES.md (Attendance Record)

The sampled contract is a **list/read view only** — no create/edit form was found for attendance records in the sampled set. Therefore frontend-side validation for attendance cannot be assessed from this contract.

| Rule | Frontend | Backend/DB | Parity |
|---|---|---|---|
| attendance_status enum (`Present,Absent,Late,HalfDay,Holiday`) | `enum_ref` used for display/filter chip only | DB CHECK | **Read-side parity only** — both reference the same enum for display/filtering, but no create-form comparison available |
| source enum (`Manual,Biometric,APIImport`) | `enum_ref` for display | DB CHECK | **Read-side parity only** |
| `lifecycle_state` / `record_state` field | Present in list contract (`enum_ref: Attendance.record_state`) | **Not present in `attendance_records` table DDL** | **Frontend only / unverified backend field** — see also `DATA_SHAPE_REGISTRY.md` note; this field's backend existence is **TBD – REQUIRES VERIFICATION** |

---

## EXPENSE CLAIM

**Source:** `contracts/hrms-h04-raise-expense-claim-contract.json` (not opened field-by-field in this pass) vs VALIDATION_RULES.md (Expense Claim)

Backend application-layer validation for expense claims is extensive (category-based amount limits, attachment requirements, state-machine transitions, approver resolution — see `backend/expense_service.py`). Whether these rules are mirrored in the frontend contract's form-field definitions is **TBD – REQUIRES VERIFICATION** — the create-expense-claim contract was not opened in this research pass.

---

## TRAVEL REQUEST

**Source:** `contracts/hrms-h04-raise-travel-request-contract.json` (not opened field-by-field) vs VALIDATION_RULES.md (Travel Request)

Per `DOMAIN_MODEL.md`, travel-service is **PLANNED (not functionally complete)** (F-023). DB-level CHECK constraints exist (`end_date >= start_date`, `estimated_cost >= 0`, status enum), but application-layer validation parity is **TBD – REQUIRES VERIFICATION** for both frontend and backend.

---

## OVERALL OBSERVATIONS

1. **Required-field parity is generally good** for the entities sampled (Employee, Leave Request, Job Posting, Salary Revision) — fields marked `required: true` in the frontend contracts correspond to `NOT NULL` columns or app-level required checks.

2. **Enum parity is good where the frontend offers a full or matching subset** of the backend enum (e.g., `employment_type` matches exactly for Employee and JobPosting). One narrowing case was found: LeaveRequest.leave_type — frontend omits `Other` from the selector while the backend/DB allow it.

3. **One frontend-only enum constraint was found**: SalaryRevision.reason is a free-text `TEXT` column in the DB with no CHECK, but the frontend contract restricts it to a 6-value pill-selector enum. This means the backend would accept any string for `reason` even though the UI never sends anything outside that list — a latent validation gap if any other client (API caller) submits a different value.

4. **Cross-field/range rules (date-order, numeric minimums beyond `openings_count >= 1`, balance sufficiency, arithmetic consistency) are essentially never encoded in the sampled frontend contracts.** These are uniformly **Backend only** (DB CHECK and/or application-layer). This is expected given the contracts are UI-rendering archetypes, not API schemas, but it means **frontend forms could submit data violating these rules** and would rely entirely on the backend's `422 VALIDATION_ERROR` response for rejection — no contract evidence of client-side pre-validation for these cases.

5. **One unverified field** (`lifecycle_state`/`record_state` on AttendanceRecord) appears in a frontend contract without a corresponding DB column — flagged as TBD for both this document and `DATA_SHAPE_REGISTRY.md`.

6. Several entities (Department create form, Expense Claim, Travel Request, Candidate create form, Performance Review, Engagement Survey) were **not sampled field-by-field** in this pass and are marked TBD throughout — a follow-up pass should open the corresponding `hrms-h04-*` create-form contracts for each.
