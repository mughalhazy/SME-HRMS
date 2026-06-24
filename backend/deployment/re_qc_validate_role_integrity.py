from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EMPLOYEE_SERVICE = (ROOT / 'services/employee-service/employee.service.ts').read_text()
ROLE_SERVICE = (ROOT / 'services/employee-service/role.service.ts').read_text()
ROLE_REPOSITORY = (ROOT / 'services/employee-service/role.repository.ts').read_text()
CORE_SCHEMA = (ROOT / 'deployment/migrations/001_core_schema.sql').read_text()

checks: list[tuple[str, bool]] = [
    ('employee assignment validates active role', 'getActiveRoleById' in EMPLOYEE_SERVICE),
    ('employee-role linkage maintained on create/update/delete', all(token in EMPLOYEE_SERVICE for token in ['linkEmployee', 'relinkEmployee', 'unlinkEmployee'])),
    ('roles cannot be deleted with linked employees', 'cannot delete role with assigned employees' in ROLE_SERVICE),
    ('role repository tracks employee assignments', 'employeeRoleIndex' in ROLE_REPOSITORY and 'assignEmployee' in ROLE_REPOSITORY and 'unassignEmployee' in ROLE_REPOSITORY),
    ('schema keeps referential integrity', 'REFERENCES roles (role_id)' in CORE_SCHEMA and 'ON DELETE RESTRICT' in CORE_SCHEMA),
]

score = sum(1 for _, ok in checks)
for name, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
print(f'RE-QC role-integrity score: {score}/{len(checks)}')
if score < len(checks):
    raise SystemExit(1)
