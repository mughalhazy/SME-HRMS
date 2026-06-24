# Employee Service

Workforce master data and organizational structure — the authoritative source for employee identity and org hierarchy consumed by all other services.

## Scope
- Manages employee lifecycle: onboarding, status changes, profile updates, offboarding.
- Manages all organizational reference data: departments, business units, legal entities, locations, cost centers, grade bands, job positions, roles.
- Publishes authoritative employee and org change events consumed by downstream services.
- Supports dynamic schema for employee profiles (custom fields per organization).
- Supports multi-entity org hierarchy.

## HTTP surface (`/api/v1`)
- `POST /api/v1/employees`
- `GET /api/v1/employees/{employee_id}`
- `PATCH /api/v1/employees/{employee_id}`
- `GET /api/v1/employees?department_id=&status=&manager_employee_id=&limit=&cursor=`
- `POST /api/v1/departments`
- `PATCH /api/v1/departments/{department_id}`
- `GET /api/v1/departments?status=&limit=&cursor=`
- `POST /api/v1/roles`
- `PATCH /api/v1/roles/{role_id}`
- `GET /api/v1/roles?status=&limit=&cursor=`
- `POST /api/v1/org/{kind}` — create org entity (business_unit, legal_entity, location, cost_center, grade_band, job_position)
- `PATCH /api/v1/org/{kind}/{entity_id}`
- `GET /api/v1/org/{kind}?status=&department_id=&business_unit_id=&legal_entity_id=&limit=&cursor=`

## Authorization capabilities
- `CAP-EMP-001`: employee directory and lifecycle management (Admin full; Manager scoped to department; Employee read limited)
- `CAP-EMP-002`: employee profile maintenance and org assignment (Admin full; Manager for direct/indirect reports; Employee updates own profile)

## Owned entities
- `Employee`
- `Department`
- `BusinessUnit`
- `LegalEntity`
- `Location`
- `CostCenter`
- `GradeBand`
- `JobPosition`
- `Role`

## Supported workflows
- `employee_onboarding`

## Events published
- `EmployeeCreated`
- `EmployeeUpdated`
- `EmployeeStatusChanged`
- `DepartmentCreated`
- `DepartmentUpdated`
- `RoleCreated`
- `RoleUpdated`
- `BusinessUnitCreated` / `BusinessUnitUpdated`
- `LegalEntityCreated` / `LegalEntityUpdated`
- `LocationCreated` / `LocationUpdated`
- `CostCenterCreated` / `CostCenterUpdated`
- `GradeBandCreated` / `GradeBandUpdated`
- `JobPositionCreated` / `JobPositionUpdated`

## Events subscribed
- `CandidateHired` — triggers employee onboarding from recruitment handoff

## Read models produced
- `employee_directory_view`
- `organization_structure_view`
- `employee_reporting_view`
- `employee_compensation_view` (consumed by payroll-service)
- enriches: `attendance_dashboard_view`, `leave_requests_view`, `payroll_summary_view`, `job_posting_directory_view`, `candidate_pipeline_view`

## Dependencies
- `auth-service` — authentication and authorization
- `notification-service` — onboarding, status-change notifications
- `hiring-service` — upstream producer of `CandidateHired` for recruitment-driven onboarding

## Notes
- All other services treat `employee-service` as read-only source for employee and org references.
- No service should own or modify employee master data except this service.
- Supports CNIC as statutory identifier for Pakistan compliance; stored and validated per `docs/specs/country/pakistan/compliance.md`.
