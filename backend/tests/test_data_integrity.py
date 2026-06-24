from __future__ import annotations

import base64
import json
from datetime import date

from audit_service.service import AuditService
from background_jobs import BackgroundJobService, JobStatus
from data_integrity import DataIntegrityValidator, build_payroll_summary_rows
from leave_service import LeaveService
from payroll_service import PayrollService
from reporting_analytics import ReportingAnalyticsService
from search_service import SearchIndexingService
from services.hiring_service.service import HiringService


def _bearer(role: str, employee_id: str | None = None, department_id: str | None = None) -> str:
    payload = {'role': role}
    if employee_id is not None:
        payload['employee_id'] = employee_id
    if department_id is not None:
        payload['department_id'] = department_id
    return 'Bearer ' + base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')


def _employee_directory_rows() -> list[dict[str, object]]:
    return [
        {
            'tenant_id': 'tenant-default',
            'employee_id': 'emp-manager',
            'employee_number': 'EMP-MGR',
            'full_name': 'Mina Lead',
            'email': 'mina.lead@example.com',
            'hire_date': '2025-01-01',
            'employment_type': 'FullTime',
            'employee_status': 'Active',
            'department_id': 'dep-eng',
            'department_name': 'Engineering',
            'role_id': 'role-manager',
            'role_title': 'Engineering Manager',
            'updated_at': '2026-03-01T00:00:00+00:00',
            'matrix_manager_employee_ids': [],
            'cost_allocations': [{'cost_center_id': 'cc-eng', 'allocation_percentage': 100}],
        },
        {
            'tenant_id': 'tenant-default',
            'employee_id': 'emp-001',
            'employee_number': 'EMP-001',
            'full_name': 'Amina Yusuf',
            'email': 'amina.yusuf@example.com',
            'hire_date': '2025-02-01',
            'employment_type': 'FullTime',
            'employee_status': 'Active',
            'department_id': 'dep-eng',
            'department_name': 'Engineering',
            'role_id': 'role-eng',
            'role_title': 'Software Engineer',
            'manager_employee_id': 'emp-manager',
            'manager_name': 'Mina Lead',
            'updated_at': '2026-03-01T00:00:00+00:00',
            'matrix_manager_employee_ids': [],
            'cost_allocations': [{'cost_center_id': 'cc-eng', 'allocation_percentage': 100}],
        },
        {
            'tenant_id': 'tenant-default',
            'employee_id': 'emp-200',
            'employee_number': 'EMP-200',
            'full_name': 'Ava Stone',
            'email': 'ava@example.com',
            'hire_date': '2026-03-10',
            'employment_type': 'FullTime',
            'employee_status': 'Draft',
            'department_id': 'dep-eng',
            'department_name': 'Engineering',
            'role_id': 'role-eng',
            'role_title': 'Backend Engineer',
            'manager_employee_id': 'emp-manager',
            'manager_name': 'Mina Lead',
            'updated_at': '2026-03-10T00:00:00+00:00',
            'matrix_manager_employee_ids': [],
            'cost_allocations': [{'cost_center_id': 'cc-eng', 'allocation_percentage': 100}],
        },
    ]


def _organization_structure_rows() -> list[dict[str, object]]:
    rows = []
    for row in _employee_directory_rows():
        rows.append(
            {
                'tenant_id': row['tenant_id'],
                'department_id': row['department_id'],
                'department_name': row['department_name'],
                'department_code': 'ENG',
                'department_status': 'Active',
                'head_employee_id': 'emp-manager',
                'head_employee_name': 'Mina Lead',
                'employee_id': row['employee_id'],
                'employee_name': row['full_name'],
                'employee_status': row['employee_status'],
                'manager_employee_id': row.get('manager_employee_id'),
                'manager_name': row.get('manager_name'),
                'role_id': row['role_id'],
                'role_title': row['role_title'],
                'updated_at': row['updated_at'],
            }
        )
    return rows


