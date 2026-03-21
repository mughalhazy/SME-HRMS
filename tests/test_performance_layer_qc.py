from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text()


def test_performance_service_is_isolated_from_employee_service_routes() -> None:
    routes = read('services/employee-service/employee.routes.ts')
    assert '/api/v1/performance-reviews' not in routes
    assert 'PerformanceReview' not in routes


def test_performance_service_covers_goals_feedback_calibration_pips_and_workflows() -> None:
    service = read('performance_service.py')
    for token in [
        'class ReviewCycle',
        'class GoalRecord',
        'class FeedbackRecord',
        'class CalibrationSession',
        'class PipPlan',
        'performance_goal_approval',
        'performance_calibration_signoff',
        'performance_pip_approval',
        'emit_audit_record',
        'emit_canonical_event',
    ]:
        assert token in service


def test_performance_api_exposes_enterprise_performance_endpoints() -> None:
    api = read('performance_api.py')
    for token in [
        'post_review_cycles',
        'post_goals',
        'post_feedback',
        'post_calibrations',
        'post_pips',
        'patch_pip_progress',
    ]:
        assert token in api


def test_performance_schema_and_docs_capture_new_service_boundary() -> None:
    schema = read('deployment/migrations/002_workflow_schema.sql')
    service_map = read('docs/canon/service-map.md')
    workflow = read('docs/canon/workflow-catalog.md')
    for token in [
        'CREATE TABLE IF NOT EXISTS performance_review_cycles',
        'CREATE TABLE IF NOT EXISTS performance_goals',
        'CREATE TABLE IF NOT EXISTS performance_feedback',
        'CREATE TABLE IF NOT EXISTS performance_calibrations',
        'CREATE TABLE IF NOT EXISTS performance_pip_plans',
        'CREATE TABLE IF NOT EXISTS performance_pip_milestones',
    ]:
        assert token in schema
    for token in ['performance-service', '/api/v1/performance/goals', '/api/v1/performance/pips']:
        assert token in service_map
    for token in ['performance_management', 'Goal: none -> Draft -> Submitted -> Approved/Rejected', 'PipPlan: none -> Draft -> Submitted -> Active/Rejected -> Completed/Cancelled']:
        assert token in workflow
