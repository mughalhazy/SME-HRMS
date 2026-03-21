from __future__ import annotations

from search_api import get_candidate_search, get_search
from search_service import SearchIndexingService
from background_jobs import BackgroundJobService


def _employee_row(*, tenant_id: str = 'tenant-default', employee_id: str = 'emp-1', full_name: str = 'Ava Patel', department_id: str = 'dep-eng', department_name: str = 'Engineering', role_id: str = 'role-eng', role_title: str = 'Platform Engineer', status: str = 'Active') -> dict[str, str]:
    return {
        'tenant_id': tenant_id,
        'employee_id': employee_id,
        'employee_number': f'EMP-{employee_id}',
        'full_name': full_name,
        'email': f'{employee_id}@example.com',
        'phone': '+1-555-0100',
        'hire_date': '2026-01-10',
        'employment_type': 'FullTime',
        'employee_status': status,
        'department_id': department_id,
        'department_name': department_name,
        'role_id': role_id,
        'role_title': role_title,
        'manager_employee_id': 'mgr-1',
        'manager_name': 'Helen Brooks',
        'updated_at': '2026-01-12T09:30:00+00:00',
    }


def _org_row(*, tenant_id: str = 'tenant-default', department_id: str = 'dep-eng', employee_id: str = 'emp-1', employee_name: str = 'Ava Patel', role_id: str = 'role-eng', role_title: str = 'Platform Engineer') -> dict[str, str]:
    return {
        'tenant_id': tenant_id,
        'department_id': department_id,
        'department_name': 'Engineering',
        'department_code': 'ENG',
        'department_status': 'Active',
        'head_employee_id': 'mgr-1',
        'head_employee_name': 'Helen Brooks',
        'employee_id': employee_id,
        'employee_name': employee_name,
        'employee_status': 'Active',
        'manager_employee_id': 'mgr-1',
        'manager_name': 'Helen Brooks',
        'role_id': role_id,
        'role_title': role_title,
        'updated_at': '2026-01-12T09:30:00+00:00',
    }


def _candidate_row(*, tenant_id: str = 'tenant-default', candidate_id: str = 'cand-1', candidate_name: str = 'Noah Kim', department_id: str = 'dep-eng', role_id: str = 'role-eng', stage: str = 'Interviewing') -> dict[str, str | int | None]:
    return {
        'tenant_id': tenant_id,
        'candidate_id': candidate_id,
        'candidate_name': candidate_name,
        'candidate_email': f'{candidate_id}@example.com',
        'job_posting_id': 'job-1',
        'job_title': 'Platform Engineer',
        'department_id': department_id,
        'department_name': 'Engineering',
        'role_id': role_id,
        'role_title': 'Platform Engineer',
        'application_date': '2026-01-03',
        'pipeline_stage': stage,
        'stage_updated_at': '2026-01-11T08:00:00+00:00',
        'source': 'Referral',
        'source_candidate_id': None,
        'next_interview_at': '2026-01-15T10:00:00+00:00',
        'interview_count': 2,
        'last_interview_recommendation': 'Hire',
        'updated_at': '2026-01-11T08:00:00+00:00',
    }


def _document_row(*, tenant_id: str = 'tenant-default', document_id: str = 'doc-1', employee_id: str = 'emp-1', employee_name: str = 'Ava Patel') -> dict[str, str | bool]:
    return {
        'tenant_id': tenant_id,
        'document_id': document_id,
        'employee_id': employee_id,
        'employee_name': employee_name,
        'department_id': 'dep-eng',
        'department_name': 'Engineering',
        'title': 'Forklift License',
        'document_type': 'Certification',
        'status': 'Active',
        'policy_code': '',
        'expiry_date': '2026-12-01',
        'requires_acknowledgement': False,
        'created_at': '2026-01-02T10:00:00+00:00',
        'updated_at': '2026-01-12T11:00:00+00:00',
    }