def _employee_reporting_rows() -> list[dict[str, object]]:
    return [
        {
            'tenant_id': 'tenant-default',
            'employee_id': 'emp-001',
            'primary_manager_employee_id': 'emp-manager',
            'primary_manager_name': 'Mina Lead',
            'matrix_managers': [],
            'reporting_lines': [{'reporting_line_id': 'line-1', 'manager_employee_id': 'emp-manager'}],
            'updated_at': '2026-03-01T00:00:00+00:00',
        },
        {
            'tenant_id': 'tenant-default',
            'employee_id': 'emp-200',
            'primary_manager_employee_id': 'emp-manager',
            'primary_manager_name': 'Mina Lead',
            'matrix_managers': [],
            'reporting_lines': [{'reporting_line_id': 'line-2', 'manager_employee_id': 'emp-manager'}],
            'updated_at': '2026-03-10T00:00:00+00:00',
        },
    ]


def _seed_runtime(tmp_path, monkeypatch):
    audit_path = tmp_path / 'audit-records.jsonl'
    monkeypatch.setenv('HRMS_AUDIT_LOG_PATH', str(audit_path))

    leave = LeaveService(db_path=str(tmp_path / 'leave.sqlite3'))
    payroll = PayrollService(db_path=str(tmp_path / 'payroll.sqlite3'))
    hiring = HiringService(db_path=str(tmp_path / 'hiring.sqlite3'))
    search = SearchIndexingService(db_path=str(tmp_path / 'search.sqlite3'))
    reporting = ReportingAnalyticsService(db_path=str(tmp_path / 'reporting.sqlite3'))
    jobs = BackgroundJobService(leave_service=leave, db_path=str(tmp_path / 'jobs.sqlite3'))

    # Leave domain activity.
    _, created_leave = leave.create_request(
        'Employee',
        'emp-001',
        'emp-001',
        'Annual',
        date(2026, 4, 10),
        date(2026, 4, 12),
        tenant_id='tenant-default',
        trace_id='trace-leave-create',
    )
    leave.submit_request('Employee', 'emp-001', created_leave['leave_request_id'], tenant_id='tenant-default', trace_id='trace-leave-submit')
    leave.decide_request('approve', 'Manager', 'emp-manager', created_leave['leave_request_id'], tenant_id='tenant-default', trace_id='trace-leave-approve')

    # Hiring handoff.
    posting = hiring.create_job_posting(
        {
            'title': 'Backend Engineer',
            'department_id': 'dep-eng',
            'role_id': 'role-eng',
            'employment_type': 'FullTime',
            'description': 'Build APIs',
            'openings_count': 1,
            'posting_date': '2026-03-01',
            'status': 'Open',
        }
    )
    candidate = hiring.create_candidate(
        {
            'job_posting_id': posting['job_posting_id'],
            'first_name': 'Ava',
            'last_name': 'Stone',
            'email': 'ava@example.com',
            'application_date': '2026-03-03',
            'source': 'Referral',
        }
    )
    hiring.update_candidate(candidate['candidate_id'], {'status': 'Screening', 'changed_by': 'recruiter-1'})
    hiring.update_candidate(candidate['candidate_id'], {'status': 'Interviewing', 'changed_by': 'recruiter-1'})
    offer = hiring.create_offer(
        {
            'candidate_id': candidate['candidate_id'],
            'salary_amount': 95000,
            'currency': 'USD',
            'start_date': '2026-03-10',
            'created_by': 'recruiter-1',
            'changed_by': 'recruiter-1',
        }
    )
    hiring.approve_offer(offer['offer_id'], {'tenant_id': 'tenant-default', 'changed_by': 'role:Admin', 'approver_assignee': 'role:Admin', 'approver_role': 'Admin'})
    hiring.mark_candidate_hired(
        candidate['candidate_id'],
        {
            'employee_id': 'emp-200',
            'employee_number': 'EMP-200',
            'department_id': 'dep-eng',
            'role_id': 'role-eng',
            'changed_by': 'role:Admin',
            'approver_assignee': 'role:Admin',
            'approver_role': 'Admin',
            'hire_date': '2026-03-10',
        },
    )

    # Payroll activity.
    admin = _bearer('Admin', 'emp-manager', 'dep-eng')
    payroll.register_employee_profile('emp-200', department_id='dep-eng', role_id='role-eng', status='Draft')
    payroll.sync_compensation_context(
        {
            'employee_id': 'emp-200',
            'department_id': 'dep-eng',
            'role_id': 'role-eng',
            'employee_status': 'Draft',
            'effective_from': '2026-03-01',
            'base_salary': '8000.00',
            'allowances': '500.00',
            'currency': 'USD',
            'overtime_rate': '50.00',
        }
    )
    _, record = payroll.create_payroll_record(
        {
            'employee_id': 'emp-200',
            'pay_period_start': '2026-03-01',
            'pay_period_end': '2026-03-31',
            'base_salary': '8000.00',
            'allowances': '500.00',
            'currency': 'USD',
        },
        admin,
        trace_id='trace-payroll-create',
    )
    payroll.run_payroll('2026-03-01', '2026-03-31', admin, trace_id='trace-payroll-run')
    payroll.mark_paid(record['payroll_record_id'], admin, payment_date='2026-04-01', trace_id='trace-payroll-paid')

    # Projection layers.
    employee_rows = _employee_directory_rows()
    org_rows = _organization_structure_rows()
    reporting_rows = _employee_reporting_rows()
    search.ingest_read_model('employee_directory_view', employee_rows, tenant_id='tenant-default', replace=True)
    search.ingest_read_model('organization_structure_view', org_rows, tenant_id='tenant-default', replace=True)
    search.ingest_read_model('candidate_pipeline_view', hiring.list_candidate_pipeline_view(tenant_id='tenant-default'), tenant_id='tenant-default', replace=True)
    search.ingest_read_model('payroll_summary_view', build_payroll_summary_rows(payroll, employee_directory_rows=employee_rows), tenant_id='tenant-default', replace=True)
    search.rebuild_index(tenant_id='tenant-default')

    reporting.sync_hiring_service(hiring)
    reporting.ingest_read_model('employee_reporting_view', reporting_rows)

    audit = AuditService(log_path=str(audit_path))
    return leave, payroll, hiring, search, reporting, jobs, audit, employee_rows, org_rows, reporting_rows


