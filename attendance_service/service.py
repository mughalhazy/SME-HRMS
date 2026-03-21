from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Iterable, List, Optional
from uuid import UUID

from attendance_service.models import (
    AttendanceAnomaly,
    AttendanceCorrection,
    AttendanceLogEvent,
    AttendanceRecord,
    AttendanceSource,
    AttendanceStatus,
    CorrectionStatus,
    OvertimeRule,
    RecordState,
    RosterAssignment,
    RosterStatus,
    Schedule,
    ScheduleStatus,
    Shift,
)
from event_contract import EventRegistry
from outbox_system import OutboxManager
from persistent_store import PersistentKVStore
from resilience import Observability
from workflow_service import WorkflowService, WorkflowServiceError


class AttendanceServiceError(Exception):
    def __init__(self, code: str, message: str, details: Optional[list] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or []


@dataclass(frozen=True)
class Actor:
    employee_id: Optional[UUID]
    role: str
    department_id: Optional[UUID] = None


@dataclass(frozen=True)
class EmployeeSnapshot:
    employee_id: UUID
    status: str
    department_id: UUID
    manager_employee_id: Optional[UUID] = None


class EmployeeDirectory:
    """Minimal dependency contract from employee-service."""

    def get(self, employee_id: UUID) -> EmployeeSnapshot:  # pragma: no cover - interface contract
        raise NotImplementedError


class InMemoryEmployeeDirectory(EmployeeDirectory):
    def __init__(self, employees: Iterable[EmployeeSnapshot]):
        self._employees = {employee.employee_id: employee for employee in employees}

    def get(self, employee_id: UUID) -> EmployeeSnapshot:
        employee = self._employees.get(employee_id)
        if not employee:
            raise AttendanceServiceError("EMPLOYEE_NOT_FOUND", "Employee does not exist")
        return employee


class AttendanceService:
    def __init__(
        self,
        employee_directory: EmployeeDirectory,
        *,
        late_after: time = time(9, 15),
        db_path: str | None = None,
        workflow_service: WorkflowService | None = None,
    ):
        self._employee_directory = employee_directory
        self._records = PersistentKVStore[UUID, AttendanceRecord](service='attendance-service', namespace='records', db_path=db_path)
        shared_db_path = self._records.db_path
        self._employee_date_index = PersistentKVStore[tuple[UUID, date], UUID](service='attendance-service', namespace='employee_date_index', db_path=shared_db_path)
        self._shifts = PersistentKVStore[UUID, Shift](service='attendance-service', namespace='shifts', db_path=shared_db_path)
        self._schedules = PersistentKVStore[UUID, Schedule](service='attendance-service', namespace='schedules', db_path=shared_db_path)
        self._rosters = PersistentKVStore[UUID, RosterAssignment](service='attendance-service', namespace='rosters', db_path=shared_db_path)
        self._roster_employee_date_index = PersistentKVStore[tuple[UUID, date], UUID](service='attendance-service', namespace='roster_employee_date_index', db_path=shared_db_path)
        self._overtime_rules = PersistentKVStore[UUID, OvertimeRule](service='attendance-service', namespace='overtime_rules', db_path=shared_db_path)
        self._corrections = PersistentKVStore[UUID, AttendanceCorrection](service='attendance-service', namespace='corrections', db_path=shared_db_path)
        self.events: List[dict] = []
        self.observability = Observability("attendance-service")
        self.outbox_observability = Observability("attendance-service-outbox")
        self._late_after = late_after
        self.tenant_id = "tenant-default"
        self.event_registry = EventRegistry()
        self.outbox = OutboxManager(
            service_name='attendance-service',
            tenant_id=self.tenant_id,
            db_path=shared_db_path,
            observability=self.outbox_observability,
            event_registry=self.event_registry,
        )
        self.workflow_service = workflow_service or WorkflowService()
        self.workflow_service.register_definition(
            tenant_id=self.tenant_id,
            code="attendance_correction_approval",
            source_service="attendance-service",
            subject_type="AttendanceCorrection",
            description="Centralized attendance correction approval workflow for anomalous or amended attendance records.",
            steps=[
                {
                    "name": "manager-approval",
                    "type": "approval",
                    "assignee_template": "{approver_employee_id}",
                    "sla": "PT24H",
                    "escalation_assignee_template": "{escalation_assignee}",
                }
            ],
        )

    def _actor_payload(self, actor: Actor, *, actor_type: str = 'user') -> dict[str, str | None]:
        return {
            'id': str(actor.employee_id) if actor.employee_id else actor.role,
            'type': actor_type,
            'role': actor.role,
            'department_id': str(actor.department_id) if actor.department_id else None,
        }

    @staticmethod
    def _record_payload(record: AttendanceRecord) -> dict:
        return {
            'attendanceId': str(record.attendance_id),
            'employeeId': str(record.employee_id),
            'attendanceDate': record.attendance_date.isoformat(),
            'attendanceStatus': record.attendance_status.value,
            'source': record.source.value if record.source else None,
            'checkInTime': record.check_in_time.isoformat() if record.check_in_time else None,
            'checkOutTime': record.check_out_time.isoformat() if record.check_out_time else None,
            'totalHours': str(record.total_hours) if record.total_hours is not None else None,
            'lifecycleState': record.lifecycle_state.value,
            'anomalies': [anomaly.value for anomaly in record.anomalies],
            'correctionNote': record.correction_note,
            'scheduledShiftId': str(record.scheduled_shift_id) if record.scheduled_shift_id else None,
            'scheduledStartTime': record.scheduled_start_time.isoformat() if record.scheduled_start_time else None,
            'scheduledEndTime': record.scheduled_end_time.isoformat() if record.scheduled_end_time else None,
            'scheduledHours': str(record.scheduled_hours) if record.scheduled_hours is not None else None,
            'rosterAssignmentId': str(record.roster_assignment_id) if record.roster_assignment_id else None,
            'overtimeHours': str(record.overtime_hours) if record.overtime_hours is not None else None,
        }

    @staticmethod
    def _shift_payload(shift: Shift) -> dict:
        return {
            'shiftId': str(shift.shift_id),
            'code': shift.code,
            'name': shift.name,
            'startTime': shift.start_time.isoformat(),
            'endTime': shift.end_time.isoformat(),
            'breakMinutes': shift.break_minutes,
            'lateGraceMinutes': shift.late_grace_minutes,
            'overtimeEligible': shift.overtime_eligible,
            'departmentId': str(shift.department_id) if shift.department_id else None,
            'scheduledHours': str(shift.scheduled_hours()),
        }

    @staticmethod
    def _schedule_payload(schedule: Schedule) -> dict:
        return {
            'scheduleId': str(schedule.schedule_id),
            'name': schedule.name,
            'effectiveFrom': schedule.effective_from.isoformat(),
            'effectiveTo': schedule.effective_to.isoformat(),
            'departmentId': str(schedule.department_id) if schedule.department_id else None,
            'status': schedule.status.value,
        }

    @staticmethod
    def _roster_payload(roster: RosterAssignment) -> dict:
        return {
            'rosterId': str(roster.roster_id),
            'employeeId': str(roster.employee_id),
            'shiftId': str(roster.shift_id),
            'scheduleId': str(roster.schedule_id) if roster.schedule_id else None,
            'rosterDate': roster.roster_date.isoformat(),
            'status': roster.status.value,
        }

    @staticmethod
    def _overtime_rule_payload(rule: OvertimeRule) -> dict:
        return {
            'ruleId': str(rule.rule_id),
            'name': rule.name,
            'appliesAfterHours': str(rule.applies_after_hours),
            'multiplier': str(rule.multiplier),
            'maxOvertimeHours': str(rule.max_overtime_hours),
            'departmentId': str(rule.department_id) if rule.department_id else None,
            'active': rule.active,
        }

    @staticmethod
    def _correction_payload(correction: AttendanceCorrection) -> dict:
        return {
            'correctionId': str(correction.correction_id),
            'attendanceId': str(correction.attendance_id),
            'employeeId': str(correction.employee_id),
            'requestedByEmployeeId': str(correction.requested_by_employee_id),
            'approverEmployeeId': str(correction.approver_employee_id) if correction.approver_employee_id else None,
            'requestedStatus': correction.requested_status.value if correction.requested_status else None,
            'requestedCheckInTime': correction.requested_check_in_time.isoformat() if correction.requested_check_in_time else None,
            'requestedCheckOutTime': correction.requested_check_out_time.isoformat() if correction.requested_check_out_time else None,
            'requestedCorrectionNote': correction.requested_correction_note,
            'reason': correction.reason,
            'status': correction.status.value,
            'workflowId': correction.workflow_id,
            'decisionNote': correction.decision_note,
            'submittedAt': correction.submitted_at.isoformat(),
            'decidedAt': correction.decided_at.isoformat() if correction.decided_at else None,
        }

    def _audit(self, action: str, actor: Actor, entity: str, entity_id: str, before: dict, after: dict) -> None:
        self.observability.logger.audit(
            action,
            actor=self._actor_payload(actor),
            entity=entity,
            entity_id=entity_id,
            context={'tenant_id': self.tenant_id, 'before': before, 'after': after},
        )

    def create_shift(
        self,
        actor: Actor,
        *,
        code: str,
        name: str,
        start_time: time,
        end_time: time,
        break_minutes: int = 0,
        late_grace_minutes: int = 15,
        overtime_eligible: bool = True,
        department_id: UUID | None = None,
    ) -> Shift:
        self._authorize_schedule_admin(actor, department_id=department_id)
        shift = Shift(
            code=code,
            name=name,
            start_time=start_time,
            end_time=end_time,
            break_minutes=break_minutes,
            late_grace_minutes=late_grace_minutes,
            overtime_eligible=overtime_eligible,
            department_id=department_id,
        )
        try:
            shift.scheduled_hours()
        except ValueError as exc:
            raise AttendanceServiceError('SHIFT_INVALID', str(exc)) from exc
        self._shifts[shift.shift_id] = shift
        self._queue_event('attendance.shift.created', self._shift_payload(shift), idempotency_key=str(shift.shift_id))
        self._dispatch_outbox()
        self._audit('attendance_shift_created', actor, 'Shift', str(shift.shift_id), {}, self._shift_payload(shift))
        return shift

    def create_schedule(
        self,
        actor: Actor,
        *,
        name: str,
        effective_from: date,
        effective_to: date,
        department_id: UUID | None = None,
    ) -> Schedule:
        self._authorize_schedule_admin(actor, department_id=department_id)
        if effective_to < effective_from:
            raise AttendanceServiceError('DATE_RANGE_INVALID', 'effective_to must be >= effective_from')
        schedule = Schedule(
            name=name,
            effective_from=effective_from,
            effective_to=effective_to,
            department_id=department_id,
        )
        self._schedules[schedule.schedule_id] = schedule
        self._queue_event('attendance.schedule.created', self._schedule_payload(schedule), idempotency_key=str(schedule.schedule_id))
        self._dispatch_outbox()
        self._audit('attendance_schedule_created', actor, 'Schedule', str(schedule.schedule_id), {}, self._schedule_payload(schedule))
        return schedule

    def publish_schedule(self, actor: Actor, schedule_id: UUID) -> Schedule:
        schedule = self._get_schedule(schedule_id)
        before = self._schedule_payload(schedule)
        self._authorize_schedule_admin(actor, department_id=schedule.department_id)
        schedule.status = ScheduleStatus.PUBLISHED
        schedule.updated_at = datetime.utcnow()
        self._schedules[schedule.schedule_id] = schedule
        self._queue_event('attendance.schedule.published', self._schedule_payload(schedule), idempotency_key=f'{schedule.schedule_id}:published')
        self._dispatch_outbox()
        self._audit('attendance_schedule_published', actor, 'Schedule', str(schedule.schedule_id), before, self._schedule_payload(schedule))
        return schedule

    def assign_roster(
        self,
        actor: Actor,
        *,
        employee_id: UUID,
        shift_id: UUID,
        roster_date: date,
        schedule_id: UUID | None = None,
        publish: bool = True,
    ) -> RosterAssignment:
        employee = self._employee_directory.get(employee_id)
        shift = self._get_shift(shift_id)
        self._authorize_schedule_admin(actor, department_id=employee.department_id)
        if shift.department_id and shift.department_id != employee.department_id:
            raise AttendanceServiceError('SHIFT_SCOPE_INVALID', 'Shift does not belong to employee department')
        schedule: Schedule | None = None
        if schedule_id:
            schedule = self._get_schedule(schedule_id)
            if schedule.department_id and schedule.department_id != employee.department_id:
                raise AttendanceServiceError('SCHEDULE_SCOPE_INVALID', 'Schedule does not belong to employee department')
            if not (schedule.effective_from <= roster_date <= schedule.effective_to):
                raise AttendanceServiceError('DATE_RANGE_INVALID', 'roster_date must fall within schedule effective range')
        existing_roster_id = self._roster_employee_date_index.get((employee_id, roster_date))
        before = self._roster_payload(self._rosters[existing_roster_id]) if existing_roster_id else {}
        roster = self._rosters.get(existing_roster_id) if existing_roster_id else None
        if roster is None:
            roster = RosterAssignment(
                employee_id=employee_id,
                shift_id=shift_id,
                roster_date=roster_date,
                schedule_id=schedule_id,
                status=RosterStatus.PUBLISHED if publish else RosterStatus.ASSIGNED,
            )
        else:
            roster.shift_id = shift_id
            roster.schedule_id = schedule_id
            roster.status = RosterStatus.PUBLISHED if publish else roster.status
            roster.updated_at = datetime.utcnow()
        self._rosters[roster.roster_id] = roster
        self._roster_employee_date_index[(employee_id, roster_date)] = roster.roster_id
        self._queue_event('attendance.roster.assigned', self._roster_payload(roster), idempotency_key=f'{employee_id}:{roster_date.isoformat()}')
        self._dispatch_outbox()
        self._audit('attendance_roster_assigned', actor, 'RosterAssignment', str(roster.roster_id), before, self._roster_payload(roster))
        return roster

    def list_roster(self, actor: Actor, *, employee_id: UUID, from_date: date, to_date: date) -> list[dict]:
        self._authorize_read(actor, employee_id)
        if to_date < from_date:
            raise AttendanceServiceError('DATE_RANGE_INVALID', 'to must be >= from')
        rows: list[dict] = []
        current = from_date
        while current <= to_date:
            roster = self._find_roster(employee_id, current)
            if roster:
                shift = self._get_shift(roster.shift_id)
                rows.append({**self._roster_payload(roster), 'shift': self._shift_payload(shift)})
            current = current + timedelta(days=1)
        return rows

    def set_overtime_rule(
        self,
        actor: Actor,
        *,
        name: str,
        applies_after_hours: Decimal,
        multiplier: Decimal,
        max_overtime_hours: Decimal,
        department_id: UUID | None = None,
        active: bool = True,
    ) -> OvertimeRule:
        self._authorize_schedule_admin(actor, department_id=department_id)
        if applies_after_hours < Decimal('0') or multiplier < Decimal('1') or max_overtime_hours < Decimal('0'):
            raise AttendanceServiceError('OVERTIME_RULE_INVALID', 'Overtime rule values must be non-negative and multiplier >= 1')
        rule = OvertimeRule(
            name=name,
            applies_after_hours=applies_after_hours,
            multiplier=multiplier,
            max_overtime_hours=max_overtime_hours,
            department_id=department_id,
            active=active,
        )
        self._overtime_rules[rule.rule_id] = rule
        self._queue_event('attendance.overtime.configured', self._overtime_rule_payload(rule), idempotency_key=str(rule.rule_id))
        self._dispatch_outbox()
        self._audit('attendance_overtime_rule_configured', actor, 'OvertimeRule', str(rule.rule_id), {}, self._overtime_rule_payload(rule))
        return rule

    def create_record(
        self,
        actor: Actor,
        *,
        employee_id: UUID,
        attendance_date: date,
        attendance_status: AttendanceStatus,
        source: Optional[AttendanceSource] = None,
        check_in_time: Optional[datetime] = None,
        check_out_time: Optional[datetime] = None,
        correction_note: Optional[str] = None,
    ) -> AttendanceRecord:
        self._authorize_capture(actor, employee_id)
        employee = self._employee_directory.get(employee_id)
        if employee.status not in {'Active', 'OnLeave'}:
            raise AttendanceServiceError(
                'EMPLOYEE_STATUS_INVALID',
                'Attendance can only be captured for active or on-leave employees',
            )

        key = (employee_id, attendance_date)
        if key in self._employee_date_index:
            raise AttendanceServiceError(
                'ATTENDANCE_DUPLICATE',
                'Attendance record already exists for employee/date',
                [{'field': 'attendance_date', 'reason': 'duplicate for employee'}],
            )

        record = AttendanceRecord(
            employee_id=employee_id,
            attendance_date=attendance_date,
            attendance_status=attendance_status,
            source=source,
            check_in_time=check_in_time,
            check_out_time=check_out_time,
            correction_note=correction_note,
        )
        self._normalize_record(record)

        validated_payload = self._validated_event_payload(record)
        with self.outbox.transaction(self._records, self._employee_date_index):
            self._records[record.attendance_id] = record
            self._employee_date_index[key] = record.attendance_id
            self._queue_event(
                'AttendanceCaptured',
                {
                    'attendance_id': str(record.attendance_id),
                    'employee_id': str(record.employee_id),
                    'attendance_date': record.attendance_date.isoformat(),
                    'attendance_status': record.attendance_status.value,
                    'record_state': record.lifecycle_state.value,
                },
                idempotency_key=str(record.attendance_id),
            )
            if validated_payload is not None:
                self._queue_event('AttendanceValidated', validated_payload, idempotency_key=f'{record.attendance_id}:validated')
        self._emit_anomaly_event_if_needed(record)
        self._dispatch_outbox()
        self.observability.logger.info(
            'attendance.captured',
            context={'employee_id': str(record.employee_id), 'attendance_id': str(record.attendance_id)},
        )

        self._auto_validate(record)
        self._audit('attendance_record_created', actor, 'AttendanceRecord', str(record.attendance_id), {}, self._record_payload(record))
        return record

    def log_attendance(
        self,
        actor: Actor,
        *,
        employee_id: UUID,
        event_type: AttendanceLogEvent,
        occurred_at: datetime,
        source: Optional[AttendanceSource] = None,
    ) -> AttendanceRecord:
        self._authorize_capture(actor, employee_id)
        attendance_date = occurred_at.date()
        key = (employee_id, attendance_date)
        attendance_id = self._employee_date_index.get(key)

        if attendance_id is None:
            record = self.create_record(
                actor,
                employee_id=employee_id,
                attendance_date=attendance_date,
                attendance_status=AttendanceStatus.PRESENT,
                source=source,
                check_in_time=occurred_at if event_type == AttendanceLogEvent.CHECK_IN else None,
                check_out_time=occurred_at if event_type == AttendanceLogEvent.CHECK_OUT else None,
            )
        else:
            record = self._get_record(attendance_id)
            before = self._record_payload(record)
            if record.lifecycle_state == RecordState.LOCKED:
                raise AttendanceServiceError('ATTENDANCE_LOCKED', 'Locked records cannot be modified')
            if source is not None:
                record.source = source
            if event_type == AttendanceLogEvent.CHECK_IN:
                if record.check_in_time and occurred_at > record.check_in_time:
                    raise AttendanceServiceError('TIME_LOGIC_INVALID', 'check-in cannot move later than existing check-in')
                record.check_in_time = occurred_at
            if event_type == AttendanceLogEvent.CHECK_OUT:
                if record.check_out_time and occurred_at < record.check_out_time:
                    raise AttendanceServiceError('TIME_LOGIC_INVALID', 'check-out cannot move earlier than existing check-out')
                record.check_out_time = occurred_at
            self._normalize_record(record)
            record.lifecycle_state = RecordState.CAPTURED
            validated_payload = self._validated_event_payload(record)
            with self.outbox.transaction(self._records):
                self._records[record.attendance_id] = record
                if validated_payload is not None:
                    self._queue_event('AttendanceValidated', validated_payload, idempotency_key=f'{record.attendance_id}:validated')
            self._emit_anomaly_event_if_needed(record)
            self._audit('attendance_record_logged', actor, 'AttendanceRecord', str(record.attendance_id), before, self._record_payload(record))

        self._queue_event(
            'AttendanceLogged',
            {
                'attendance_id': str(record.attendance_id),
                'employee_id': str(record.employee_id),
                'event_type': event_type.value,
                'occurred_at': occurred_at.isoformat(),
            },
            idempotency_key=f'{record.attendance_id}:{event_type.value}:{occurred_at.isoformat()}',
        )
        self._dispatch_outbox()
        self.observability.logger.info(
            'attendance.logged',
            context={
                'employee_id': str(record.employee_id),
                'attendance_id': str(record.attendance_id),
                'event_type': event_type.value,
            },
        )
        return record

    def update_record(
        self,
        actor: Actor,
        attendance_id: UUID,
        *,
        attendance_status: Optional[AttendanceStatus] = None,
        check_in_time: Optional[datetime] = None,
        check_out_time: Optional[datetime] = None,
        correction_note: Optional[str] = None,
    ) -> AttendanceRecord:
        record = self._get_record(attendance_id)
        before = self._record_payload(record)
        self._authorize_capture(actor, record.employee_id)

        if record.lifecycle_state == RecordState.LOCKED:
            raise AttendanceServiceError('ATTENDANCE_LOCKED', 'Locked records cannot be modified')

        if attendance_status:
            record.attendance_status = attendance_status
        if check_in_time is not None:
            record.check_in_time = check_in_time
        if check_out_time is not None:
            record.check_out_time = check_out_time
        if correction_note is not None:
            record.correction_note = correction_note
        self._normalize_record(record)
        record.lifecycle_state = RecordState.CAPTURED
        validated_payload = self._validated_event_payload(record)
        with self.outbox.transaction(self._records):
            self._records[record.attendance_id] = record
            self._queue_event(
                'AttendanceCorrected',
                {
                    'attendance_id': str(record.attendance_id),
                    'employee_id': str(record.employee_id),
                    'attendance_date': record.attendance_date.isoformat(),
                    'attendance_status': record.attendance_status.value,
                    'record_state': record.lifecycle_state.value,
                },
                idempotency_key=f'{record.attendance_id}:corrected:{record.updated_at.isoformat()}',
            )
            if validated_payload is not None:
                self._queue_event('AttendanceValidated', validated_payload, idempotency_key=f'{record.attendance_id}:validated')
        self._emit_anomaly_event_if_needed(record)
        self._dispatch_outbox()
        self.observability.logger.info(
            'attendance.updated',
            context={'employee_id': str(record.employee_id), 'attendance_id': str(record.attendance_id)},
        )
        self._audit('attendance_record_corrected', actor, 'AttendanceRecord', str(record.attendance_id), before, self._record_payload(record))
        return record

    def submit_correction(
        self,
        actor: Actor,
        attendance_id: UUID,
        *,
        reason: str,
        requested_status: AttendanceStatus | None = None,
        requested_check_in_time: datetime | None = None,
        requested_check_out_time: datetime | None = None,
        requested_correction_note: str | None = None,
    ) -> AttendanceCorrection:
        record = self._get_record(attendance_id)
        self._authorize_read(actor, record.employee_id)
        employee = self._employee_directory.get(record.employee_id)
        if actor.role == 'Employee' and actor.employee_id != record.employee_id:
            raise AttendanceServiceError('FORBIDDEN', 'Employees can only request corrections for their own attendance')
        approver_id = employee.manager_employee_id or actor.employee_id
        correction = AttendanceCorrection(
            attendance_id=record.attendance_id,
            employee_id=record.employee_id,
            requested_by_employee_id=actor.employee_id or record.employee_id,
            approver_employee_id=approver_id,
            requested_status=requested_status,
            requested_check_in_time=requested_check_in_time,
            requested_check_out_time=requested_check_out_time,
            requested_correction_note=requested_correction_note,
            reason=reason,
        )
        approver_actor_id = str(approver_id) if approver_id else 'attendance-admin'
        try:
            workflow = self.workflow_service.start_workflow(
                tenant_id=self.tenant_id,
                definition_code='attendance_correction_approval',
                source_service='attendance-service',
                subject_type='AttendanceCorrection',
                subject_id=str(correction.correction_id),
                actor_id=str(actor.employee_id or record.employee_id),
                actor_type='user',
                context={
                    'approver_employee_id': approver_actor_id,
                    'escalation_assignee': 'attendance-admin',
                    'attendance_id': str(record.attendance_id),
                    'employee_id': str(record.employee_id),
                },
            )
        except WorkflowServiceError as exc:
            raise AttendanceServiceError('WORKFLOW_ERROR', exc.message) from exc
        correction.workflow_id = workflow['workflow_id']
        self._corrections[correction.correction_id] = correction
        self._queue_event('attendance.correction.submitted', self._correction_payload(correction), idempotency_key=str(correction.correction_id))
        self._dispatch_outbox()
        self._audit('attendance_correction_submitted', actor, 'AttendanceCorrection', str(correction.correction_id), {}, self._correction_payload(correction))
        return correction

    def review_correction(self, actor: Actor, correction_id: UUID, *, approve: bool, decision_note: str | None = None) -> AttendanceCorrection:
        correction = self._get_correction(correction_id)
        before = self._correction_payload(correction)
        self._authorize_validate_and_lock(actor, correction.employee_id)
        actor_id = str(actor.employee_id or actor.role)
        try:
            workflow = (
                self.workflow_service.approve_step(
                    correction.workflow_id or '',
                    tenant_id=self.tenant_id,
                    actor_id=actor_id,
                    actor_type='user',
                    actor_role=actor.role,
                    comment=decision_note,
                )
                if approve
                else self.workflow_service.reject_step(
                    correction.workflow_id or '',
                    tenant_id=self.tenant_id,
                    actor_id=actor_id,
                    actor_type='user',
                    actor_role=actor.role,
                    comment=decision_note,
                )
            )
        except WorkflowServiceError as exc:
            raise AttendanceServiceError('WORKFLOW_ERROR', exc.message) from exc

        correction.status = CorrectionStatus.APPROVED if approve else CorrectionStatus.REJECTED
        correction.decision_note = decision_note
        correction.decided_at = datetime.utcnow()
        correction.updated_at = datetime.utcnow()
        self._corrections[correction.correction_id] = correction

        if approve:
            record = self._get_record(correction.attendance_id)
            record_before = self._record_payload(record)
            self._apply_correction_to_record(record, correction)
            self._records[record.attendance_id] = record
            self._queue_event('attendance.correction.approved', {**self._correction_payload(correction), 'workflowStatus': workflow['status']}, idempotency_key=f'{correction.correction_id}:approved')
            self._emit_anomaly_event_if_needed(record)
            self._audit('attendance_correction_approved', actor, 'AttendanceRecord', str(record.attendance_id), record_before, self._record_payload(record))
        else:
            self._queue_event('attendance.correction.rejected', {**self._correction_payload(correction), 'workflowStatus': workflow['status']}, idempotency_key=f'{correction.correction_id}:rejected')

        self._dispatch_outbox()
        self._audit('attendance_correction_reviewed', actor, 'AttendanceCorrection', str(correction.correction_id), before, self._correction_payload(correction))
        return correction

    def approve_record(self, actor: Actor, attendance_id: UUID) -> AttendanceRecord:
        record = self._get_record(attendance_id)
        before = self._record_payload(record)
        self._authorize_validate_and_lock(actor, record.employee_id)
        if record.lifecycle_state == RecordState.LOCKED:
            raise AttendanceServiceError('ATTENDANCE_LOCKED', 'Locked records cannot be approved')
        if record.lifecycle_state == RecordState.CAPTURED:
            validated_payload = self._validated_event_payload(record)
            if validated_payload is not None:
                with self.outbox.transaction(self._records):
                    self._records[record.attendance_id] = record
                    self._queue_event('AttendanceValidated', validated_payload, idempotency_key=f'{record.attendance_id}:validated')
                self._dispatch_outbox()
        if record.lifecycle_state != RecordState.VALIDATED:
            raise AttendanceServiceError(
                'APPROVAL_REQUIRES_VALIDATED',
                'Only validated attendance records can be approved.',
                [{'attendance_id': str(record.attendance_id), 'lifecycle_state': record.lifecycle_state.value}],
            )
        record.lifecycle_state = RecordState.APPROVED
        record.updated_at = datetime.utcnow()
        with self.outbox.transaction(self._records):
            self._records[record.attendance_id] = record
            self._queue_event(
                'AttendanceApproved',
                {
                    'attendance_id': str(record.attendance_id),
                    'employee_id': str(record.employee_id),
                    'attendance_date': record.attendance_date.isoformat(),
                    'record_state': record.lifecycle_state.value,
                    'overtime_hours': str(record.overtime_hours) if record.overtime_hours is not None else None,
                },
                idempotency_key=f'{record.attendance_id}:approved',
            )
        self._dispatch_outbox()
        self.observability.logger.info(
            'attendance.approved',
            context={'employee_id': str(record.employee_id), 'attendance_id': str(record.attendance_id)},
        )
        self._audit('attendance_record_approved', actor, 'AttendanceRecord', str(record.attendance_id), before, self._record_payload(record))
        return record

    def get_record(self, actor: Actor, attendance_id: UUID) -> AttendanceRecord:
        record = self._get_record(attendance_id)
        self._authorize_read(actor, record.employee_id)
        return record

    def list_records(
        self,
        actor: Actor,
        *,
        employee_id: UUID,
        from_date: date,
        to_date: date,
    ) -> list[AttendanceRecord]:
        self._authorize_read(actor, employee_id)
        if to_date < from_date:
            raise AttendanceServiceError('DATE_RANGE_INVALID', 'to must be >= from')

        results = [
            record
            for record in self._records.values()
            if record.employee_id == employee_id and from_date <= record.attendance_date <= to_date
        ]
        return sorted(results, key=lambda x: x.attendance_date)

    def list_anomalies(
        self,
        actor: Actor,
        *,
        employee_id: UUID | None,
        from_date: date,
        to_date: date,
    ) -> dict:
        if to_date < from_date:
            raise AttendanceServiceError('DATE_RANGE_INVALID', 'to must be >= from')
        rows: list[dict] = []
        for record in self._records.values():
            if not (from_date <= record.attendance_date <= to_date):
                continue
            if employee_id and record.employee_id != employee_id:
                continue
            if not record.anomalies:
                continue
            self._authorize_read(actor, record.employee_id)
            rows.append(self._record_payload(record))
        rows.sort(key=lambda item: (item['attendanceDate'], item['employeeId']))
        return {
            'from': from_date.isoformat(),
            'to': to_date.isoformat(),
            'count': len(rows),
            'records': rows,
        }

    def aggregate_period(self, actor: Actor, *, employee_id: UUID, from_date: date, to_date: date) -> dict:
        rows = self.list_records(actor, employee_id=employee_id, from_date=from_date, to_date=to_date)
        total_hours = sum((record.total_hours or Decimal('0')) for record in rows)
        overtime_hours = sum((record.overtime_hours or Decimal('0')) for record in rows)
        scheduled_hours = sum((record.scheduled_hours or Decimal('0')) for record in rows)
        status_breakdown: dict[str, int] = {}
        anomaly_breakdown: dict[str, int] = {}
        for record in rows:
            status_breakdown[record.attendance_status.value] = status_breakdown.get(record.attendance_status.value, 0) + 1
            for anomaly in record.anomalies:
                anomaly_breakdown[anomaly.value] = anomaly_breakdown.get(anomaly.value, 0) + 1
        return {
            'employeeId': str(employee_id),
            'from': from_date.isoformat(),
            'to': to_date.isoformat(),
            'records': len(rows),
            'totalHours': str(total_hours.quantize(Decimal('0.01'))),
            'overtimeHours': str(overtime_hours.quantize(Decimal('0.01'))),
            'scheduledHours': str(scheduled_hours.quantize(Decimal('0.01'))),
            'statusBreakdown': status_breakdown,
            'anomalyBreakdown': anomaly_breakdown,
            'anomalousRecords': sum(1 for row in rows if row.anomalies),
            'completeRecords': sum(1 for row in rows if not row.anomalies),
            'rosteredDays': sum(1 for row in rows if row.roster_assignment_id is not None),
        }

    def lock_period(self, actor: Actor, *, period_id: str, from_date: date, to_date: date) -> dict:
        self._authorize_period_lock(actor)
        if to_date < from_date:
            raise AttendanceServiceError('DATE_RANGE_INVALID', 'to must be >= from')

        locked_before = [self._record_payload(record) for record in self._records.values() if from_date <= record.attendance_date <= to_date]
        locked_ids: list[str] = []
        touched_records: list[AttendanceRecord] = []
        for record in self._records.values():
            if from_date <= record.attendance_date <= to_date:
                if record.lifecycle_state not in {RecordState.APPROVED, RecordState.LOCKED}:
                    raise AttendanceServiceError(
                        'LOCK_REQUIRES_APPROVAL',
                        'All records in range must be approved before lock',
                    )
                record.lifecycle_state = RecordState.LOCKED
                record.updated_at = datetime.utcnow()
                locked_ids.append(str(record.attendance_id))
                touched_records.append(record)

        with self.outbox.transaction(self._records):
            for record in touched_records:
                self._records[record.attendance_id] = record
            self._queue_event(
                'AttendanceLocked',
                {'period_id': period_id, 'record_ids': locked_ids, 'record_state': RecordState.LOCKED.value},
                idempotency_key=f'{period_id}:locked',
            )
            self._queue_event(
                'AttendancePeriodClosed',
                {
                    'period_id': period_id,
                    'period_start': from_date.isoformat(),
                    'period_end': to_date.isoformat(),
                    'employee_count': len({str(record.employee_id) for record in touched_records}),
                    'closed_at': datetime.utcnow().isoformat(),
                },
                idempotency_key=f'{period_id}:closed',
            )
        self._dispatch_outbox()
        self.observability.logger.info(
            'attendance.period_locked',
            context={'period_id': period_id, 'locked_count': len(locked_ids)},
        )
        self.observability.logger.audit(
            'attendance_period_locked',
            actor=self._actor_payload(actor),
            entity='AttendancePeriod',
            entity_id=period_id,
            context={'tenant_id': self.tenant_id, 'before': {'records': locked_before}, 'after': {'period_id': period_id, 'record_ids': locked_ids, 'from_date': from_date.isoformat(), 'to_date': to_date.isoformat()}},
        )
        return {'periodId': period_id, 'lockedCount': len(locked_ids)}

    def sync_approved_leave(
        self,
        actor: Actor,
        *,
        employee_id: UUID,
        from_date: date,
        to_date: date,
        leave_request_id: str,
        leave_type: str,
    ) -> list[AttendanceRecord]:
        self._authorize_validate_and_lock(actor, employee_id)
        if to_date < from_date:
            raise AttendanceServiceError('DATE_RANGE_INVALID', 'from_date must be on or before to_date')

        records: list[AttendanceRecord] = []
        current = from_date
        while current <= to_date:
            key = (employee_id, current)
            attendance_id = self._employee_date_index.get(key)
            if attendance_id is None:
                record = self.create_record(
                    actor,
                    employee_id=employee_id,
                    attendance_date=current,
                    attendance_status=AttendanceStatus.ABSENT,
                    source=AttendanceSource.API_IMPORT,
                    correction_note=f'Approved leave: {leave_type} ({leave_request_id})',
                )
            else:
                record = self._get_record(attendance_id)
                if record.attendance_status in {AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY} and record.total_hours:
                    raise AttendanceServiceError(
                        'ATTENDANCE_CONFLICT',
                        'Cannot mark approved leave on a worked attendance date',
                        [{'attendance_id': str(record.attendance_id), 'attendance_date': current.isoformat()}],
                    )
                record.attendance_status = AttendanceStatus.ABSENT
                record.source = AttendanceSource.API_IMPORT
                record.check_in_time = None
                record.check_out_time = None
                record.correction_note = f'Approved leave: {leave_type} ({leave_request_id})'
                self._normalize_record(record)
                record.lifecycle_state = RecordState.APPROVED
                self._records[record.attendance_id] = record
            records.append(record)
            current = current + timedelta(days=1)

        self._queue_event(
            'AttendanceSyncedFromLeave',
            {
                'employee_id': str(employee_id),
                'leave_request_id': leave_request_id,
                'from_date': from_date.isoformat(),
                'to_date': to_date.isoformat(),
            },
            idempotency_key=leave_request_id,
        )
        self._dispatch_outbox()
        return records

    def get_employee_detail(self, actor: Actor, *, employee_id: UUID, period_start: date, period_end: date) -> dict:
        employee = self._employee_directory.get(employee_id)
        summary = self.get_summary(actor, employee_id=employee_id, period_start=period_start, period_end=period_end)
        records = self.list_records(actor, employee_id=employee_id, from_date=period_start, to_date=period_end)
        roster = self.list_roster(actor, employee_id=employee_id, from_date=period_start, to_date=period_end)
        return {
            'employee': {
                'employeeId': str(employee.employee_id),
                'status': employee.status,
                'departmentId': str(employee.department_id),
                'managerEmployeeId': str(employee.manager_employee_id) if employee.manager_employee_id else None,
            },
            'summary': summary,
            'records': [self._record_payload(record) for record in records],
            'roster': roster,
        }

    def get_summary(self, actor: Actor, *, employee_id: UUID, period_start: date, period_end: date) -> dict:
        summary = self.aggregate_period(actor, employee_id=employee_id, from_date=period_start, to_date=period_end)
        return {
            'employeeId': summary['employeeId'],
            'periodStart': period_start.isoformat(),
            'periodEnd': period_end.isoformat(),
            'totalHours': summary['totalHours'],
            'overtimeHours': summary['overtimeHours'],
            'scheduledHours': summary['scheduledHours'],
            'statusBreakdown': summary['statusBreakdown'],
            'records': summary['records'],
            'anomalyBreakdown': summary['anomalyBreakdown'],
            'anomalousRecords': summary['anomalousRecords'],
            'rosteredDays': summary['rosteredDays'],
        }

    def attendance_absence_alerts(self, actor: Actor, *, attendance_date: date) -> dict:
        """Return absence alert candidates for a specific date."""

        if actor.role not in {'Admin', 'Manager'}:
            raise AttendanceServiceError('FORBIDDEN', 'Not allowed to generate absence alerts')

        alert_records: list[dict] = []
        for record in self._records.values():
            if record.attendance_date != attendance_date or record.attendance_status != AttendanceStatus.ABSENT:
                continue

            employee = self._employee_directory.get(record.employee_id)
            if actor.role == 'Manager' and actor.department_id != employee.department_id:
                continue

            alert_records.append(
                {
                    'attendanceId': str(record.attendance_id),
                    'employeeId': str(record.employee_id),
                    'attendanceDate': record.attendance_date.isoformat(),
                    'attendanceStatus': record.attendance_status.value,
                    'managerEmployeeId': str(employee.manager_employee_id) if employee.manager_employee_id else None,
                }
            )

        self._queue_event(
            'AttendanceAbsenceAlertsGenerated',
            {
                'attendance_date': attendance_date.isoformat(),
                'count': len(alert_records),
            },
            idempotency_key=f'absence-alerts:{attendance_date.isoformat()}',
        )
        self._dispatch_outbox()
        self.observability.logger.info(
            'attendance.absence_alerts_generated',
            context={'attendance_date': attendance_date.isoformat(), 'count': len(alert_records)},
        )
        return {
            'attendanceDate': attendance_date.isoformat(),
            'alerts': alert_records,
            'count': len(alert_records),
        }

    def health_snapshot(self) -> dict:
        return self.observability.health_status(
            checks={
                'employee_directory': self._employee_directory.__class__.__name__,
                'records': len(self._records),
                'shifts': len(self._shifts),
                'rosters': len(self._rosters),
                'corrections': len(self._corrections),
            }
        )

    def _get_record(self, attendance_id: UUID) -> AttendanceRecord:
        record = self._records.get(attendance_id)
        if not record:
            raise AttendanceServiceError('ATTENDANCE_NOT_FOUND', 'Attendance record not found')
        return record

    def _get_shift(self, shift_id: UUID) -> Shift:
        shift = self._shifts.get(shift_id)
        if not shift:
            raise AttendanceServiceError('SHIFT_NOT_FOUND', 'Shift not found')
        return shift

    def _get_schedule(self, schedule_id: UUID) -> Schedule:
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            raise AttendanceServiceError('SCHEDULE_NOT_FOUND', 'Schedule not found')
        return schedule

    def _get_correction(self, correction_id: UUID) -> AttendanceCorrection:
        correction = self._corrections.get(correction_id)
        if not correction:
            raise AttendanceServiceError('CORRECTION_NOT_FOUND', 'Attendance correction not found')
        return correction

    def _find_roster(self, employee_id: UUID, attendance_date: date) -> RosterAssignment | None:
        roster_id = self._roster_employee_date_index.get((employee_id, attendance_date))
        return self._rosters.get(roster_id) if roster_id else None

    def _has_published_schedule(self, department_id: UUID | None, attendance_date: date) -> bool:
        for schedule in self._schedules.values():
            if schedule.status != ScheduleStatus.PUBLISHED:
                continue
            if schedule.department_id and schedule.department_id != department_id:
                continue
            if schedule.effective_from <= attendance_date <= schedule.effective_to:
                return True
        return False

    def _resolve_overtime_rule(self, department_id: UUID | None) -> OvertimeRule | None:
        department_rule: OvertimeRule | None = None
        fallback_rule: OvertimeRule | None = None
        for rule in self._overtime_rules.values():
            if not rule.active:
                continue
            if rule.department_id == department_id:
                department_rule = rule
                break
            if rule.department_id is None and fallback_rule is None:
                fallback_rule = rule
        return department_rule or fallback_rule

    def _normalize_record(self, record: AttendanceRecord) -> None:
        employee = self._employee_directory.get(record.employee_id)
        roster = self._find_roster(record.employee_id, record.attendance_date)
        shift = self._get_shift(roster.shift_id) if roster else None
        rule = self._resolve_overtime_rule(employee.department_id)
        try:
            record.validate_time_consistency()
            record.recalculate_total_hours()
            anomalies = record.derive_base_anomalies(late_after=self._late_after)
            record.roster_assignment_id = roster.roster_id if roster else None
            record.scheduled_shift_id = shift.shift_id if shift else None
            record.scheduled_start_time = shift.start_time if shift else None
            record.scheduled_end_time = shift.end_time if shift else None
            record.scheduled_hours = shift.scheduled_hours() if shift else None
            record.overtime_hours = Decimal('0.00')
            schedule_active = self._has_published_schedule(employee.department_id, record.attendance_date)
            if roster is None and schedule_active and record.attendance_status not in {AttendanceStatus.ABSENT, AttendanceStatus.HOLIDAY}:
                anomalies.extend([AttendanceAnomaly.MISSING_ROSTER, AttendanceAnomaly.UNSCHEDULED_ATTENDANCE])
            if shift is not None and record.check_in_time is not None:
                scheduled_start = datetime.combine(record.attendance_date, shift.start_time)
                if record.check_in_time > scheduled_start + timedelta(minutes=shift.late_grace_minutes):
                    if AttendanceAnomaly.LATE not in anomalies:
                        anomalies.append(AttendanceAnomaly.LATE)
                    if record.attendance_status == AttendanceStatus.PRESENT:
                        record.attendance_status = AttendanceStatus.LATE
            if shift is not None and record.check_out_time is not None:
                scheduled_end = datetime.combine(record.attendance_date, shift.end_time)
                if record.check_out_time < scheduled_end:
                    anomalies.append(AttendanceAnomaly.EARLY_DEPARTURE)
            if shift is not None and record.total_hours is not None and record.scheduled_hours is not None and record.total_hours < record.scheduled_hours:
                anomalies.append(AttendanceAnomaly.SHORT_SHIFT)
            if rule is not None and record.total_hours is not None:
                overtime = record.total_hours - rule.applies_after_hours
                if overtime > Decimal('0'):
                    capped_overtime = min(overtime, rule.max_overtime_hours)
                    record.overtime_hours = capped_overtime.quantize(Decimal('0.01'))
                    if record.overtime_hours > Decimal('0'):
                        anomalies.append(AttendanceAnomaly.OVERTIME)
            record.anomalies = list(dict.fromkeys(anomalies))
            record.updated_at = datetime.utcnow()
        except ValueError as exc:
            raise AttendanceServiceError(
                'TIME_LOGIC_INVALID',
                'Attendance time logic is invalid.',
                [{'reason': str(exc)}],
            ) from exc

    def _apply_correction_to_record(self, record: AttendanceRecord, correction: AttendanceCorrection) -> None:
        if correction.requested_status is not None:
            record.attendance_status = correction.requested_status
        if correction.requested_check_in_time is not None:
            record.check_in_time = correction.requested_check_in_time
        if correction.requested_check_out_time is not None:
            record.check_out_time = correction.requested_check_out_time
        if correction.requested_correction_note is not None:
            record.correction_note = correction.requested_correction_note
        self._normalize_record(record)
        record.lifecycle_state = RecordState.VALIDATED if self._validated_event_payload(record) else RecordState.CAPTURED
        self._queue_event('AttendanceCorrected', self._record_payload(record), idempotency_key=f'{record.attendance_id}:workflow-correction:{correction.correction_id}')

    def _emit_anomaly_event_if_needed(self, record: AttendanceRecord) -> None:
        if not record.anomalies:
            return
        self._queue_event(
            'attendance.anomaly.detected',
            {
                'attendance_id': str(record.attendance_id),
                'employee_id': str(record.employee_id),
                'attendance_date': record.attendance_date.isoformat(),
                'anomalies': [item.value for item in record.anomalies],
                'roster_assignment_id': str(record.roster_assignment_id) if record.roster_assignment_id else None,
                'scheduled_shift_id': str(record.scheduled_shift_id) if record.scheduled_shift_id else None,
            },
            idempotency_key=f'{record.attendance_id}:anomalies:{"-".join(item.value for item in record.anomalies)}',
        )

    def _auto_validate(self, record: AttendanceRecord) -> None:
        """Compatibility hook: records are normalized and validation events are queued before this call."""
        return None

    def _validated_event_payload(self, record: AttendanceRecord) -> dict | None:
        if record.attendance_status in {AttendanceStatus.ABSENT, AttendanceStatus.HOLIDAY} or record.total_hours is not None:
            record.lifecycle_state = RecordState.VALIDATED
            record.updated_at = datetime.utcnow()
            return {
                'attendance_id': str(record.attendance_id),
                'employee_id': str(record.employee_id),
                'attendance_date': record.attendance_date.isoformat(),
                'record_state': record.lifecycle_state.value,
                'total_hours': str(record.total_hours) if record.total_hours is not None else None,
                'anomalies': [anomaly.value for anomaly in record.anomalies],
                'overtime_hours': str(record.overtime_hours) if record.overtime_hours is not None else None,
            }
        return None

    def _queue_event(self, legacy_event_name: str, data: dict[str, object], *, idempotency_key: str | None = None) -> None:
        self.outbox.enqueue(legacy_event_name=legacy_event_name, data=data, idempotency_key=idempotency_key)

    def _dispatch_outbox(self) -> None:
        self.outbox.dispatch_pending(self.events.append)

    def _authorize_capture(self, actor: Actor, target_employee_id: UUID) -> None:
        if actor.role == 'Admin':
            return
        if actor.role == 'Employee' and actor.employee_id == target_employee_id:
            return
        if actor.role == 'Manager':
            target = self._employee_directory.get(target_employee_id)
            if actor.department_id and actor.department_id == target.department_id:
                return
        raise AttendanceServiceError('FORBIDDEN', 'Not allowed to capture attendance for target employee')

    def _authorize_validate_and_lock(self, actor: Actor, target_employee_id: UUID) -> None:
        if actor.role == 'Admin':
            return
        if actor.role == 'Manager':
            target = self._employee_directory.get(target_employee_id)
            if actor.department_id and actor.department_id == target.department_id:
                return
        raise AttendanceServiceError('FORBIDDEN', 'Not allowed to validate/lock attendance')

    def _authorize_read(self, actor: Actor, target_employee_id: UUID) -> None:
        if actor.role == 'Admin':
            return
        if actor.role == 'Employee' and actor.employee_id == target_employee_id:
            return
        if actor.role == 'Manager':
            target = self._employee_directory.get(target_employee_id)
            if actor.department_id and actor.department_id == target.department_id:
                return
        raise AttendanceServiceError('FORBIDDEN', 'Not allowed to read attendance for target employee')

    def _authorize_period_lock(self, actor: Actor) -> None:
        if actor.role in {'Admin', 'Manager'}:
            return
        raise AttendanceServiceError('FORBIDDEN', 'Not allowed to lock attendance periods')

    def _authorize_schedule_admin(self, actor: Actor, *, department_id: UUID | None) -> None:
        if actor.role == 'Admin':
            return
        if actor.role == 'Manager' and department_id is not None and actor.department_id == department_id:
            return
        raise AttendanceServiceError('FORBIDDEN', 'Not allowed to manage workforce scheduling configuration')
