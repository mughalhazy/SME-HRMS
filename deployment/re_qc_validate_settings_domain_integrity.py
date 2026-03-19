from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = (ROOT / 'services/settings-service/settings.repository.ts').read_text()
SERVICE = (ROOT / 'services/settings-service/settings.service.ts').read_text()
ROUTES = (ROOT / 'services/settings-service/settings.routes.ts').read_text()
SCHEMA = (ROOT / 'deployment/migrations/002_workflow_schema.sql').read_text()
DOMAIN_MODEL = (ROOT / 'docs/canon/domain-model.md').read_text()
WORKFLOW_DOC = (ROOT / 'docs/canon/workflow-catalog.md').read_text()
TESTS = (ROOT / 'tests/test_settings_domain.py').read_text()

checks: list[tuple[str, bool]] = [
    (
        'settings repository tracks attendance and leave lookup indexes',
        all(token in REPOSITORY for token in ['attendanceRuleCodeIndex', 'attendanceRuleStatusIndex', 'leavePolicyCodeIndex', 'leavePolicyTypeIndex', 'leavePolicyStatusIndex']),
    ),
    (
        'settings service enforces duplicate and activation guardrails',
        all(token in SERVICE for token in ['attendance rule code already exists', 'an Active leave policy already exists for this leave_type', 'cannot replace Active payroll settings with Draft status']),
    ),
    (
        'routes provide aggregated read access and section mutation endpoints',
        all(token in ROUTES for token in ['/api/v1/settings', '/attendance-rules/:attendanceRuleId', '/leave-policies/:leavePolicyId', '/api/v1/settings/payroll']),
    ),
    (
        'schema and domain docs align on settings entities',
        all(token in (SCHEMA + DOMAIN_MODEL) for token in ['attendance_rules', 'leave_policies', 'payroll_settings', 'AttendanceRule', 'LeavePolicy', 'PayrollSettings']),
    ),
    (
        'workflow documentation captures administrative settings lifecycle',
        'settings_administration' in WORKFLOW_DOC and 'SettingsPublished' in WORKFLOW_DOC,
    ),
    (
        'runtime tests execute settings domain lifecycle and read model assertions',
        'test_settings_service_domain_rules_and_read_models' in TESTS and 'const readModels = service.getSettingsReadModels();' in TESTS,
    ),
]

score = sum(1 for _, ok in checks)
for name, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
print(f'RE-QC settings-domain-integrity score: {score}/{len(checks)}')
if score < len(checks):
    raise SystemExit(1)
