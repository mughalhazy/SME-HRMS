from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from time import perf_counter
from typing import Any, Callable
from uuid import uuid4

from event_outbox import EventOutbox, OutboxEvent
from notification_service import EVENT_NOTIFICATION_PLANS, NotificationService, serialize_message
from resilience import CentralErrorLogger, DeadLetterQueue, IdempotencyStore, Observability, run_with_retry
from tenant_support import DEFAULT_TENANT_ID, assert_tenant_access, normalize_tenant_id
from workflow_contract import ensure_workflow_contract

JobHandler = Callable[['JobExecutionContext'], dict[str, Any]]


class JobStatus(str, Enum):
    SCHEDULED = 'Scheduled'
    RUNNING = 'Running'
    SUCCEEDED = 'Succeeded'
    FAILED = 'Failed'
    DEAD_LETTERED = 'DeadLettered'
    CANCELLED = 'Cancelled'


@dataclass
class JobRecord:
    job_id: str
    tenant_id: str
    job_type: str
    payload: dict[str, Any]
    status: JobStatus
    attempts: int
    max_attempts: int
    scheduled_at: str
    started_at: str | None
    finished_at: str | None
    failure_reason: str | None
    trace_id: str
    correlation_id: str
    actor_id: str | None
    actor_type: str
    dead_lettered_at: str | None = None
    last_result: dict[str, Any] | None = None
    idempotency_key: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['status'] = self.status.value
        return payload


@dataclass
class JobFailureRecord:
    background_job_failure_id: str
    tenant_id: str
    job_id: str
    attempt_number: int
    failure_reason: str
    retryable: bool
    occurred_at: str
    recovered_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class JobExecutionContext:
    job: JobRecord
    tenant_id: str
    trace_id: str
    correlation_id: str


