from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = (ROOT / 'engagement_service.py').read_text()
API = (ROOT / 'engagement_api.py').read_text()
EVENTS = (ROOT / 'event_contract.py').read_text()
SERVICE_MAP = (ROOT / 'docs/canon/service-map.md').read_text()
CAPABILITY = (ROOT / 'docs/canon/capability-matrix.md').read_text()
DOMAIN = (ROOT / 'docs/canon/domain-model.md').read_text()
DATA = (ROOT / 'docs/canon/data-architecture.md').read_text()
READ_MODELS = (ROOT / 'docs/canon/read-model-catalog.md').read_text()
EVENT_CATALOG = (ROOT / 'docs/canon/event-catalog.md').read_text()
MIGRATION = (ROOT / 'deployment/migrations/010_engagement_service.sql').read_text()
TESTS = (ROOT / 'tests/test_engagement_service.py').read_text()

checks: list[tuple[str, bool]] = [
    ('service persists surveys responses and aggregated results', all(token in SERVICE for token in ['class Survey', 'class SurveyResponse', 'class AggregatedSurveyResult', 'self.surveys', 'self.responses', 'self.aggregated_results'])),
    ('tenant isolation is enforced across survey reads and writes', 'assert_tenant_access' in SERVICE and 'normalize_tenant_id' in SERVICE and 'target_population' in SERVICE),
    ('aggregation logic calculates per-question and per-dimension results', all(token in SERVICE for token in ['question_scores', 'dimension_scores', 'participation_rate', 'overall_average_score', 'favorable_ratio'])),
    ('api exposes survey response and aggregate handlers', all(token in API for token in ['post_surveys', 'post_responses', 'get_surveys', 'get_aggregated_results'])),
    ('canonical event registry includes engagement survey lifecycle events', all(token in EVENTS for token in ['EngagementSurveyCreated', 'EngagementSurveyPublished', 'EngagementSurveyClosed', 'EngagementSurveyResponseSubmitted', 'EngagementSurveyResultsAggregated'])),
    ('schema defines engagement survey persistence tables', all(token in MIGRATION for token in ['engagement_surveys', 'engagement_survey_questions', 'engagement_survey_responses', 'engagement_survey_answers', 'engagement_survey_aggregates'])),
    ('canonical docs point to engagement service and read model', all(token in (SERVICE_MAP + CAPABILITY + DOMAIN + DATA + READ_MODELS + EVENT_CATALOG) for token in ['engagement-service', '/api/v1/engagement/surveys', 'engagement_survey_view', 'EngagementSurveyResponseSubmitted'])),
    ('tests cover domain workflow and D1 wrappers', all(token in TESTS for token in ['test_engagement_service_supports_surveys_responses_and_aggregates', 'test_engagement_service_enforces_tenant_isolation_and_target_population', 'test_engagement_api_wraps_d1_responses_and_aggregation_reads'])),
]

score = sum(1 for _, ok in checks if ok)
for name, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
print(f'Engagement QC score: {score}/{len(checks)}')
if score < len(checks):
    raise SystemExit(1)
