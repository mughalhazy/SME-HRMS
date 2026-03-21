from __future__ import annotations

import base64
import importlib.util
import json
import pathlib
import sys
from datetime import date

from event_contract import legacy_event_name_for, normalize_event_type
from leave_api import get_leave_requests
from leave_service import LeaveService
from payroll_api import get_payroll_records
from payroll_service import PayrollService


MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "api-gateway" / "routes.py"
SPEC = importlib.util.spec_from_file_location("api_gateway_routes_compat", MODULE_PATH)
api_gateway_routes = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = api_gateway_routes
SPEC.loader.exec_module(api_gateway_routes)


def _token(role: str, employee_id: str | None = None) -> str:
    payload = {"role": role}
    if employee_id:
        payload["employee_id"] = employee_id
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"Bearer {encoded}"


def test_gateway_preserves_legacy_unversioned_route_aliases() -> None:
    route = api_gateway_routes.resolve_route("/payroll/records")
    assert route.upstream_service == "payroll-service"
    assert api_gateway_routes.is_legacy_route("/payroll/records") is True

    workflow_route = api_gateway_routes.resolve_route("/workflows/123")
    assert workflow_route.upstream_service == "workflow-service"
    assert api_gateway_routes.is_legacy_route("/api/v1/workflows/123") is False


def test_leave_list_preserves_legacy_data_alias_alongside_d1_items() -> None:
    service = LeaveService()
    _, created = service.create_request(
        "Employee",
        "emp-001",
        "emp-001",
        "Annual",
        date(2026, 3, 1),
        date(2026, 3, 2),
    )
    service.submit_request("Employee", "emp-001", created["leave_request_id"])

    status, payload = get_leave_requests(
        service,
        "Employee",
        "emp-001",
        {"employee_id": "emp-001", "status": "Submitted"},
        trace_id="trace-compat-leave-list",
    )

    assert status == 200
    assert payload["data"]["items"] == payload["data"]["data"]
    assert payload["meta"]["pagination"]["count"] == 1


def test_payroll_list_preserves_legacy_data_alias_and_pagination_flags() -> None:
    service = PayrollService()
    admin = _token("Admin")
    service.create_payroll_record(
        {
            "employee_id": "emp-compat-001",
            "pay_period_start": "2026-03-01",
            "pay_period_end": "2026-03-31",
            "base_salary": "1000.00",
            "allowances": "50.00",
            "deductions": "20.00",
            "overtime_pay": "0.00",
            "currency": "USD",
        },
        admin,
        trace_id="trace-compat-payroll-create",
    )

    status, payload = get_payroll_records(
        service,
        admin,
        {"employee_id": "emp-compat-001", "pay_period_start": "2026-03-01", "pay_period_end": "2026-03-31", "limit": "10"},
        trace_id="trace-compat-payroll-list",
    )

    assert status == 200
    assert payload["data"]["items"] == payload["data"]["data"]
    assert payload["meta"]["pagination"]["has_next"] is False
    assert payload["data"]["filters"]["pay_period_start"] == "2026-03-01"


def test_event_contract_preserves_legacy_name_lookup_for_canonical_types() -> None:
    assert normalize_event_type("LeaveRequestApproved") == "leave.request.approved"
    assert legacy_event_name_for("leave.request.approved") == "LeaveRequestApproved"