def _payroll_row(*, tenant_id: str = 'tenant-default', employee_id: str = 'emp-1', department_name: str = 'Engineering') -> dict[str, str]:
    return {
        'tenant_id': tenant_id,
        'payroll_record_id': f'pay-{employee_id}',
        'employee_id': employee_id,
        'employee_number': f'EMP-{employee_id}',
        'employee_name': 'Ava Patel',
        'department_id': 'dep-eng',
        'department_name': department_name,
        'pay_period_start': '2026-01-01',
        'pay_period_end': '2026-01-31',
        'base_salary': '10000.00',
        'allowances': '500.00',
        'deductions': '100.00',
        'overtime_pay': '0.00',
        'gross_pay': '10500.00',
        'net_pay': '10400.00',
        'currency': 'USD',
        'payment_date': '2026-02-01',
        'status': 'Processed',
        'attendance_days_count': 22,
        'approved_leave_days': 0,
        'updated_at': '2026-02-01T09:00:00+00:00',
    }


def test_search_indexing_pipeline_uses_events_and_projection_reads(tmp_path) -> None:
    service = SearchIndexingService(db_path=str(tmp_path / 'search.sqlite3'))
    jobs = BackgroundJobService(db_path=str(tmp_path / 'search.sqlite3'))
    service.register_background_jobs(jobs)

    service.ingest_read_model('employee_directory_view', [_employee_row()], replace=True)
    service.ingest_read_model('organization_structure_view', [_org_row()], replace=True)
    service.ingest_read_model('candidate_pipeline_view', [_candidate_row()], replace=True)
    service.ingest_read_model('document_library_view', [_document_row()], replace=True)
    service.ingest_read_model('payroll_summary_view', [_payroll_row()], replace=True)

    service.consume_event({'event_id': 'evt-emp-1', 'event_name': 'EmployeeUpdated', 'tenant_id': 'tenant-default', 'trace_id': 'trace-search-1'}, background_jobs=jobs)
    service.consume_event({'event_id': 'evt-cand-1', 'event_name': 'CandidateStageChanged', 'tenant_id': 'tenant-default', 'trace_id': 'trace-search-2'}, background_jobs=jobs)
    service.consume_event({'event_id': 'evt-doc-1', 'event_name': 'DocumentStored', 'tenant_id': 'tenant-default', 'trace_id': 'trace-search-3'}, background_jobs=jobs)
    service.consume_event({'event_id': 'evt-pay-1', 'event_name': 'PayrollProcessed', 'tenant_id': 'tenant-default', 'trace_id': 'trace-search-4'}, background_jobs=jobs)

    executed = jobs.run_due_jobs(tenant_id='tenant-default')
    assert len(executed) == 4

    payload = service.search(tenant_id='tenant-default', q='Engineering', limit=10)
    entity_types = {item['entity_type'] for item in payload['items']}
    assert {'employee', 'department', 'candidate', 'document', 'payroll_run'}.issubset(entity_types)

    state = service.get_projection_state(tenant_id='tenant-default')
    assert state['last_query']['used_index_only'] is True
    assert 'global_index:tenant-default' in state['states']


def test_search_updates_incrementally_when_read_model_rows_change(tmp_path) -> None:
    service = SearchIndexingService(db_path=str(tmp_path / 'search.sqlite3'))
    jobs = BackgroundJobService(db_path=str(tmp_path / 'search.sqlite3'))
    service.register_background_jobs(jobs)

    service.ingest_read_model('employee_directory_view', [_employee_row(role_title='Platform Engineer')], replace=True)
    service.consume_event({'event_id': 'evt-1', 'event_name': 'EmployeeCreated', 'tenant_id': 'tenant-default'}, background_jobs=jobs)
    jobs.run_due_jobs(tenant_id='tenant-default')

    first = service.search(tenant_id='tenant-default', q='Platform', entity_types=['employee'])
    assert first['items'][0]['metadata']['employee_id'] == 'emp-1'

    service.ingest_read_model('employee_directory_view', [_employee_row(role_title='Staff Platform Engineer')], replace=False)
    service.consume_event({'event_id': 'evt-2', 'event_name': 'EmployeeUpdated', 'tenant_id': 'tenant-default'}, background_jobs=jobs)
    jobs.run_due_jobs(tenant_id='tenant-default')

    updated = service.search(tenant_id='tenant-default', q='Staff', entity_types=['employee'])
    assert updated['items'][0]['role_title'] == 'Staff Platform Engineer'
    state = service.get_projection_state(tenant_id='tenant-default')
    assert state['states']['index:tenant-default:employee_directory_view']['document_count'] == 1


