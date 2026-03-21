from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_SERVICE = (ROOT / 'audit_service' / 'service.py').read_text()
MIGRATION = (ROOT / 'deployment' / 'migrations' / '005_audit_service.sql').read_text()
ATTENDANCE = (ROOT / 'attendance_service' / 'service.py').read_text()
LEAVE = (ROOT / 'leave_service.py').read_text()
PAYROLL = (ROOT / 'payroll_service.py').read_text()
HIRING = (ROOT / 'services' / 'hiring_service' / 'service.py').read_text()
AUTH = (ROOT / 'services' / 'auth-service' / 'service.py').read_text()
TS_LOGGER = (ROOT / 'middleware' / 'logger.ts').read_text()

checks = [
    ('audit schema includes D4 fields', all(token in MIGRATION for token in ['audit_id', 'tenant_id', 'actor', 'action', 'entity', 'entity_id', 'before', 'after', 'timestamp'])),
    ('append-only SQL triggers configured', 'append-only' in MIGRATION and 'BEFORE UPDATE' in MIGRATION and 'BEFORE DELETE' in MIGRATION),
    ('audit query enforces tenant_id', 'tenant_id is required' in AUDIT_SERVICE and 'row[\'tenant_id\'] == tenant' in AUDIT_SERVICE),
    ('attendance mutations emit audit', ATTENDANCE.count('_audit(') >= 4 and 'attendance_period_locked' in ATTENDANCE),
    ('leave mutations emit audit', LEAVE.count('_audit_leave_mutation(') >= 5),
    ('payroll mutations emit audit', PAYROLL.count('_audit_payroll_mutation(') >= 6),
    ('hiring mutations emit audit', HIRING.count('_audit_hiring_mutation(') >= 6),
    ('auth mutations emit audit', AUTH.count('_audit_auth_mutation(') >= 4),
    ('ts logger appends centralized audit records', 'appendCentralizedAuditRecord' in TS_LOGGER),
]

for description, ok in checks:
    print(f"{'PASS' if ok else 'FAIL'}: {description}")

if not all(ok for _, ok in checks):
    raise SystemExit(1)
