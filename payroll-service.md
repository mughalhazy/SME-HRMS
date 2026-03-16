# payroll-service

This module implements the canonical `payroll-service` business workflow in code:

- `POST /payroll/records` → `PayrollService.create_payroll_record`
- `POST /payroll/run?period_start=&period_end=` → `PayrollService.run_payroll`
- `PATCH /payroll/records/{payroll_record_id}` → `PayrollService.patch_payroll_record`
- `POST /payroll/records/{payroll_record_id}/mark-paid` → `PayrollService.mark_paid`
- `GET /payroll/records/{payroll_record_id}` → `PayrollService.get_payroll_record`
- `GET /payroll/records?...` → `PayrollService.list_payroll_records`

## Security model alignment

- Write operations require `Admin` (`CAP-PAY-001`, `CAP-PAY-002` behavior).
- Employees can only read their own payroll records.
- Managers are read-only and cannot execute write operations.

## API standards alignment

- Uses canonical error envelope via `ServiceError.to_error(...)`.
- Supports cursor-based pagination for list operation (`limit`, `cursor`, `nextCursor`, `hasNext`).
- Implements payroll lifecycle transitions: `Draft` → `Processed` → `Paid`.
