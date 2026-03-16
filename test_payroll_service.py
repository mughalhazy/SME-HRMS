import base64
import json

import pytest

from payroll_service import PayrollService, ServiceError


def token(role: str, employee_id: str | None = None) -> str:
    payload = {"role": role}
    if employee_id:
        payload["employee_id"] = employee_id
    return "Bearer " + base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")


@pytest.fixture()
def service() -> PayrollService:
    return PayrollService()


def test_create_run_mark_paid_flow(service: PayrollService):
    admin = token("Admin")
    status, created = service.create_payroll_record(
        {
            "employee_id": "emp-1",
            "pay_period_start": "2026-01-01",
            "pay_period_end": "2026-01-31",
            "base_salary": "1000.00",
            "allowances": "100.00",
            "deductions": "50.00",
            "overtime_pay": "20.00",
            "currency": "usd",
        },
        admin,
    )
    assert status == 201
    assert created["status"] == "Draft"

    status, run = service.run_payroll("2026-01-01", "2026-01-31", admin)
    assert status == 200
    assert run["data"]["processed_count"] == 1

    status, paid = service.mark_paid(created["payroll_record_id"], admin)
    assert status == 200
    assert paid["status"] == "Paid"


def test_employee_scope_read(service: PayrollService):
    admin = token("Admin")
    for emp in ["emp-1", "emp-2"]:
        service.create_payroll_record(
            {
                "employee_id": emp,
                "pay_period_start": "2026-02-01",
                "pay_period_end": "2026-02-28",
                "base_salary": "1000.00",
                "currency": "USD",
            },
            admin,
        )

    status, result = service.list_payroll_records(token("Employee", "emp-1"))
    assert status == 200
    assert len(result["data"]) == 1
    assert result["data"][0]["employee_id"] == "emp-1"


def test_manager_cannot_write(service: PayrollService):
    with pytest.raises(ServiceError) as exc:
        service.create_payroll_record(
            {
                "employee_id": "emp-1",
                "pay_period_start": "2026-01-01",
                "pay_period_end": "2026-01-31",
                "base_salary": "1000.00",
                "currency": "USD",
            },
            token("Manager"),
        )
    assert exc.value.status == 403


def test_cursor_pagination(service: PayrollService):
    admin = token("Admin")
    for idx in range(3):
        service.create_payroll_record(
            {
                "employee_id": f"emp-{idx}",
                "pay_period_start": "2026-03-01",
                "pay_period_end": "2026-03-31",
                "base_salary": "1200.00",
                "currency": "USD",
            },
            admin,
        )

    _, first = service.list_payroll_records(admin, limit=2)
    assert len(first["data"]) == 2
    assert first["page"]["hasNext"] is True

    _, second = service.list_payroll_records(admin, limit=2, cursor=first["page"]["nextCursor"])
    assert len(second["data"]) == 1
    assert second["page"]["hasNext"] is False


def test_manager_can_read_records(service: PayrollService):
    admin = token("Admin")
    service.create_payroll_record(
        {
            "employee_id": "emp-1",
            "pay_period_start": "2026-04-01",
            "pay_period_end": "2026-04-30",
            "base_salary": "900.00",
            "currency": "USD",
        },
        admin,
    )

    status, result = service.list_payroll_records(token("Manager"))
    assert status == 200
    assert len(result["data"]) == 1


def test_monthly_trigger_runs_full_month_period(service: PayrollService):
    admin = token("Admin")
    status, payload = service.payroll_monthly_trigger(
        "2026-05-15",
        admin,
        records=[
            {
                "employee_id": "emp-7",
                "pay_period_start": "2026-05-01",
                "pay_period_end": "2026-05-31",
                "base_salary": "1000.00",
                "currency": "USD",
            }
        ],
    )
    assert status == 200
    assert payload["data"]["trigger"] == "monthly"
    assert payload["data"]["period_start"] == "2026-05-01"
    assert payload["data"]["period_end"] == "2026-05-31"
    assert payload["data"]["processed_count"] == 1
    assert service.events[-1]["type"] == "PayrollMonthlyTriggerExecuted"


def test_invalid_money_value_returns_validation_error(service: PayrollService):
    with pytest.raises(ServiceError) as exc:
        service.create_payroll_record(
            {
                "employee_id": "emp-1",
                "pay_period_start": "2026-06-01",
                "pay_period_end": "2026-06-30",
                "base_salary": "not-a-number",
                "currency": "USD",
            },
            token("Admin"),
        )

    assert exc.value.status == 422
    assert exc.value.code == "VALIDATION_ERROR"
    assert "base_salary" in exc.value.message


def test_invalid_cursor_returns_validation_error(service: PayrollService):
    with pytest.raises(ServiceError) as exc:
        service.list_payroll_records(token("Admin"), cursor="%%%")

    assert exc.value.status == 422
    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.message == "cursor is invalid"
