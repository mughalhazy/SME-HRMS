# payroll-service

This module implements the canonical `payroll-service` business workflow in code:

- `POST /payroll/records` → `PayrollService.create_payroll_record`
- `POST /payroll/run?period_start=&period_end=` → `PayrollService.run_payroll`
- `PATCH /payroll/records/{payroll_record_id}` → `PayrollService.patch_payroll_record`
- `POST /payroll/records/{payroll_record_id}/mark-paid` → `PayrollService.mark_paid`
- `GET /payroll/records/{payroll_record_id}` → `PayrollService.get_payroll_record`
- `GET /payroll/records?...` → `PayrollService.list_payroll_records`

## Enterprise payroll engine extensions

- Payroll logic remains centralized in `PayrollService`; component evaluation, rule execution, tax abstraction, payslip generation, adjustments, and reversals are not delegated to other domain services.
- Heavy payroll execution is job-ready through `BackgroundJobService` using the existing `payroll.run` handler, with optional payslip generation in the same background workflow.
- Mutating payroll flows now use shared persistent-store transactions so payroll records, batches, reversals, adjustments, and staged outbox events commit atomically.
- Audit coverage includes payroll components, rules, tax profiles, payslips, adjustments, reversals, cycle upserts, draft generation, processing, and payment.

## Security model alignment

- Write operations require `Admin` (`CAP-PAY-001`, `CAP-PAY-002` behavior).
- Employees can only read their own payroll records.
- Managers are read-only and cannot execute write operations.

## API standards alignment

- Uses canonical error envelope via `ServiceError.to_error(...)`.
- Supports cursor-based pagination for list operation (`limit`, `cursor`, `nextCursor`, `hasNext`).
- Implements payroll lifecycle transitions: `Draft` → `Processed` → `Paid`.
