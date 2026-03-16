from __future__ import annotations

from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable


REQUIRED_ATTENDANCE_VIEW_FIELDS = {
    "employee_id",
    "employee_number",
    "employee_name",
    "department_id",
    "department_name",
    "attendance_date",
    "attendance_status",
    "check_in_time",
    "check_out_time",
    "total_hours",
    "source",
    "record_state",
    "updated_at",
}


def _coerce_hours(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid total_hours value: {value}") from exc


def _coerce_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise ValueError(f"Invalid attendance_date value: {value}")


def build_attendance_ui(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Build a UI-ready payload for the `attendance_dashboard` surface.

    Input rows are expected to follow the canonical `attendance_dashboard_view`
    contract from docs/canon/read-model-catalog.md.
    """

    materialized_rows = list(rows)
    for index, row in enumerate(materialized_rows):
        missing = REQUIRED_ATTENDANCE_VIEW_FIELDS.difference(row.keys())
        if missing:
            raise ValueError(
                f"Row {index} does not match attendance_dashboard_view. Missing fields: {sorted(missing)}"
            )

    if not materialized_rows:
        return {
            "surface": "attendance_dashboard",
            "readModel": "attendance_dashboard_view",
            "capabilityIds": ["CAP-ATT-001", "CAP-ATT-002"],
            "ownerService": "attendance-service",
            "summary": {
                "totalRecords": 0,
                "uniqueEmployees": 0,
                "dateRange": {"from": None, "to": None},
                "statusBreakdown": {},
                "averageHours": "0.00",
            },
            "records": [],
        }

    statuses = Counter()
    employee_ids = set()
    attendance_dates = []
    total_hours = Decimal("0")

    normalized_records = []
    for row in materialized_rows:
        attendance_date = _coerce_date(row["attendance_date"])
        hours = _coerce_hours(row["total_hours"])

        statuses[row["attendance_status"]] += 1
        employee_ids.add(row["employee_id"])
        attendance_dates.append(attendance_date)
        total_hours += hours

        normalized_records.append(
            {
                "employeeId": str(row["employee_id"]),
                "employeeNumber": row["employee_number"],
                "employeeName": row["employee_name"],
                "departmentId": str(row["department_id"]),
                "departmentName": row["department_name"],
                "attendanceDate": attendance_date.isoformat(),
                "attendanceStatus": row["attendance_status"],
                "checkInTime": row["check_in_time"],
                "checkOutTime": row["check_out_time"],
                "totalHours": str(hours),
                "source": row["source"],
                "recordState": row["record_state"],
                "updatedAt": row["updated_at"],
            }
        )

    normalized_records.sort(key=lambda r: (r["attendanceDate"], r["employeeName"]), reverse=True)

    average_hours = total_hours / Decimal(len(normalized_records))
    return {
        "surface": "attendance_dashboard",
        "readModel": "attendance_dashboard_view",
        "capabilityIds": ["CAP-ATT-001", "CAP-ATT-002"],
        "ownerService": "attendance-service",
        "summary": {
            "totalRecords": len(normalized_records),
            "uniqueEmployees": len(employee_ids),
            "dateRange": {
                "from": min(attendance_dates).isoformat(),
                "to": max(attendance_dates).isoformat(),
            },
            "statusBreakdown": dict(statuses),
            "averageHours": str(average_hours.quantize(Decimal("0.01"))),
        },
        "records": normalized_records,
    }
