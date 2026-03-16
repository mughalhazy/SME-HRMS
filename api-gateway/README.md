# API Gateway

Canonical gateway entrypoints aligned with `docs/canon/service-map.md` and versioning rules in `docs/canon/api-standards.md`.

## Route groups

All routes are namespaced under `/api/v1`:

- `/api/v1/employees` → `employee-service`
- `/api/v1/attendance` → `attendance-service`
- `/api/v1/leave` → `leave-service`
- `/api/v1/payroll` → `payroll-service`
- `/api/v1/hiring` → `hiring-service`

The route registry is defined in `api-gateway/routes.py`.
