# Bank Service

Disbursement and banking integration layer: generates bank-specific salary files, executes Raast payouts, tracks payment status, and runs reconciliation against payroll records.

## Scope
- Integration/access layer service — bridges `payroll-service` and `ewa-financial-service` to banking channels.
- Generates bank-specific salary disbursement files (per bank format requirements).
- Executes Raast (Pakistan instant payment) payouts for salary and EWA disbursements.
- Tracks payment status per employee per pay period.
- Runs reconciliation engine to match payment confirmations against payroll records.
- Does NOT own payroll calculations — it receives finalized payroll data and executes disbursement only.

## HTTP surface (`/api/v1`)
- `POST /api/v1/banking/disbursements` — initiate salary disbursement batch for a pay period
- `GET /api/v1/banking/disbursements/{disbursement_id}` — retrieve disbursement batch status
- `GET /api/v1/banking/disbursements?period=&status=&limit=&cursor=`
- `POST /api/v1/banking/disbursements/{disbursement_id}/execute` — trigger bank/Raast submission
- `GET /api/v1/banking/payments?disbursement_id=&employee_id=&status=&limit=&cursor=` — per-employee payment status
- `POST /api/v1/banking/reconcile` — run reconciliation for a disbursement batch
- `GET /api/v1/banking/reconciliation/{reconciliation_id}` — retrieve reconciliation report
- `POST /api/v1/banking/raast/payout` — single Raast payout (EWA, advance)
- `GET /api/v1/banking/accounts?employee_id=` — employee bank account details
- `POST /api/v1/banking/accounts` — register employee bank account
- `PATCH /api/v1/banking/accounts/{account_id}` — update bank account

## Disbursement lifecycle states
```
PENDING → GENERATED → SUBMITTED → CONFIRMED → RECONCILED
                                → FAILED → RETRY
```

## Domain rules
- Disbursement only allowed after `PayrollPaid` event is received (payroll-service marks as paid first).
- Raast payouts require valid IBAN or account number + CNIC match validation.
- Reconciliation flags discrepancies between expected and confirmed amounts.
- Bank account changes require audit log entry and re-verification.
- Failed payments surface as reconciliation exceptions requiring manual resolution.

## Authorization capabilities
- `CAP-BNK-001`: disbursement initiation and execution (PayrollAdmin, Admin)
- `CAP-BNK-002`: payment tracking and reconciliation (PayrollAdmin, Admin)
- `CAP-BNK-003`: bank account management (Admin; employee can view own only)

## Owned entities
- `DisbursementBatch`
- `PaymentRecord`
- `ReconciliationReport`
- `EmployeeBankAccount`

## Supported workflows
- `salary_disbursement`
- `payment_reconciliation`

## Events published
- `DisbursementBatchCreated`
- `DisbursementSubmitted`
- `DisbursementConfirmed`
- `DisbursementFailed`
- `PaymentConfirmed`
- `PaymentFailed`
- `ReconciliationCompleted`
- `ReconciliationExceptionRaised`

## Events subscribed
- `PayrollPaid` — trigger disbursement batch creation
- `EWADisbursed` — trigger Raast single payout
- `AdvanceDisbursed` — trigger Raast single payout
- `EmployeeStatusChanged` — freeze disbursements for terminated employees

## Read models produced
- `disbursement_status_view` — per-period payment tracking by employee
- `reconciliation_view` — confirmed vs. expected amounts, exception list

## Dependencies
- `payroll-service` — finalized payroll records for disbursement input
- `ewa-financial-service` — EWA and advance disbursement requests
- `employee-service` — bank account and CNIC validation context
- `audit-service` — immutable payment and reconciliation records
- `notification-service` — payment confirmation and failure alerts to employees
- Raast API — Pakistan instant payment rail
- Bank APIs — per-bank file format adapters (HBL, UBL, MCB, etc.)

## Implementation files

| Component | File |
|---|---|
| BankService (orchestrator) | `bank_service.py` |
| Banking HTTP surface | `banking_api.py` |
| Raast payment export | `integrations/pakistan/raast_payment.py` (86 lines) |
| Bank salary CSV/Excel | `integrations/pakistan/bank_salary.py` (107 lines) |
| Payment reconciliation | `integrations/pakistan/payment_reconciliation.py` (97 lines) |

`payment_reconciliation.py` implements `reconcile_payroll_payments()` — matches payment confirmations against payroll records, flags mismatches, missing payments, and failures. Called internally by `BankService.run_reconciliation()`.

## Notes
- Bank-specific salary file formats are handled by internal adapters per bank code.
- Raast is the preferred rail for instant payouts; bank file transfer is the fallback for bulk salary runs.
- All financial transactions are immutable once confirmed; corrections go through reconciliation exception flow.
