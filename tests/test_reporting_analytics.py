from __future__ import annotations

from datetime import datetime, timezone

from background_jobs import BackgroundJobService, JobStatus
from reporting_analytics import ReportingAnalyticsService
from reporting_analytics_api import (
    get_reporting_aggregates,
    get_reporting_exports,
    get_reporting_reports,
    get_reporting_schedules,
    post_reporting_export,
    post_reporting_report,
    post_reporting_run,
    post_reporting_schedule,
)
from services.hiring_service.service import HiringService


def _seed_hiring_data() -> HiringService:
    service = HiringService()
    backend = service.create_job_posting(
        {
            'title': 'Backend Engineer',
            'department_id': 'dep-eng',
            'role_id': 'role-eng',
            'employment_type': 'FullTime',
            'description': 'Build APIs',
            'openings_count': 2,
            'posting_date': '2026-03-01',
            'status': 'Open',
        }
    )
    designer = service.create_job_posting(
        {
            'title': 'Product Designer',
            'department_id': 'dep-design',
            'role_id': 'role-design',
            'employment_type': 'FullTime',
            'description': 'Design experiences',
            'openings_count': 1,
            'posting_date': '2026-03-02',
            'status': 'Open',
        }
    )

    hired = service.create_candidate(
        {
            'job_posting_id': backend['job_posting_id'],
            'first_name': 'Ava',
            'last_name': 'Stone',
            'email': 'ava@example.com',
            'application_date': '2026-03-03',
            'source': 'LinkedIn',
        }
    )
    service.update_candidate(hired['candidate_id'], {'status': 'Screening'})
    service.update_candidate(hired['candidate_id'], {'status': 'Interviewing'})
    interview = service.create_interview(
        {
            'candidate_id': hired['candidate_id'],
            'interview_type': 'Technical',
            'scheduled_start': '2026-03-05T10:00:00Z',
            'scheduled_end': '2026-03-05T11:00:00Z',
            'interviewer_employee_ids': ['emp-mgr-1'],
        }
    )
    service.update_interview(interview['interview_id'], {'status': 'Completed', 'recommendation': 'Hire'})
    service.update_candidate(hired['candidate_id'], {'status': 'Offered'})
    service.mark_candidate_hired(
        hired['candidate_id'],
        {
            'hire_date': '2026-03-10',
            'department_id': 'dep-eng',
            'role_id': 'role-eng',
        },
    )

    active = service.create_candidate(
        {
            'job_posting_id': backend['job_posting_id'],
            'first_name': 'Noah',
            'last_name': 'Lane',
            'email': 'noah@example.com',
            'application_date': '2026-03-04',
            'source': 'Referral',
        }
    )
    service.update_candidate(active['candidate_id'], {'status': 'Screening'})
    service.update_candidate(active['candidate_id'], {'status': 'Interviewing'})
    service.create_interview(
        {
            'candidate_id': active['candidate_id'],
            'interview_type': 'Panel',
            'scheduled_start': '2026-03-12T09:00:00Z',
            'scheduled_end': '2026-03-12T10:00:00Z',
            'interviewer_employee_ids': ['emp-mgr-2'],
        }
    )

    service.create_candidate(
        {
            'job_posting_id': designer['job_posting_id'],
            'first_name': 'Mia',
            'last_name': 'Gray',
            'email': 'mia@example.com',
            'application_date': '2026-03-06',
            'source': 'LinkedIn',
        }
    )
    return service


def _seed_reporting_service() -> tuple[ReportingAnalyticsService, HiringService]:
    hiring = _seed_hiring_data()
    reporting = ReportingAnalyticsService()
    reporting.sync_hiring_service(hiring)
    reporting.ingest_read_model(
        'employee_reporting_view',
        [
            {
                'employee_id': 'emp-1',
                'primary_manager_employee_id': 'mgr-1',
                'primary_manager_name': 'Priya Lead',
                'matrix_managers': [{'employee_id': 'mgr-2', 'manager_name': 'Theo Matrix'}],
                'reporting_lines': [{'reporting_line_id': 'line-1', 'manager_employee_id': 'mgr-1'}],
                'updated_at': '2026-03-10T00:00:00+00:00',
            },
            {
                'employee_id': 'emp-2',
                'primary_manager_employee_id': 'mgr-1',
                'primary_manager_name': 'Priya Lead',
                'matrix_managers': [],
                'reporting_lines': [{'reporting_line_id': 'line-2', 'manager_employee_id': 'mgr-1'}],
                'updated_at': '2026-03-10T00:00:00+00:00',
            },
        ],
    )
    return reporting, hiring


def test_reporting_service_builds_projection_backed_aggregates() -> None:
    reporting, _ = _seed_reporting_service()

    pipeline = reporting.list_aggregates(aggregate_type='hiring.pipeline.summary', dimension_key='department_id', dimension_value='dep-eng')
    assert len(pipeline) == 1
    assert pipeline[0]['metrics']['candidate_count'] == 2
    assert pipeline[0]['metrics']['hired_count'] == 1
    assert pipeline[0]['metrics']['stage_counts']['Hired'] == 1
    assert pipeline[0]['metrics']['stage_counts']['Interviewing'] == 1

    source_rows = reporting.list_aggregates(aggregate_type='hiring.source.effectiveness', dimension_key='source', dimension_value='LinkedIn')
    assert source_rows[0]['metrics']['candidate_count'] == 2
    assert source_rows[0]['metrics']['hire_count'] == 1
    assert source_rows[0]['metrics']['hire_rate'] == 0.5

    time_to_hire = reporting.list_aggregates(aggregate_type='hiring.time_to_hire', dimension_key='department_id', dimension_value='dep-eng')
    assert time_to_hire[0]['metrics']['hire_count'] == 1
    assert time_to_hire[0]['metrics']['average_days_to_hire'] == 7.0

    manager_span = reporting.list_aggregates(aggregate_type='organization.manager.span', dimension_key='manager_employee_id', dimension_value='mgr-1')
    assert manager_span[0]['metrics']['direct_report_count'] == 2
    assert manager_span[0]['metrics']['matrix_report_count'] == 1


