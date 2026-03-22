from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any, Iterable
from uuid import uuid4

from event_contract import EventContractError, EventRegistry, ensure_event_contract
from persistent_store import PersistentKVStore
from tenant_support import normalize_tenant_id


class ReportingAnalyticsError(ValueError):
    """Raised when reporting and analytics requests are invalid."""


@dataclass(slots=True)
class AggregateSnapshot:
    aggregate_id: str
    tenant_id: str
    aggregate_type: str
    dimension_key: str
    dimension_value: str
    window_start: str | None
    window_end: str | None
    metrics: dict[str, Any]
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ReportDefinition:
    report_id: str
    tenant_id: str
    name: str
    report_type: str
    filters: dict[str, Any]
    delivery: dict[str, Any]
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ReportRun:
    report_run_id: str
    tenant_id: str
    report_id: str
    report_type: str
    filters: dict[str, Any]
    summary: dict[str, Any]
    rows: list[dict[str, Any]]
    generated_at: str
    trace_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ExportRecord:
    export_id: str
    tenant_id: str
    report_id: str
    report_run_id: str
    export_format: str
    file_name: str
    row_count: int
    content_type: str
    content: str
    created_at: str
    trace_id: str
    schedule_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ScheduledReport:
    schedule_id: str
    tenant_id: str
    report_id: str
    cadence: str
    export_format: str
    next_run_at: str
    delivery: dict[str, Any]
    active: bool
    last_enqueued_at: str | None
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReportingAnalyticsService:
    REPORT_TYPES = {
        'hiring.pipeline.summary',
        'hiring.funnel.summary',
        'hiring.source.effectiveness',
        'hiring.time_to_hire',
        'organization.manager.span',
        'workforce.attrition.summary',
        'workforce.attendance.trend',
        'workforce.dashboard.summary',
    }
    EXPORT_FORMATS = {'json', 'csv'}
    CADENCES = {'daily', 'weekly', 'monthly'}

    def __init__(self, db_path: str | None = None, *, tenant_id: str = 'tenant-default') -> None:
        self.tenant_id = normalize_tenant_id(tenant_id)
        self.aggregate_snapshots = PersistentKVStore[str, AggregateSnapshot](service='reporting-analytics', namespace='aggregate_snapshots', db_path=db_path)
        self.report_definitions = PersistentKVStore[str, ReportDefinition](service='reporting-analytics', namespace='report_definitions', db_path=db_path)
        self.report_runs = PersistentKVStore[str, ReportRun](service='reporting-analytics', namespace='report_runs', db_path=db_path)
        self.exports = PersistentKVStore[str, ExportRecord](service='reporting-analytics', namespace='exports', db_path=db_path)
        self.schedules = PersistentKVStore[str, ScheduledReport](service='reporting-analytics', namespace='scheduled_reports', db_path=db_path)
        self.processed_events = PersistentKVStore[str, dict[str, Any]](service='reporting-analytics', namespace='processed_events', db_path=db_path)
        self.read_models = PersistentKVStore[str, dict[str, Any]](service='reporting-analytics', namespace='read_models', db_path=db_path)
        self.projection_state = PersistentKVStore[str, dict[str, Any]](service='reporting-analytics', namespace='projection_state', db_path=db_path)
        self.event_registry = EventRegistry()
        self._lock = RLock()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _coerce_datetime(value: str | None, field_name: str) -> datetime:
        if not value:
            raise ReportingAnalyticsError(f'{field_name} is required')
        try:
            return datetime.fromisoformat(str(value).replace('Z', '+00:00')).astimezone(timezone.utc)
        except ValueError as exc:  # noqa: PERF203
            raise ReportingAnalyticsError(f'{field_name} must be a valid ISO-8601 datetime') from exc

    def _next_run_at(self, *, now: datetime, cadence: str) -> str:
        if cadence == 'daily':
            return (now + timedelta(days=1)).isoformat()
        if cadence == 'weekly':
            return (now + timedelta(days=7)).isoformat()
        if cadence == 'monthly':
            return (now + timedelta(days=30)).isoformat()
        raise ReportingAnalyticsError('cadence must be one of: daily, weekly, monthly')

    def _read_rows(self, model_name: str) -> list[dict[str, Any]]:
        rows = self.read_models.get(model_name, {}).get('rows', [])
        return [dict(row) for row in rows]

    def ingest_read_model(self, model_name: str, rows: Iterable[dict[str, Any]]) -> None:
        payload = {
            'model_name': model_name,
            'rows': [
                {**dict(row), 'tenant_id': normalize_tenant_id(dict(row).get('tenant_id') or self.tenant_id)}
                for row in rows
                if normalize_tenant_id(dict(row).get('tenant_id') or self.tenant_id) == self.tenant_id
            ],
            'updated_at': self._now(),
        }
        self.read_models[model_name] = payload
        self.rebuild_projections()

    def sync_hiring_service(self, hiring_service: Any) -> dict[str, Any]:
        self.ingest_read_model('job_posting_directory_view', hiring_service.list_job_postings())
        self.ingest_read_model('candidate_pipeline_view', hiring_service.list_candidate_pipeline_view())
        if hasattr(hiring_service, 'list_employee_profiles'):
            self.ingest_read_model('employee_profile_view', hiring_service.list_employee_profiles())
        new_events = 0
        for event in getattr(hiring_service, 'events', []):
            event_id = str(event.get('event_id') or '')
            if event_id and self.processed_events.get(event_id) is not None:
                continue
            self.ingest_event(event)
            new_events += 1
        return {
            'job_posting_count': len(self._read_rows('job_posting_directory_view')),
            'candidate_count': len(self._read_rows('candidate_pipeline_view')),
            'processed_event_count': new_events,
        }

    def sync_workforce_read_models(
        self,
        *,
        employee_directory_rows: Iterable[dict[str, Any]] | None = None,
        attendance_rows: Iterable[dict[str, Any]] | None = None,
        employee_reporting_rows: Iterable[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if employee_directory_rows is not None:
            self.ingest_read_model('employee_directory_view', employee_directory_rows)
        if attendance_rows is not None:
            self.ingest_read_model('attendance_dashboard_view', attendance_rows)
        if employee_reporting_rows is not None:
            self.ingest_read_model('employee_reporting_view', employee_reporting_rows)
        return {
            'employee_count': len(self._read_rows('employee_directory_view')),
            'attendance_record_count': len(self._read_rows('attendance_dashboard_view')),
            'reporting_line_count': len(self._read_rows('employee_reporting_view')),
        }

    def ingest_event(self, event: dict[str, Any]) -> None:
        try:
            payload, _ = ensure_event_contract(event, source=str(event.get('source') or 'reporting-analytics'), registry=self.event_registry)
        except EventContractError as exc:
            if str(exc) == 'missing_tenant_context':
                raise ReportingAnalyticsError('tenant_id is required') from exc
            raise ReportingAnalyticsError(f'event contract validation failed: {exc}') from exc

        tenant_id = normalize_tenant_id(str(payload.get('tenant_id') or self.tenant_id))
        if tenant_id != self.tenant_id:
            raise ReportingAnalyticsError('cross_tenant_event_blocked')

        event_id = str(payload.get('event_id') or uuid4())
        if self.processed_events.get(event_id) is not None:
            return
        payload['ingested_at'] = self._now()
        self.processed_events[event_id] = payload
        self.projection_state['last_event'] = {
            'event_id': event_id,
            'event_type': payload.get('event_type') or payload.get('legacy_event_type') or payload.get('event_name'),
            'processed_at': self._now(),
        }
        self.rebuild_projections()

    def rebuild_projections(self) -> dict[str, Any]:
        with self._lock:
            candidate_rows = self._read_rows('candidate_pipeline_view')
            employee_profile_rows = self._read_rows('employee_profile_view')
            employee_reporting_rows = self._read_rows('employee_reporting_view')
            event_rows = [dict(event) for event in self.processed_events.values()]
            event_rows.sort(key=lambda row: (str(row.get('timestamp') or row.get('occurred_at') or ''), str(row.get('event_id') or '')))

            snapshots = self._build_hiring_pipeline_snapshots(candidate_rows)
            snapshots.extend(self._build_hiring_funnel_snapshots(candidate_rows))
            snapshots.extend(self._build_source_effectiveness_snapshots(candidate_rows))
            snapshots.extend(self._build_time_to_hire_snapshots(event_rows, candidate_rows, employee_profile_rows))
            snapshots.extend(self._build_manager_span_snapshots(employee_reporting_rows))
            snapshots.extend(self._build_attrition_snapshots(self._read_rows('employee_directory_view'), employee_profile_rows, event_rows))
            snapshots.extend(self._build_attendance_trend_snapshots(self._read_rows('attendance_dashboard_view')))
            snapshots.extend(self._build_workforce_dashboard_snapshots(candidate_rows, self._read_rows('employee_directory_view'), self._read_rows('attendance_dashboard_view'), event_rows))

            current_ids = {snapshot.aggregate_id for snapshot in snapshots}
            for aggregate_id in list(self.aggregate_snapshots.keys()):
                if aggregate_id not in current_ids:
                    del self.aggregate_snapshots[aggregate_id]
            for snapshot in snapshots:
                self.aggregate_snapshots[snapshot.aggregate_id] = snapshot
            return {'aggregate_count': len(snapshots), 'updated_at': self._now()}

    def _build_hiring_pipeline_snapshots(self, candidate_rows: list[dict[str, Any]]) -> list[AggregateSnapshot]:
        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        for row in candidate_rows:
            for dimension_key, dimension_value in (
                ('tenant', self.tenant_id),
                ('department_id', str(row.get('department_id') or 'unknown')),
                ('job_posting_id', str(row.get('job_posting_id') or 'unknown')),
            ):
                metrics = grouped.setdefault(
                    (dimension_key, dimension_value),
                    {
                        'candidate_count': 0,
                        'scheduled_interview_count': 0,
                        'completed_or_recommended_interview_count': 0,
                        'hired_count': 0,
                        'stage_counts': {},
                    },
                )
                metrics['candidate_count'] += 1
                stage = str(row.get('pipeline_stage') or 'Unknown')
                metrics['stage_counts'][stage] = metrics['stage_counts'].get(stage, 0) + 1
                if row.get('next_interview_at'):
                    metrics['scheduled_interview_count'] += 1
                if row.get('last_interview_recommendation') is not None:
                    metrics['completed_or_recommended_interview_count'] += 1
                if stage == 'Hired' or row.get('hired_employee_id'):
                    metrics['hired_count'] += 1
        updated_at = self._now()
        return [
            AggregateSnapshot(
                aggregate_id=f'hiring.pipeline.summary:{dimension_key}:{dimension_value}',
                tenant_id=self.tenant_id,
                aggregate_type='hiring.pipeline.summary',
                dimension_key=dimension_key,
                dimension_value=dimension_value,
                window_start=None,
                window_end=None,
                metrics=metrics,
                updated_at=updated_at,
            )
            for (dimension_key, dimension_value), metrics in grouped.items()
        ]

    def _build_hiring_funnel_snapshots(self, candidate_rows: list[dict[str, Any]]) -> list[AggregateSnapshot]:
        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        stage_aliases = {
            'Applied': 'application_count',
            'Screening': 'screening_count',
            'Interview': 'interview_count',
            'Interviewing': 'interview_count',
            'Offer': 'offer_count',
            'Offered': 'offer_count',
            'Hired': 'hired_count',
        }
        for row in candidate_rows:
            normalized_stage = str(row.get('pipeline_stage_normalized') or row.get('pipeline_stage') or 'Applied')
            for dimension_key, dimension_value in (
                ('tenant', self.tenant_id),
                ('department_id', str(row.get('department_id') or 'unknown')),
                ('job_posting_id', str(row.get('job_posting_id') or 'unknown')),
            ):
                metrics = grouped.setdefault(
                    (dimension_key, dimension_value),
                    {
                        'application_count': 0,
                        'screening_count': 0,
                        'interview_count': 0,
                        'offer_count': 0,
                        'hired_count': 0,
                    },
                )
                metrics['application_count'] += 1
                bucket = stage_aliases.get(normalized_stage)
                if bucket and bucket != 'application_count':
                    metrics[bucket] += 1
        updated_at = self._now()
        snapshots: list[AggregateSnapshot] = []
        for (dimension_key, dimension_value), metrics in grouped.items():
            applications = metrics['application_count'] or 1
            metrics['screening_conversion_rate'] = round(metrics['screening_count'] / applications, 4)
            metrics['interview_conversion_rate'] = round(metrics['interview_count'] / applications, 4)
            metrics['offer_conversion_rate'] = round(metrics['offer_count'] / applications, 4)
            metrics['hire_conversion_rate'] = round(metrics['hired_count'] / applications, 4)
            snapshots.append(
                AggregateSnapshot(
                    aggregate_id=f'hiring.funnel.summary:{dimension_key}:{dimension_value}',
                    tenant_id=self.tenant_id,
                    aggregate_type='hiring.funnel.summary',
                    dimension_key=dimension_key,
                    dimension_value=dimension_value,
                    window_start=None,
                    window_end=None,
                    metrics=metrics,
                    updated_at=updated_at,
                )
            )
        return snapshots

    def _build_source_effectiveness_snapshots(self, candidate_rows: list[dict[str, Any]]) -> list[AggregateSnapshot]:
        grouped: dict[str, dict[str, Any]] = {}
        for row in candidate_rows:
            source = str(row.get('source') or 'Unknown')
            metrics = grouped.setdefault(source, {'candidate_count': 0, 'interview_count': 0, 'hire_count': 0})
            metrics['candidate_count'] += 1
            metrics['interview_count'] += int(row.get('interview_count') or 0)
            if row.get('pipeline_stage') == 'Hired' or row.get('hired_employee_id'):
                metrics['hire_count'] += 1
        updated_at = self._now()
        snapshots: list[AggregateSnapshot] = []
        for source, metrics in grouped.items():
            candidate_count = metrics['candidate_count'] or 1
            metrics['hire_rate'] = round(metrics['hire_count'] / candidate_count, 4)
            metrics['interview_per_candidate'] = round(metrics['interview_count'] / candidate_count, 4)
            snapshots.append(
                AggregateSnapshot(
                    aggregate_id=f'hiring.source.effectiveness:source:{source}',
                    tenant_id=self.tenant_id,
                    aggregate_type='hiring.source.effectiveness',
                    dimension_key='source',
                    dimension_value=source,
                    window_start=None,
                    window_end=None,
                    metrics=metrics,
                    updated_at=updated_at,
                )
            )
        return snapshots

    def _build_time_to_hire_snapshots(self, event_rows: list[dict[str, Any]], candidate_rows: list[dict[str, Any]], employee_profile_rows: list[dict[str, Any]]) -> list[AggregateSnapshot]:
        application_dates = {
            str(row['candidate_id']): self._coerce_datetime(f"{row['application_date']}T00:00:00+00:00", 'application_date')
            for row in candidate_rows
            if row.get('candidate_id') and row.get('application_date')
        }
        candidate_departments = {
            str(row['candidate_id']): str(row.get('department_id') or 'all')
            for row in candidate_rows
            if row.get('candidate_id')
        }
        hire_dates = {
            str(row.get('candidate_id')): self._coerce_datetime(f"{row['hire_date']}T00:00:00+00:00", 'hire_date')
            for row in employee_profile_rows
            if row.get('candidate_id') and row.get('hire_date')
        }
        grouped: dict[str, list[float]] = {}
        for event in event_rows:
            event_type = str(event.get('event_type') or event.get('legacy_event_type') or event.get('event_name') or '')
            if event_type not in {'hiring.candidate.hired', 'CandidateHired'}:
                continue
            data = dict(event.get('data') or event.get('payload') or {})
            candidate_id = str(data.get('candidate_id') or '')
            if not candidate_id or candidate_id not in application_dates:
                continue
            hired_at = hire_dates.get(candidate_id)
            if hired_at is None:
                hired_at = self._coerce_datetime(str(event.get('timestamp') or event.get('occurred_at') or self._now()), 'occurred_at')
            days = max(0.0, (hired_at - application_dates[candidate_id]).total_seconds() / 86400)
            dimension_value = str(data.get('department_id') or candidate_departments.get(candidate_id) or 'all')
            grouped.setdefault(dimension_value, []).append(days)
            grouped.setdefault('all', []).append(days)
        updated_at = self._now()
        snapshots: list[AggregateSnapshot] = []
        for dimension_value, values in grouped.items():
            metrics = {
                'hire_count': len(values),
                'average_days_to_hire': round(sum(values) / len(values), 2),
                'min_days_to_hire': round(min(values), 2),
                'max_days_to_hire': round(max(values), 2),
            }
            snapshots.append(
                AggregateSnapshot(
                    aggregate_id=f'hiring.time_to_hire:department_id:{dimension_value}',
                    tenant_id=self.tenant_id,
                    aggregate_type='hiring.time_to_hire',
                    dimension_key='department_id',
                    dimension_value=dimension_value,
                    window_start=None,
                    window_end=None,
                    metrics=metrics,
                    updated_at=updated_at,
                )
            )
        return snapshots

    def _build_manager_span_snapshots(self, employee_reporting_rows: list[dict[str, Any]]) -> list[AggregateSnapshot]:
        grouped: dict[str, dict[str, Any]] = {}
        for row in employee_reporting_rows:
            manager_id = str(row.get('primary_manager_employee_id') or 'unassigned')
            metrics = grouped.setdefault(manager_id, {'direct_report_count': 0, 'matrix_report_count': 0, 'reporting_line_count': 0})
            if row.get('primary_manager_employee_id'):
                metrics['direct_report_count'] += 1
            metrics['matrix_report_count'] += len(row.get('matrix_managers') or [])
            metrics['reporting_line_count'] += len(row.get('reporting_lines') or [])
        updated_at = self._now()
        return [
            AggregateSnapshot(
                aggregate_id=f'organization.manager.span:manager_employee_id:{manager_id}',
                tenant_id=self.tenant_id,
                aggregate_type='organization.manager.span',
                dimension_key='manager_employee_id',
                dimension_value=manager_id,
                window_start=None,
                window_end=None,
                metrics=metrics,
                updated_at=updated_at,
            )
            for manager_id, metrics in grouped.items()
        ]

    def _build_attrition_snapshots(
        self,
        employee_directory_rows: list[dict[str, Any]],
        employee_profile_rows: list[dict[str, Any]],
        event_rows: list[dict[str, Any]],
    ) -> list[AggregateSnapshot]:
        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        department_lookup = {
            str(row.get('employee_id') or ''): str(row.get('department_id') or 'unknown')
            for row in employee_directory_rows
            if row.get('employee_id')
        }
        for row in employee_directory_rows:
            status = str(row.get('employee_status') or 'Unknown')
            department_id = str(row.get('department_id') or 'unknown')
            for dimension_key, dimension_value in (('tenant', self.tenant_id), ('department_id', department_id)):
                metrics = grouped.setdefault(
                    (dimension_key, dimension_value),
                    {
                        'current_headcount': 0,
                        'active_headcount': 0,
                        'inactive_headcount': 0,
                        'terminated_employee_count': 0,
                        'hire_count': 0,
                        'termination_event_count': 0,
                    },
                )
                if status != 'Terminated':
                    metrics['current_headcount'] += 1
                if status == 'Active':
                    metrics['active_headcount'] += 1
                elif status in {'OnLeave', 'Suspended'}:
                    metrics['inactive_headcount'] += 1
                elif status == 'Terminated':
                    metrics['terminated_employee_count'] += 1

        for row in employee_profile_rows:
            department_id = str(row.get('department_id') or 'unknown')
            for dimension_key, dimension_value in (('tenant', self.tenant_id), ('department_id', department_id)):
                metrics = grouped.setdefault(
                    (dimension_key, dimension_value),
                    {
                        'current_headcount': 0,
                        'active_headcount': 0,
                        'inactive_headcount': 0,
                        'terminated_employee_count': 0,
                        'hire_count': 0,
                        'termination_event_count': 0,
                    },
                )
                metrics['hire_count'] += 1

        for event in event_rows:
            event_type = str(event.get('event_type') or event.get('legacy_event_type') or event.get('event_name') or '')
            if event_type not in {'employee.status.changed', 'EmployeeStatusChanged'}:
                continue
            data = dict(event.get('data') or event.get('payload') or {})
            status = str(data.get('to_status') or data.get('status') or '')
            if status != 'Terminated':
                continue
            employee_id = str(data.get('employee_id') or '')
            department_id = str(data.get('department_id') or department_lookup.get(employee_id) or 'unknown')
            for dimension_key, dimension_value in (('tenant', self.tenant_id), ('department_id', department_id)):
                metrics = grouped.setdefault(
                    (dimension_key, dimension_value),
                    {
                        'current_headcount': 0,
                        'active_headcount': 0,
                        'inactive_headcount': 0,
                        'terminated_employee_count': 0,
                        'hire_count': 0,
                        'termination_event_count': 0,
                    },
                )
                metrics['termination_event_count'] += 1

        updated_at = self._now()
        snapshots: list[AggregateSnapshot] = []
        for (dimension_key, dimension_value), metrics in grouped.items():
            population = metrics['current_headcount'] + metrics['terminated_employee_count']
            metrics['attrition_rate'] = round(metrics['terminated_employee_count'] / (population or 1), 4)
            metrics['net_hiring_change'] = metrics['hire_count'] - metrics['terminated_employee_count']
            snapshots.append(
                AggregateSnapshot(
                    aggregate_id=f'workforce.attrition.summary:{dimension_key}:{dimension_value}',
                    tenant_id=self.tenant_id,
                    aggregate_type='workforce.attrition.summary',
                    dimension_key=dimension_key,
                    dimension_value=dimension_value,
                    window_start=None,
                    window_end=None,
                    metrics=metrics,
                    updated_at=updated_at,
                )
            )
        return snapshots

    def _build_attendance_trend_snapshots(self, attendance_rows: list[dict[str, Any]]) -> list[AggregateSnapshot]:
        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        for row in attendance_rows:
            attendance_date = str(row.get('attendance_date') or 'unknown')
            department_id = str(row.get('department_id') or 'unknown')
            status = str(row.get('attendance_status') or 'Unknown')
            total_hours = float(row.get('total_hours') or 0)
            for dimension_key, dimension_value in (('attendance_date', attendance_date), ('department_id', department_id)):
                metrics = grouped.setdefault(
                    (dimension_key, dimension_value),
                    {
                        'record_count': 0,
                        'present_count': 0,
                        'late_count': 0,
                        'absent_count': 0,
                        'half_day_count': 0,
                        'total_hours': 0.0,
                    },
                )
                metrics['record_count'] += 1
                metrics['total_hours'] += total_hours
                if status == 'Present':
                    metrics['present_count'] += 1
                elif status == 'Late':
                    metrics['late_count'] += 1
                elif status == 'Absent':
                    metrics['absent_count'] += 1
                elif status == 'HalfDay':
                    metrics['half_day_count'] += 1
        updated_at = self._now()
        snapshots: list[AggregateSnapshot] = []
        for (dimension_key, dimension_value), metrics in grouped.items():
            record_count = metrics['record_count'] or 1
            productive = metrics['present_count'] + metrics['late_count'] + metrics['half_day_count']
            metrics['attendance_rate'] = round(productive / record_count, 4)
            metrics['average_hours'] = round(metrics['total_hours'] / record_count, 2)
            metrics['total_hours'] = round(metrics['total_hours'], 2)
            snapshots.append(
                AggregateSnapshot(
                    aggregate_id=f'workforce.attendance.trend:{dimension_key}:{dimension_value}',
                    tenant_id=self.tenant_id,
                    aggregate_type='workforce.attendance.trend',
                    dimension_key=dimension_key,
                    dimension_value=dimension_value,
                    window_start=dimension_value if dimension_key == 'attendance_date' else None,
                    window_end=dimension_value if dimension_key == 'attendance_date' else None,
                    metrics=metrics,
                    updated_at=updated_at,
                )
            )
        return snapshots

    def _build_workforce_dashboard_snapshots(
        self,
        candidate_rows: list[dict[str, Any]],
        employee_directory_rows: list[dict[str, Any]],
        attendance_rows: list[dict[str, Any]],
        event_rows: list[dict[str, Any]],
    ) -> list[AggregateSnapshot]:
        attrition_metrics = next(
            (
                snapshot.metrics
                for snapshot in self._build_attrition_snapshots(employee_directory_rows, self._read_rows('employee_profile_view'), event_rows)
                if snapshot.dimension_key == 'tenant'
            ),
            {
                'current_headcount': 0,
                'active_headcount': 0,
                'inactive_headcount': 0,
                'terminated_employee_count': 0,
                'hire_count': 0,
                'termination_event_count': 0,
                'attrition_rate': 0.0,
                'net_hiring_change': 0,
            },
        )
        attendance_snapshots = [
            snapshot
            for snapshot in self._build_attendance_trend_snapshots(attendance_rows)
            if snapshot.dimension_key == 'attendance_date'
        ]
        attendance_snapshots.sort(key=lambda snapshot: snapshot.dimension_value, reverse=True)
        attendance_metrics = attendance_snapshots[0].metrics if attendance_snapshots else None
        latest_attendance = attendance_metrics or {
            'record_count': len(attendance_rows),
            'present_count': 0,
            'late_count': 0,
            'absent_count': 0,
            'half_day_count': 0,
            'total_hours': 0.0,
            'attendance_rate': 0.0,
            'average_hours': 0.0,
        }
        funnel_metrics = next(
            (
                snapshot.metrics
                for snapshot in self._build_hiring_funnel_snapshots(candidate_rows)
                if snapshot.dimension_key == 'tenant'
            ),
            {
                'application_count': len(candidate_rows),
                'screening_count': 0,
                'interview_count': 0,
                'offer_count': 0,
                'hired_count': 0,
                'screening_conversion_rate': 0.0,
                'interview_conversion_rate': 0.0,
                'offer_conversion_rate': 0.0,
                'hire_conversion_rate': 0.0,
            },
        )
        metrics = {
            'headcount': {
                'current': attrition_metrics['current_headcount'],
                'active': attrition_metrics['active_headcount'],
                'inactive': attrition_metrics['inactive_headcount'],
            },
            'attrition': {
                'terminated_employee_count': attrition_metrics['terminated_employee_count'],
                'termination_event_count': attrition_metrics['termination_event_count'],
                'attrition_rate': attrition_metrics['attrition_rate'],
                'net_hiring_change': attrition_metrics['net_hiring_change'],
            },
            'hiring_funnel': dict(funnel_metrics),
            'attendance': {
                'record_count': latest_attendance['record_count'],
                'attendance_rate': latest_attendance['attendance_rate'],
                'average_hours': latest_attendance['average_hours'],
                'late_count': latest_attendance['late_count'],
                'absent_count': latest_attendance['absent_count'],
            },
        }
        return [
            AggregateSnapshot(
                aggregate_id=f'workforce.dashboard.summary:tenant:{self.tenant_id}',
                tenant_id=self.tenant_id,
                aggregate_type='workforce.dashboard.summary',
                dimension_key='tenant',
                dimension_value=self.tenant_id,
                window_start=None,
                window_end=None,
                metrics=metrics,
                updated_at=self._now(),
            )
        ]

    def list_aggregates(
        self,
        *,
        aggregate_type: str | None = None,
        dimension_key: str | None = None,
        dimension_value: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = [snapshot.to_dict() for snapshot in self.aggregate_snapshots.values() if snapshot.tenant_id == self.tenant_id]
        if aggregate_type is not None:
            if aggregate_type not in self.REPORT_TYPES:
                raise ReportingAnalyticsError('aggregate_type is not supported')
            rows = [row for row in rows if row['aggregate_type'] == aggregate_type]
        if dimension_key is not None:
            rows = [row for row in rows if row['dimension_key'] == dimension_key]
        if dimension_value is not None:
            rows = [row for row in rows if row['dimension_value'] == dimension_value]
        rows.sort(key=lambda row: (row['aggregate_type'], row['dimension_key'], row['dimension_value']))
        return rows

    def create_report_definition(self, payload: dict[str, Any]) -> dict[str, Any]:
        report_type = str(payload.get('report_type') or '')
        if report_type not in self.REPORT_TYPES:
            raise ReportingAnalyticsError('report_type is not supported')
        name = str(payload.get('name') or '').strip()
        if not name:
            raise ReportingAnalyticsError('name is required')
        report = ReportDefinition(
            report_id=str(uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            report_type=report_type,
            filters=dict(payload.get('filters') or {}),
            delivery=dict(payload.get('delivery') or {}),
            created_at=self._now(),
            updated_at=self._now(),
        )
        self.report_definitions[report.report_id] = report
        return report.to_dict()

    def get_report_definition(self, report_id: str) -> dict[str, Any]:
        report = self.report_definitions.get(report_id)
        if report is None or report.tenant_id != self.tenant_id:
            raise ReportingAnalyticsError('report was not found')
        return report.to_dict()

    def list_report_definitions(self) -> list[dict[str, Any]]:
        rows = [report.to_dict() for report in self.report_definitions.values() if report.tenant_id == self.tenant_id]
        rows.sort(key=lambda row: (row['name'], row['report_id']))
        return rows

    def run_report(self, report_id: str, *, trace_id: str | None = None, filters_override: dict[str, Any] | None = None) -> dict[str, Any]:
        report = self.get_report_definition(report_id)
        filters = {**report['filters'], **dict(filters_override or {})}
        rows = self.list_aggregates(
            aggregate_type=report['report_type'],
            dimension_key=filters.get('dimension_key'),
            dimension_value=filters.get('dimension_value'),
        )
        run = ReportRun(
            report_run_id=str(uuid4()),
            tenant_id=self.tenant_id,
            report_id=report_id,
            report_type=report['report_type'],
            filters=filters,
            summary={
                'row_count': len(rows),
                'aggregate_type': report['report_type'],
                'generated_from_projection': True,
            },
            rows=rows,
            generated_at=self._now(),
            trace_id=trace_id or uuid4().hex,
        )
        self.report_runs[run.report_run_id] = run
        return run.to_dict()

    def list_report_runs(self, *, report_id: str | None = None) -> list[dict[str, Any]]:
        rows = [run.to_dict() for run in self.report_runs.values() if run.tenant_id == self.tenant_id]
        if report_id is not None:
            rows = [row for row in rows if row['report_id'] == report_id]
        rows.sort(key=lambda row: (row['generated_at'], row['report_run_id']), reverse=True)
        return rows

    def _serialize_export(self, rows: list[dict[str, Any]], export_format: str) -> tuple[str, str]:
        if export_format == 'json':
            return json.dumps(rows, indent=2, sort_keys=True), 'application/json'
        if export_format != 'csv':
            raise ReportingAnalyticsError('export_format must be csv or json')
        output = io.StringIO()
        normalized = [self._flatten_row(row) for row in rows]
        fieldnames: list[str] = []
        for row in normalized:
            for key in row.keys():
                if key not in fieldnames:
                    fieldnames.append(key)
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in normalized:
            writer.writerow(row)
        return output.getvalue(), 'text/csv'

    def _flatten_row(self, row: dict[str, Any], *, prefix: str = '') -> dict[str, Any]:
        flattened: dict[str, Any] = {}
        for key, value in row.items():
            composite = f'{prefix}{key}' if not prefix else f'{prefix}.{key}'
            if isinstance(value, dict):
                flattened.update(self._flatten_row(value, prefix=composite))
            elif isinstance(value, list):
                flattened[composite] = json.dumps(value, sort_keys=True)
            else:
                flattened[composite] = value
        return flattened

    def export_report(
        self,
        *,
        report_id: str,
        export_format: str,
        trace_id: str | None = None,
        report_run_id: str | None = None,
        schedule_id: str | None = None,
    ) -> dict[str, Any]:
        if export_format not in self.EXPORT_FORMATS:
            raise ReportingAnalyticsError('export_format must be csv or json')
        run = self.report_runs.get(report_run_id) if report_run_id else None
        if run is None:
            generated = self.run_report(report_id, trace_id=trace_id)
            run = self.report_runs[generated['report_run_id']]
        content, content_type = self._serialize_export(run.rows, export_format)
        export = ExportRecord(
            export_id=str(uuid4()),
            tenant_id=self.tenant_id,
            report_id=report_id,
            report_run_id=run.report_run_id,
            export_format=export_format,
            file_name=f"{run.report_type.replace('.', '_')}-{run.report_run_id}.{export_format}",
            row_count=len(run.rows),
            content_type=content_type,
            content=content,
            created_at=self._now(),
            trace_id=trace_id or run.trace_id,
            schedule_id=schedule_id,
        )
        self.exports[export.export_id] = export
        return export.to_dict()

    def list_exports(self, *, report_id: str | None = None) -> list[dict[str, Any]]:
        rows = [record.to_dict() for record in self.exports.values() if record.tenant_id == self.tenant_id]
        if report_id is not None:
            rows = [row for row in rows if row['report_id'] == report_id]
        rows.sort(key=lambda row: (row['created_at'], row['export_id']), reverse=True)
        return rows

    def create_schedule(self, payload: dict[str, Any]) -> dict[str, Any]:
        report_id = str(payload.get('report_id') or '')
        self.get_report_definition(report_id)
        cadence = str(payload.get('cadence') or '')
        if cadence not in self.CADENCES:
            raise ReportingAnalyticsError('cadence must be daily, weekly, or monthly')
        export_format = str(payload.get('export_format') or 'json')
        if export_format not in self.EXPORT_FORMATS:
            raise ReportingAnalyticsError('export_format must be csv or json')
        next_run_at = self._coerce_datetime(str(payload.get('next_run_at') or self._now()), 'next_run_at').isoformat()
        schedule = ScheduledReport(
            schedule_id=str(uuid4()),
            tenant_id=self.tenant_id,
            report_id=report_id,
            cadence=cadence,
            export_format=export_format,
            next_run_at=next_run_at,
            delivery=dict(payload.get('delivery') or {}),
            active=bool(payload.get('active', True)),
            last_enqueued_at=None,
            created_at=self._now(),
            updated_at=self._now(),
        )
        self.schedules[schedule.schedule_id] = schedule
        return schedule.to_dict()

    def list_schedules(self, *, active_only: bool = False) -> list[dict[str, Any]]:
        rows = [schedule.to_dict() for schedule in self.schedules.values() if schedule.tenant_id == self.tenant_id]
        if active_only:
            rows = [row for row in rows if row['active']]
        rows.sort(key=lambda row: (row['next_run_at'], row['schedule_id']))
        return rows

    def claim_due_schedules(self, *, now: str | None = None) -> list[dict[str, Any]]:
        effective_now = self._coerce_datetime(now or self._now(), 'now')
        due: list[dict[str, Any]] = []
        with self._lock:
            rows = [schedule for schedule in self.schedules.values() if schedule.tenant_id == self.tenant_id and schedule.active]
            rows.sort(key=lambda row: (row.next_run_at, row.schedule_id))
            for schedule in rows:
                if self._coerce_datetime(schedule.next_run_at, 'next_run_at') > effective_now:
                    continue
                due.append(schedule.to_dict())
                schedule.last_enqueued_at = effective_now.isoformat()
                schedule.next_run_at = self._next_run_at(now=effective_now, cadence=schedule.cadence)
                schedule.updated_at = self._now()
                self.schedules[schedule.schedule_id] = schedule
        return due
