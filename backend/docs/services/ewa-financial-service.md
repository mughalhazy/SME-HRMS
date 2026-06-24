# EWA Financial Service

Payroll-linked financial services: earned wage access (EWA) and salary advances with automated payroll deduction repayment.

## Scope
- Separate from `expense-service` (which handles reimbursements and accounting-facing claims).
- Manages employee-initiated access to earned but unpaid wages before pay day.
- Manages salary advance requests with structured repayment schedules.
- Integrates with `payroll-service` for deduction injection at payroll run time.
- Enforces eligibility rules (tenure, active employment, outstanding advance limits).

## HTTP surface (`/api/v1`)
- `POST /api/v1/financial-wellness/ewa` — request earned wage access disbursement
- `GET /api/v1/financial-wellness/ewa/{request_id}` — retrieve EWA request status
- `GET /api/v1/financial-wellness/ewa?employee_id=&status=&limit=&cursor=`
- `POST /api/v1/financial-wellness/loan` — request salary advance
- `GET /api/v1/financial-wellness/loan/{loan_id}` — retrieve advance/loan status
- `GET /api/v1/financial-wellness/loan?employee_id=&status=&limit=&cursor=`
- `GET /api/v1/financial-wellness/eligibility/{employee_id}` — check EWA + advance eligibility
- `GET /api/v1/financial-wellness/repayment-schedule/{loan_id}` — view deduction schedule

## Domain rules
- EWA disbursement capped at configurable percentage of earned (accrued) wages for the current period.
- Salary advance repayment is deducted from future payroll runs; deduction injected as a `PayrollDeduction` record.
- Only one active advance per employee at a time (configurable per policy).
- Advance request requires approval for amounts above threshold.
- Disbursement routed through `bank-service` (Raast or bank transfer).
- All disbursements and deductions are audit-logged.

## Authorization capabilities
- `CAP-EWA-001`: EWA request and status (Employee self-service, Admin)
- `CAP-EWA-002`: advance request and approval (Employee initiates, Manager/Admin approves)
- `CAP-EWA-003`: repayment schedule and deduction management (PayrollAdmin, Admin)

## Owned entities
- `EWARequest`
- `SalaryAdvance`
- `RepaymentSchedule`
- `PayrollDeduction` (deduction records injected into payroll)

## Supported workflows
- `ewa_disbursement`
- `advance_request`

## Events published
- `EWARequested`
- `EWAApproved`
- `EWADisbursed`
- `EWARejected`
- `AdvanceRequested`
- `AdvanceApproved`
- `AdvanceDisbursed`
- `AdvanceRejected`
- `RepaymentDeductionInjected`

## Events subscribed
- `PayrollProcessed` — trigger deduction collection for active repayment schedules
- `EmployeeStatusChanged` — freeze disbursements for inactive/terminated employees
- `AttendancePeriodClosed` — update accrued wage calculation basis for EWA eligibility

## Read models produced
- `financial_wellness_view` — employee EWA balance, advance status, repayment schedule

## Dependencies
- `payroll-service` — earned wage calculation basis, deduction injection
- `employee-service` — employment status, tenure, compensation context
- `bank-service` — disbursement execution (Raast / bank transfer)
- `auth-service` — authorization for advance approval
- `notification-service` — EWA approval, disbursement, repayment reminders
- `audit-service` — immutable financial transaction records

## Notes
- `expense-service` handles reimbursements (claims, receipts, approvals) and is accounting-facing.
- This service handles payroll-linked finance only. Do not merge.
- Endpoints `/api/v1/financial-wellness/loan` and `/api/v1/financial-wellness/ewa` are the canonical stable contracts per `docs/specs/experience-layer.md`.
- **Existing implementation:** `services/finance/ewa.py` — contains `FinancialWellnessService` (salary advance request, approval, payroll deduction) and executable `loan_request()` / `salary_advance()` contract functions. This is the implementation base for this service.
