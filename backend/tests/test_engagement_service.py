from __future__ import annotations

from pathlib import Path

from engagement_api import get_aggregated_results, get_engagement_dashboard, get_sentiment_trends, get_surveys, post_responses, post_survey_close, post_survey_publish, post_surveys
from engagement_service import EngagementService


def _seed_employees(service: EngagementService) -> None:
    service.register_employee_profile({
        'employee_id': 'emp-hr-1',
        'employee_number': 'E-001',
        'full_name': 'Harper HR',
        'department_id': 'dep-hr',
        'department_name': 'People Operations',
        'manager_employee_id': 'hr-admin',
        'tenant_id': 'tenant-default',
    })
    service.register_employee_profile({
        'employee_id': 'emp-eng-1',
        'employee_number': 'E-002',
        'full_name': 'Noah Bennett',
        'department_id': 'dep-eng',
        'department_name': 'Engineering',
        'manager_employee_id': 'emp-mgr-1',
        'tenant_id': 'tenant-default',
    })
    service.register_employee_profile({
        'employee_id': 'emp-eng-2',
        'employee_number': 'E-003',
        'full_name': 'Mina Patel',
        'department_id': 'dep-eng',
        'department_name': 'Engineering',
        'manager_employee_id': 'emp-mgr-1',
        'tenant_id': 'tenant-default',
    })
    service.register_employee_profile({
        'employee_id': 'emp-mgr-1',
        'employee_number': 'E-004',
        'full_name': 'Max Manager',
        'department_id': 'dep-eng',
        'department_name': 'Engineering',
        'manager_employee_id': 'emp-hr-1',
        'tenant_id': 'tenant-default',
    })
    service.register_employee_profile({
        'employee_id': 'emp-other-1',
        'employee_number': 'E-005',
        'full_name': 'Taylor Other',
        'department_id': 'dep-sales',
        'department_name': 'Sales',
        'manager_employee_id': 'emp-hr-1',
        'tenant_id': 'tenant-other',
    })


def _questions() -> list[dict[str, object]]:
    return [
        {'question_id': 'q-d1', 'prompt': 'I understand company goals', 'dimension': 'D1', 'kind': 'Likert5', 'required': True},
        {'question_id': 'q-d2', 'prompt': 'My team collaborates well', 'dimension': 'D2', 'kind': 'Likert5', 'required': True},
        {'question_id': 'q-d3', 'prompt': 'I feel supported by my manager', 'dimension': 'D3', 'kind': 'Likert5', 'required': True},
        {'question_id': 'q-d4', 'prompt': 'I have tools to succeed', 'dimension': 'D4', 'kind': 'Likert5', 'required': True},
        {'question_id': 'q-d5', 'prompt': 'I see growth opportunities here', 'dimension': 'D5', 'kind': 'Likert5', 'required': True},
    ]


