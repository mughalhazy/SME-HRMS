from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Iterable, Mapping

from audit_service.service import AuditService
from background_jobs import BackgroundJobService
from persistent_store import PersistentKVStore
from reporting_analytics import ReportingAnalyticsService
from search_service import SearchIndexingService
from tenant_support import DEFAULT_TENANT_ID, normalize_tenant_id


@dataclass(slots=True)
class IntegrityIssue:
    dimension: str
    code: str
    severity: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)
    repairable: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class IntegrityReport:
    checked_at: str
    tenant_id: str
    scores: dict[str, int]
    summary: dict[str, Any]
    issues: list[IntegrityIssue]
    applied_repairs: list[dict[str, Any]] = field(default_factory=list)
    recheck: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            'checked_at': self.checked_at,
            'tenant_id': self.tenant_id,
            'scores': dict(self.scores),
            'summary': dict(self.summary),
            'issues': [issue.to_dict() for issue in self.issues],
            'applied_repairs': [dict(item) for item in self.applied_repairs],
            'recheck': dict(self.recheck),
        }


class DataIntegrityValidator:
    """Cross-service integrity validation and safe repair orchestration.

    The validator preserves service ownership by reading each domain's authoritative service state
    and validating consistency through projections, events, workflow traces, and audit records.
    """

    DIMENSIONS = (
        'entity_integrity',
        'cross_service_consistency',
        'projection_integrity',
        'tenant_integrity',
        'audit_event_alignment',
    )

    def __init__(
        self,
        *,
        tenant_id: str = DEFAULT_TENANT_ID,
        employee_directory_rows: Iterable[Mapping[str, Any]] | None = None,
        organization_structure_rows: Iterable[Mapping[str, Any]] | None = None,
        employee_reporting_rows: Iterable[Mapping[str, Any]] | None = None,
        leave_service: Any | None = None,
        payroll_service: Any | None = None,
        hiring_service: Any | None = None,
        workflow_service: Any | None = None,
        search_service: SearchIndexingService | None = None,
        reporting_service: ReportingAnalyticsService | None = None,
        audit_service: AuditService | None = None,
        background_jobs: BackgroundJobService | None = None,
    ) -> None:
        self.tenant_id = normalize_tenant_id(tenant_id)
        self.employee_directory_rows = [dict(row) for row in (employee_directory_rows or []) if normalize_tenant_id(row.get('tenant_id')) == self.tenant_id]
        self.organization_structure_rows = [dict(row) for row in (organization_structure_rows or []) if normalize_tenant_id(row.get('tenant_id')) == self.tenant_id]
        self.employee_reporting_rows = [dict(row) for row in (employee_reporting_rows or []) if normalize_tenant_id(row.get('tenant_id')) == self.tenant_id]
        self.leave_service = leave_service
        self.payroll_service = payroll_service
        self.hiring_service = hiring_service
        self.workflow_service = workflow_service or getattr(leave_service, 'workflow_service', None) or getattr(payroll_service, 'workflow_service', None) or getattr(hiring_service, 'workflow_service', None)
        self.search_service = search_service
        self.reporting_service = reporting_service
        self.audit_service = audit_service or AuditService()
        self.background_jobs = background_jobs

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def validate(self, *, auto_fix: bool = False) -> IntegrityReport:
        issues = self._collect_issues()
        repairs: list[dict[str, Any]] = []
        recheck: dict[str, Any] = {}
        if auto_fix:
            repairs = self.repair_minor_issues(issues)
            issues = self._collect_issues()
            recheck = {
                'entity_integrity': not any(issue.dimension == 'entity_integrity' for issue in issues),
                'projection_alignment': not any(issue.dimension == 'projection_integrity' for issue in issues),
                'cross_service_consistency': not any(issue.dimension == 'cross_service_consistency' for issue in issues),
            }
        scores = self._score_dimensions(issues)
        summary = {
            'issue_count': len(issues),
            'repair_count': len(repairs),
            'fail_conditions': [issue.code for issue in issues if issue.severity == 'error'],
            'no_hidden_integrity_issues_remain': len(issues) == 0,
        }
        return IntegrityReport(
            checked_at=self._now(),
            tenant_id=self.tenant_id,
            scores=scores,
            summary=summary,
            issues=issues,
            applied_repairs=repairs,
            recheck=recheck,
        )

    def register_background_jobs(self, background_jobs: BackgroundJobService) -> None:
        def handler(context: Any) -> dict[str, Any]:
            report = self.validate(auto_fix=bool(context.job.payload.get('auto_fix', True)))
            return report.to_dict()

        background_jobs.register_handler('integrity.repair', handler, max_attempts=1)

    def repair_minor_issues(self, issues: Iterable[IntegrityIssue]) -> list[dict[str, Any]]:
        applied: list[dict[str, Any]] = []
        issue_codes = {issue.code for issue in issues if issue.repairable}
        if not issue_codes:
            return applied

        if self.search_service is not None and any(code in issue_codes for code in {'search_projection_drift', 'search_projection_tenant_mismatch'}):
            result = self.search_service.rebuild_index(tenant_id=self.tenant_id)
            applied.append({'action': 'repair_minor_projection_drift', 'target': 'search-service', 'result': result})

        if self.reporting_service is not None and any(code in issue_codes for code in {'analytics_projection_drift', 'analytics_projection_tenant_mismatch'}):
            normalized = self._normalize_reporting_tenant_fields()
            result = self.reporting_service.rebuild_projections()
            applied.append({'action': 'rebuild_inconsistent_indexes_or_projections', 'target': 'reporting-analytics', 'normalized_records': normalized, 'result': result})

        if self.leave_service is not None and 'leave_balance_mismatch' in issue_codes:
            employees = sorted({issue.context['employee_id'] for issue in issues if issue.code == 'leave_balance_mismatch'})
            results = []
            if self.background_jobs is not None:
                for employee_id in employees:
                    job = self.background_jobs.enqueue_job(
                        tenant_id=self.tenant_id,
                        job_type='leave.balance.recompute',
                        payload={'employee_id': employee_id},
                        actor_type='service',
                        idempotency_key=f'integrity:leave.balance.recompute:{self.tenant_id}:{employee_id}',
                    )
                    completed = self.background_jobs.execute_job(job.job_id, tenant_id=self.tenant_id)
                    results.append({'employee_id': employee_id, 'job_id': job.job_id, 'status': completed.status.value})
            else:
                for employee_id in employees:
                    recomputed = self.leave_service.recompute_employee_balance(employee_id, tenant_id=self.tenant_id)
                    results.append({'employee_id': employee_id, 'recomputed': recomputed['leave_balances']})
            applied.append({'action': 'patch_orphan_reference_issues_where_safe', 'target': 'leave-service', 'result': results})

        if self.payroll_service is not None and any(code in issue_codes for code in {'payroll_batch_index_mismatch', 'payroll_batch_missing_record_reference'}):
            result = self._repair_payroll_batches()
            applied.append({'action': 'patch_orphan_reference_issues_where_safe', 'target': 'payroll-service', 'result': result})

        if any(code in issue_codes for code in {'search_projection_tenant_mismatch', 'analytics_projection_tenant_mismatch'}):
            applied.append({'action': 'normalize_tenant_ownership_fields', 'target': 'projection-stores', 'tenant_id': self.tenant_id})
        return applied

    def _score_dimensions(self, issues: list[IntegrityIssue]) -> dict[str, int]:
        scores = {dimension: 10 for dimension in self.DIMENSIONS}
        penalties = {
            'warning': 1,
            'error': 3,
        }
        for issue in issues:
            scores[issue.dimension] = max(0, scores[issue.dimension] - penalties.get(issue.severity, 1))
        return scores

    def _collect_issues(self) -> list[IntegrityIssue]:
        issues: list[IntegrityIssue] = []
        issues.extend(self._validate_employee_entity_integrity())
        issues.extend(self._validate_leave_integrity())
        issues.extend(self._validate_payroll_integrity())
        issues.extend(self._validate_hiring_integrity())
        issues.extend(self._validate_projection_integrity())
        issues.extend(self._validate_audit_event_alignment())
        return issues

    def _employee_directory_index(self) -> dict[str, dict[str, Any]]:
        return {str(row['employee_id']): row for row in self.employee_directory_rows}

    def _workflow_instance(self, workflow_id: str | None) -> Mapping[str, Any] | None:
        if not workflow_id or self.workflow_service is None:
            return None
        try:
            return self.workflow_service.get_instance(workflow_id, tenant_id=self.tenant_id)
        except Exception:  # noqa: BLE001
            return None

    def _audit_records(self) -> list[dict[str, Any]]:
        rows, _ = self.audit_service.list_records(tenant_id=self.tenant_id, limit=100)
        return rows

    def _validate_employee_entity_integrity(self) -> list[IntegrityIssue]:
        issues: list[IntegrityIssue] = []
        seen_numbers: dict[str, str] = {}
        seen_emails: dict[str, str] = {}
        employee_ids = {str(row.get('employee_id') or '') for row in self.employee_directory_rows}
        for row in self.employee_directory_rows:
            employee_id = str(row.get('employee_id') or '')
            employee_number = str(row.get('employee_number') or '')
            email = str(row.get('email') or '').lower()
            if employee_number in seen_numbers and seen_numbers[employee_number] != employee_id:
                issues.append(IntegrityIssue('entity_integrity', 'employee_duplicate_number', 'error', 'Duplicate logical employee number detected.', {'employee_number': employee_number, 'employee_ids': [seen_numbers[employee_number], employee_id]}))
            else:
                seen_numbers[employee_number] = employee_id
            if email in seen_emails and seen_emails[email] != employee_id:
                issues.append(IntegrityIssue('entity_integrity', 'employee_duplicate_email', 'error', 'Duplicate logical employee email detected.', {'email': email, 'employee_ids': [seen_emails[email], employee_id]}))
            else:
                seen_emails[email] = employee_id
            if row.get('manager_employee_id') and row['manager_employee_id'] not in employee_ids:
                issues.append(IntegrityIssue('cross_service_consistency', 'employee_manager_missing', 'error', 'Employee references a missing primary manager.', {'employee_id': employee_id, 'manager_employee_id': row['manager_employee_id']}))
            allocations = row.get('cost_allocations') or []
            if allocations:
                total = round(sum(float(item.get('allocation_percentage', item.get('percentage', 0)) or 0) for item in allocations), 2)
                if abs(total - 100.0) > 0.01:
                    issues.append(IntegrityIssue('entity_integrity', 'employee_cost_allocations_invalid', 'error', 'Employee cost allocations must total 100 percent.', {'employee_id': employee_id, 'total_allocation_percentage': total}))
        for row in self.organization_structure_rows:
            if str(row.get('employee_id') or '') not in employee_ids:
                issues.append(IntegrityIssue('cross_service_consistency', 'organization_orphan_employee', 'error', 'Organization structure row references an employee not present in employee_directory_view.', {'employee_id': row.get('employee_id'), 'department_id': row.get('department_id')}))
        return issues

    def _validate_leave_integrity(self) -> list[IntegrityIssue]:
        if self.leave_service is None:
            return []
        issues: list[IntegrityIssue] = []
        employee_rows = self._employee_directory_index()
        for employee_id, employee in getattr(self.leave_service, 'employees', {}).items():
            if normalize_tenant_id(getattr(employee, 'tenant_id', None)) != self.tenant_id:
                continue
            directory_row = employee_rows.get(employee_id)
            if directory_row is not None and directory_row.get('employee_status') != employee.status.value:
                issues.append(IntegrityIssue('cross_service_consistency', 'employee_status_cross_service_mismatch', 'error', 'Leave-service employee state diverges from employee directory state.', {'employee_id': employee_id, 'leave_service_status': employee.status.value, 'employee_directory_status': directory_row.get('employee_status')}))
            expected_balances: dict[str, dict[str, Any]] = {}
            for balance in self.leave_service.leave_balances.values():
                if balance.employee_id != employee_id:
                    continue
                expected_balances[balance.leave_type.value] = {
                    'reserved_days': round(sum(leave.total_days for leave in self.leave_service.requests.values() if leave.tenant_id == self.tenant_id and leave.employee_id == employee_id and leave.leave_type == balance.leave_type and leave.status.value == 'Submitted'), 2),
                    'approved_days': round(sum(leave.total_days for leave in self.leave_service.requests.values() if leave.tenant_id == self.tenant_id and leave.employee_id == employee_id and leave.leave_type == balance.leave_type and leave.status.value == 'Approved'), 2),
                }
            for leave_type in getattr(self.leave_service, 'LeaveType', []):
                _ = leave_type
            for _, balance in getattr(self.leave_service, 'leave_balances', {}).items():
                if balance.employee_id != employee_id:
                    continue
                expected = expected_balances.get(balance.leave_type.value)
                if expected is None:
                    continue
                if round(balance.reserved_days, 2) != round(float(expected['reserved_days']), 2) or round(balance.approved_days, 2) != round(float(expected['approved_days']), 2):
                    issues.append(IntegrityIssue('entity_integrity', 'leave_balance_mismatch', 'error', 'Leave balance totals do not match the authoritative request ledger.', {'employee_id': employee_id, 'leave_type': balance.leave_type.value, 'stored_reserved_days': balance.reserved_days, 'stored_approved_days': balance.approved_days, 'expected_reserved_days': expected['reserved_days'], 'expected_approved_days': expected['approved_days']}, repairable=True))
            for leave in self.leave_service.requests.values():
                if leave.tenant_id != self.tenant_id or leave.employee_id != employee_id:
                    continue
                workflow = self.leave_service.workflow_service.get_instance(leave.workflow_id, tenant_id=self.tenant_id) if leave.workflow_id else None
                if leave.status.value == 'Approved' and (workflow is None or workflow.get('metadata', {}).get('terminal_result') != 'approved'):
                    issues.append(IntegrityIssue('cross_service_consistency', 'leave_workflow_state_mismatch', 'error', 'Approved leave request is missing an approved workflow trace.', {'leave_request_id': leave.leave_request_id, 'workflow_id': leave.workflow_id, 'status': leave.status.value}))
                if leave.status.value == 'Submitted' and workflow is None:
                    issues.append(IntegrityIssue('cross_service_consistency', 'leave_workflow_missing', 'error', 'Submitted leave request is missing a workflow trace.', {'leave_request_id': leave.leave_request_id}))
        return issues

    def _validate_payroll_integrity(self) -> list[IntegrityIssue]:
        if self.payroll_service is None:
            return []
        issues: list[IntegrityIssue] = []
        employee_rows = self._employee_directory_index()
        seen_periods: set[tuple[str, str, str]] = set()
        for record in self.payroll_service.records.values():
            employee_id = record.employee_id
            key = (employee_id, record.pay_period_start.isoformat(), record.pay_period_end.isoformat())
            if key in seen_periods:
                issues.append(IntegrityIssue('entity_integrity', 'payroll_duplicate_employee_period', 'error', 'Duplicate payroll record exists for the same employee and pay period.', {'employee_id': employee_id, 'pay_period_start': key[1], 'pay_period_end': key[2]}))
            seen_periods.add(key)
            if employee_id not in self.payroll_service.employee_profiles:
                issues.append(IntegrityIssue('cross_service_consistency', 'payroll_orphan_employee_profile', 'error', 'Payroll record references a missing payroll employee profile.', {'employee_id': employee_id, 'payroll_record_id': record.payroll_record_id}))
            directory_row = employee_rows.get(employee_id)
            if directory_row and directory_row.get('employee_status') == 'Terminated' and record.status.value != 'Cancelled':
                issues.append(IntegrityIssue('cross_service_consistency', 'payroll_employee_status_mismatch', 'warning', 'Payroll record remains active for a terminated employee.', {'employee_id': employee_id, 'payroll_record_id': record.payroll_record_id, 'employee_status': directory_row.get('employee_status'), 'payroll_status': record.status.value}))
            gross = (record.base_salary + record.allowances + record.overtime_pay).quantize(Decimal('0.01'))
            net = (gross - record.deductions).quantize(Decimal('0.01'))
            if gross != record.gross_pay or net != record.net_pay:
                issues.append(IntegrityIssue('entity_integrity', 'payroll_total_mismatch', 'error', 'Payroll totals do not match stored component calculations.', {'payroll_record_id': record.payroll_record_id, 'gross_pay': str(record.gross_pay), 'expected_gross_pay': str(gross), 'net_pay': str(record.net_pay), 'expected_net_pay': str(net)}))
            if record.payroll_cycle_id:
                cycle = self.payroll_service.payroll_cycles.get(record.payroll_cycle_id)
                if cycle is None:
                    issues.append(IntegrityIssue('cross_service_consistency', 'payroll_cycle_missing', 'error', 'Payroll record references a missing payroll cycle.', {'payroll_record_id': record.payroll_record_id, 'payroll_cycle_id': record.payroll_cycle_id}))
                elif cycle.pay_period_start != record.pay_period_start or cycle.pay_period_end != record.pay_period_end:
                    issues.append(IntegrityIssue('entity_integrity', 'payroll_cycle_period_mismatch', 'error', 'Payroll record period conflicts with the owning payroll cycle.', {'payroll_record_id': record.payroll_record_id, 'payroll_cycle_id': record.payroll_cycle_id}))
        for batch in self.payroll_service.batches.values():
            validation = self.payroll_service._validate_batch_consistency(batch)
            for issue in validation['issues']:
                code = 'payroll_batch_missing_record_reference' if 'missing record reference' in issue else 'payroll_batch_index_mismatch'
                issues.append(IntegrityIssue('cross_service_consistency', code, 'error', 'Payroll batch/index integrity drift detected.', {'batch_id': batch.batch_id, 'detail': issue}, repairable=True))
        return issues

    def _validate_hiring_integrity(self) -> list[IntegrityIssue]:
        if self.hiring_service is None:
            return []
        issues: list[IntegrityIssue] = []
        employee_rows = self._employee_directory_index()
        seen_candidate_keys: set[tuple[str, str]] = set()
        for candidate in self.hiring_service.candidates.values():
            if normalize_tenant_id(candidate.tenant_id) != self.tenant_id:
                continue
            dedupe_key = (candidate.job_posting_id, candidate.email.lower())
            if dedupe_key in seen_candidate_keys:
                issues.append(IntegrityIssue('entity_integrity', 'candidate_duplicate_email_per_posting', 'error', 'Candidate email must be unique per job posting.', {'job_posting_id': candidate.job_posting_id, 'email': candidate.email}))
            seen_candidate_keys.add(dedupe_key)
            if candidate.job_posting_id not in self.hiring_service.job_postings:
                issues.append(IntegrityIssue('cross_service_consistency', 'candidate_orphan_job_posting', 'error', 'Candidate references a missing job posting.', {'candidate_id': candidate.candidate_id, 'job_posting_id': candidate.job_posting_id}))
            if candidate.status == 'Hired':
                employee_id = self.hiring_service.hired_candidate_index.get(candidate.candidate_id)
                profile = self.hiring_service.employee_profiles.get(employee_id) if employee_id else None
                workflow = self.hiring_service.workflow_service.get_instance(candidate.hire_workflow_id, tenant_id=self.tenant_id) if candidate.hire_workflow_id else None
                if employee_id is None or profile is None:
                    issues.append(IntegrityIssue('cross_service_consistency', 'candidate_handoff_missing_employee_profile', 'error', 'Hired candidate is missing the employee handoff profile.', {'candidate_id': candidate.candidate_id, 'employee_id': employee_id}))
                else:
                    if profile.candidate_id != candidate.candidate_id or profile.job_posting_id != candidate.job_posting_id:
                        issues.append(IntegrityIssue('cross_service_consistency', 'candidate_handoff_profile_mismatch', 'error', 'Employee handoff profile does not match the hired candidate linkage.', {'candidate_id': candidate.candidate_id, 'employee_id': profile.employee_id}))
                    employee_row = employee_rows.get(profile.employee_id)
                    if employee_row and employee_row.get('email', '').lower() != profile.email.lower():
                        issues.append(IntegrityIssue('cross_service_consistency', 'candidate_to_employee_email_mismatch', 'error', 'Candidate handoff email diverges from employee directory email.', {'candidate_id': candidate.candidate_id, 'employee_id': profile.employee_id, 'hiring_email': profile.email, 'employee_directory_email': employee_row.get('email')}))
                if workflow is None or workflow.get('metadata', {}).get('terminal_result') != 'approved':
                    issues.append(IntegrityIssue('cross_service_consistency', 'candidate_hire_workflow_state_mismatch', 'error', 'Hired candidate is missing an approved hire workflow trace.', {'candidate_id': candidate.candidate_id, 'workflow_id': candidate.hire_workflow_id}))
        for interview in self.hiring_service.interviews.values():
            if normalize_tenant_id(interview.tenant_id) != self.tenant_id:
                continue
            if interview.candidate_id not in self.hiring_service.candidates:
                issues.append(IntegrityIssue('cross_service_consistency', 'interview_orphan_candidate', 'error', 'Interview references a missing candidate.', {'interview_id': interview.interview_id, 'candidate_id': interview.candidate_id}))
        return issues

    def _validate_projection_integrity(self) -> list[IntegrityIssue]:
        issues: list[IntegrityIssue] = []
        if self.search_service is not None:
            snapshot = {doc_id: doc.to_dict() for doc_id, doc in self.search_service.index_documents.items() if doc.tenant_id == self.tenant_id}
            rebuilt = SearchIndexingService()
            rebuilt.ingest_read_model('employee_directory_view', self.search_service._read_model_rows(self.tenant_id, 'employee_directory_view'), tenant_id=self.tenant_id, replace=True)
            rebuilt.ingest_read_model('organization_structure_view', self.search_service._read_model_rows(self.tenant_id, 'organization_structure_view'), tenant_id=self.tenant_id, replace=True)
            rebuilt.ingest_read_model('candidate_pipeline_view', self.search_service._read_model_rows(self.tenant_id, 'candidate_pipeline_view'), tenant_id=self.tenant_id, replace=True)
            rebuilt.ingest_read_model('document_library_view', self.search_service._read_model_rows(self.tenant_id, 'document_library_view'), tenant_id=self.tenant_id, replace=True)
            rebuilt.ingest_read_model('payroll_summary_view', self.search_service._read_model_rows(self.tenant_id, 'payroll_summary_view'), tenant_id=self.tenant_id, replace=True)
            rebuilt.rebuild_index(tenant_id=self.tenant_id)
            expected = {doc_id: doc.to_dict() for doc_id, doc in rebuilt.index_documents.items() if doc.tenant_id == self.tenant_id}
            if self._normalize_search_snapshot(snapshot) != self._normalize_search_snapshot(expected):
                issues.append(IntegrityIssue('projection_integrity', 'search_projection_drift', 'error', 'global_search_view documents drift from the canonical read-model rebuild.', {'stored_document_count': len(snapshot), 'expected_document_count': len(expected)}, repairable=True))
            if any(normalize_tenant_id(row.get('tenant_id')) != self.tenant_id for row in snapshot.values()):
                issues.append(IntegrityIssue('tenant_integrity', 'search_projection_tenant_mismatch', 'error', 'Search projection contains inconsistent tenant ownership.', {'tenant_id': self.tenant_id}, repairable=True))
        if self.reporting_service is not None:
            stored = {aggregate_id: aggregate.to_dict() for aggregate_id, aggregate in self.reporting_service.aggregate_snapshots.items() if aggregate.tenant_id == self.tenant_id}
            shadow = ReportingAnalyticsService(tenant_id=self.tenant_id)
            for model_name, payload in self.reporting_service.read_models.items():
                shadow.ingest_read_model(model_name, payload.get('rows', []))
            for event_id, payload in self.reporting_service.processed_events.items():
                shadow.processed_events[event_id] = dict(payload)
            shadow.rebuild_projections()
            expected = {aggregate_id: aggregate.to_dict() for aggregate_id, aggregate in shadow.aggregate_snapshots.items() if aggregate.tenant_id == self.tenant_id}
            if self._normalize_aggregate_snapshot(stored) != self._normalize_aggregate_snapshot(expected):
                issues.append(IntegrityIssue('projection_integrity', 'analytics_projection_drift', 'error', 'Analytics aggregate snapshots drift from the authoritative read-model/event rebuild.', {'stored_aggregate_count': len(stored), 'expected_aggregate_count': len(expected)}, repairable=True))
            if any(normalize_tenant_id(row.get('tenant_id')) != self.tenant_id for row in stored.values()):
                issues.append(IntegrityIssue('tenant_integrity', 'analytics_projection_tenant_mismatch', 'error', 'Analytics projection contains inconsistent tenant ownership.', {'tenant_id': self.tenant_id}, repairable=True))
        return issues

    def _validate_audit_event_alignment(self) -> list[IntegrityIssue]:
        issues: list[IntegrityIssue] = []
        records = self._audit_records()
        record_index = {(row['action'], row['entity'], row['entity_id']) for row in records}
        if self.leave_service is not None:
            for leave in self.leave_service.requests.values():
                if leave.tenant_id != self.tenant_id or leave.status.value not in {'Submitted', 'Approved', 'Rejected', 'Cancelled'}:
                    continue
                if leave.status.value == 'Approved':
                    expected_action = ('leave_request_approve', 'LeaveRequest', leave.leave_request_id)
                    expected_event = 'LeaveRequestApproved'
                elif leave.status.value == 'Submitted':
                    expected_action = ('leave_request_submitted', 'LeaveRequest', leave.leave_request_id)
                    expected_event = 'LeaveRequestSubmitted'
                elif leave.status.value == 'Rejected':
                    expected_action = ('leave_request_reject', 'LeaveRequest', leave.leave_request_id)
                    expected_event = 'LeaveRequestRejected'
                else:
                    expected_action = ('leave_request_cancel', 'LeaveRequest', leave.leave_request_id)
                    expected_event = 'LeaveRequestCancelled'
                if expected_action not in record_index:
                    issues.append(IntegrityIssue('audit_event_alignment', 'leave_audit_event_gap', 'error', 'Major leave mutation is missing a matching audit record.', {'leave_request_id': leave.leave_request_id, 'expected_action': expected_action[0]}))
                if not any((record.payload.get('legacy_event_name') == expected_event or record.payload.get('event_name') == expected_event) and record.payload.get('data', {}).get('leave_request_id') == leave.leave_request_id for record in self.leave_service.outbox.records.values()):
                    issues.append(IntegrityIssue('audit_event_alignment', 'leave_event_trace_gap', 'error', 'Major leave mutation is missing a matching event trace.', {'leave_request_id': leave.leave_request_id, 'expected_event': expected_event}))
        if self.hiring_service is not None:
            for candidate in self.hiring_service.candidates.values():
                if candidate.tenant_id != self.tenant_id or candidate.status != 'Hired':
                    continue
                action = ('candidate_hired', 'Candidate', candidate.candidate_id)
                if action not in record_index:
                    issues.append(IntegrityIssue('audit_event_alignment', 'candidate_hire_audit_gap', 'error', 'Candidate hire is missing a matching audit record.', {'candidate_id': candidate.candidate_id}))
                if not any((event.get('legacy_event_name') == 'CandidateHired' or event.get('event_name') == 'CandidateHired') and event.get('data', {}).get('candidate_id') == candidate.candidate_id for event in self.hiring_service.events):
                    issues.append(IntegrityIssue('audit_event_alignment', 'candidate_hire_event_gap', 'error', 'Candidate hire is missing a matching event trace.', {'candidate_id': candidate.candidate_id}))
        if self.payroll_service is not None:
            for record in self.payroll_service.records.values():
                if record.status.value != 'Paid':
                    continue
                if not any(audit.get('action') == 'payroll_record_paid' and audit.get('entity_id') == record.payroll_record_id for audit in records):
                    issues.append(IntegrityIssue('audit_event_alignment', 'payroll_paid_audit_gap', 'error', 'Paid payroll record is missing a matching audit record.', {'payroll_record_id': record.payroll_record_id}))
                if not any((event.get('legacy_event_name') == 'PayrollPaid' or event.get('event_name') == 'PayrollPaid') and event.get('data', {}).get('payroll_record_id') == record.payroll_record_id for event in self.payroll_service.events):
                    issues.append(IntegrityIssue('audit_event_alignment', 'payroll_paid_event_gap', 'error', 'Paid payroll record is missing a matching event trace.', {'payroll_record_id': record.payroll_record_id}))
        return issues


    @staticmethod
    def _normalize_search_snapshot(rows: Mapping[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        normalized: dict[str, dict[str, Any]] = {}
        for key, row in rows.items():
            payload = dict(row)
            payload.pop('updated_at', None)
            normalized[key] = payload
        return normalized

    @staticmethod
    def _normalize_aggregate_snapshot(rows: Mapping[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        normalized: dict[str, dict[str, Any]] = {}
        for key, row in rows.items():
            payload = dict(row)
            payload.pop('updated_at', None)
            normalized[key] = payload
        return normalized

    def _normalize_reporting_tenant_fields(self) -> int:
        if self.reporting_service is None:
            return 0
        normalized = 0
        for aggregate in self.reporting_service.aggregate_snapshots.values():
            if normalize_tenant_id(aggregate.tenant_id) != self.tenant_id:
                aggregate.tenant_id = self.tenant_id
                normalized += 1
        for payload in self.reporting_service.read_models.values():
            rows = payload.get('rows', [])
            for row in rows:
                if 'tenant_id' in row and normalize_tenant_id(row.get('tenant_id')) != self.tenant_id:
                    row['tenant_id'] = self.tenant_id
                    normalized += 1
        return normalized

    def _repair_payroll_batches(self) -> dict[str, Any]:
        repaired_batches = []
        for batch in self.payroll_service.batches.values():
            cleaned_ids: list[str] = []
            seen_ids: set[str] = set()
            for record_id in batch.record_ids:
                if record_id in seen_ids or record_id not in self.payroll_service.records:
                    continue
                seen_ids.add(record_id)
                cleaned_ids.append(record_id)
                self.payroll_service.record_batches[record_id] = batch.batch_id
            batch.record_ids = cleaned_ids
            self.payroll_service._recompute_batch(batch)
            repaired_batches.append({'batch_id': batch.batch_id, 'record_count': len(batch.record_ids), 'status': batch.status.value})
        return {'repaired_batches': repaired_batches}


def build_payroll_summary_rows(payroll_service: Any, *, tenant_id: str = DEFAULT_TENANT_ID, employee_directory_rows: Iterable[Mapping[str, Any]] | None = None) -> list[dict[str, Any]]:
    employee_index = {str(row.get('employee_id')): dict(row) for row in (employee_directory_rows or [])}
    rows: list[dict[str, Any]] = []
    for record in payroll_service.records.values():
        profile = payroll_service.employee_profiles.get(record.employee_id)
        employee_row = employee_index.get(record.employee_id, {})
        rows.append(
            {
                'tenant_id': normalize_tenant_id(employee_row.get('tenant_id') or tenant_id),
                'payroll_record_id': record.payroll_record_id,
                'employee_id': record.employee_id,
                'employee_number': employee_row.get('employee_number') or f'EMP-{record.employee_id}',
                'employee_name': employee_row.get('full_name') or record.employee_id,
                'department_id': employee_row.get('department_id') or getattr(profile, 'department_id', None),
                'department_name': employee_row.get('department_name'),
                'pay_period_start': record.pay_period_start.isoformat(),
                'pay_period_end': record.pay_period_end.isoformat(),
                'base_salary': str(record.base_salary),
                'allowances': str(record.allowances),
                'deductions': str(record.deductions),
                'overtime_pay': str(record.overtime_pay),
                'gross_pay': str(record.gross_pay),
                'net_pay': str(record.net_pay),
                'currency': record.currency,
                'payment_date': record.payment_date.isoformat() if record.payment_date else None,
                'status': record.status.value,
                'updated_at': record.updated_at.isoformat(),
            }
        )
    rows.sort(key=lambda row: (row['pay_period_start'], row['employee_id']))
    return rows


__all__ = ['DataIntegrityValidator', 'IntegrityIssue', 'IntegrityReport', 'build_payroll_summary_rows']
