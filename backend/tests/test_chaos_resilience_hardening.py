from __future__ import annotations

import base64
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import pytest

from leave_service import LeaveService, LeaveServiceError
from payroll_service import PayrollService
from services.hiring_service import HiringService
from services.hiring_service.service import HiringValidationError


def bearer(role: str) -> str:
    return "Bearer " + base64.urlsafe_b64encode(json.dumps({"role": role}).encode()).decode().rstrip("=")


def test_leave_submission_stays_consistent_under_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    service = LeaveService()
    _, first = service.create_request(
        "Employee",
        "emp-001",
        "emp-001",
        "Annual",
        date(2026, 9, 1),
        date(2026, 9, 2),
        reason="First draft",
    )
    _, second = service.create_request(
        "Employee",
        "emp-001",
        "emp-001",
        "Annual",
        date(2026, 9, 1),
        date(2026, 9, 2),
        reason="Second draft",
    )
    original_overlap = service._overlap_exists

    def slow_overlap(*args, **kwargs):
        time.sleep(0.02)
        return original_overlap(*args, **kwargs)

    monkeypatch.setattr(service, "_overlap_exists", slow_overlap)

    def submit_leave(leave_request_id: str) -> str:
        _, payload = service.submit_request("Employee", "emp-001", leave_request_id)
        return payload["leave_request_id"]

    successes: list[str] = []
    failures: list[Exception] = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(submit_leave, first["leave_request_id"]),
            executor.submit(submit_leave, second["leave_request_id"]),
        ]
        for future in futures:
            try:
                successes.append(future.result())
            except Exception as exc:  # noqa: BLE001
                failures.append(exc)

    assert len(successes) == 1
    assert len(service.requests) == 2
    assert failures
    assert all(isinstance(exc, LeaveServiceError) for exc in failures)
    assert all(exc.payload["error"]["code"] == "LEAVE_OVERLAP" for exc in failures)


def test_payroll_draft_creation_is_idempotent_under_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    service = PayrollService()
    original_money = service._money

    def slow_money(*args, **kwargs):
        time.sleep(0.02)
        return original_money(*args, **kwargs)

    monkeypatch.setattr(service, "_money", slow_money)
    payload = {
        "employee_id": "emp-1",
        "pay_period_start": "2026-09-01",
        "pay_period_end": "2026-09-30",
        "base_salary": "1000.00",
        "currency": "USD",
    }

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(service.create_payroll_record, payload, bearer("Admin")) for _ in range(6)]
        results = [future.result() for future in futures]

    record_ids = {body["payroll_record_id"] for _, body in results}
    statuses = {status for status, _ in results}

    assert record_ids and len(record_ids) == 1
    assert statuses == {201}
    assert len(service.records) == 1
    assert len(service.period_index) == 1


def test_hiring_candidate_import_blocks_duplicate_email_under_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    service = HiringService()
    posting = service.create_job_posting(
        {
            "title": "Site Reliability Engineer",
            "department_id": "dep-ops",
            "role_id": "role-sre",
            "employment_type": "FullTime",
            "description": "Own resilience and incident response",
            "openings_count": 1,
            "posting_date": "2026-01-01",
            "status": "Open",
        }
    )
    original_coerce_date = service._coerce_date

    def slow_date(*args, **kwargs):
        time.sleep(0.02)
        return original_coerce_date(*args, **kwargs)

    monkeypatch.setattr(service, "_coerce_date", slow_date)
    payload = {
        "job_posting_id": posting["job_posting_id"],
        "first_name": "Nina",
        "last_name": "Shaw",
        "email": "nina@example.com",
        "application_date": "2026-01-03",
    }

    successes: list[str] = []
    failures: list[Exception] = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(service.create_candidate, payload) for _ in range(6)]
        for future in futures:
            try:
                successes.append(future.result()["candidate_id"])
            except Exception as exc:  # noqa: BLE001
                failures.append(exc)

    assert len(successes) == 1
    assert len(service.candidates) == 1
    assert failures
    assert all(isinstance(exc, HiringValidationError) for exc in failures)
    assert all("unique within the job posting" in str(exc) for exc in failures)
