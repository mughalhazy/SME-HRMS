from __future__ import annotations

from datetime import datetime
from typing import Any


def ingest_device_logs(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize biometric device logs for attendance ingestion."""

    logs = []
    rejected = 0
    for log in list(payload.get("logs", [])):
        employee_id = str(log.get("employee_id", "")).strip()
        event_type = str(log.get("event_type", "")).strip().lower()
        timestamp = str(log.get("timestamp", "")).strip()
        if not employee_id or not event_type or not timestamp:
            rejected += 1
            continue

        try:
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            rejected += 1
            continue

        logs.append(
            {
                "employee_id": employee_id,
                "event_type": event_type,
                "timestamp": timestamp,
                "device_id": str(log.get("device_id", "")),
                "source": "biometric_device",
            }
        )

    return {
        "status": "success",
        "accepted_logs": len(logs),
        "rejected_logs": rejected,
        "logs": logs,
    }
