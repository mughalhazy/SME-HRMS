from __future__ import annotations

from typing import Any


def error_payload(code: str, message: str, trace_id: str, details: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "trace_id": trace_id,
        }
    }


def error_response(status: int, code: str, message: str, *, trace_id: str, details: list[dict[str, Any]] | None = None) -> tuple[int, dict[str, Any]]:
    return status, error_payload(code, message, trace_id, details)
