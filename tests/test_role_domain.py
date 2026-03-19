from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLE_MODEL = (ROOT / 'services/employee-service/role.model.ts').read_text()
ROLE_SERVICE = (ROOT / 'services/employee-service/role.service.ts').read_text()
ROLE_REPOSITORY = (ROOT / 'services/employee-service/role.repository.ts').read_text()
EMPLOYEE_SERVICE = (ROOT / 'services/employee-service/employee.service.ts').read_text()
ROUTES = (ROOT / 'services/employee-service/employee.routes.ts').read_text()
CORE_SCHEMA = (ROOT / 'deployment/migrations/001_core_schema.sql').read_text()


def test_role_domain_defines_permissions_mapping() -> None:
    assert 'DEFAULT_ROLE_PERMISSIONS' in ROLE_MODEL
    for capability in ['CAP-EMP-001', 'CAP-ATT-001', 'CAP-LEV-001', 'CAP-PRF-001']:
        assert capability in ROLE_MODEL
    assert 'resolveRolePermissions' in ROLE_MODEL


def test_employee_service_enforces_role_assignment_integrity() -> None:
    assert 'getActiveRoleById' in EMPLOYEE_SERVICE
    assert 'linkEmployee' in EMPLOYEE_SERVICE
    assert 'relinkEmployee' in EMPLOYEE_SERVICE
    assert 'unlinkEmployee' in EMPLOYEE_SERVICE


def test_role_repository_tracks_employee_linkage() -> None:
    assert 'employeeRoleIndex' in ROLE_REPOSITORY
    assert 'assignEmployee' in ROLE_REPOSITORY
    assert 'unassignEmployee' in ROLE_REPOSITORY
    assert 'countEmployees' in ROLE_REPOSITORY


def test_role_routes_are_registered() -> None:
    for route in [
        "router.post('/api/v1/roles'",
        "router.get('/api/v1/roles/:roleId'",
        "router.get('/api/v1/roles'",
        "router.patch('/api/v1/roles/:roleId'",
        "router.delete('/api/v1/roles/:roleId'",
    ]:
        assert route in ROUTES


def test_schema_persists_role_permissions_and_integrity() -> None:
    assert "permissions TEXT[] NOT NULL DEFAULT '{}'" in CORE_SCHEMA
    assert "status VARCHAR(20) NOT NULL CHECK (status IN ('Draft', 'Active', 'Inactive', 'Archived'))" in CORE_SCHEMA
    assert 'REFERENCES roles (role_id)' in CORE_SCHEMA
    assert 'idx_roles_employment_category' in CORE_SCHEMA
    assert 'idx_employees_role_id' in CORE_SCHEMA


def test_role_service_blocks_deletion_with_assigned_employees() -> None:
    assert 'cannot delete role with assigned employees' in ROLE_SERVICE
    assert 'cannot deactivate or archive a role with assigned employees' in ROLE_SERVICE
