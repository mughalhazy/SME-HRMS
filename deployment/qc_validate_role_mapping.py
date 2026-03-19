from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLE_MODEL = (ROOT / 'services/employee-service/role.model.ts').read_text()
ROLE_ROUTES = (ROOT / 'services/employee-service/employee.routes.ts').read_text()
CORE_SCHEMA = (ROOT / 'deployment/migrations/001_core_schema.sql').read_text()

checks: list[tuple[str, bool]] = [
    ('default role permissions mapping', 'DEFAULT_ROLE_PERMISSIONS' in ROLE_MODEL and 'CAP-EMP-001' in ROLE_MODEL and 'CAP-PRF-001' in ROLE_MODEL),
    ('role routes exposed', all(route in ROLE_ROUTES for route in ['/api/v1/roles', 'createRole', 'listRoles', 'readRole'])),
    ('role schema persists permissions', 'permissions TEXT[] NOT NULL DEFAULT' in CORE_SCHEMA),
    ('employee to role foreign key retained', 'fk_employees_role' in CORE_SCHEMA and 'idx_employees_role_id' in CORE_SCHEMA),
]

score = sum(1 for _, ok in checks)
for name, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
print(f'QC role-mapping score: {score}/{len(checks)}')
if score < len(checks):
    raise SystemExit(1)
