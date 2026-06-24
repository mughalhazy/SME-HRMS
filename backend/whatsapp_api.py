from __future__ import annotations

import uuid
from typing import Any

from api_contract import error_payload, success_payload
from whatsapp_service import WhatsAppService

SERVICE_NAME = "whatsapp-service"

_ERROR_STATUS = {
    "NOT_FOUND": 404,
    "VALIDATION_ERROR": 422,
    "CONFLICT": 409,
    "FORBIDDEN": 403,
}


def _ok(data: Any, status: int = 200) -> tuple[int, dict]:
    return status, success_payload(data, str(uuid.uuid4()), service=SERVICE_NAME)


def _err(code: str, message: str) -> tuple[int, dict]:
    return _ERROR_STATUS.get(code, 400), error_payload(code, message, str(uuid.uuid4()), service=SERVICE_NAME)


# ---------------------------------------------------------------------------
# POST /api/v1/whatsapp/webhook
# ---------------------------------------------------------------------------

def post_webhook(
    service: WhatsAppService,
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    """Inbound WhatsApp message handler (WhatsApp provider callback)."""
    status, data = service.process_inbound(payload)
    return _ok(data, status=status)


# ---------------------------------------------------------------------------
# POST /api/v1/whatsapp/identity/register
# ---------------------------------------------------------------------------

def post_identity_register(
    service: WhatsAppService,
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    """Register phone ↔ employee mapping. Issues OTP."""
    required = ("employee_id", "phone_e164")
    missing = [k for k in required if not payload.get(k)]
    if missing:
        return _err("VALIDATION_ERROR", f"Missing required fields: {', '.join(missing)}")
    try:
        mapping = service.register_identity(
            employee_id=payload["employee_id"],
            phone_e164=payload["phone_e164"],
            actor=payload.get("actor", "api"),
        )
    except ValueError as exc:
        msg = str(exc)
        code = "CONFLICT" if "already mapped" in msg else "VALIDATION_ERROR"
        return _err(code, msg)
    return _ok({
        "mapping_id": mapping.mapping_id,
        "employee_id": mapping.employee_id,
        "phone_e164": mapping.phone_e164,
        "status": mapping.status,
        "otp_expires_at": mapping.otp_expires_at,
        "created_at": mapping.created_at,
    }, status=201)


# ---------------------------------------------------------------------------
# POST /api/v1/whatsapp/identity/verify
# ---------------------------------------------------------------------------

def post_identity_verify(
    service: WhatsAppService,
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    """Verify OTP and activate identity mapping."""
    employee_id = payload.get("employee_id", "").strip()
    otp_code = payload.get("otp_code", "").strip()
    if not employee_id or not otp_code:
        return _err("VALIDATION_ERROR", "employee_id and otp_code are required")
    try:
        mapping = service.verify_identity(
            employee_id=employee_id,
            otp_code=otp_code,
            verified_by=payload.get("verified_by", "api"),
        )
    except ValueError as exc:
        return _err("VALIDATION_ERROR", str(exc))
    return _ok({
        "employee_id": mapping.employee_id,
        "phone_e164": mapping.phone_e164,
        "status": mapping.status,
        "verified_at": mapping.verified_at,
    })


# ---------------------------------------------------------------------------
# DELETE /api/v1/whatsapp/identity/{employee_id}
# ---------------------------------------------------------------------------

def delete_identity(
    service: WhatsAppService,
    employee_id: str,
    authorization: str | None = None,
) -> tuple[int, dict]:
    """Revoke phone mapping for an employee."""
    try:
        result = service.revoke_identity(employee_id, actor="api")
    except ValueError as exc:
        return _err("NOT_FOUND", str(exc))
    return _ok(result)


# ---------------------------------------------------------------------------
# GET /api/v1/whatsapp/identity/{employee_id}
# ---------------------------------------------------------------------------

def get_identity(
    service: WhatsAppService,
    employee_id: str,
    authorization: str | None = None,
) -> tuple[int, dict]:
    """Retrieve identity mapping status."""
    mapping = service.get_identity(employee_id)
    if mapping is None:
        return _err("NOT_FOUND", f"No identity mapping found for employee {employee_id}")
    return _ok({
        "mapping_id": mapping.mapping_id,
        "employee_id": mapping.employee_id,
        "phone_e164": mapping.phone_e164,
        "status": mapping.status,
        "verified_at": mapping.verified_at,
        "last_seen_at": mapping.last_seen_at,
        "created_at": mapping.created_at,
    })


# ---------------------------------------------------------------------------
# POST /api/v1/whatsapp/send
# ---------------------------------------------------------------------------

def post_send_message(
    service: WhatsAppService,
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    """Outbound message dispatch (system → employee)."""
    required = ("employee_id", "message_type", "text")
    missing = [k for k in required if not payload.get(k)]
    if missing:
        return _err("VALIDATION_ERROR", f"Missing required fields: {', '.join(missing)}")
    try:
        result = service.send_message(
            employee_id=payload["employee_id"],
            message_type=payload["message_type"],
            text=payload["text"],
            extra=payload.get("extra"),
            actor=payload.get("actor", "api"),
        )
    except ValueError as exc:
        return _err("NOT_FOUND", str(exc))
    return _ok(result, status=201)


# ---------------------------------------------------------------------------
# GET /api/v1/whatsapp/conversations
# ---------------------------------------------------------------------------

def get_conversations(
    service: WhatsAppService,
    authorization: str | None = None,
    query: dict[str, Any] | None = None,
) -> tuple[int, dict]:
    """Conversation log for audit and analytics."""
    params = query or {}
    events = service.list_conversations(
        employee_id=params.get("employee_id"),
        from_dt=params.get("from"),
        to_dt=params.get("to"),
        limit=int(params.get("limit", 50)),
        cursor=params.get("cursor"),
    )
    return _ok({
        "items": [
            {
                "event_id": e.event_id,
                "session_id": e.session_id,
                "employee_id": e.employee_id,
                "direction": e.direction,
                "message_type": e.message_type,
                "intent": e.intent,
                "recorded_at": e.recorded_at,
            }
            for e in events
        ],
        "count": len(events),
    })


# ---------------------------------------------------------------------------
# GET /api/v1/whatsapp/sessions/{session_id}
# ---------------------------------------------------------------------------

def get_session(
    service: WhatsAppService,
    session_id: str,
    authorization: str | None = None,
) -> tuple[int, dict]:
    """Retrieve active session state."""
    session = service.get_session(session_id)
    if session is None:
        return _err("NOT_FOUND", f"Session {session_id} not found")
    return _ok({
        "session_id": session.session_id,
        "employee_id": session.employee_id,
        "phone_e164": session.phone_e164,
        "role_context": session.role_context,
        "state": session.state,
        "last_activity_at": session.last_activity_at,
        "expires_at": session.expires_at,
        "created_at": session.created_at,
    })
