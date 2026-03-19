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


def test_payroll_observability_captures_metrics_and_audit_logs(service: PayrollService):
    admin = token("Admin")
    _, created = service.create_payroll_record(
        {
            "employee_id": "emp-9",
            "pay_period_start": "2026-07-01",
            "pay_period_end": "2026-07-31",
            "base_salary": "1500.00",
            "currency": "USD",
        },
        admin,
        trace_id="trace-payroll-create",
    )
    service.run_payroll("2026-07-01", "2026-07-31", admin, trace_id="trace-payroll-run")
    service.mark_paid(created["payroll_record_id"], admin, trace_id="trace-payroll-paid")

    metrics = service.observability.metrics.snapshot()
    assert metrics["request_count"] >= 3
    assert any(record["trace_id"] == "trace-payroll-paid" and record["message"] == "payroll_record_paid" for record in service.observability.logger.records)
    assert service.health_snapshot()["status"] == "ok"


def test_generate_fetch_and_update_payroll_with_salary_structure_and_cycle(service: PayrollService):
    admin = token("Admin")
    _, structure = service.create_salary_structure(
        {
            "employee_id": "emp-10",
            "base_salary": "3000.00",
            "allowances": "250.00",
            "deductions": "100.00",
            "overtime_rate": "25.00",
            "currency": "USD",
            "effective_from": "2026-10-01",
        },
        admin,
    )
    _, cycle = service.upsert_payroll_cycle(
        {
            "name": "October 2026 Monthly",
            "pay_period_start": "2026-10-01",
            "pay_period_end": "2026-10-31",
            "payment_date": "2026-11-05",
        },
        admin,
    )

    status, created = service.generate_payroll(
        {
            "salary_structure_id": structure["salary_structure_id"],
            "payroll_cycle_id": cycle["payroll_cycle_id"],
            "overtime_hours": "4",
        },
        admin,
    )

    assert status == 201
    assert created["salary_structure_id"] == structure["salary_structure_id"]
    assert created["payroll_cycle_id"] == cycle["payroll_cycle_id"]
    assert created["overtime_pay"] == "100.00"
    assert created["gross_pay"] == "3350.00"
    assert created["net_pay"] == "3250.00"

    status, fetched = service.fetch_payroll(admin, payroll_record_id=created["payroll_record_id"])
    assert status == 200
    assert fetched["data"]["salary_structure"]["salary_structure_id"] == structure["salary_structure_id"]
    assert fetched["data"]["payroll_cycle"]["payroll_cycle_id"] == cycle["payroll_cycle_id"]

    status, updated = service.update_payroll(
        created["payroll_record_id"],
        {
            "allowances": "300.00",
            "deductions": "125.00",
            "gross_pay": "3400.00",
            "net_pay": "3275.00",
        },
        admin,
    )
    assert status == 200
    assert updated["gross_pay"] == "3400.00"
    assert updated["net_pay"] == "3275.00"


def test_generate_payroll_rejects_invalid_calculations(service: PayrollService):
    admin = token("Admin")
    _, structure = service.create_salary_structure(
        {
            "employee_id": "emp-11",
            "base_salary": "2000.00",
            "allowances": "100.00",
            "deductions": "50.00",
            "overtime_rate": "10.00",
            "currency": "USD",
            "effective_from": "2026-11-01",
        },
        admin,
    )

    with pytest.raises(ServiceError) as exc:
        service.generate_payroll(
            {
                "salary_structure_id": structure["salary_structure_id"],
                "pay_period_start": "2026-11-01",
                "pay_period_end": "2026-11-30",
                "overtime_hours": "2",
                "gross_pay": "9999.99",
            },
            admin,
        )

    assert exc.value.status == 422
    assert exc.value.message == "gross_pay does not match validated calculation"


def test_generate_payroll_rejects_negative_net_pay_edge_case(service: PayrollService):
    admin = token("Admin")

    with pytest.raises(ServiceError) as exc:
        service.generate_payroll(
            {
                "employee_id": "emp-12",
                "pay_period_start": "2026-12-01",
                "pay_period_end": "2026-12-31",
                "base_salary": "100.00",
                "allowances": "0.00",
                "deductions": "125.00",
                "currency": "USD",
            },
            admin,
        )

    assert exc.value.status == 422
    assert exc.value.message == "net_pay must be >= 0"


def test_payroll_cycle_rejects_payment_before_period_end_edge_case(service: PayrollService):
    admin = token("Admin")

    with pytest.raises(ServiceError) as exc:
        service.upsert_payroll_cycle(
            {
                "name": "Invalid Cycle",
                "pay_period_start": "2026-12-01",
                "pay_period_end": "2026-12-31",
                "payment_date": "2026-12-15",
            },
            admin,
        )

    assert exc.value.status == 422
    assert exc.value.message == "payment_date must be on or after pay_period_end"
