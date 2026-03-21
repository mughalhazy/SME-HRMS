from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TENANT_MIGRATION = (ROOT / 'deployment' / 'migrations' / '004_tenant_foundation.sql').read_text()
AUDIT_MIGRATION = (ROOT / 'deployment' / 'migrations' / '005_audit_service.sql').read_text()
SECURITY_MODEL = (ROOT / 'docs' / 'canon' / 'security-model.md').read_text()
TENANT_SUPPORT = (ROOT / 'tenant_support.py').read_text()
AUDIT_SERVICE = (ROOT / 'audit_service' / 'service.py').read_text()
RESILIENCE = (ROOT / 'resilience.py').read_text()
AUTH_SERVICE = (ROOT / 'services' / 'auth-service' / 'service.py').read_text()
ROLE_REPOSITORY = (ROOT / 'services' / 'employee-service' / 'role.repository.ts').read_text()
DEPARTMENT_REPOSITORY = (ROOT / 'services' / 'employee-service' / 'department.repository.ts').read_text()
RBAC_MIDDLEWARE = (ROOT / 'services' / 'employee-service' / 'rbac.middleware.ts').read_text()
LEAVE_SERVICE = (ROOT / 'leave_service.py').read_text()
HIRING_SERVICE = (ROOT / 'services' / 'hiring_service' / 'service.py').read_text()
INTEGRATION_SERVICE = (ROOT / 'integration_service.py').read_text()
NOTIFICATION_SERVICE = (ROOT / 'notification_service.py').read_text()
SEARCH_SERVICE = (ROOT / 'search_service.py').read_text()
PAYROLL_SERVICE = (ROOT / 'payroll_service.py').read_text()
AUTH_TESTS = (ROOT / 'tests' / 'test_auth_service.py').read_text()
LEAVE_TESTS = (ROOT / 'tests' / 'test_leave_service.py').read_text()
NOTIFICATION_TESTS = (ROOT / 'tests' / 'test_notification_service.py').read_text()
INTEGRATION_TESTS = (ROOT / 'tests' / 'test_integration_service.py').read_text()
SECURITY_LOGGING_TESTS = (ROOT / 'tests' / 'test_security_logging.py').read_text()
AUDIT_TESTS = (ROOT / 'tests' / 'test_audit_service.py').read_text()


checks: list[tuple[str, bool]] = [
    (
        'D3 tenant foundation persists tenant registry and tenant configs',
        all(marker in TENANT_MIGRATION for marker in [
            'CREATE TABLE IF NOT EXISTS tenants',
            'tenant_id VARCHAR(80) NOT NULL PRIMARY KEY',
            'CREATE TABLE IF NOT EXISTS tenant_configs',
            'FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)',
        ]),
    ),
    (
        'tenant access helper blocks cross-tenant resource access',
        'def assert_tenant_access' in TENANT_SUPPORT and "raise PermissionError(code)" in TENANT_SUPPORT,
    ),
    (
        'tenant isolation is enforced across critical services',
        all(token in LEAVE_SERVICE for token in ['assert_tenant_access', '_assert_resource_tenant'])
        and 'assert_tenant_access' in HIRING_SERVICE
        and 'assert_tenant_access' in INTEGRATION_SERVICE
        and 'assert_tenant_access' in NOTIFICATION_SERVICE
        and 'assert_tenant_access' in SEARCH_SERVICE,
    ),
    (
        'cross-tenant repository filters are rejected server-side',
        'cross_tenant_filter_blocked' in ROLE_REPOSITORY and 'cross_tenant_filter_blocked' in DEPARTMENT_REPOSITORY,
    ),
    (
        'D4 audit store is append-only and tenant-scoped',
        all(marker in AUDIT_MIGRATION for marker in [
            'CREATE TABLE IF NOT EXISTS audit_records',
            'tenant_id VARCHAR(80) NOT NULL',
            'trace_id VARCHAR(120) NOT NULL',
            'append-only',
            'BEFORE UPDATE ON audit_records',
            'BEFORE DELETE ON audit_records',
        ]),
    ),
    (
        'audit query requires tenant filtering',
        'tenant_id is required' in AUDIT_SERVICE and "row['tenant_id'] == tenant" in AUDIT_SERVICE,
    ),
    (
        'privileged domains emit audit records',
        LEAVE_SERVICE.count('_audit_leave_mutation(') >= 5
        and HIRING_SERVICE.count('_audit_hiring_mutation(') >= 6
        and PAYROLL_SERVICE.count('_audit_payroll_mutation(') >= 6
        and AUTH_SERVICE.count('_audit_auth_mutation(') >= 4,
    ),
    (
        'security model defines deny-by-default tenant-scoped authorization',
        all(marker in SECURITY_MODEL for marker in [
            'Authorization is deny-by-default.',
            'Access requires both a granted capability and a matching scope.',
            'Scope filters must be enforced in API handlers, service methods, and read-model queries.',
            'Sensitive attributes such as compensation, password hashes, refresh tokens, and review narratives require least-privilege access.',
            'Audit logs | Read | Read (scoped) | Deny | Deny | Read (payroll scope) | emit only',
        ]),
    ),
    (
        'auth service capability matrix includes privileged access administration control',
        all(marker in AUTH_SERVICE for marker in [
            "'Admin'",
            "'Manager'",
            "'Employee'",
            "'Recruiter'",
            "'PayrollAdmin'",
            "'CAP-AUT-001'",
        ]),
    ),
    (
        'rbac middleware actively denies insufficient permissions',
        RBAC_MIDDLEWARE.count("sendError(req, res, 403, 'FORBIDDEN', 'Insufficient permissions')") >= 4,
    ),
    (
        'sensitive fields are redacted before logs persist',
        all(marker in RESILIENCE for marker in [
            'password_hash',
            'refresh_token_hash',
            'authorization',
            'bank_account',
            'tax_id',
            '"[REDACTED]"',
        ])
        and all(marker in AUTH_SERVICE for marker in ['refresh_token_hash', 'token_hash', 'password_hash']),
    ),
    (
        'automated tests cover tenant boundaries, audit behavior, and redaction',
        all(marker in AUTH_TESTS for marker in [
            'test_tenant_and_scope_checks_deny_cross_tenant_access',
            'test_role_binding_and_permission_policy_changes_are_audited',
        ])
        and 'test_cross_tenant_request_access_is_denied' in LEAVE_TESTS
        and 'test_cross_tenant_recipient_access_is_blocked' in NOTIFICATION_TESTS
        and 'TENANT_SCOPE_VIOLATION' in INTEGRATION_TESTS
        and 'test_sanitize_log_context_redacts_sensitive_fields' in SECURITY_LOGGING_TESTS
        and 'get_audit_records' in AUDIT_TESTS
        and 'AuditService' in AUDIT_TESTS,
    ),
]

for description, ok in checks:
    print(f"{'PASS' if ok else 'FAIL'}: {description}")

if not all(ok for _, ok in checks):
    raise SystemExit(1)
