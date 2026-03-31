from __future__ import annotations

from datetime import datetime, timezone

from background_jobs import BackgroundJobService, JobStatus
from reporting_analytics import ReportingAnalyticsService
from reporting_analytics_api import (
    get_reporting_aggregates,
    get_reporting_exports,
    get_reporting_reports,
    get_reporting_schedules,
    get_workforce_attendance_trends,
    get_workforce_attrition_metrics,
    get_workforce_dashboard,
    get_workforce_hiring_funnel,
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
    reporting.sync_workforce_read_models(
        employee_directory_rows=[
            {
                'employee_id': 'emp-1',
                'employee_number': 'E-001',
                'full_name': 'Priya Lead',
                'hire_date': '2024-01-10',
                'employment_type': 'FullTime',
                'employee_status': 'Active',
                'department_id': 'dep-eng',
                'department_name': 'Engineering',
                'role_id': 'role-eng-lead',
                'role_title': 'Engineering Manager',
            },
            {
                'employee_id': 'emp-2',
                'employee_number': 'E-002',
                'full_name': 'Theo Matrix',
                'hire_date': '2024-04-15',
                'employment_type': 'FullTime',
                'employee_status': 'OnLeave',
                'department_id': 'dep-eng',
                'department_name': 'Engineering',
                'role_id': 'role-eng',
                'role_title': 'Senior Engineer',
            },
            {
                'employee_id': 'emp-legacy-1',
                'employee_number': 'E-099',
                'full_name': 'Former Designer',
                'hire_date': '2023-02-01',
                'employment_type': 'FullTime',
                'employee_status': 'Terminated',
                'department_id': 'dep-design',
                'department_name': 'Design',
                'role_id': 'role-design',
                'role_title': 'Designer',
            },
        ],
        attendance_rows=[
            {
                'employee_id': 'emp-1',
                'employee_number': 'E-001',
                'employee_name': 'Priya Lead',
                'department_id': 'dep-eng',
                'department_name': 'Engineering',
                'attendance_date': '2026-03-10',
                'attendance_status': 'Present',
                'check_in_time': '2026-03-10T09:00:00+00:00',
                'check_out_time': '2026-03-10T17:30:00+00:00',
                'total_hours': '8.50',
                'source': 'Manual',
                'record_state': 'Approved',
                'updated_at': '2026-03-10T17:30:00+00:00',
            },
            {
                'employee_id': 'emp-2',
                'employee_number': 'E-002',
                'employee_name': 'Theo Matrix',
                'department_id': 'dep-eng',
                'department_name': 'Engineering',
                'attendance_date': '2026-03-10',
                'attendance_status': 'Late',
                'check_in_time': '2026-03-10T09:30:00+00:00',
                'check_out_time': '2026-03-10T17:00:00+00:00',
                'total_hours': '7.50',
                'source': 'Manual',
                'record_state': 'Approved',
                'updated_at': '2026-03-10T17:00:00+00:00',
            },
            {
                'employee_id': 'emp-legacy-1',
                'employee_number': 'E-099',
                'employee_name': 'Former Designer',
                'department_id': 'dep-design',
                'department_name': 'Design',
                'attendance_date': '2026-03-10',
                'attendance_status': 'Absent',
                'check_in_time': None,
                'check_out_time': None,
                'total_hours': '0.00',
                'source': 'Manual',
                'record_state': 'Approved',
                'updated_at': '2026-03-10T17:00:00+00:00',
            },
        ],
    )
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
    reporting.ingest_event(
        {
            'event_name': 'EmployeeStatusChanged',
            'tenant_id': 'tenant-default',
            'source': 'employee-service',
            'data': {
                'employee_id': 'emp-legacy-1',
                'department_id': 'dep-design',
                'from_status': 'Active',
                'to_status': 'Terminated',
                'effective_at': '2026-03-09T00:00:00+00:00',
            },
        }
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

    hiring_funnel = reporting.list_aggregates(aggregate_type='hiring.funnel.summary', dimension_key='department_id', dimension_value='dep-eng')
    assert hiring_funnel[0]['metrics']['application_count'] == 2
    assert hiring_funnel[0]['metrics']['interview_count'] == 1
    assert hiring_funnel[0]['metrics']['hire_conversion_rate'] == 0.5

    attrition = reporting.list_aggregates(aggregate_type='workforce.attrition.summary', dimension_key='department_id', dimension_value='dep-design')
    assert attrition[0]['metrics']['terminated_employee_count'] == 1
    assert attrition[0]['metrics']['termination_event_count'] == 1
    assert attrition[0]['metrics']['attrition_rate'] == 1.0

    attendance = reporting.list_aggregates(aggregate_type='workforce.attendance.trend', dimension_key='attendance_date', dimension_value='2026-03-10')
    assert attendance[0]['metrics']['record_count'] == 3
    assert attendance[0]['metrics']['attendance_rate'] == 0.6667
    assert attendance[0]['metrics']['average_hours'] == 5.33

    dashboard = reporting.list_aggregates(aggregate_type='workforce.dashboard.summary', dimension_key='tenant', dimension_value='tenant-default')
    assert dashboard[0]['metrics']['headcount']['current'] == 2
    assert dashboard[0]['metrics']['attrition']['terminated_employee_count'] == 1
    assert dashboard[0]['metrics']['hiring_funnel']['hire_conversion_rate'] == 0.3333
    assert dashboard[0]['metrics']['attendance']['attendance_rate'] == 0.6667


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

    dashboard_report_status, dashboard_report = post_reporting_report(
        reporting,
        {
            'name': 'Workforce intelligence dashboard',
            'report_type': 'workforce.dashboard.summary',
            'filters': {'dimension_key': 'tenant', 'dimension_value': 'tenant-default'},
        },
    )
    assert dashboard_report_status == 201

    dashboard_run_status, dashboard_run = post_reporting_run(reporting, dashboard_report['data']['report_id'], {'filters': {}})
    assert dashboard_run_status == 202
    assert dashboard_run['data']['rows'][0]['metrics']['attendance']['attendance_rate'] == 0.6667


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


def test_workforce_intelligence_api_shortcuts_expose_advanced_metrics() -> None:
    reporting, _ = _seed_reporting_service()

    status, attrition = get_workforce_attrition_metrics(reporting, {'dimension_key': 'tenant', 'dimension_value': 'tenant-default'})
    assert status == 200
    assert attrition['data']['items'][0]['aggregate_type'] == 'workforce.attrition.summary'

    status, funnel = get_workforce_hiring_funnel(reporting, {'dimension_key': 'tenant', 'dimension_value': 'tenant-default'})
    assert status == 200
    assert funnel['data']['items'][0]['metrics']['hire_conversion_rate'] == 0.3333

    status, attendance = get_workforce_attendance_trends(reporting, {'dimension_key': 'attendance_date', 'dimension_value': '2026-03-10'})
    assert status == 200
    assert attendance['data']['items'][0]['metrics']['attendance_rate'] == 0.6667

    status, dashboard = get_workforce_dashboard(reporting, {'dimension_key': 'tenant', 'dimension_value': 'tenant-default'})
    assert status == 200
    assert dashboard['data']['items'][0]['aggregate_type'] == 'workforce.dashboard.summary'
