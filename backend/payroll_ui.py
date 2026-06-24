from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

PAYROLL_DASHBOARD_SURFACE = "payroll_dashboard"
PAYROLL_READ_MODEL = "payroll_summary_view"
PAYROLL_READ_CAPABILITIES = ("CAP-PAY-001", "CAP-PAY-002")

# Canonical field contract from docs/canon/read-model-catalog.md (payroll_summary_view)
PAYROLL_SUMMARY_FIELDS: tuple[str, ...] = (
    "payroll_record_id",
    "employee_id",
    "employee_number",
    "employee_name",
    "department_id",
    "department_name",
    "pay_period_start",
    "pay_period_end",
    "base_salary",
    "allowances",
    "deductions",
    "overtime_pay",
    "gross_pay",
    "net_pay",
    "currency",
    "payment_date",
    "status",
    "updated_at",
)


@dataclass(frozen=True)
class PayrollUiPermissions:
    can_read: bool
    can_run_payroll: bool
    can_mark_paid: bool


def _to_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _derive_permissions(capabilities: Iterable[str]) -> PayrollUiPermissions:
    cap_set = set(capabilities)
    can_read = "CAP-PAY-001" in cap_set
    return PayrollUiPermissions(
        can_read=can_read,
        can_run_payroll=can_read,
        can_mark_paid="CAP-PAY-002" in cap_set,
    )


def _project_row(row: dict[str, Any]) -> dict[str, Any]:
    return {field: row.get(field) for field in PAYROLL_SUMMARY_FIELDS}


def build_payroll_ui(rows: Iterable[dict[str, Any]], capabilities: Iterable[str]) -> dict[str, Any]:
    """Builds a payroll dashboard UI payload from `payroll_summary_view` rows.

    Output is intentionally read-model driven so the UI shape remains stable with
    the canonical map defined in docs/canon/ui-surface-map.md and
    docs/canon/read-model-catalog.md.
    """

    permissions = _derive_permissions(capabilities)
    if not permissions.can_read:
        return {
            "surface": PAYROLL_DASHBOARD_SURFACE,
            "readModel": PAYROLL_READ_MODEL,
            "capabilities": list(PAYROLL_READ_CAPABILITIES),
            "permissions": permissions.__dict__,
            "summary": {"records": 0, "totalGrossPay": "0", "totalNetPay": "0", "statusBreakdown": {}},
            "table": {"columns": list(PAYROLL_SUMMARY_FIELDS), "rows": []},
            "actions": {"runPayroll": False, "markPaid": False},
        }

    projected_rows = [_project_row(row) for row in rows]
    status_breakdown = Counter(str(row.get("status", "Unknown")) for row in projected_rows)
    total_gross = sum((_to_decimal(row.get("gross_pay")) for row in projected_rows), Decimal("0"))
    total_net = sum((_to_decimal(row.get("net_pay")) for row in projected_rows), Decimal("0"))

    return {
        "surface": PAYROLL_DASHBOARD_SURFACE,
        "readModel": PAYROLL_READ_MODEL,
        "capabilities": list(PAYROLL_READ_CAPABILITIES),
        "permissions": permissions.__dict__,
        "summary": {
            "records": len(projected_rows),
            "totalGrossPay": str(total_gross.quantize(Decimal("0.01"))),
            "totalNetPay": str(total_net.quantize(Decimal("0.01"))),
            "statusBreakdown": dict(status_breakdown),
        },
        "table": {"columns": list(PAYROLL_SUMMARY_FIELDS), "rows": projected_rows},
        "actions": {
            "runPayroll": permissions.can_run_payroll,
            "markPaid": permissions.can_mark_paid,
        },
    }