def test_data_integrity_validator_detects_cross_service_and_projection_drift(tmp_path, monkeypatch) -> None:
    leave, payroll, hiring, search, reporting, jobs, audit, employee_rows, org_rows, reporting_rows = _seed_runtime(tmp_path, monkeypatch)

    # Introduce minor repairable drift and a critical event gap.
    leave.leave_balances[('emp-001', next(iter({balance.leave_type for balance in leave.leave_balances.values() if balance.employee_id == 'emp-001'})))].reserved_days = 99.0
    first_doc_id = next(iter(search.index_documents.keys()))
    broken_doc = search.index_documents[first_doc_id]
    broken_doc.display_name = 'Corrupted Search Document'
    broken_doc.tenant_id = 'tenant-other'
    search.index_documents[first_doc_id] = broken_doc
    first_aggregate_id = next(iter(reporting.aggregate_snapshots.keys()))
    broken_aggregate = reporting.aggregate_snapshots[first_aggregate_id]
    broken_aggregate.metrics['candidate_count'] = 999
    broken_aggregate.tenant_id = 'tenant-other'
    reporting.aggregate_snapshots[first_aggregate_id] = broken_aggregate
    hiring.events = [event for event in hiring.events if event.get('event_name') != 'CandidateHired' and event.get('legacy_event_name') != 'CandidateHired']

    validator = DataIntegrityValidator(
        tenant_id='tenant-default',
        employee_directory_rows=employee_rows,
        organization_structure_rows=org_rows,
        employee_reporting_rows=reporting_rows,
        leave_service=leave,
        payroll_service=payroll,
        hiring_service=hiring,
        search_service=search,
        reporting_service=reporting,
        audit_service=audit,
        background_jobs=jobs,
    )

    report = validator.validate()

    codes = {issue.code for issue in report.issues}
    assert 'leave_balance_mismatch' in codes
    assert 'search_projection_drift' in codes
    assert 'analytics_projection_drift' in codes
    assert 'candidate_hire_event_gap' in codes
    assert report.scores['projection_integrity'] < 10
    assert report.scores['audit_event_alignment'] < 10


