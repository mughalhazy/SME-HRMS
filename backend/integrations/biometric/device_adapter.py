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
    "0": "check_in",
    "1": "check_out",
}


def _extract_field(raw: dict[str, Any], *paths: str) -> str:
    for path in paths:
        value: Any = raw
        for key in path.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _normalize_log(raw: dict[str, Any]) -> dict[str, str] | None:
    employee_id = _extract_field(raw, "employee_id", "emp_code", "employee.code", "user_id")
    event_raw = _extract_field(raw, "event_type", "event_code", "event", "event.id", "punch")
    timestamp = _extract_field(raw, "timestamp", "event_time", "event.ts", "occurred_at", "datetime")
    device_id = _extract_field(raw, "device_id", "terminal_id", "device.serial", "source_device")

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
