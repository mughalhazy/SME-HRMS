# Alignment Report (Final Convergence)

Date: 2026-03-31
Status: ✅ Full alignment verified after end-to-end convergence pass

## Executive conclusion

Final convergence checks confirm that gateway exposure, runtime handlers, and service topology are now aligned and executable end-to-end for all declared public routes.

## 1) Re-audit outcomes

### Service topology and runtime handlers

- Revalidated runtime bootability for every declared domain service.
- Confirmed each declared domain runtime has at least one concrete executable handler and published route inventory context.

### Gateway exposure and public route execution

- Re-audited gateway route declarations and removed stale/non-executable mapping (`jobs`).
- Removed stale singular aliases (`project`, `workflow`, `integration`, `automation`) to enforce canonical public route policy.
- Verified canonical route translation behavior into runtime handler paths.

### Docs and tests

- Updated canonical wording in docs to reflect alias removal.
- Updated route compatibility tests to reject removed stale aliases.
- Expanded gateway-runtime alignment test into full declared-route execution coverage.

## 2) Evidence from executed checks (2026-03-31)

### Full regression

- `pytest -q` → `281 passed, 70 subtests passed`

### Quality/certification gates

- `python deployment/qc_validate.py` → `QC score: 11/11`
- `python deployment/re_qc_validate_master_certification.py` → `5/5`
- `python deployment/re_qc_validate_addon_convergence.py` → `5/5`
- `python deployment/re_qc_validate_data_integrity.py` → `6/6`

## 3) Final declarations

- ✅ Every declared service is runnable in runtime handler space.
- ✅ Every declared public gateway route is executable through gateway translation and downstream runtime matching.
- ✅ Stale aliases, stale docs, and dead mappings from the prior convergence state were removed.

## 4) Alignment decision

✅ **FULL ALIGNMENT DECLARED**

This final declaration is evidence-backed and gated by verified checks across:

1. gateway route contracts,
2. runtime service executability,
3. service topology completeness,
4. repository-wide regression and QC/RE-QC validators.

## 5) Pakistan compliance doc alignment update (2026-04-01)

- Implemented Pakistan slab-based tax calculation for tax years 2024, 2025, and 2026 in a shared compliance service with exact thresholds/base/rate definitions from the compliance spec.
- Implemented `validate_payroll()` checks for missing tax, invalid salary, and missing/invalid CNIC with blocking error output.
- Implemented `generate_reports()` output for FBR Annexure-C JSON, EOBI PR-01 JSON, and province-aware social security payloads (PESSI for Punjab, SESSI for Sindh, KP for Khyber Pakhtunkhwa).
- Integrated payroll run flow to map finalized payroll records into compliance input records and block completion when compliance validation fails.
- Added targeted tests to verify slab formula behavior, report schema presence, and invalid-payroll blocking.
- Added `services/compliance_autopilot.py` with `run_precheck(payroll_batch)` orchestration to always call `validate_payroll()`, block invalid payroll runs, and emit `fbr_json`, `eobi_json`, and `pessi_json` outputs from generated reports.
- Hardened submission lifecycle with persisted states `DRAFT → VALIDATED → SUBMITTED → ACKNOWLEDGED`, failure handling `FAILED → RETRY`, retry attempts, audit logging on each transition, and manual fallback utilities for export/reconcile flows.


## 6) Pakistan payroll doc alignment update (2026-04-01)

- Added `services/payroll_service.py` with spec-exact calculation flow: `gross = basic + allowances`, `taxable = gross - deductions`, `net = taxable - tax`.
- Added payroll component helpers for `gratuity()`, `provident_fund()`, and `loan_deduction()` aligned to documented component requirements.
- Added final-settlement support for leave encashment and pending deductions with explicit net settlement output.
- Added configurable frequency handling for monthly, weekly, and daily runs while preserving the same calculation order.
- Integrated payroll calculations with Pakistan country-layer `TaxEngine` and `ComplianceEngine` calls during computation.

## 7) Pakistan attendance + payroll linkage alignment update (2026-04-01)

- Added `services/attendance_service.py` to support attendance input sources `biometric`, `gps`, and `manual`.
- Added shift-assignment and worked-hours calculation primitives with overtime derived by spec rule: `hours > shift => overtime`.
- Added attendance-to-payroll sync output that exports period totals (`total_hours`, `overtime_hours`) as payroll variable inputs.
- Updated `services/payroll_service.py` to include overtime as payroll input and compute `overtime_pay = overtime_hours × overtime_rate`.
- Integrated overtime pay into gross salary calculation so payroll outputs now explicitly include `overtime_pay` in result payloads.
- Added targeted tests to verify source capture, overtime computation, attendance→payroll sync accuracy, and overtime inclusion in payroll totals.