class BackgroundJobError(Exception):
    def __init__(self, status_code: int, code: str, message: str, *, details: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []

    def to_dict(self) -> dict[str, Any]:
        return {
            'code': self.code,
            'message': self.message,
            'details': self.details,
        }


class BackgroundJobService:
    def __init__(
        self,
        *,
        payroll_service: Any | None = None,
        leave_service: Any | None = None,
        notification_service: NotificationService | None = None,
        reporting_service: Any | None = None,
        outbox: EventOutbox | None = None,
        db_path: str | None = None,
    ):
        from persistent_store import PersistentKVStore

        self.jobs = PersistentKVStore[str, JobRecord](service='background-jobs', namespace='jobs', db_path=db_path)
        self.job_types = PersistentKVStore[str, dict[str, Any]](service='background-jobs', namespace='job_types', db_path=db_path)
        self.job_results = PersistentKVStore[str, dict[str, Any]](service='background-jobs', namespace='job_results', db_path=db_path)
        self.job_failures = PersistentKVStore[str, JobFailureRecord](service='background-jobs', namespace='job_failures', db_path=db_path)
        self.handlers: dict[str, JobHandler] = {}
        self.default_max_attempts = 3
        self.idempotency = IdempotencyStore()
        self.dead_letters = DeadLetterQueue()
        self.error_logger = CentralErrorLogger('background-jobs')
        self.observability = Observability('background-jobs')
        self.outbox = outbox or EventOutbox(db_path=db_path)
        self.notification_service = notification_service
        self._lock = RLock()
        if payroll_service is not None:
            self.register_payroll_run_handler(payroll_service)
        if leave_service is not None:
            self.register_leave_balance_recompute_handler(leave_service)
        if notification_service is not None:
            self.register_notification_dispatch_handler(notification_service)
            self.register_outbox_dispatch_handler(notification_service)
        if reporting_service is not None:
            self.register_reporting_handlers(reporting_service)
        self.register_workflow_escalation_handler()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _trace(self, trace_id: str | None) -> str:
        return self.observability.trace_id(trace_id)

    def register_handler(self, job_type: str, handler: JobHandler, *, max_attempts: int | None = None) -> None:
        self.handlers[job_type] = handler
        self.job_types[job_type] = {
            'job_type': job_type,
            'max_attempts': max_attempts or self.default_max_attempts,
            'registered_at': self._now(),
        }

    def enqueue_job(
        self,
        *,
        tenant_id: str,
        job_type: str,
        payload: dict[str, Any],
        scheduled_at: str | None = None,
        actor_id: str | None = None,
        actor_type: str = 'service',
        trace_id: str | None = None,
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
        max_attempts: int | None = None,
    ) -> JobRecord:
        tenant = normalize_tenant_id(tenant_id)
        job_trace = self._trace(trace_id)
        fingerprint = json.dumps({'job_type': job_type, 'tenant_id': tenant, 'payload': payload, 'scheduled_at': scheduled_at}, sort_keys=True, default=str)
        replay_key = idempotency_key or f'job:{job_type}:{tenant}:{fingerprint}'
        replay = self.idempotency.replay_or_conflict(replay_key, fingerprint)
        if replay is not None:
            existing = self.jobs[replay.payload['job_id']]
            return existing
        if job_type not in self.handlers:
            raise BackgroundJobError(422, 'UNKNOWN_JOB_TYPE', f'No job handler registered for {job_type}')
        job = JobRecord(
            job_id=str(uuid4()),
            tenant_id=tenant,
            job_type=job_type,
            payload=dict(payload),
            status=JobStatus.SCHEDULED,
            attempts=0,
            max_attempts=max_attempts or self.job_types.get(job_type, {}).get('max_attempts', self.default_max_attempts),
            scheduled_at=scheduled_at or self._now(),
            started_at=None,
            finished_at=None,
            failure_reason=None,
            trace_id=job_trace,
            correlation_id=correlation_id or job_trace,
            actor_id=actor_id,
            actor_type=actor_type,
            idempotency_key=idempotency_key,
        )
        with self._lock:
            self.jobs[job.job_id] = job
            self.idempotency.record(replay_key, fingerprint, 202, {'job_id': job.job_id})
        self.observability.logger.info(
            'job.enqueued',
            trace_id=job.trace_id,
            message=job.job_type,
            action='job.enqueue',
            status=job.status.value,
            tenant_id=job.tenant_id,
            correlation_id=job.correlation_id,
            context={'job_id': job.job_id, 'tenant_id': job.tenant_id, 'scheduled_at': job.scheduled_at, 'job_type': job.job_type, 'trace_stage': 'job'},
        )
        self.observability.record_trace('job.enqueue', request_id=job.trace_id, status=job.status.value, stage='job', context={'tenant_id': job.tenant_id, 'job_id': job.job_id, 'job_type': job.job_type, 'scheduled_at': job.scheduled_at, 'correlation_id': job.correlation_id})
        return job

    def get_job(self, job_id: str, *, tenant_id: str, actor_role: str = 'Admin') -> JobRecord:
        job = self.jobs.get(job_id)
        if job is None:
            raise BackgroundJobError(404, 'JOB_NOT_FOUND', 'Background job not found')
        assert_tenant_access(job.tenant_id, tenant_id)
        if actor_role not in {'Admin', 'Service'}:
            raise BackgroundJobError(403, 'FORBIDDEN', 'Insufficient permissions for background job access')
        return job

    def list_jobs(self, *, tenant_id: str, actor_role: str = 'Admin', status: str | None = None) -> list[JobRecord]:
        if actor_role not in {'Admin', 'Service'}:
            raise BackgroundJobError(403, 'FORBIDDEN', 'Insufficient permissions for background job access')
        tenant = normalize_tenant_id(tenant_id)
        rows = [job for job in self.jobs.values() if job.tenant_id == tenant]
        if status is not None:
            rows = [job for job in rows if job.status.value == status]
        rows.sort(key=lambda row: (row.scheduled_at, row.job_id))
        return rows

    def cancel_job(self, job_id: str, *, tenant_id: str, actor_role: str = 'Admin') -> JobRecord:
        with self._lock:
            job = self.get_job(job_id, tenant_id=tenant_id, actor_role=actor_role)
            if job.status in {JobStatus.SUCCEEDED, JobStatus.DEAD_LETTERED}:
                raise BackgroundJobError(409, 'INVALID_JOB_STATE', 'Completed jobs cannot be cancelled')
            job.status = JobStatus.CANCELLED
            job.finished_at = self._now()
            job.updated_at = self._now()
            self.jobs[job.job_id] = job
            return job

    def retry_job(self, job_id: str, *, tenant_id: str, actor_role: str = 'Admin', trace_id: str | None = None) -> JobRecord:
        with self._lock:
            job = self.get_job(job_id, tenant_id=tenant_id, actor_role=actor_role)
            if job.status not in {JobStatus.FAILED, JobStatus.DEAD_LETTERED}:
                raise BackgroundJobError(409, 'INVALID_JOB_STATE', 'Only failed or dead-lettered jobs can be retried')
            job.status = JobStatus.SCHEDULED
            job.failure_reason = None
            job.dead_lettered_at = None
            job.scheduled_at = self._now()
            job.trace_id = self._trace(trace_id) if trace_id else job.trace_id
            job.updated_at = self._now()
            self.jobs[job.job_id] = job
            return job

    def run_due_jobs(self, *, now: str | None = None, tenant_id: str | None = None) -> list[JobRecord]:
        effective_now = now or self._now()
        rows = [job for job in self.jobs.values() if job.status == JobStatus.SCHEDULED and job.scheduled_at <= effective_now]
        if tenant_id is not None:
            tenant = normalize_tenant_id(tenant_id)
            rows = [job for job in rows if job.tenant_id == tenant]
        rows.sort(key=lambda row: (row.scheduled_at, row.job_id))
        executed: list[JobRecord] = []
        for job in rows:
            executed.append(self.execute_job(job.job_id, tenant_id=job.tenant_id))
        return executed

    def execute_job(self, job_id: str, *, tenant_id: str, trace_id: str | None = None) -> JobRecord:
        started = perf_counter()
        with self._lock:
            job = self.get_job(job_id, tenant_id=tenant_id)
            if job.status == JobStatus.SUCCEEDED:
                self.observability.track('execute_job', trace_id=job.trace_id, started_at=started, success=True, context={'job_id': job.job_id, 'job_type': job.job_type, 'tenant_id': job.tenant_id, 'status': job.status.value, 'replayed': True, 'trace_stage': 'job', 'correlation_id': job.correlation_id})
                return job
            if job.status == JobStatus.CANCELLED:
                raise BackgroundJobError(409, 'INVALID_JOB_STATE', 'Cancelled jobs cannot be executed')
            handler = self.handlers.get(job.job_type)
            if handler is None:
                raise BackgroundJobError(422, 'UNKNOWN_JOB_TYPE', f'No job handler registered for {job.job_type}')
            job.status = JobStatus.RUNNING
            job.started_at = self._now()
            job.updated_at = self._now()
            if trace_id:
                job.trace_id = self._trace(trace_id)
            self.jobs[job.job_id] = job

        context = JobExecutionContext(job=job, tenant_id=job.tenant_id, trace_id=job.trace_id, correlation_id=job.correlation_id)
        attempt_counter = 0

        def invoke() -> dict[str, Any]:
            nonlocal attempt_counter
            attempt_counter += 1
            return handler(context)

        try:
            result = run_with_retry(
                invoke,
                attempts=max(1, job.max_attempts - job.attempts),
                base_delay=0.001,
                timeout_seconds=1.0,
                retryable=lambda exc: not isinstance(exc, BackgroundJobError) or exc.status_code >= 500,
                on_retry=lambda attempt, exc, delay: self.observability.logger.info(
                    'job.retry',
                    trace_id=job.trace_id,
                    message=job.job_type,
                    context={'job_id': job.job_id, 'attempt': attempt, 'delay_seconds': delay, 'error': str(exc)},
                ),
            )
            with self._lock:
                job = self.jobs[job.job_id]
                job.attempts += max(1, attempt_counter)
                job.status = JobStatus.SUCCEEDED
                job.finished_at = self._now()
                job.updated_at = self._now()
                job.failure_reason = None
                job.last_result = result
                self.jobs[job.job_id] = job
                self.job_results[job.job_id] = {'result': result, 'finished_at': job.finished_at}
            self.observability.logger.audit(
                'background_job_succeeded',
                trace_id=job.trace_id,
                actor=job.actor_id or job.actor_type,
                entity='BackgroundJob',
                entity_id=job.job_id,
                context={'job_type': job.job_type, 'tenant_id': job.tenant_id, 'attempts': job.attempts},
            )
            self.observability.track('execute_job', trace_id=job.trace_id, started_at=started, success=True, context={'job_id': job.job_id, 'job_type': job.job_type, 'tenant_id': job.tenant_id, 'status': job.status.value, 'trace_stage': 'job', 'correlation_id': job.correlation_id})
            return job
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                job = self.jobs[job.job_id]
                job.attempts += max(1, attempt_counter)
                job.finished_at = self._now()
                job.updated_at = self._now()
                job.failure_reason = str(exc)
                terminal = job.attempts >= job.max_attempts
                job.status = JobStatus.DEAD_LETTERED if terminal else JobStatus.FAILED
                if terminal:
                    job.dead_lettered_at = self._now()
                self.jobs[job.job_id] = job
                failure_record = JobFailureRecord(
                    background_job_failure_id=str(uuid4()),
                    tenant_id=job.tenant_id,
                    job_id=job.job_id,
                    attempt_number=job.attempts,
                    failure_reason=str(exc),
                    retryable=not terminal,
                    occurred_at=self._now(),
                )
                self.job_failures[failure_record.background_job_failure_id] = failure_record
                dead_letter = self.dead_letters.push(
                    'background_jobs',
                    job.job_type,
                    {'job_id': job.job_id, 'payload': job.payload, 'tenant_id': job.tenant_id, 'background_job_failure_id': failure_record.background_job_failure_id},
                    str(exc),
                    trace_id=job.trace_id,
                    retryable=not terminal,
                )
            self.error_logger.log(job.job_type, exc, trace_id=job.trace_id, details={'job_id': job.job_id, 'tenant_id': job.tenant_id})
            self.observability.track('execute_job', trace_id=job.trace_id, started_at=started, success=False, context={'job_id': job.job_id, 'job_type': job.job_type, 'tenant_id': job.tenant_id, 'status': job.status.value, 'trace_stage': 'job', 'error_category': 'system', 'correlation_id': job.correlation_id})
            if job.status == JobStatus.DEAD_LETTERED:
                self.observability.logger.error('job.dead_lettered', trace_id=job.trace_id, message=job.job_type, context={'job_id': job.job_id, 'dead_letter_id': dead_letter.dead_letter_id})
            return job

    def register_payroll_run_handler(self, payroll_service: Any) -> None:
        def handler(context: JobExecutionContext) -> dict[str, Any]:
            before = len(getattr(payroll_service, 'events', []))
            payload = context.job.payload
            status, response = payroll_service.run_payroll(
                payload['period_start'],
                payload['period_end'],
                payload['authorization'],
                records=payload.get('records'),
                idempotency_key=payload.get('idempotency_key') or context.job.idempotency_key or context.job.job_id,
                trace_id=context.trace_id,
            )
            generated_payslips: list[str] = []
            if payload.get('generate_payslips', False):
                for record_id in response.get('data', {}).get('record_ids', []):
                    _, payslip = payroll_service.generate_payslip(
                        record_id,
                        payload['authorization'],
                        job_id=context.job.job_id,
                        trace_id=context.trace_id,
                    )
                    generated_payslips.append(payslip['payslip_id'])
            self._stage_new_events(getattr(payroll_service, 'events', []), before=before, aggregate_type='PayrollRun', aggregate_id=f"{payload['period_start']}:{payload['period_end']}")
            return {'status_code': status, 'response': response, 'generated_payslip_ids': generated_payslips}

        self.register_handler('payroll.run', handler, max_attempts=3)
        def payslip_handler(context: JobExecutionContext) -> dict[str, Any]:
            status, payslip = payroll_service.generate_payslip(
                str(context.job.payload['payroll_record_id']),
                str(context.job.payload['authorization']),
                job_id=context.job.job_id,
                trace_id=context.trace_id,
            )
            return {'status_code': status, 'payslip': payslip}

        self.register_handler('payroll.payslip.generate', payslip_handler, max_attempts=3)

    def register_leave_balance_recompute_handler(self, leave_service: Any) -> None:
        def handler(context: JobExecutionContext) -> dict[str, Any]:
            payload = context.job.payload
            employee_id = payload['employee_id']
            if hasattr(leave_service, 'recompute_employee_balance'):
                result = leave_service.recompute_employee_balance(employee_id, tenant_id=context.tenant_id, trace_id=context.trace_id)
                return {'employee_id': employee_id, 'balance_count': len(result['leave_balances']), 'employee_status': result['employee']['status']}
            detail = leave_service.get_employee_detail(employee_id)
            balances = detail.get('leave_balances') or []
            return {'employee_id': employee_id, 'balance_count': len(balances), 'employee_status': detail['employee']['status']}

        self.register_handler('leave.balance.recompute', handler, max_attempts=3)

    def register_notification_dispatch_handler(self, notification_service: NotificationService) -> None:
        def handler(context: JobExecutionContext) -> dict[str, Any]:
            created = notification_service.ingest_event(context.job.payload['event'])
            return {'dispatched_count': len(created), 'notifications': [serialize_message(message) for message in created]}

        self.register_handler('notification.dispatch', handler, max_attempts=3)

    def register_outbox_dispatch_handler(self, notification_service: NotificationService) -> None:
        def dispatch_event(outbox_event: OutboxEvent) -> None:
            if outbox_event.event_name in EVENT_NOTIFICATION_PLANS:
                notification_service.ingest_event(outbox_event.payload)

        def handler(context: JobExecutionContext) -> dict[str, Any]:
            max_events = context.job.payload.get('max_events')
            result = self.outbox.dispatch_pending(dispatch_event, tenant_id=context.tenant_id, max_events=max_events)
            return result

        self.register_handler('outbox.dispatch', handler, max_attempts=3)

    def register_reporting_handlers(self, reporting_service: Any) -> None:
        def export_handler(context: JobExecutionContext) -> dict[str, Any]:
            payload = context.job.payload
            export = reporting_service.export_report(
                report_id=str(payload['report_id']),
                report_run_id=payload.get('report_run_id'),
                export_format=str(payload.get('export_format') or 'json'),
                trace_id=context.trace_id,
                schedule_id=payload.get('schedule_id'),
            )
            self.outbox.stage_event(
                tenant_id=context.tenant_id,
                aggregate_type='ReportingExport',
                aggregate_id=export['export_id'],
                event_name='ReportingExportGenerated',
                payload={
                    'tenant_id': context.tenant_id,
                    'report_id': export['report_id'],
                    'report_run_id': export['report_run_id'],
                    'export_id': export['export_id'],
                    'schedule_id': export.get('schedule_id'),
                    'export_format': export['export_format'],
                    'row_count': export['row_count'],
                    'file_name': export['file_name'],
                },
                trace_id=context.trace_id,
            )
            return export

        self.register_handler('reporting.export', export_handler, max_attempts=3)

        def schedule_dispatch_handler(context: JobExecutionContext) -> dict[str, Any]:
            payload = context.job.payload
            schedules = reporting_service.claim_due_schedules(now=payload.get('now'))
            enqueued: list[dict[str, Any]] = []
            for schedule in schedules:
                idempotency_key = f"reporting.schedule:{schedule['schedule_id']}:{schedule['last_enqueued_at']}"
                job = self.enqueue_job(
                    tenant_id=context.tenant_id,
                    job_type='reporting.export',
                    payload={
                        'report_id': schedule['report_id'],
                        'export_format': schedule['export_format'],
                        'schedule_id': schedule['schedule_id'],
                    },
                    actor_type='service',
                    trace_id=context.trace_id,
                    correlation_id=context.correlation_id,
                    idempotency_key=idempotency_key,
                )
                enqueued.append({'job_id': job.job_id, 'schedule_id': schedule['schedule_id'], 'report_id': schedule['report_id']})
            return {'schedule_count': len(schedules), 'enqueued_jobs': enqueued}

        self.register_handler('reporting.schedule.dispatch', schedule_dispatch_handler, max_attempts=3)

    def register_workflow_escalation_handler(self) -> None:
        def handler(context: JobExecutionContext) -> dict[str, Any]:
            payload = context.job.payload
            workflow = ensure_workflow_contract(payload['workflow'])
            now = payload.get('now') or self._now()
            overdue_steps = []
            for step in workflow['steps']:
                deadline_at = str(step.get('metadata', {}).get('deadline_at'))
                if step['status'] == 'pending' and deadline_at <= now:
                    overdue_steps.append({'step_id': step['step_id'], 'assignee': step['assignee'], 'deadline_at': deadline_at})
            if overdue_steps:
                self.outbox.stage_event(
                    tenant_id=context.tenant_id,
                    aggregate_type='Workflow',
                    aggregate_id=workflow['workflow_id'],
                    event_name='WorkflowEscalationReady',
                    payload={
                        'tenant_id': context.tenant_id,
                        'workflow_id': workflow['workflow_id'],
                        'overdue_steps': overdue_steps,
                        'checked_at': now,
                    },
                    trace_id=context.trace_id,
                )
            return {'workflow_id': workflow['workflow_id'], 'overdue_steps': overdue_steps, 'escalation_count': len(overdue_steps)}

        self.register_handler('workflow.escalation', handler, max_attempts=2)

    def _stage_new_events(self, events: list[dict[str, Any]], *, before: int, aggregate_type: str, aggregate_id: str) -> None:
        for event in events[before:]:
            self.outbox.stage_canonical_event(event, aggregate_type=aggregate_type, aggregate_id=aggregate_id)
