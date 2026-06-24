# Payroll Service

Core payroll engine: salary structures, tax calculation, deductions, and payout lifecycle — with zero-error accuracy as the non-negotiable target.

## Scope
- Owns the payroll record lifecycle: `DRAFT → PROCESSED → PAID → CANCELLED`.
- Orchestrates country-specific tax and rules via the country abstraction layer — no hardcoded Pakistan logic inside this service.
- Combines compensation, attendance, and leave inputs into final net pay.
- Supports: salary structures, allowances, deductions, tax (via country adapter), gratuity/PF, loans, arrears, bonuses, final settlement.
- MUST call `country_adapter.tax_engine` and `country_adapter.payroll_rules` — never compute statutory values directly.
- Blocks finalization if `compliance-service` validation gate has not passed for the same period.

## HTTP surface (`/api/v1`)
- `POST /api/v1/payroll/records` — create payroll record for an employee
- `PATCH /api/v1/payroll/records/{payroll_record_id}`
- `GET /api/v1/payroll/records/{payroll_record_id}`
- `GET /api/v1/payroll/records?employee_id=&pay_period_start=&pay_period_end=&status=&limit=&cursor=`
- `POST /api/v1/payroll/run?period_start=&period_end=` — batch payroll run for all active employees
- `POST /api/v1/payroll/records/{payroll_record_id}/process` — compute and finalize individual record
- `POST /api/v1/payroll/records/{payroll_record_id}/mark-paid` — mark as disbursed
- `POST /api/v1/payroll/records/{payroll_record_id}/cancel`

## Calculation inputs
- Base salary from `employee-service` compensation snapshot
- Allowances: HRA, conveyance, medical, utility, shift/overtime allowances
- Deductions: income tax (country adapter), provident fund, loans/advances (EWA deductions), absence/late penalties
- Attendance summary from `attendance-service` (approved/locked period)
- Leave impacts from `leave-service` (approved leave affecting pay)
- Country rules applied by `PayrollRulesInterface.apply_rules()` before tax
- Tax computed by `TaxEngineInterface.calculate_tax()` on adjusted gross

## Country abstraction rule
```
PayrollService → CountryResolver → CountryAdapter
                                 ↓
                        apply_rules() → calculate_tax()
```
Services NEVER import country modules directly. See `docs/canon/country-layer.md`.

## Authorization capabilities
- `CAP-PAY-001`: payroll processing and data access (Admin, PayrollAdmin; Manager and Employee read-scoped)
- `CAP-PAY-002`: payroll disbursement completion / mark-paid (Admin, PayrollAdmin only)

## Owned entities
- `PayrollRecord`

## Entities provided by dependencies
- `PayrollDeduction` — owned by `ewa-financial-service` per service-map.md; injected as repayment deduction inputs during payroll processing.

## Supported workflows
- `payroll_processing`

## Events published
- `PayrollDrafted`
- `PayrollProcessed`
- `PayrollPaid`
- `PayrollCancelled`

## Events subscribed
- `AttendancePeriodClosed` — trigger payroll run for the closed period
- `LeaveRequestApproved` — update leave impact on in-progress payroll records
- `EmployeeStatusChanged` — update roster for next payroll cycle
- `ComplianceValidationPassed` — unblock finalization for the validated period

## Read models produced
- `payroll_summary_view` — per-employee per-period: gross, net, deductions, status

## Dependencies
- `employee-service` — roster and compensation context
- `attendance-service` — approved/locked attendance summaries
- `leave-service` — approved leave impacts
- `compliance-service` — validation gate (blocks finalization until passed)
- `ewa-financial-service` — deduction injection for advance repayments
- `auth-service` — payroll-admin authorization
- `notification-service` — payslip-ready and payment notifications
- Country adapter (resolved at runtime via country-layer)

## Notes
- Payroll must never break: any run that cannot complete cleanly must halt and surface errors, not partially apply.
- See `docs/specs/country/pakistan/payroll.md` for Pakistan salary structure, allowances, deduction rules, and calculation spec.
- **Policy engine:** `services/payroll_policy_engine.py` — dynamic payroll policy evaluation layer (allowance rules, deduction caps, policy overrides). Invoked during payroll processing.
- **PaaS mode:** `services/payroll/paas.py` — Payroll-as-a-Service managed mode implementation. See `docs/specs/experience-layer.md`.
- **Main implementation:** `payroll_service.py` (root) — canonical implementation. `services/payroll_service.py` is a secondary wrapper; see gap G04 in `docs/system/gap-register.md`.
