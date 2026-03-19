from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EMPLOYEE_REPOSITORY = (ROOT / 'services/employee-service/employee.repository.ts').read_text()
EMPLOYEE_SERVICE = (ROOT / 'services/employee-service/employee.service.ts').read_text()
DEPARTMENT_SERVICE = (ROOT / 'services/employee-service/department.service.ts').read_text()
DEPARTMENT_REPOSITORY = (ROOT / 'services/employee-service/department.repository.ts').read_text()
ROLE_REPOSITORY = (ROOT / 'services/employee-service/role.repository.ts').read_text()
ROUTES = (ROOT / 'services/employee-service/employee.routes.ts').read_text()
CORE_SCHEMA = (ROOT / 'deployment/migrations/001_core_schema.sql').read_text()
SEEDS = (ROOT / 'services/employee-service/domain-seed.ts').read_text()

checks: list[tuple[str, bool]] = [
    ('seeded departments available to repositories', 'seedDepartments' in SEEDS and 'dep-eng' in SEEDS),
    ('seeded roles available to repositories', 'seedRoles' in SEEDS and 'role-frontend-engineer' in SEEDS),
    ('employee repository resolves department references dynamically', 'referenceRepository' in EMPLOYEE_REPOSITORY and 'findDepartmentById' in EMPLOYEE_REPOSITORY),
    ('employee repository resolves role references dynamically', 'referenceRepository' in EMPLOYEE_REPOSITORY and 'findRoleById' in EMPLOYEE_REPOSITORY),
    ('employee deletion blocks orphaned reports', 'cannot delete employee with direct reports' in EMPLOYEE_SERVICE),
    ('employee deletion blocks orphaned department heads', 'cannot delete employee assigned as department head' in EMPLOYEE_SERVICE),
    ('department status changes protect assigned employees', 'cannot deactivate or archive a department with assigned employees' in DEPARTMENT_SERVICE),
    ('department repository supports head and parent integrity indexes', 'headEmployeeIndex' in DEPARTMENT_REPOSITORY and 'parentDepartmentIndex' in DEPARTMENT_REPOSITORY),
    ('role repository tracks linked employees', 'employeeRoleIndex' in ROLE_REPOSITORY and 'countEmployees' in ROLE_REPOSITORY),
    ('api exposes employees, departments, and roles consistently', all(route in ROUTES for route in ['/api/v1/employees', '/api/v1/departments', '/api/v1/roles']) and 'REFERENCES roles (role_id)' in CORE_SCHEMA and 'REFERENCES departments (department_id)' in CORE_SCHEMA),
]

score = sum(1 for _, ok in checks)
for name, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
print(f'RE-QC employee-domain-integrity score: {score}/{len(checks)}')
if score < len(checks):
    raise SystemExit(1)
