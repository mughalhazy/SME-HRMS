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
    assert service.events[-1]["event_type"] == "payroll.run.monthly_trigger_executed"


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


def test_run_payroll_returns_batch_and_validates_processing(service: PayrollService):
    admin = token("Admin")

    status, payload = service.run_payroll(
        "2026-08-01",
        "2026-08-31",
        admin,
        records=[
            {
                "employee_id": "emp-10",
                "pay_period_start": "2026-08-01",
                "pay_period_end": "2026-08-31",
                "base_salary": "1000.00",
                "currency": "USD",
            },
            {
                "employee_id": "emp-11",
                "pay_period_start": "2026-07-01",
                "pay_period_end": "2026-07-31",
                "base_salary": "1100.00",
                "currency": "USD",
            },
        ],
    )

    assert status == 200
    assert payload["data"]["batch"]["status"] == "PartialFailure"
    assert payload["data"]["batch"]["processed_count"] == 1
    assert payload["data"]["batch"]["failed_count"] == 1
    assert payload["data"]["consistency"]["consistent"] is True

    validation_status, validation = service.validate_batch_processing(payload["data"]["batch"]["batch_id"], admin)
    assert validation_status == 200
    assert validation["data"]["validation"]["consistent"] is True
    assert validation["data"]["batch"]["record_ids"] == payload["data"]["batch"]["record_ids"]


def test_run_payroll_is_consistent_across_repeated_runs(service: PayrollService):
    admin = token("Admin")
    records = [
        {
            "employee_id": "emp-30",
            "pay_period_start": "2026-10-01",
            "pay_period_end": "2026-10-31",
            "base_salary": "1200.00",
            "allowances": "125.00",
            "deductions": "75.00",
            "overtime_pay": "30.00",
            "currency": "USD",
        },
        {
            "employee_id": "emp-31",
            "pay_period_start": "2026-10-01",
            "pay_period_end": "2026-10-31",
            "base_salary": "1600.00",
            "allowances": "175.00",
            "deductions": "90.00",
            "overtime_pay": "40.00",
            "currency": "USD",
        },
    ]

    first_status, first_payload = service.run_payroll("2026-10-01", "2026-10-31", admin, records=records)
    second_status, second_payload = service.run_payroll("2026-10-01", "2026-10-31", admin, records=records)

    assert first_status == 200
    assert second_status == 200
    assert second_payload == first_payload
    assert first_payload["data"]["consistency"]["consistent"] is True
    assert first_payload["data"]["batch"]["failed_count"] == 0
    assert sorted(first_payload["data"]["record_ids"]) == sorted(first_payload["data"]["batch"]["record_ids"])

    consistency_status, consistency = service.validate_consistency(admin)
    assert consistency_status == 200
    assert consistency["data"]["status"] == "ok"
    assert consistency["data"]["orphan_record_ids"] == []


def test_create_payroll_record_rejects_total_mismatches_and_persists_calculated_totals(service: PayrollService):
    admin = token("Admin")

    with pytest.raises(ServiceError) as exc:
        service.create_payroll_record(
            {
                "employee_id": "emp-40",
                "pay_period_start": "2026-11-01",
                "pay_period_end": "2026-11-30",
                "base_salary": "1000.00",
                "allowances": "100.00",
                "deductions": "50.00",
                "overtime_pay": "20.00",
                "gross_pay": "9999.99",
                "currency": "USD",
            },
            admin,
        )

    assert exc.value.status == 422
    assert exc.value.message == "gross_pay does not match validated calculation"

    status, created = service.create_payroll_record(
        {
            "employee_id": "emp-41",
            "pay_period_start": "2026-11-01",
            "pay_period_end": "2026-11-30",
            "base_salary": "1000.00",
            "allowances": "100.00",
            "deductions": "50.00",
            "overtime_pay": "20.00",
            "gross_pay": "1120.00",
            "net_pay": "1070.00",
            "currency": "USD",
        },
        admin,
    )

    assert status == 201
    assert created["gross_pay"] == "1120.00"
    assert created["net_pay"] == "1070.00"


def test_mark_paid_updates_batch_and_global_consistency(service: PayrollService):
    admin = token("Admin")
    _, payload = service.run_payroll(
        "2026-09-01",
        "2026-09-30",
        admin,
        records=[
            {
                "employee_id": "emp-20",
                "pay_period_start": "2026-09-01",
                "pay_period_end": "2026-09-30",
                "base_salary": "1000.00",
                "currency": "USD",
            },
            {
                "employee_id": "emp-21",
                "pay_period_start": "2026-09-01",
                "pay_period_end": "2026-09-30",
                "base_salary": "1500.00",
                "currency": "USD",
            },
        ],
    )

    batch = payload["data"]["batch"]
    for record_id in batch["record_ids"]:
        status, paid = service.mark_paid(record_id, admin, payment_date="2026-10-01")
        assert status == 200
        assert paid["status"] == "Paid"

    validation_status, validation = service.validate_batch_processing(batch["batch_id"], admin)
    assert validation_status == 200
    assert validation["data"]["batch"]["status"] == "Paid"
    assert validation["data"]["batch"]["paid_count"] == 2

    consistency_status, consistency = service.validate_consistency(admin)
    assert consistency_status == 200
    assert consistency["data"]["status"] == "ok"
    assert consistency["data"]["orphan_record_ids"] == []
    assert consistency["data"]["batches"][0]["consistent"] is True