def test_reporting_api_uses_d1_envelopes_for_reports_runs_exports_and_schedules() -> None:
    reporting, _ = _seed_reporting_service()

    status, created = post_reporting_report(
        reporting,
        {
            'name': 'Engineering pipeline summary',
            'report_type': 'hiring.pipeline.summary',
            'filters': {'dimension_key': 'department_id', 'dimension_value': 'dep-eng'},
        },
    )
    assert status == 201
    assert created['status'] == 'success'
    report_id = created['data']['report_id']

    list_status, listed = get_reporting_reports(reporting)
    assert list_status == 200
    assert listed['status'] == 'success'
    assert listed['meta']['pagination']['count'] == 1

    run_status, run_payload = post_reporting_run(reporting, report_id, {'filters': {}})
    assert run_status == 202
    assert run_payload['data']['summary']['generated_from_projection'] is True
    report_run_id = run_payload['data']['report_run_id']

    export_status, export_payload = post_reporting_export(
        reporting,
        {'report_id': report_id, 'report_run_id': report_run_id, 'export_format': 'csv'},
    )
    assert export_status == 202
    assert export_payload['data']['content_type'] == 'text/csv'
    assert 'aggregate_id' in export_payload['data']['content']

    exports_status, exports = get_reporting_exports(reporting, {'report_id': report_id})
    assert exports_status == 200
    assert exports['meta']['pagination']['count'] == 1

    schedule_status, schedule_payload = post_reporting_schedule(
        reporting,
        {
            'report_id': report_id,
            'cadence': 'daily',
            'export_format': 'json',
            'next_run_at': '2026-03-21T12:00:00+00:00',
            'delivery': {'channel': 'email', 'recipients': ['ops@example.com']},
        },
    )
    assert schedule_status == 201
    assert schedule_payload['data']['delivery']['channel'] == 'email'

    schedules_status, schedules = get_reporting_schedules(reporting, {'active_only': True})
    assert schedules_status == 200
    assert schedules['meta']['pagination']['count'] == 1

    aggregate_status, aggregates = get_reporting_aggregates(reporting, {'aggregate_type': 'hiring.pipeline.summary'})
    assert aggregate_status == 200
    assert aggregates['status'] == 'success'
    assert aggregates['meta']['pagination']['count'] >= 1


def test_reporting_background_jobs_generate_exports_and_dispatch_scheduled_reports() -> None:
    reporting, _ = _seed_reporting_service()
    created = reporting.create_report_definition(
        {
            'name': 'Daily hiring source report',
            'report_type': 'hiring.source.effectiveness',
            'filters': {},
        }
    )
    schedule = reporting.create_schedule(
        {
            'report_id': created['report_id'],
            'cadence': 'daily',
            'export_format': 'json',
            'next_run_at': '2026-03-21T12:00:00+00:00',
            'delivery': {'channel': 'email'},
        }
    )

    jobs = BackgroundJobService(reporting_service=reporting)
    dispatch = jobs.enqueue_job(
        tenant_id='tenant-default',
        job_type='reporting.schedule.dispatch',
        payload={'now': '2026-03-21T12:00:00+00:00'},
    )
    dispatched = jobs.execute_job(dispatch.job_id, tenant_id='tenant-default')

    assert dispatched.status == JobStatus.SUCCEEDED
    assert dispatched.last_result is not None
    assert dispatched.last_result['schedule_count'] == 1
    export_job_id = dispatched.last_result['enqueued_jobs'][0]['job_id']

    exported = jobs.execute_job(export_job_id, tenant_id='tenant-default')

    assert exported.status == JobStatus.SUCCEEDED
    assert exported.last_result is not None
    assert exported.last_result['schedule_id'] == schedule['schedule_id']
    assert len(reporting.list_exports(report_id=created['report_id'])) == 1
    assert any(event.event_name == 'ReportingExportGenerated' for event in jobs.outbox.list_events(tenant_id='tenant-default'))

    refreshed_schedule = reporting.list_schedules(active_only=True)[0]
    assert refreshed_schedule['last_enqueued_at'] == '2026-03-21T12:00:00+00:00'
    assert refreshed_schedule['next_run_at'] > '2026-03-21T12:00:00+00:00'


def test_reporting_event_ingestion_is_replay_safe_and_tenant_scoped() -> None:
    reporting, hiring = _seed_reporting_service()
    hire_event = next(event for event in hiring.events if event['event_type'] == 'hiring.candidate.hired')

    baseline = len(reporting.processed_events)
    reporting.ingest_event(hire_event)
    reporting.ingest_event(hire_event)

    assert len(reporting.processed_events) == baseline

    cross_tenant_event = {
        **hire_event,
        'event_id': 'evt-cross-tenant',
        'tenant_id': 'tenant-other',
        'data': {**hire_event['data'], 'tenant_id': 'tenant-other'},
    }

    try:
        reporting.ingest_event(cross_tenant_event)
    except ValueError as exc:
        assert str(exc) == 'cross_tenant_event_blocked'
    else:
        raise AssertionError('expected reporting to reject cross-tenant events')