def test_data_integrity_auto_fix_repairs_minor_drift_without_masking_critical_gaps(tmp_path, monkeypatch) -> None:
    leave, payroll, hiring, search, reporting, jobs, audit, employee_rows, org_rows, reporting_rows = _seed_runtime(tmp_path, monkeypatch)

    leave.leave_balances[('emp-001', next(iter({balance.leave_type for balance in leave.leave_balances.values() if balance.employee_id == 'emp-001'})))].reserved_days = 99.0
    doc_id = next(iter(search.index_documents.keys()))
    doc = search.index_documents[doc_id]
    doc.display_name = 'Drifted'
    search.index_documents[doc_id] = doc
    aggregate_id = next(iter(reporting.aggregate_snapshots.keys()))
    aggregate = reporting.aggregate_snapshots[aggregate_id]
    aggregate.metrics['hire_count'] = 999
    reporting.aggregate_snapshots[aggregate_id] = aggregate
    hiring.events = [event for event in hiring.events if event.get('event_name') != 'CandidateHired' and event.get('legacy_event_name') != 'CandidateHired']

    validator = DataIntegrityValidator(
        tenant_id='tenant-default',
        employee_directory_rows=employee_rows,
        organization_structure_rows=org_rows,
        employee_reporting_rows=reporting_rows,
        leave_service=leave,
        payroll_service=payroll,
        hiring_service=hiring,
        search_service=search,
        reporting_service=reporting,
        audit_service=audit,
        background_jobs=jobs,
    )

    report = validator.validate(auto_fix=True)
    codes = {issue.code for issue in report.issues}

    assert report.applied_repairs
    assert report.recheck == {
        'entity_integrity': True,
        'projection_alignment': True,
        'cross_service_consistency': True,
    }
    assert 'leave_balance_mismatch' not in codes
    assert 'search_projection_drift' not in codes
    assert 'analytics_projection_drift' not in codes
    assert 'candidate_hire_event_gap' in codes
    assert report.scores['entity_integrity'] == 10
    assert report.scores['projection_integrity'] == 10
    assert report.scores['audit_event_alignment'] < 10


def test_integrity_repair_background_job_executes_safe_repairs(tmp_path, monkeypatch) -> None:
    leave, payroll, hiring, search, reporting, jobs, audit, employee_rows, org_rows, reporting_rows = _seed_runtime(tmp_path, monkeypatch)

    leave.leave_balances[('emp-001', next(iter({balance.leave_type for balance in leave.leave_balances.values() if balance.employee_id == 'emp-001'})))].reserved_days = 99.0
    validator = DataIntegrityValidator(
        tenant_id='tenant-default',
        employee_directory_rows=employee_rows,
        organization_structure_rows=org_rows,
        employee_reporting_rows=reporting_rows,
        leave_service=leave,
        payroll_service=payroll,
        hiring_service=hiring,
        search_service=search,
        reporting_service=reporting,
        audit_service=audit,
        background_jobs=jobs,
    )
    validator.register_background_jobs(jobs)

    job = jobs.enqueue_job(
        tenant_id='tenant-default',
        job_type='integrity.repair',
        payload={'auto_fix': True},
        idempotency_key='integrity-repair-job',
    )
    completed = jobs.execute_job(job.job_id, tenant_id='tenant-default')

    assert completed.status == JobStatus.SUCCEEDED
    assert completed.last_result is not None
    assert completed.last_result['summary']['repair_count'] >= 1
    assert all(issue['code'] != 'leave_balance_mismatch' for issue in completed.last_result['issues'])