def test_engagement_service_supports_surveys_responses_and_aggregates(tmp_path: Path) -> None:
    service = EngagementService(db_path=str(tmp_path / 'engagement.sqlite3'))
    _seed_employees(service)

    status, survey = service.create_survey(
        {
            'tenant_id': 'tenant-default',
            'code': 'ENG-FY26-Q1',
            'title': 'Q1 Engagement Pulse',
            'description': 'Baseline pulse for engineering.',
            'owner_employee_id': 'emp-hr-1',
            'target_department_id': 'dep-eng',
            'questions': _questions(),
        },
        actor_id='emp-hr-1',
        trace_id='trace-engagement-create',
    )
    assert status == 201
    assert survey['status'] == 'Draft'

    _, published = service.publish_survey(survey['survey_id'], tenant_id='tenant-default', actor_id='emp-hr-1', trace_id='trace-engagement-publish')
    assert published['status'] == 'Open'

    _, first_response = service.submit_response(
        {
            'tenant_id': 'tenant-default',
            'survey_id': survey['survey_id'],
            'employee_id': 'emp-eng-1',
            'answers': [
                {'question_id': 'q-d1', 'score': 5},
                {'question_id': 'q-d2', 'score': 4},
                {'question_id': 'q-d3', 'score': 4},
                {'question_id': 'q-d4', 'score': 5},
                {'question_id': 'q-d5', 'score': 4},
            ],
            'overall_comment': 'Strong quarter.',
        },
        actor_id='emp-eng-1',
        trace_id='trace-engagement-response-1',
    )
    assert first_response['aggregate']['response_count'] == 1
    assert first_response['aggregate']['overall_average_score'] == 4.4

    _, second_response = service.submit_response(
        {
            'tenant_id': 'tenant-default',
            'survey_id': survey['survey_id'],
            'employee_id': 'emp-eng-2',
            'answers': [
                {'question_id': 'q-d1', 'score': 3},
                {'question_id': 'q-d2', 'score': 3},
                {'question_id': 'q-d3', 'score': 4},
                {'question_id': 'q-d4', 'score': 4},
                {'question_id': 'q-d5', 'score': 5},
            ],
        },
        actor_id='emp-eng-2',
        trace_id='trace-engagement-response-2',
    )
    aggregate = second_response['aggregate']
    assert aggregate['response_count'] == 2
    assert aggregate['participant_count'] == 2
    assert aggregate['target_population'] == 3
    assert aggregate['participation_rate'] == 0.6667
    assert aggregate['overall_average_score'] == 4.1
    assert aggregate['score_distribution']['5'] == 3
    assert next(item for item in aggregate['dimension_scores'] if item['dimension'] == 'D1')['average_score'] == 4.0

    _, results = service.get_aggregated_results(survey['survey_id'], tenant_id='tenant-default')
    assert results['aggregate']['favorable_ratio'] == 0.8
    assert len(results['aggregate']['question_scores']) == 5

    _, responses = service.list_responses(survey['survey_id'], tenant_id='tenant-default')
    assert len(responses['items']) == 2

    _, closed = service.close_survey(survey['survey_id'], tenant_id='tenant-default', actor_id='emp-hr-1', trace_id='trace-engagement-close')
    assert closed['status'] == 'Closed'
    assert any(event['legacy_event_name'] == 'EngagementSurveyResponseSubmitted' for event in service.events)
    assert any(event['legacy_event_name'] == 'EngagementSurveyResultsAggregated' for event in service.events)


def test_engagement_service_enforces_tenant_isolation_and_target_population(tmp_path: Path) -> None:
    service = EngagementService(db_path=str(tmp_path / 'engagement-tenant.sqlite3'))
    _seed_employees(service)

    _, survey = service.create_survey(
        {
            'tenant_id': 'tenant-default',
            'code': 'ENG-FY26-Q2',
            'title': 'Q2 Engineering Pulse',
            'owner_employee_id': 'emp-hr-1',
            'target_department_id': 'dep-eng',
            'questions': _questions(),
        },
        actor_id='emp-hr-1',
        trace_id='trace-engagement-create-tenant',
    )
    service.publish_survey(survey['survey_id'], tenant_id='tenant-default', actor_id='emp-hr-1', trace_id='trace-engagement-publish-tenant')

    try:
        service.get_survey(survey['survey_id'], tenant_id='tenant-other')
    except Exception as exc:  # pragma: no cover
        assert 'TENANT_SCOPE_VIOLATION' in str(exc)
    else:  # pragma: no cover
        raise AssertionError('expected tenant mismatch to be enforced')

    try:
        service.submit_response(
            {
                'tenant_id': 'tenant-default',
                'survey_id': survey['survey_id'],
                'employee_id': 'emp-other-1',
                'answers': [{'question_id': 'q-d1', 'score': 5}, {'question_id': 'q-d2', 'score': 5}, {'question_id': 'q-d3', 'score': 5}, {'question_id': 'q-d4', 'score': 5}, {'question_id': 'q-d5', 'score': 5}],
            },
            actor_id='emp-other-1',
            trace_id='trace-engagement-forbidden',
        )
    except Exception as exc:  # pragma: no cover
        assert 'employee_id was not found in employee-service read model' in str(exc)
    else:  # pragma: no cover
        raise AssertionError('expected cross-tenant employee reference to fail')