def test_attendance_summary_enriches_payroll_overtime(service: PayrollService):
    admin = token("Admin")
    service.register_employee_profile("emp-77", department_id="dept-eng", role_id="role-eng")
    service.create_salary_structure(
        {
            "employee_id": "emp-77",
            "effective_from": "2026-09-01",
            "base_salary": "1000.00",
            "allowances": "0.00",
            "deductions": "0.00",
            "overtime_rate": "10.00",
            "currency": "USD",
        },
        admin,
    )
    service.sync_attendance_summary("emp-77", "2026-09-01", "2026-09-30", {"overtime_hours": "3.00"})

    status, created = service.create_payroll_record(
        {
            "employee_id": "emp-77",
            "pay_period_start": "2026-09-01",
            "pay_period_end": "2026-09-30",
            "currency": "USD",
        },
        admin,
    )

    assert status == 201
    assert created["overtime_pay"] == "30.00"
    summary = service.get_employee_payroll_summary("emp-77")
    assert summary["employee"]["employee_id"] == "emp-77"
    assert summary["attendance_summaries"][0]["overtime_hours"] == "3.00"


def test_payroll_components_rules_tax_and_payslip_are_centralized_in_payroll_service(service: PayrollService):
    admin = token("Admin")
    service.register_employee_profile("emp-42", department_id="dept-fin", role_id="role-analyst")
    service.create_salary_structure(
        {
            "employee_id": "emp-42",
            "effective_from": "2026-01-01",
            "base_salary": "4000.00",
            "allowances": "100.00",
            "deductions": "25.00",
            "overtime_rate": "20.00",
            "currency": "USD",
        },
        admin,
    )
    service.create_payroll_component(
        {
            "employee_id": "emp-42",
            "code": "SHIFT",
            "name": "Shift allowance",
            "category": "earning",
            "amount": "150.00",
            "taxable": True,
            "effective_from": "2026-11-01",
        },
        admin,
    )
    service.upsert_payroll_rule(
        {
            "code": "RETIREMENT",
            "name": "Retirement contribution",
            "category": "deduction",
            "calculation_mode": "percentage",
            "value": "10.00",
            "input_key": "taxable_earnings",
        },
        admin,
    )
    service.upsert_payroll_tax_profile(
        {
            "employee_id": "emp-42",
            "jurisdiction": "US-FED",
            "tax_code": "FIT",
            "metadata": {"rate": "5.00"},
        },
        admin,
    )

    _, record = service.create_payroll_record(
        {
            "employee_id": "emp-42",
            "pay_period_start": "2026-11-01",
            "pay_period_end": "2026-11-30",
            "currency": "USD",
        },
        admin,
    )

    assert record["allowances"] == "250.00"
    assert record["deductions"] == "662.50"
    assert record["gross_pay"] == "4250.00"
    assert record["net_pay"] == "3587.50"

    payslip_status, payslip = service.generate_payslip(record["payroll_record_id"], admin)
    assert payslip_status == 201
    assert payslip["summary"]["net_pay"] == "3587.50"
    assert any(item["code"] == "SHIFT" for item in payslip["line_items"])


def test_adjustment_and_reversal_preserve_transactional_payroll_history(service: PayrollService):
    admin = token("Admin", "pay-admin")
    _, record = service.create_payroll_record(
        {
            "employee_id": "emp-55",
            "pay_period_start": "2026-12-01",
            "pay_period_end": "2026-12-31",
            "base_salary": "2000.00",
            "currency": "USD",
        },
        admin,
    )
    service.run_payroll("2026-12-01", "2026-12-31", admin)
    service.mark_paid(record["payroll_record_id"], admin, payment_date="2027-01-02")

    adjustment_status, adjustment_payload = service.apply_adjustment(
        record["payroll_record_id"],
        {"reason": "Year-end correction", "delta_allowances": "100.00"},
        admin,
    )
    assert adjustment_status == 200
    assert adjustment_payload["record"]["status"] == "Processed"
    assert adjustment_payload["record"]["net_pay"] == "2100.00"

    reversal_status, reversal_payload = service.reverse_payroll_record(
        record["payroll_record_id"],
        {"reason": "ACH recall"},
        admin,
    )
    assert reversal_status == 200
    assert reversal_payload["record"]["status"] == "Cancelled"
    assert reversal_payload["reversal_record"]["net_pay"] == "-2100.00"