def test_search_enforces_tenant_isolation_and_domain_filters(tmp_path) -> None:
    service = SearchIndexingService(db_path=str(tmp_path / 'search.sqlite3'))
    jobs = BackgroundJobService(db_path=str(tmp_path / 'search.sqlite3'))
    service.register_background_jobs(jobs)

    service.ingest_read_model('employee_directory_view', [_employee_row(tenant_id='tenant-default', full_name='Ava Patel')], replace=True)
    service.ingest_read_model('employee_directory_view', [_employee_row(tenant_id='tenant-other', employee_id='emp-2', full_name='Omar Diaz', department_id='dep-fin', department_name='Finance', role_id='role-fin', role_title='Finance Manager')], tenant_id='tenant-other', replace=True)
    service.ingest_read_model('candidate_pipeline_view', [_candidate_row(tenant_id='tenant-default')], replace=True)
    service.ingest_read_model('candidate_pipeline_view', [_candidate_row(tenant_id='tenant-other', candidate_id='cand-2', candidate_name='Lina Cruz', department_id='dep-fin', role_id='role-fin', stage='Applied')], tenant_id='tenant-other', replace=True)

    service.consume_event({'event_id': 'evt-a', 'event_name': 'EmployeeUpdated', 'tenant_id': 'tenant-default'}, background_jobs=jobs)
    service.consume_event({'event_id': 'evt-b', 'event_name': 'EmployeeUpdated', 'tenant_id': 'tenant-other'}, background_jobs=jobs)
    service.consume_event({'event_id': 'evt-c', 'event_name': 'CandidateApplied', 'tenant_id': 'tenant-default'}, background_jobs=jobs)
    service.consume_event({'event_id': 'evt-d', 'event_name': 'CandidateApplied', 'tenant_id': 'tenant-other'}, background_jobs=jobs)
    jobs.run_due_jobs()

    default_payload = service.search(tenant_id='tenant-default', q='Ava', limit=10)
    other_payload = service.search(tenant_id='tenant-other', q='Omar', limit=10)
    candidate_payload = service.search(tenant_id='tenant-default', q='Noah', domains=['hiring'])

    assert len(default_payload['items']) == 1
    assert default_payload['items'][0]['tenant_id'] == 'tenant-default'
    assert len(other_payload['items']) == 1
    assert other_payload['items'][0]['tenant_id'] == 'tenant-other'
    assert all(item['domain'] == 'hiring' for item in candidate_payload['items'])


def test_search_api_is_d1_compliant_and_supports_domain_specific_endpoints(tmp_path) -> None:
    service = SearchIndexingService(db_path=str(tmp_path / 'search.sqlite3'))
    jobs = BackgroundJobService(db_path=str(tmp_path / 'search.sqlite3'))
    service.register_background_jobs(jobs)

    service.ingest_read_model('candidate_pipeline_view', [_candidate_row()], replace=True)
    service.consume_event({'event_id': 'evt-api-1', 'event_name': 'CandidateApplied', 'tenant_id': 'tenant-default'}, background_jobs=jobs)
    jobs.run_due_jobs(tenant_id='tenant-default')

    status, payload = get_search(service, {'tenant_id': 'tenant-default', 'q': 'Noah', 'limit': '10'}, trace_id='trace-search-api')
    assert status == 200
    assert payload['status'] == 'success'
    assert payload['meta']['request_id'] == 'trace-search-api'
    assert payload['meta']['pagination']['count'] == 1
    assert payload['data'][0]['entity_type'] == 'candidate'

    status, candidates_only = get_candidate_search(service, {'tenant_id': 'tenant-default', 'q': 'Noah'}, trace_id='trace-search-candidates')
    assert status == 200
    assert candidates_only['meta']['pagination']['count'] == 1
    assert all(item['entity_type'] == 'candidate' for item in candidates_only['data'])

    error_status, error_payload = get_search(service, {'q': 'Noah'}, trace_id='trace-search-missing-tenant')
    assert error_status == 422
    assert error_payload['status'] == 'error'
    assert error_payload['error']['code'] == 'VALIDATION_ERROR'
    assert error_payload['meta']['request_id'] == 'trace-search-missing-tenant'
