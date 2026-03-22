# project-service

Project staffing and resource-allocation management for SME-HRMS.

## Scope
- Creates project records without duplicating payroll calculations.
- Reuses `employee-service` snapshots/read models for employee, manager, and department references.
- Uses the centralized `workflow-service` for optional assignment/allocation approvals.
- Tracks allocation changes through an append-only ledger for audit and reporting use cases.

## Core operations
- `POST /api/v1/projects`
- `PATCH /api/v1/projects/{project_id}/status`
- `GET /api/v1/projects/{project_id}`
- `GET /api/v1/projects`
- `POST /api/v1/projects/assignments`
- `PATCH /api/v1/projects/assignments/{assignment_id}/allocation`
- `POST /api/v1/projects/assignments/{assignment_id}/approve`
- `POST /api/v1/projects/assignments/{assignment_id}/reject`
- `POST /api/v1/projects/assignments/{assignment_id}/release`
- `GET /api/v1/projects/assignments`

## Notes
- Approval workflows are optional and tenant-scoped.
- Allocation capacity is validated across overlapping assignments and capped at 100 percent per employee.
- Events are emitted in canonical form and staged into the outbox for downstream processing.