## 8) AI Payroll Guardian decision-system alignment update (2026-04-01)

- Added `services/ai/payroll_guardian.py` with canonical anomaly detectors:
  - `detect_salary_spike()`
  - `detect_overtime_spike()`
  - `detect_missing_tax()`
  - `detect_ghost_employee()`
- Aligned outputs to decision canon scoring contract for each detector:
  - `risk_score` (0-100)
  - `confidence` (0-100)
  - `reason` in canonical `WHY_FLAGGED` explanation format with anomaly type, evidence, risk, confidence, and threshold level.
- Added targeted tests in `tests/test_payroll_guardian.py` covering anomaly detection and scoring behavior.

## 9) Recruitment experience-layer alignment update (2026-04-01)

- Added `services/recruitment/` service layer for deterministic, explainable hiring workflows aligned to the experience-layer principle of showing action + rationale.
- Implemented CV parsing for both text and PDF-like inputs with explicit extraction of `name`, `skills`, `experience`, and `education` fields.
- Implemented deterministic candidate scoring using fixed weighted logic: `70% skills match + 30% experience years`, returning both numeric score and textual explanation.
- Implemented candidate ranking sorted by descending score with stable deterministic tie-break behavior.
- Implemented interview workflow stage definitions and controlled forward-only stage transitions.
- Implemented onboarding checklist generation with deterministic task assignment across provided assignees.
- Added targeted tests validating parsing, scoring consistency, ranking order, workflow transitions, and onboarding task generation.

## 10) Employee portal experience-layer alignment update (2026-04-01)

- Added `api/employee_portal.py` with employee self-service endpoints: `/payslip`, `/leave/apply`, `/attendance`, and `/profile`.
- Enforced decision-first UX response contract on every endpoint by returning a `decision` object with `next_action`, `why`, and `confidence`.
- Implemented leave request submission flow with default `submitted` status and explicit next-step guidance.
- Implemented payslip retrieval flow with compact payroll essentials for employee self-service usage.
- Applied mobile optimization by stripping null/empty fields through compact payload shaping to minimize response size.
- Added targeted endpoint and payload tests in `tests/test_employee_portal_api.py` to validate functionality and optimization behavior.

## 11) Governance decision lifecycle alignment update (2026-04-01)

- Added `services/governance/` service module to enforce governance-level decision controls.
- Implemented payroll approval lifecycle as strict `pending -> approved/rejected` transitions.
- Enforced compliance submission gating so submissions are blocked until approval is `approved`.
- Added anomaly override control that allows override only when a non-empty reason is provided.
- Added governance audit trail records that store canonical fields: `user`, `action`, `timestamp`, and `reason`.
- Added decision lifecycle handlers aligned to canon lifecycle semantics: `create`, `update`, and `expire`.
- Added targeted tests in `tests/test_governance_service.py` covering approval enforcement, override tracking, audit completeness, and lifecycle behavior.

## 12) Experience mode and tier-logic alignment update (2026-04-01)

- Added `services/experience_layer_service.py` to centralize experience-mode toggles and deterministic feature gating.
- Implemented **SME Lite mode** toggle to simplify feature exposure while preserving core HR, attendance, leave, and basic payroll.
- Implemented **Payroll-as-a-Service** controls with managed payroll mode and admin override gating, including explicit SMB denial and Mid/Enterprise allowance.
- Added **financial wellness hooks** for loan and earned-wage-access (EWA) as executable API contracts:
  - `POST /api/v1/financial-wellness/loan`
  - `POST /api/v1/financial-wellness/ewa`
- Added tier-based feature policy for **SMB / Mid / Enterprise** with monotonic gating (`SMB ⊆ Mid ⊆ Enterprise`).
- Added focused tests in `tests/test_experience_layer_service.py` verifying mode toggles, tier gating consistency, and live hook contracts.

## 13) Face-recognition attendance → payroll alignment update (2026-04-01)

- Added `services/attendance/face_recognition.py` with deterministic face-encoding ingestion and identity matching for attendance capture.
- Added a face attendance output contract with `employee_id`, `timestamp`, and `confidence` to support downstream auditability.
- Integrated face recognition into `services/attendance_service.py` via `ingest_face_encodings()` and `record_face_attendance()` so matched identities are recorded as attendance source `face_recognition`.
- Kept attendance-to-payroll sync on the same aggregation path (`sync_attendance_to_payroll_inputs`) so face-recognized records now automatically contribute worked/overtime totals for payroll calculations.
- Added focused tests simulating matching scenarios, confidence presence, attendance recording correctness, and payroll-sync integration.
