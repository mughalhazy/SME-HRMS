from __future__ import annotations

from typing import Any
from uuid import uuid4


_REQUIRED_KEYS = {"period", "employer", "employees"}


def submit_pr01(payload: dict[str, Any]) -> dict[str, Any]:
    """Submit EOBI PR-01 monthly contribution payload (simulated)."""

    errors: list[str] = []
    missing = _REQUIRED_KEYS.difference(payload.keys())
    if missing:
        errors.append(f"Missing top-level keys: {sorted(missing)}")

    period = payload.get("period")
    if not isinstance(period, dict) or "month" not in period or "year" not in period:
        errors.append("Invalid period shape; expected month/year.")

    employer = payload.get("employer")
    if not isinstance(employer, dict) or "registration_number" not in employer:
        errors.append("Missing employer registration_number.")

    employees = payload.get("employees")
    if not isinstance(employees, list):
        errors.append("employees must be an array.")

    submission_id = f"eobi_{uuid4().hex[:12]}"
    return {
        "status": "success" if not errors else "failure",
        "submitted": not errors,
        "submission_id": submission_id,
        "provider": "EOBI",
        "format": "pr_01",
        "mode": "simulated",
        "errors": errors,
    }