def test_engagement_api_wraps_d1_responses_and_aggregation_reads(tmp_path: Path) -> None:
    service = EngagementService(db_path=str(tmp_path / 'engagement-api.sqlite3'))
    _seed_employees(service)

    status, survey_response = post_surveys(
        service,
        'HRAdmin',
        'emp-hr-1',
        {
            'tenant_id': 'tenant-default',
            'code': 'ENG-FY26-Q3',
            'title': 'Q3 Company Pulse',
            'owner_employee_id': 'emp-hr-1',
            'questions': _questions(),
        },
        trace_id='trace-api-survey',
    )
    assert status == 201
    assert survey_response['status'] == 'success'
    survey_id = survey_response['data']['survey_id']

    status, _ = post_survey_publish(service, 'HRAdmin', 'emp-hr-1', survey_id, {'tenant_id': 'tenant-default'}, trace_id='trace-api-publish')
    assert status == 200

    status, response = post_responses(
        service,
        'Employee',
        'emp-eng-1',
        {
            'tenant_id': 'tenant-default',
            'survey_id': survey_id,
            'employee_id': 'emp-eng-1',
            'answers': [{'question_id': 'q-d1', 'score': 4}, {'question_id': 'q-d2', 'score': 4}, {'question_id': 'q-d3', 'score': 4}, {'question_id': 'q-d4', 'score': 4}, {'question_id': 'q-d5', 'score': 4}],
        },
        trace_id='trace-api-response',
    )
    assert status == 201
    assert response['data']['aggregate']['overall_average_score'] == 4.0

    status, surveys = get_surveys(service, 'HRAdmin', 'emp-hr-1', {'tenant_id': 'tenant-default'}, trace_id='trace-api-list')
    assert status == 200
    assert surveys['data']['items'][0]['survey_id'] == survey_id

    status, aggregates = get_aggregated_results(service, 'HRAdmin', 'emp-hr-1', survey_id, {'tenant_id': 'tenant-default'}, trace_id='trace-api-aggregate')
    assert status == 200
    assert aggregates['data']['aggregate']['response_count'] == 1

    status, closed = post_survey_close(service, 'HRAdmin', 'emp-hr-1', survey_id, {'tenant_id': 'tenant-default'}, trace_id='trace-api-close')
    assert status == 200
    assert closed['data']['status'] == 'Closed'


def test_engagement_sentiment_trends_and_dashboard(tmp_path: Path) -> None:
    service = EngagementService(db_path=str(tmp_path / 'engagement-sentiment.sqlite3'))
    _seed_employees(service)

    _, survey_response = post_surveys(
        service,
        'HRAdmin',
        'emp-hr-1',
        {
            'tenant_id': 'tenant-default',
            'code': 'ENG-FY26-Q4',
            'title': 'Q4 Pulse',
            'owner_employee_id': 'emp-hr-1',
            'target_department_id': 'dep-eng',
            'questions': _questions(),
        },
        trace_id='trace-api-survey-sentiment',
    )
    survey_id = survey_response['data']['survey_id']
    post_survey_publish(service, 'HRAdmin', 'emp-hr-1', survey_id, {'tenant_id': 'tenant-default'}, trace_id='trace-api-publish-sentiment')

    post_responses(
        service,
        'Employee',
        'emp-eng-1',
        {
            'tenant_id': 'tenant-default',
            'survey_id': survey_id,
            'employee_id': 'emp-eng-1',
            'answers': [{'question_id': 'q-d1', 'score': 5}, {'question_id': 'q-d2', 'score': 5}, {'question_id': 'q-d3', 'score': 4}, {'question_id': 'q-d4', 'score': 5}, {'question_id': 'q-d5', 'score': 5}],
            'overall_comment': 'Strong growth and excellent support from my manager.',
        },
        trace_id='trace-api-response-sentiment-1',
    )
    post_responses(
        service,
        'Employee',
        'emp-eng-2',
        {
            'tenant_id': 'tenant-default',
            'survey_id': survey_id,
            'employee_id': 'emp-eng-2',
            'answers': [{'question_id': 'q-d1', 'score': 3}, {'question_id': 'q-d2', 'score': 3}, {'question_id': 'q-d3', 'score': 3}, {'question_id': 'q-d4', 'score': 3}, {'question_id': 'q-d5', 'score': 3}],
            'overall_comment': 'Feeling overloaded and stressed this month.',
        },
        trace_id='trace-api-response-sentiment-2',
    )

    status, trends = get_sentiment_trends(service, 'HRAdmin', 'emp-hr-1', {'tenant_id': 'tenant-default', 'department_id': 'dep-eng'}, trace_id='trace-api-trends')
    assert status == 200
    assert trends['data']['items'][0]['responses'] == 2
    assert trends['data']['items'][0]['positive'] == 1
    assert trends['data']['items'][0]['negative'] == 1

    status, dashboard = get_engagement_dashboard(service, 'HRAdmin', 'emp-hr-1', {'tenant_id': 'tenant-default', 'department_id': 'dep-eng'}, trace_id='trace-api-dashboard')
    assert status == 200
    assert dashboard['data']['snapshot']['survey_count'] == 1
    assert dashboard['data']['snapshot']['latest_response_count'] == 2
