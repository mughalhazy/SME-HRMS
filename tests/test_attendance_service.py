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
    EmployeeSnapshot,
    InMemoryEmployeeDirectory,
    RecordState,
)
from attendance_service.api import (
    get_attendance_absence_alerts,
    get_attendance_record,
    get_attendance_records,
    get_attendance_summary,
    patch_attendance_record,
    post_attendance_approval,
    post_attendance_log,
    post_attendance_period_lock,
    post_attendance_records,
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
        self.assertEqual(payload["error"]["traceId"], "trace-1")

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
        self.assertEqual(payload["error"]["traceId"], "trace-404")

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
        self.assertIn("Late", payload["anomalies"])
        self.assertIn("MissingCheckOut", payload["anomalies"])

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
        self.assertEqual(len(payload["records"]), 2)
        self.assertEqual(payload["aggregation"]["anomalyBreakdown"]["MissingCheckOut"], 1)

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
        self.assertEqual(payload["anomalies"], [])
        self.assertEqual(payload["correction_note"], "Backfilled missing check-out")

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
            created["attendance_id"],
            trace_id="trace-get-api",
        )
        self.assertEqual(status, 200)
        self.assertEqual(fetched["attendance_id"], created["attendance_id"])

        status, approved = post_attendance_approval(
            self.service,
            admin,
            created["attendance_id"],
            trace_id="trace-approve-api",
        )
        self.assertEqual(status, 200)
        self.assertEqual(approved["lifecycle_state"], "Approved")

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
        self.assertEqual(summary["records"], 1)

        status, alerts = get_attendance_absence_alerts(
            self.service,
            admin,
            {"attendance_date": "2026-05-06"},
            trace_id="trace-alerts-api",
        )
        self.assertEqual(status, 200)
        self.assertEqual(alerts["count"], 1)

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
        self.assertEqual(payload["lockedCount"], 1)

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



if __name__ == "__main__":
    unittest.main()
