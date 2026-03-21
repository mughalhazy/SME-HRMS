from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = (ROOT / 'performance_service.py').read_text()
API = (ROOT / 'performance_api.py').read_text()
SCHEMA = (ROOT / 'deployment/migrations/002_workflow_schema.sql').read_text()
SERVICE_MAP = (ROOT / 'docs/canon/service-map.md').read_text()
WORKFLOW_DOC = (ROOT / 'docs/canon/workflow-catalog.md').read_text()
EMPLOYEE_ROUTES = (ROOT / 'services/employee-service/employee.routes.ts').read_text()

checks: list[tuple[str, bool]] = [
    ('employee-service no longer exposes performance routes', '/api/v1/performance-reviews' not in EMPLOYEE_ROUTES),
    ('performance service models enterprise domain objects', all(token in SERVICE for token in ['ReviewCycle', 'GoalRecord', 'FeedbackRecord', 'CalibrationSession', 'PipPlan'])),
    ('workflow approvals registered for goal calibration and pip paths', all(token in SERVICE for token in ['performance_goal_approval', 'performance_calibration_signoff', 'performance_pip_approval'])),
    ('audit integrated on performance mutations', 'emit_audit_record' in SERVICE and 'performance_pip_progress_updated' in SERVICE),
    ('api exposes review cycle goal feedback calibration and pip handlers', all(token in API for token in ['post_review_cycles', 'post_goals', 'post_feedback', 'post_calibrations', 'post_pips'])),
    ('schema persists enterprise performance aggregates', all(token in SCHEMA for token in ['performance_review_cycles', 'performance_goals', 'performance_feedback', 'performance_calibrations', 'performance_pip_plans', 'performance_pip_milestones'])),
    ('canonical docs point performance to new bounded service', all(token in (SERVICE_MAP + WORKFLOW_DOC) for token in ['performance-service', 'performance_management', '/api/v1/performance/goals'])),
]

score = sum(1 for _, ok in checks if ok)
for name, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
print(f'Performance QC score: {score}/{len(checks)}')
if score < len(checks):
    raise SystemExit(1)
