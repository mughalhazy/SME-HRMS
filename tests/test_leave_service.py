from datetime import date

import pytest

from leave_service import LeaveService, LeaveServiceError


def test_employee_create_submit_and_manager_approve():
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

    code, submitted = svc.submit_request("Employee", "emp-001", created["leave_request_id"])
    assert code == 200
    assert submitted["status"] == "Submitted"

    code, approved = svc.decide_request("approve", "Manager", "emp-manager", created["leave_request_id"])
    assert code == 200
    assert approved["status"] == "Approved"


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
