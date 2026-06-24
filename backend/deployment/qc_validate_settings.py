from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTES = (ROOT / 'services/settings-service/settings.routes.ts').read_text()
MODEL = (ROOT / 'services/settings-service/settings.model.ts').read_text()
REPOSITORY = (ROOT / 'services/settings-service/settings.repository.ts').read_text()
SERVICE = (ROOT / 'services/settings-service/settings.service.ts').read_text()
VALIDATION = (ROOT / 'services/settings-service/settings.validation.ts').read_text()
WORKFLOW_SCHEMA = (ROOT / 'deployment/migrations/002_workflow_schema.sql').read_text()
SERVICE_MAP = (ROOT / 'docs/canon/service-map.md').read_text()
READ_MODEL = (ROOT / 'docs/canon/read-model-catalog.md').read_text()
DOMAIN_MODEL = (ROOT / 'docs/canon/domain-model.md').read_text()
WORKFLOW_DOC = (ROOT / 'docs/canon/workflow-catalog.md').read_text()

checks: list[tuple[str, bool]] = [
    (
        'settings routes expose attendance leave and payroll endpoints',
        all(token in ROUTES for token in [
            '/api/v1/settings',
            '/api/v1/settings/attendance-rules',
            '/api/v1/settings/leave-policies',
            '/api/v1/settings/payroll',
        ]),
    ),
    (
        'settings model includes attendance leave payroll entities and read model',
        all(token in MODEL for token in ['interface AttendanceRule', 'interface LeavePolicy', 'interface PayrollSettings', 'settings_configuration_view']),
    ),
    (
        'repository enforces code indexes and consolidated read models',
        all(token in REPOSITORY for token in ['attendanceRuleCodeIndex', 'leavePolicyCodeIndex', 'toReadModelBundle', 'approval_chain']),
    ),
    (
        'service blocks duplicate attendance codes and duplicate active leave types',
        all(token in SERVICE for token in ['attendance rule code already exists', 'an Active leave policy already exists for this leave_type', 'cannot replace Active payroll settings with Draft status']),
    ),
    (
        'validation covers workdays unpaid leave and payroll pay-day constraints',
        all(token in VALIDATION for token in ['must include at least one workday', 'must be 0 for Unpaid leave policies', 'must be between 1 and 7 for Weekly or BiWeekly schedules']),
    ),
    (
        'workflow schema persists settings tables and integrity constraints',
        all(token in WORKFLOW_SCHEMA for token in ['CREATE TABLE IF NOT EXISTS attendance_rules', 'CREATE TABLE IF NOT EXISTS leave_policies', 'CREATE TABLE IF NOT EXISTS payroll_settings', 'uq_leave_policies_code']),
    ),
    (
        'canonical docs reference settings-service and settings_administration workflow',
        all(token in (SERVICE_MAP + DOMAIN_MODEL + WORKFLOW_DOC + READ_MODEL) for token in ['settings-service', 'settings_administration', 'AttendanceRule', 'LeavePolicy', 'PayrollSettings', 'settings_configuration_view']),
    ),
]

score = sum(1 for _, ok in checks)
for name, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
print(f'Settings QC score: {score}/{len(checks)}')
if score < len(checks):
    raise SystemExit(1)
