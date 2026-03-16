from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Iterable

DASHBOARD_SURFACE = "dashboard"


@dataclass(frozen=True)
class DashboardWidget:
    widget_id: str
    title: str
    read_model: str
    capability_id: str
    owner_service: str


DASHBOARD_WIDGETS: tuple[DashboardWidget, ...] = (
    DashboardWidget("employees", "Employees", "employee_directory_view", "CAP-EMP-001", "employee-service"),
    DashboardWidget("attendance", "Attendance", "attendance_dashboard_view", "CAP-ATT-001", "attendance-service"),
    DashboardWidget("leave", "Leave Requests", "leave_requests_view", "CAP-LEV-001", "leave-service"),
    DashboardWidget("payroll", "Payroll", "payroll_summary_view", "CAP-PAY-001", "payroll-service"),
    DashboardWidget("hiring", "Hiring Pipeline", "candidate_pipeline_view", "CAP-HIR-001", "hiring-service"),
    DashboardWidget("performance", "Performance Reviews", "performance_review_view", "CAP-PRF-001", "employee-service"),
)


def iter_dashboard_widgets() -> Iterable[DashboardWidget]:
    return DASHBOARD_WIDGETS


def build_dashboard_ui(read_models: dict[str, list[dict[str, Any]]], *, today: date | None = None) -> dict[str, Any]:
    current_day = today or date.today()

    employee_rows = read_models.get("employee_directory_view", [])
    attendance_rows = read_models.get("attendance_dashboard_view", [])
    leave_rows = read_models.get("leave_requests_view", [])
    payroll_rows = read_models.get("payroll_summary_view", [])
    candidate_rows = read_models.get("candidate_pipeline_view", [])
    review_rows = read_models.get("performance_review_view", [])

    todays_attendance = [
        row for row in attendance_rows if _parse_date(row.get("attendance_date")) == current_day
    ]

    ui = {
        "surface": DASHBOARD_SURFACE,
        "capabilities": [widget.capability_id for widget in DASHBOARD_WIDGETS],
        "widgets": {
            "employees": {
                "summary": {
                    "total": len(employee_rows),
                    "active": sum(1 for row in employee_rows if row.get("employee_status") == "Active"),
                },
                "recent": _take(employee_rows, 5, ["employee_id", "full_name", "department_name", "employee_status"]),
            },
            "attendance": {
                "summary": {
                    "today_records": len(todays_attendance),
                    "present": sum(1 for row in todays_attendance if row.get("attendance_status") == "Present"),
                },
                "recent": _take(attendance_rows, 5, ["employee_id", "employee_name", "attendance_date", "attendance_status"]),
            },
            "leave": {
                "summary": {
                    "pending": sum(1 for row in leave_rows if row.get("status") == "Submitted"),
                    "approved": sum(1 for row in leave_rows if row.get("status") == "Approved"),
                },
                "recent": _take(leave_rows, 5, ["leave_request_id", "employee_name", "start_date", "end_date", "status"]),
            },
            "payroll": {
                "summary": {
                    "records": len(payroll_rows),
                    "net_pay_total": str(sum(Decimal(str(row.get("net_pay", 0))) for row in payroll_rows)),
                },
                "recent": _take(payroll_rows, 5, ["payroll_record_id", "employee_name", "pay_period_start", "pay_period_end", "status", "net_pay"]),
            },
            "hiring": {
                "summary": {
                    "applications": len(candidate_rows),
                    "openings": len({row.get("job_posting_id") for row in candidate_rows if row.get("job_posting_id")}),
                },
                "recent": _take(candidate_rows, 5, ["candidate_id", "candidate_name", "job_title", "pipeline_stage", "next_interview_at"]),
            },
            "performance": {
                "summary": {
                    "reviews": len(review_rows),
                    "submitted": sum(1 for row in review_rows if row.get("status") == "Submitted"),
                },
                "recent": _take(review_rows, 5, ["performance_review_id", "employee_name", "reviewer_name", "overall_rating", "status"]),
            },
        },
    }

    return ui


def _take(rows: list[dict[str, Any]], limit: int, fields: list[str]) -> list[dict[str, Any]]:
    return [{field: row.get(field) for field in fields} for row in rows[:limit]]


def _parse_date(raw: Any) -> date | None:
    if isinstance(raw, date):
        return raw
    if not isinstance(raw, str):
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None
