from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = (ROOT / 'engagement_service.py').read_text()
TESTS = (ROOT / 'tests/test_engagement_service.py').read_text()
MIGRATION = (ROOT / 'deployment/migrations/010_engagement_service.sql').read_text()

checks: list[tuple[str, bool]] = [
    ('service retains employee-service read model reuse', all(token in SERVICE for token in ['register_employee_profile', 'employee_snapshots', '_require_employee'])),
    ('service recomputes aggregates after response submission and survey close', all(token in SERVICE for token in ['self._rebuild_aggregate(survey, trace_id=trace)', 'EngagementSurveyResultsAggregated'])),
    ('service rejects out-of-scope or duplicate responses', all(token in SERVICE for token in ['already responded to this survey', 'outside the target population', 'required survey questions are unanswered'])),
    ('migration is tenant-scoped and aggregate-ready', all(token in MIGRATION for token in ['tenant_id VARCHAR(80) NOT NULL', 'engagement_survey_aggregates', 'question_scores JSONB NOT NULL', 'dimension_scores JSONB NOT NULL'])),
    ('tests assert aggregation math and tenant boundaries', all(token in TESTS for token in ["overall_average_score'] == 4.1", "participation_rate'] == 0.6667", 'TENANT_SCOPE_VIOLATION', 'cross-tenant employee reference to fail'])),
]

score = sum(1 for _, ok in checks if ok)
for name, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
print(f'Engagement re-QC score: {score}/{len(checks)}')
if score < len(checks):
    raise SystemExit(1)
