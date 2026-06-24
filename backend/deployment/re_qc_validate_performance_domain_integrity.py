from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = (ROOT / 'performance_service.py').read_text()
API = (ROOT / 'performance_api.py').read_text()
SCHEMA = (ROOT / 'deployment/migrations/002_workflow_schema.sql').read_text()
DOMAIN_MODEL = (ROOT / 'docs/canon/domain-model.md').read_text()
WORKFLOW_DOC = (ROOT / 'docs/canon/workflow-catalog.md').read_text()
TESTS = (ROOT / 'tests/test_performance_domain.py').read_text()

checks: list[tuple[str, bool]] = [
    ('service persists goals feedback calibration and pip plans', all(token in SERVICE for token in ['self.goals', 'self.feedback', 'self.calibrations', 'self.pips'])),
    ('service integrates workflow decisions and audit hooks', all(token in SERVICE for token in ['_resolve_workflow', 'emit_audit_record', 'PerformanceGoalSubmitted', 'PerformancePipProgressUpdated'])),
    ('api covers approval and progress endpoints', all(token in API for token in ['post_goal_decision', 'post_calibration_decision', 'post_pip_decision', 'patch_pip_progress'])),
    ('schema and domain model align on performance service entities', all(token in (SCHEMA + DOMAIN_MODEL) for token in ['performance_goals', 'ReviewCycle', 'CalibrationSession', 'PipPlan'])),
    (
        'workflow documentation captures enterprise lifecycle',
        all(
            token in WORKFLOW_DOC
            for token in [
                'Goal: none -> Draft -> Submitted -> Approved/Rejected',
                'PipPlan: none -> Draft -> Submitted -> Active/Rejected -> Completed/Cancelled',
            ]
        )
        and any(
            token in WORKFLOW_DOC
            for token in [
                'ReviewCycle: none -> Draft -> Open -> Closed',
                'ReviewCycle: none -> Draft -> PendingApproval -> Open -> Closed',
            ]
        ),
    ),
    ('runtime tests cover end-to-end enterprise performance flow', 'test_performance_service_supports_cycles_goals_feedback_calibration_and_pips' in TESTS and 'service.update_pip_progress' in TESTS),
]

score = sum(1 for _, ok in checks if ok)
for name, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
print(f'RE-QC performance-domain-integrity score: {score}/{len(checks)}')
if score < len(checks):
    raise SystemExit(1)
