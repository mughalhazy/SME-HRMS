from datetime import date

import pytest

from leave_service import EmployeeStatus, LeaveService, LeaveServiceError


def test_employee_create_submit_and_manager_approve_updates_balance_and_status():
    svc = LeaveService()
    code, created = svc.create_request(
        actor_role="Employee",
        actor_employee_id="emp-001",
        employee_id="emp-001",
        leave_type="Annual",
        start_date=date(2026, 1, 10),
        end_date=date(2026, 1, 12),
        reason="Vacation",
    )
    assert code == 201
    assert created["leave_balance"]["remaining_days"] == 18.0

    code, submitted = svc.submit_request("Employee", "emp-001", created["leave_request_id"])
    assert code == 200
    assert submitted["status"] == "Submitted"
    assert submitted["leave_balance"]["reserved_days"] == 3.0
    assert submitted["leave_balance"]["remaining_days"] == 15.0

    code, approved = svc.decide_request("approve", "Manager", "emp-manager", created["leave_request_id"])
    assert code == 200
    assert approved["status"] == "Approved"
    assert approved["leave_balance"]["reserved_days"] == 0.0
    assert approved["leave_balance"]["approved_days"] == 3.0
    assert approved["leave_balance"]["remaining_days"] == 15.0


def test_overlap_blocked_after_submission():
    svc = LeaveService()
    _, first = svc.create_request("Employee", "emp-001", "emp-001", "Annual", date(2026, 2, 1), date(2026, 2, 3))
    svc.submit_request("Employee", "emp-001", first["leave_request_id"])

    with pytest.raises(LeaveServiceError) as ex:
        svc.create_request("Employee", "emp-001", "emp-001", "Annual", date(2026, 2, 2), date(2026, 2, 4))
    assert ex.value.status_code == 409
    assert ex.value.payload["error"]["code"] == "LEAVE_OVERLAP"


def test_employee_cannot_approve():
    svc = LeaveService()
    _, created = svc.create_request("Employee", "emp-001", "emp-001", "Sick", date(2026, 3, 1), date(2026, 3, 1))
    svc.submit_request("Employee", "emp-001", created["leave_request_id"])

    with pytest.raises(LeaveServiceError) as ex:
        svc.decide_request("approve", "Employee", "emp-001", created["leave_request_id"])
    assert ex.value.status_code == 403
    assert ex.value.payload["error"]["code"] == "FORBIDDEN"


def test_leave_observability_captures_metrics_and_audit_logs():
    svc = LeaveService()
    _, created = svc.create_request("Employee", "emp-001", "emp-001", "Annual", date(2026, 4, 1), date(2026, 4, 2), trace_id="trace-create")
    svc.submit_request("Employee", "emp-001", created["leave_request_id"], trace_id="trace-submit")
    svc.decide_request("approve", "Manager", "emp-manager", created["leave_request_id"], trace_id="trace-approve")

    metrics = svc.observability.metrics.snapshot()
    assert metrics["request_count"] >= 3
    assert metrics["error_rate"] == 0.0
    assert any(record["trace_id"] == "trace-approve" and record["message"] == "leave_request_approve" for record in svc.observability.logger.records)
    assert svc.health_snapshot()["status"] == "ok"


def test_reject_releases_reserved_balance_and_blocks_broken_transition():
    svc = LeaveService()
    _, created = svc.create_request("Employee", "emp-001", "emp-001", "Casual", date(2026, 5, 5), date(2026, 5, 6))
    svc.submit_request("Employee", "emp-001", created["leave_request_id"])

    code, rejected = svc.decide_request("reject", "Manager", "emp-manager", created["leave_request_id"], reason="Coverage gap")
    assert code == 200
    assert rejected["status"] == "Rejected"
    assert rejected["leave_balance"]["reserved_days"] == 0.0
    assert rejected["leave_balance"]["approved_days"] == 0.0
    assert rejected["leave_balance"]["remaining_days"] == 7.0
    assert "[Rejection] Coverage gap" in rejected["reason"]

    with pytest.raises(LeaveServiceError) as ex:
        svc.submit_request("Employee", "emp-001", created["leave_request_id"])
    assert ex.value.status_code == 409
    assert ex.value.payload["error"]["code"] == "INVALID_TRANSITION"


def test_cancel_approved_future_leave_restores_balance_and_employee_status(monkeypatch: pytest.MonkeyPatch):
    svc = LeaveService()
    monkeypatch.setattr(svc, "_today", lambda: date(2026, 6, 1))

    _, created = svc.create_request("Employee", "emp-001", "emp-001", "Annual", date(2026, 6, 2), date(2026, 6, 4))
    svc.submit_request("Employee", "emp-001", created["leave_request_id"])
    _, approved = svc.decide_request("approve", "Manager", "emp-manager", created["leave_request_id"])
    assert approved["leave_balance"]["approved_days"] == 3.0
    assert svc.employees["emp-001"].status == EmployeeStatus.ACTIVE

    code, cancelled = svc.patch_request("Employee", "emp-001", created["leave_request_id"], {"status": "Cancelled"})
    assert code == 200
    assert cancelled["status"] == "Cancelled"
    assert cancelled["leave_balance"]["approved_days"] == 0.0
    assert cancelled["leave_balance"]["remaining_days"] == 18.0
    assert svc.employees["emp-001"].status == EmployeeStatus.ACTIVE


def test_request_leave_fails_when_balance_is_exhausted():
    svc = LeaveService()

    _, first = svc.create_request("Employee", "emp-001", "emp-001", "Annual", date(2026, 7, 1), date(2026, 7, 18))
    svc.submit_request("Employee", "emp-001", first["leave_request_id"])
    svc.decide_request("approve", "Manager", "emp-manager", first["leave_request_id"])

    with pytest.raises(LeaveServiceError) as ex:
        svc.create_request("Employee", "emp-001", "emp-001", "Annual", date(2026, 8, 1), date(2026, 8, 2))
    assert ex.value.status_code == 409
    assert ex.value.payload["error"]["code"] == "INSUFFICIENT_LEAVE_BALANCE"


def test_list_requests_returns_balances_for_employee_scope():
    svc = LeaveService()
    _, created = svc.create_request("Employee", "emp-001", "emp-001", "Sick", date(2026, 9, 8), date(2026, 9, 8))
    svc.submit_request("Employee", "emp-001", created["leave_request_id"])

    code, payload = svc.list_requests("Employee", "emp-001", employee_id="emp-001", status="Submitted")
    assert code == 200
    assert len(payload["data"]) == 1
    assert any(balance["leave_type"] == "Sick" and balance["reserved_days"] == 1.0 for balance in payload["leave_balances"])
