from datetime import date, datetime
from uuid import uuid4

import unittest

from attendance_service import (
    Actor,
    AttendanceAnomaly,
    AttendanceLogEvent,
    AttendanceService,
    AttendanceServiceError,
    AttendanceStatus,
    CorrectionStatus,
    EmployeeSnapshot,
    InMemoryEmployeeDirectory,
    RecordState,
)
from attendance_service.api import (
    get_attendance_absence_alerts,
    get_attendance_anomalies,
    get_attendance_record,
    get_attendance_records,
    get_attendance_summary,
    get_roster,
    patch_attendance_record,
    post_attendance_approval,
    post_attendance_correction,
    post_attendance_correction_decision,
    post_attendance_log,
    post_attendance_period_lock,
    post_attendance_records,
    post_overtime_rule,
    post_roster_assignment,
    post_schedule,
    post_schedule_publish,
    post_shift,
)


class AttendanceServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dep_a = uuid4()
        self.dep_b = uuid4()
        self.emp_1 = uuid4()
        self.emp_2 = uuid4()
        self.directory = InMemoryEmployeeDirectory(
            [
                EmployeeSnapshot(employee_id=self.emp_1, status="Active", department_id=self.dep_a),
                EmployeeSnapshot(employee_id=self.emp_2, status="Active", department_id=self.dep_b),
            ]
        )
        self.service = AttendanceService(self.directory)

    def test_employee_can_create_own_record(self) -> None:
        actor = Actor(employee_id=self.emp_1, role="Employee")
        record = self.service.create_record(
            actor,
            employee_id=self.emp_1,
            attendance_date=date(2026, 1, 2),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 1, 2, 9, 0),
            check_out_time=datetime(2026, 1, 2, 18, 0),
        )
        self.assertEqual(record.total_hours, 9)
        self.assertEqual(record.lifecycle_state, RecordState.VALIDATED)
        self.assertEqual(record.anomalies, [])

    def test_employee_cannot_create_other_employee_record(self) -> None:
        actor = Actor(employee_id=self.emp_1, role="Employee")
        with self.assertRaises(AttendanceServiceError):
            self.service.create_record(
                actor,
                employee_id=self.emp_2,
                attendance_date=date(2026, 1, 2),
                attendance_status=AttendanceStatus.PRESENT,
            )

    def test_manager_can_approve_same_department(self) -> None:
        manager = Actor(employee_id=uuid4(), role="Manager", department_id=self.dep_a)
        record = self.service.create_record(
            manager,
            employee_id=self.emp_1,
            attendance_date=date(2026, 2, 10),
            attendance_status=AttendanceStatus.ABSENT,
        )
        updated = self.service.approve_record(manager, record.attendance_id)
        self.assertEqual(updated.lifecycle_state, RecordState.APPROVED)

    def test_cannot_approve_incomplete_captured_record(self) -> None:
        admin = Actor(employee_id=uuid4(), role="Admin")
        record = self.service.create_record(
            admin,
            employee_id=self.emp_1,
            attendance_date=date(2026, 2, 11),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 2, 11, 9, 0),
        )

        with self.assertRaises(AttendanceServiceError) as context:
            self.service.approve_record(admin, record.attendance_id)

        self.assertEqual(context.exception.code, "APPROVAL_REQUIRES_VALIDATED")
        self.assertEqual(record.lifecycle_state, RecordState.CAPTURED)

    def test_period_lock_requires_approval(self) -> None:
        admin = Actor(employee_id=uuid4(), role="Admin")
        self.service.create_record(
            admin,
            employee_id=self.emp_1,
            attendance_date=date(2026, 2, 10),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 2, 10, 10, 0),
            check_out_time=datetime(2026, 2, 10, 14, 0),
        )
        with self.assertRaises(AttendanceServiceError):
            self.service.lock_period(admin, period_id="2026-02", from_date=date(2026, 2, 1), to_date=date(2026, 2, 28))

    def test_summary_aggregates_hours_status_and_anomalies(self) -> None:
        admin = Actor(employee_id=uuid4(), role="Admin")
        r1 = self.service.create_record(
            admin,
            employee_id=self.emp_1,
            attendance_date=date(2026, 3, 1),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 3, 1, 9, 0),
            check_out_time=datetime(2026, 3, 1, 17, 0),
        )
        r2 = self.service.create_record(
            admin,
            employee_id=self.emp_1,
            attendance_date=date(2026, 3, 2),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 3, 2, 9, 0),
        )
        self.service.approve_record(admin, r1.attendance_id)

        summary = self.service.get_summary(
            admin, employee_id=self.emp_1, period_start=date(2026, 3, 1), period_end=date(2026, 3, 31)
        )
        self.assertEqual(summary["totalHours"], "8.00")
        self.assertEqual(summary["statusBreakdown"]["Present"], 2)
        self.assertEqual(summary["anomalyBreakdown"]["MissingCheckOut"], 1)
        self.assertEqual(summary["anomalousRecords"], 1)

    def test_log_attendance_handles_check_in_then_check_out(self) -> None:
        actor = Actor(employee_id=self.emp_1, role="Employee")
        check_in_record = self.service.log_attendance(
            actor,
            employee_id=self.emp_1,
            event_type=AttendanceLogEvent.CHECK_IN,
            occurred_at=datetime(2026, 4, 4, 9, 5),
        )
        self.assertIn(AttendanceAnomaly.MISSING_CHECK_OUT, check_in_record.anomalies)

        completed_record = self.service.log_attendance(
            actor,
            employee_id=self.emp_1,
            event_type=AttendanceLogEvent.CHECK_OUT,
            occurred_at=datetime(2026, 4, 4, 17, 45),
        )
        self.assertEqual(str(completed_record.total_hours), "8.67")
        self.assertEqual(completed_record.anomalies, [])
        self.assertEqual(completed_record.lifecycle_state, RecordState.VALIDATED)

    def test_late_check_in_sets_late_status_and_anomaly(self) -> None:
        actor = Actor(employee_id=self.emp_1, role="Employee")
        record = self.service.log_attendance(
            actor,
            employee_id=self.emp_1,
            event_type=AttendanceLogEvent.CHECK_IN,
            occurred_at=datetime(2026, 4, 5, 9, 16),
        )
        self.assertEqual(record.attendance_status, AttendanceStatus.LATE)
        self.assertIn(AttendanceAnomaly.LATE, record.anomalies)

    def test_exact_threshold_is_not_late(self) -> None:
        actor = Actor(employee_id=self.emp_1, role="Employee")
        record = self.service.log_attendance(
            actor,
            employee_id=self.emp_1,
            event_type=AttendanceLogEvent.CHECK_IN,
            occurred_at=datetime(2026, 4, 5, 9, 15),
        )
        self.assertEqual(record.attendance_status, AttendanceStatus.PRESENT)
        self.assertNotIn(AttendanceAnomaly.LATE, record.anomalies)

    def test_update_correction_clears_missing_anomaly(self) -> None:
        admin = Actor(employee_id=uuid4(), role="Admin")
        record = self.service.create_record(
            admin,
            employee_id=self.emp_1,
            attendance_date=date(2026, 4, 6),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 4, 6, 9, 0),
        )
        corrected = self.service.update_record(
            admin,
            record.attendance_id,
            check_out_time=datetime(2026, 4, 6, 17, 0),
            correction_note="Manager approved manual checkout",
        )
        self.assertEqual(corrected.anomalies, [])
        self.assertEqual(corrected.correction_note, "Manager approved manual checkout")

    def test_time_logic_validation_rejects_invalid_ranges(self) -> None:
        admin = Actor(employee_id=uuid4(), role="Admin")
        with self.assertRaises(AttendanceServiceError) as context:
            self.service.create_record(
                admin,
                employee_id=self.emp_1,
                attendance_date=date(2026, 4, 7),
                attendance_status=AttendanceStatus.PRESENT,
                check_in_time=datetime(2026, 4, 7, 18, 0),
                check_out_time=datetime(2026, 4, 7, 9, 0),
            )
        self.assertEqual(context.exception.code, "TIME_LOGIC_INVALID")

    def test_time_logic_validation_rejects_cross_date_punch(self) -> None:
        admin = Actor(employee_id=uuid4(), role="Admin")
        with self.assertRaises(AttendanceServiceError) as context:
            self.service.create_record(
                admin,
                employee_id=self.emp_1,
                attendance_date=date(2026, 4, 7),
                attendance_status=AttendanceStatus.PRESENT,
                check_in_time=datetime(2026, 4, 8, 9, 0),
            )
        self.assertEqual(context.exception.code, "TIME_LOGIC_INVALID")

    def test_absence_alerts_returns_absent_records_for_admin(self) -> None:
        admin = Actor(employee_id=uuid4(), role="Admin")
        self.service.create_record(
            admin,
            employee_id=self.emp_1,
            attendance_date=date(2026, 4, 10),
            attendance_status=AttendanceStatus.ABSENT,
        )
        self.service.create_record(
            admin,
            employee_id=self.emp_2,
            attendance_date=date(2026, 4, 10),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 4, 10, 9, 0),
            check_out_time=datetime(2026, 4, 10, 18, 0),
        )

        alerts = self.service.attendance_absence_alerts(admin, attendance_date=date(2026, 4, 10))
        self.assertEqual(alerts["count"], 1)
        self.assertEqual(alerts["alerts"][0]["employeeId"], str(self.emp_1))
        self.assertEqual(self.service.events[-1]["type"], "AttendanceAbsenceAlertsGenerated")

    def test_absence_alerts_scoped_to_manager_department(self) -> None:
        admin = Actor(employee_id=uuid4(), role="Admin")
        self.service.create_record(
            admin,
            employee_id=self.emp_1,
            attendance_date=date(2026, 4, 11),
            attendance_status=AttendanceStatus.ABSENT,
        )
        self.service.create_record(
            admin,
            employee_id=self.emp_2,
            attendance_date=date(2026, 4, 11),
            attendance_status=AttendanceStatus.ABSENT,
        )

        manager = Actor(employee_id=uuid4(), role="Manager", department_id=self.dep_a)
        alerts = self.service.attendance_absence_alerts(manager, attendance_date=date(2026, 4, 11))
        self.assertEqual(alerts["count"], 1)
        self.assertEqual(alerts["alerts"][0]["employeeId"], str(self.emp_1))

    def test_api_uses_error_envelope(self) -> None:
        actor = Actor(employee_id=self.emp_1, role="Employee")
        status, payload = post_attendance_records(
            self.service,
            actor,
            {
                "employee_id": str(self.emp_2),
                "attendance_date": "2026-01-01",
                "attendance_status": "Present",
            },
            trace_id="trace-1",
        )
        self.assertEqual(status, 403)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["meta"]["request_id"], "trace-1")

    def test_api_maps_employee_not_found_to_404(self) -> None:
        admin = Actor(employee_id=self.emp_1, role="Admin")
        status, payload = post_attendance_records(
            self.service,
            admin,
            {
                "employee_id": str(uuid4()),
                "attendance_date": "2026-01-01",
                "attendance_status": "Present",
            },
            trace_id="trace-404",
        )
        self.assertEqual(status, 404)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["meta"]["request_id"], "trace-404")

    def test_api_maps_invalid_payload_to_422(self) -> None:
        admin = Actor(employee_id=self.emp_1, role="Admin")
        status, payload = post_attendance_records(
            self.service,
            admin,
            {
                "employee_id": str(self.emp_1),
                "attendance_date": "not-a-date",
                "attendance_status": "Present",
            },
            trace_id="trace-422",
        )
        self.assertEqual(status, 422)
        self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")

    def test_api_log_attendance_returns_serialized_anomalies(self) -> None:
        actor = Actor(employee_id=self.emp_1, role="Employee")
        status, payload = post_attendance_log(
            self.service,
            actor,
            {
                "employee_id": str(self.emp_1),
                "event_type": "CheckIn",
                "occurred_at": "2026-05-02T09:20:00",
            },
            trace_id="trace-log",
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "success")
        self.assertIn("Late", payload["data"]["anomalies"])
        self.assertIn("MissingCheckOut", payload["data"]["anomalies"])

    def test_api_fetch_records_returns_aggregation(self) -> None:
        admin = Actor(employee_id=uuid4(), role="Admin")
        self.service.create_record(
            admin,
            employee_id=self.emp_1,
            attendance_date=date(2026, 5, 3),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 5, 3, 9, 0),
            check_out_time=datetime(2026, 5, 3, 17, 0),
        )
        self.service.create_record(
            admin,
            employee_id=self.emp_1,
            attendance_date=date(2026, 5, 4),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 5, 4, 9, 0),
        )
        status, payload = get_attendance_records(
            self.service,
            admin,
            {
                "employee_id": str(self.emp_1),
                "from_date": "2026-05-01",
                "to_date": "2026-05-31",
            },
            trace_id="trace-fetch",
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["data"]["records"]), 2)
        self.assertEqual(payload["data"]["aggregation"]["anomalyBreakdown"]["MissingCheckOut"], 1)
        self.assertEqual(payload["meta"]["pagination"]["count"], 2)

    def test_api_update_correction_returns_cleared_anomalies(self) -> None:
        admin = Actor(employee_id=uuid4(), role="Admin")
        record = self.service.create_record(
            admin,
            employee_id=self.emp_1,
            attendance_date=date(2026, 5, 5),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 5, 5, 9, 0),
        )
        status, payload = patch_attendance_record(
            self.service,
            admin,
            str(record.attendance_id),
            {
                "check_out_time": "2026-05-05T17:30:00",
                "correction_note": "Backfilled missing check-out",
            },
            trace_id="trace-patch",
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["anomalies"], [])
        self.assertEqual(payload["data"]["correction_note"], "Backfilled missing check-out")

    def test_attendance_observability_records_metrics_and_health(self) -> None:
        admin = Actor(employee_id=self.emp_1, role="Admin")
        status, _ = post_attendance_records(
            self.service,
            admin,
            {
                "employee_id": str(self.emp_1),
                "attendance_date": "2026-05-01",
                "attendance_status": "Present",
            },
            trace_id="trace-attendance",
        )
        self.assertEqual(status, 201)
        metrics = self.service.observability.metrics.snapshot()
        self.assertEqual(metrics["request_count"], 1)
        self.assertEqual(metrics["recent_requests"][0]["trace_id"], "trace-attendance")
        self.assertEqual(self.service.health_snapshot()["status"], "ok")

    def test_api_supports_read_approve_summary_alerts_and_lock_workflow(self) -> None:
        admin = Actor(employee_id=uuid4(), role="Admin")
        status, created = post_attendance_records(
            self.service,
            admin,
            {
                "employee_id": str(self.emp_1),
                "attendance_date": "2026-05-06",
                "attendance_status": "Absent",
            },
            trace_id="trace-create-api",
        )
        self.assertEqual(status, 201)

        status, fetched = get_attendance_record(
            self.service,
            admin,
            created["data"]["attendance_id"],
            trace_id="trace-get-api",
        )
        self.assertEqual(status, 200)
        self.assertEqual(fetched["data"]["attendance_id"], created["data"]["attendance_id"])

        status, approved = post_attendance_approval(
            self.service,
            admin,
            created["data"]["attendance_id"],
            trace_id="trace-approve-api",
        )
        self.assertEqual(status, 200)
        self.assertEqual(approved["data"]["lifecycle_state"], "Approved")

        status, summary = get_attendance_summary(
            self.service,
            admin,
            {
                "employee_id": str(self.emp_1),
                "period_start": "2026-05-01",
                "period_end": "2026-05-31",
            },
            trace_id="trace-summary-api",
        )
        self.assertEqual(status, 200)
        self.assertEqual(summary["data"]["records"], 1)

        status, alerts = get_attendance_absence_alerts(
            self.service,
            admin,
            {"attendance_date": "2026-05-06"},
            trace_id="trace-alerts-api",
        )
        self.assertEqual(status, 200)
        self.assertEqual(alerts["data"]["count"], 1)

        status, payload = post_attendance_period_lock(
            self.service,
            admin,
            {
                "period_id": "2026-05",
                "from_date": "2026-05-01",
                "to_date": "2026-05-31",
            },
            trace_id="trace-lock-api",
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["lockedCount"], 1)

    def test_api_approval_rejects_incomplete_record(self) -> None:
        admin = Actor(employee_id=uuid4(), role="Admin")
        record = self.service.create_record(
            admin,
            employee_id=self.emp_1,
            attendance_date=date(2026, 5, 7),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 5, 7, 9, 0),
        )

        status, payload = post_attendance_approval(
            self.service,
            admin,
            str(record.attendance_id),
            trace_id="trace-approve-invalid",
        )

        self.assertEqual(status, 409)
        self.assertEqual(payload["error"]["code"], "APPROVAL_REQUIRES_VALIDATED")


    def test_roster_and_overtime_drive_anomaly_detection(self) -> None:
        admin = Actor(employee_id=uuid4(), role="Admin")
        shift = self.service.create_shift(
            admin,
            code="DAY",
            name="Day Shift",
            start_time=datetime(2026, 1, 1, 9, 0).time(),
            end_time=datetime(2026, 1, 1, 17, 0).time(),
            break_minutes=60,
            department_id=self.dep_a,
        )
        schedule = self.service.create_schedule(
            admin,
            name="Week 1",
            effective_from=date(2026, 6, 1),
            effective_to=date(2026, 6, 7),
            department_id=self.dep_a,
        )
        self.service.publish_schedule(admin, schedule.schedule_id)
        self.service.assign_roster(
            admin,
            employee_id=self.emp_1,
            shift_id=shift.shift_id,
            schedule_id=schedule.schedule_id,
            roster_date=date(2026, 6, 2),
        )
        self.service.set_overtime_rule(
            admin,
            name="Default OT",
            applies_after_hours=8,
            multiplier=1.5,
            max_overtime_hours=3,
            department_id=self.dep_a,
        )

        record = self.service.create_record(
            admin,
            employee_id=self.emp_1,
            attendance_date=date(2026, 6, 2),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 6, 2, 9, 45),
            check_out_time=datetime(2026, 6, 2, 18, 30),
        )

        self.assertEqual(str(record.overtime_hours), "0.75")
        self.assertEqual(str(record.scheduled_hours), "7.0")
        self.assertIn(AttendanceAnomaly.LATE, record.anomalies)
        self.assertIn(AttendanceAnomaly.OVERTIME, record.anomalies)
        self.assertEqual(record.roster_assignment_id is not None, True)

    def test_missing_roster_anomaly_and_anomaly_listing(self) -> None:
        admin = Actor(employee_id=uuid4(), role="Admin")
        schedule = self.service.create_schedule(
            admin,
            name="Week 1",
            effective_from=date(2026, 6, 1),
            effective_to=date(2026, 6, 7),
            department_id=self.dep_a,
        )
        self.service.publish_schedule(admin, schedule.schedule_id)
        self.service.create_record(
            admin,
            employee_id=self.emp_1,
            attendance_date=date(2026, 6, 3),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 6, 3, 9, 0),
            check_out_time=datetime(2026, 6, 3, 17, 0),
        )

        anomalies = self.service.list_anomalies(
            admin,
            employee_id=self.emp_1,
            from_date=date(2026, 6, 1),
            to_date=date(2026, 6, 30),
        )
        self.assertEqual(anomalies["count"], 1)
        self.assertIn("MissingRoster", anomalies["records"][0]["anomalies"])
        self.assertEqual(self.service.events[-1]["type"], "attendance.anomaly.detected")

    def test_correction_workflow_approval_updates_record(self) -> None:
        manager_id = uuid4()
        self.directory = InMemoryEmployeeDirectory(
            [
                EmployeeSnapshot(employee_id=self.emp_1, status="Active", department_id=self.dep_a, manager_employee_id=manager_id),
                EmployeeSnapshot(employee_id=self.emp_2, status="Active", department_id=self.dep_b),
            ]
        )
        self.service = AttendanceService(self.directory)
        employee_actor = Actor(employee_id=self.emp_1, role="Employee")
        manager_actor = Actor(employee_id=manager_id, role="Manager", department_id=self.dep_a)
        record = self.service.create_record(
            employee_actor,
            employee_id=self.emp_1,
            attendance_date=date(2026, 6, 4),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 6, 4, 9, 0),
        )

        correction = self.service.submit_correction(
            employee_actor,
            record.attendance_id,
            reason="Missed check-out on mobile app",
            requested_check_out_time=datetime(2026, 6, 4, 17, 30),
            requested_correction_note="Manager reviewed kiosk outage",
        )
        self.assertIsNotNone(correction.workflow_id)

        reviewed = self.service.review_correction(
            manager_actor,
            correction.correction_id,
            approve=True,
            decision_note="Approved after roster verification",
        )
        updated = self.service.get_record(manager_actor, record.attendance_id)
        self.assertEqual(reviewed.status, CorrectionStatus.APPROVED)
        self.assertEqual(updated.anomalies, [])
        self.assertEqual(updated.check_out_time, datetime(2026, 6, 4, 17, 30))
        self.assertEqual(updated.lifecycle_state, RecordState.VALIDATED)

    def test_api_supports_workforce_scheduling_and_correction_flows(self) -> None:
        admin = Actor(employee_id=uuid4(), role="Admin")
        manager_id = uuid4()
        self.directory = InMemoryEmployeeDirectory(
            [
                EmployeeSnapshot(employee_id=self.emp_1, status="Active", department_id=self.dep_a, manager_employee_id=manager_id),
                EmployeeSnapshot(employee_id=self.emp_2, status="Active", department_id=self.dep_b),
            ]
        )
        self.service = AttendanceService(self.directory)
        employee_actor = Actor(employee_id=self.emp_1, role="Employee")
        manager_actor = Actor(employee_id=manager_id, role="Manager", department_id=self.dep_a)

        status, shift_payload = post_shift(
            self.service,
            admin,
            {
                "code": "DAY",
                "name": "Day Shift",
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "break_minutes": 60,
                "department_id": str(self.dep_a),
            },
            trace_id="trace-shift",
        )
        self.assertEqual(status, 201)

        status, schedule_payload = post_schedule(
            self.service,
            admin,
            {
                "name": "Week 2",
                "effective_from": "2026-06-08",
                "effective_to": "2026-06-14",
                "department_id": str(self.dep_a),
            },
            trace_id="trace-schedule",
        )
        self.assertEqual(status, 201)

        status, published = post_schedule_publish(
            self.service,
            admin,
            schedule_payload["data"]["schedule_id"],
            trace_id="trace-schedule-publish",
        )
        self.assertEqual(status, 200)
        self.assertEqual(published["data"]["status"], "Published")

        status, _ = post_overtime_rule(
            self.service,
            admin,
            {
                "name": "Dept OT",
                "applies_after_hours": "8",
                "multiplier": "1.5",
                "max_overtime_hours": "2",
                "department_id": str(self.dep_a),
            },
            trace_id="trace-ot",
        )
        self.assertEqual(status, 201)

        status, roster_payload = post_roster_assignment(
            self.service,
            admin,
            {
                "employee_id": str(self.emp_1),
                "shift_id": shift_payload["data"]["shift_id"],
                "schedule_id": schedule_payload["data"]["schedule_id"],
                "roster_date": "2026-06-09",
            },
            trace_id="trace-roster",
        )
        self.assertEqual(status, 201)
        self.assertEqual(roster_payload["data"]["status"], "Published")

        status, roster_list = get_roster(
            self.service,
            manager_actor,
            {
                "employee_id": str(self.emp_1),
                "from_date": "2026-06-08",
                "to_date": "2026-06-10",
            },
            trace_id="trace-roster-list",
        )
        self.assertEqual(status, 200)
        self.assertEqual(roster_list["meta"]["pagination"]["count"], 1)

        record = self.service.create_record(
            employee_actor,
            employee_id=self.emp_1,
            attendance_date=date(2026, 6, 9),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 6, 9, 9, 30),
            check_out_time=datetime(2026, 6, 9, 18, 15),
        )
        status, anomalies = get_attendance_anomalies(
            self.service,
            manager_actor,
            {
                "employee_id": str(self.emp_1),
                "from_date": "2026-06-01",
                "to_date": "2026-06-30",
            },
            trace_id="trace-anomalies",
        )
        self.assertEqual(status, 200)
        self.assertEqual(anomalies["data"]["count"], 1)

        missing_record = self.service.create_record(
            employee_actor,
            employee_id=self.emp_1,
            attendance_date=date(2026, 6, 10),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 6, 10, 9, 0),
        )
        status, correction_payload = post_attendance_correction(
            self.service,
            employee_actor,
            str(missing_record.attendance_id),
            {
                "reason": "Missed checkout",
                "requested_check_out_time": "2026-06-10T17:10:00",
                "requested_correction_note": "Manual correction request",
            },
            trace_id="trace-correction",
        )
        self.assertEqual(status, 201)

        status, reviewed = post_attendance_correction_decision(
            self.service,
            manager_actor,
            correction_payload["data"]["correction_id"],
            {
                "approve": True,
                "decision_note": "Approved",
            },
            trace_id="trace-correction-review",
        )
        self.assertEqual(status, 200)
        self.assertEqual(reviewed["data"]["status"], "Approved")
        self.assertEqual(missing_record.lifecycle_state, RecordState.VALIDATED)


if __name__ == "__main__":
    unittest.main()
