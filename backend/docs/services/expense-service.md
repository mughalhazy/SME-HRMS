# Expense Service

Employee expense reimbursement management: claim submission, receipt attachment, approval workflow, and accounting-facing export.

## Scope
- Handles reimbursements, claims, and receipts — accounting-facing, not payroll-linked finance.
- Separate from `ewa-financial-service` (which handles earned wage access and salary advances).
- Manages expense claim lifecycle from draft through approval to reimbursement.
- Supports policy-based limits and category validation.
- Exports approved claims to accounting/finance systems.

## HTTP surface (`/api/v1`)
- `POST /api/v1/expenses/claims` — submit expense claim
- `GET /api/v1/expenses/claims/{claim_id}`
- `PATCH /api/v1/expenses/claims/{claim_id}`
- `POST /api/v1/expenses/claims/{claim_id}/submit`
- `POST /api/v1/expenses/claims/{claim_id}/approve`
- `POST /api/v1/expenses/claims/{claim_id}/reject`
- `POST /api/v1/expenses/claims/{claim_id}/cancel`
- `GET /api/v1/expenses/claims?employee_id=&status=&category=&limit=&cursor=`
- `POST /api/v1/expenses/claims/{claim_id}/receipts` — attach receipt
- `GET /api/v1/expenses/reports?period=&department_id=&limit=&cursor=` — accounting export

## Claim lifecycle states
```
DRAFT → SUBMITTED → APPROVED → REIMBURSED
               → REJECTED
```

## Domain rules
- Claims require at least one receipt attachment before submission.
- Category-level spending limits enforced per policy.
- Manager approves within-policy claims; Admin required for over-limit claims.
- Approved claims are exported to accounting; not injected into payroll records.

## Authorization capabilities
- `CAP-EXP-001`: claim submission and management (Employee self-service)
- `CAP-EXP-002`: claim approval (Manager scoped, Admin)
- `CAP-EXP-003`: expense reports and accounting export (Admin, Finance)

## Owned entities
- `ExpenseClaim`
- `ExpenseReceipt`
- `ExpenseCategory`

## Supported workflows
- `expense_reimbursement`

## Events published
- `ExpenseClaimSubmitted`
- `ExpenseClaimApproved`
- `ExpenseClaimRejected`
- `ExpenseClaimReimbursed`

## Events subscribed
- `EmployeeStatusChanged` — freeze pending claims for terminated employees

## Read models produced
- `expense_claims_view` — per-employee claim status and history

## Dependencies
- `employee-service` — employee and manager context
- `auth-service` — submitter and approver authorization
- `notification-service` — submission, approval, rejection notifications
- `audit-service` — claim approval audit trail

## Notes
- Expense reimbursements are accounting-facing; do not inject into payroll deduction records.
- For payroll-linked finance (EWA, salary advances), see `docs/services/ewa-financial-service.md`.
