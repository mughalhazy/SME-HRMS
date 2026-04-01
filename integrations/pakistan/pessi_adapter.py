from __future__ import annotations

from typing import Any
from uuid import uuid4


_REQUIRED_KEYS = {"period", "establishment", "employees"}


def submit_contribution_return(payload: dict[str, Any]) -> dict[str, Any]:
    """Submit PESSI/SESSI social security return payload (simulated)."""

    errors: list[str] = []
    missing = _REQUIRED_KEYS.difference(payload.keys())
    if missing:
        errors.append(f"Missing top-level keys: {sorted(missing)}")

    establishment = payload.get("establishment")
    if not isinstance(establishment, dict) or "registration_number" not in establishment:
        errors.append("Missing establishment registration_number.")

    employees = payload.get("employees")
    if not isinstance(employees, list):
        errors.append("employees must be an array.")

    submission_id = f"pessi_{uuid4().hex[:12]}"
    return {
        "status": "success" if not errors else "failure",
        "submitted": not errors,
        "submission_id": submission_id,
        "provider": "PESSI_SESSI",
        "format": "contribution_return",
        "mode": "simulated",
        "errors": errors,
    }
