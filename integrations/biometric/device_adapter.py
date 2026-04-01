from __future__ import annotations

from datetime import datetime
from typing import Any


_EVENT_MAP = {
    "IN": "check_in",
    "OUT": "check_out",
    "BREAK_IN": "break_start",
    "BREAK_OUT": "break_end",
    "check_in": "check_in",
    "check_out": "check_out",
}


def _normalize_log(raw: dict[str, Any]) -> dict[str, str] | None:
    # Supports canonical format and common vendor format:
    # {"emp_code": "E1", "event_code": "IN", "event_time": "2026-01-01T09:00:00Z", "terminal_id": "D1"}
    employee_id = str(raw.get("employee_id") or raw.get("emp_code") or "").strip()
    event_raw = str(raw.get("event_type") or raw.get("event_code") or "").strip()
    timestamp = str(raw.get("timestamp") or raw.get("event_time") or "").strip()
    device_id = str(raw.get("device_id") or raw.get("terminal_id") or "")

    event_type = _EVENT_MAP.get(event_raw, event_raw.lower())
    if not employee_id or not event_type or not timestamp:
        return None

    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None

    return {
        "employee_id": employee_id,
        "event_type": event_type,
        "timestamp": timestamp,
        "device_id": device_id,
        "source": "biometric_device",
    }


def ingest_device_logs(payload: dict[str, Any]) -> dict[str, Any]:
    logs: list[dict[str, str]] = []
    rejected = 0
    for raw in list(payload.get("logs", [])):
        normalized = _normalize_log(raw)
        if normalized is None:
            rejected += 1
            continue
        logs.append(normalized)

    return {"status": "success", "accepted_logs": len(logs), "rejected_logs": rejected, "logs": logs}
