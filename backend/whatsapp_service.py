from __future__ import annotations

import random
import string
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from event_contract import EventRegistry, emit_canonical_event
from integrations.whatsapp.webhook import receive_message, parse_intent
from tenant_support import DEFAULT_TENANT_ID


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

@dataclass
class WhatsAppIdentityMap:
    mapping_id: str
    employee_id: str
    phone_e164: str
    status: str = "pending"          # pending | active | revoked
    otp_code: str | None = None
    otp_expires_at: str | None = None
    verified_at: str | None = None
    verified_by: str | None = None
    last_seen_at: str | None = None
    created_at: str = field(default_factory=lambda: _now())
    updated_at: str = field(default_factory=lambda: _now())


@dataclass
class WhatsAppSession:
    session_id: str
    employee_id: str
    phone_e164: str
    role_context: str = "employee"   # employee | manager
    state: dict = field(default_factory=dict)
    last_activity_at: str = field(default_factory=lambda: _now())
    expires_at: str = field(default_factory=lambda: _session_expiry())
    created_at: str = field(default_factory=lambda: _now())


@dataclass
class WhatsAppConversationEvent:
    event_id: str
    session_id: str
    employee_id: str
    direction: str                    # inbound | outbound
    message_type: str
    intent: str | None = None
    payload: dict = field(default_factory=dict)
    recorded_at: str = field(default_factory=lambda: _now())


# ---------------------------------------------------------------------------
# In-process stores (replace with DB repository in production)
# ---------------------------------------------------------------------------

_identity_maps: dict[str, WhatsAppIdentityMap] = {}    # employee_id → mapping
_phone_index: dict[str, str] = {}                       # phone_e164 → employee_id
_sessions: dict[str, WhatsAppSession] = {}              # session_id → session
_conversation_log: list[WhatsAppConversationEvent] = []
_outbox: list[dict] = []
_registry = EventRegistry()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _session_expiry(minutes: int = 15) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def _otp_expiry(minutes: int = 5) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def _generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def _is_expired(iso_timestamp: str) -> bool:
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return datetime.now(timezone.utc) > dt
    except (ValueError, TypeError):
        return True


# ---------------------------------------------------------------------------
# WhatsAppService
# ---------------------------------------------------------------------------

class WhatsAppService:
    """
    Access channel service for WhatsApp-initiated HRMS workflows.

    Responsibilities:
    - Phone ↔ employee identity mapping with OTP verification.
    - Session management with inactivity timeout.
    - Inbound message processing (intent parsing + domain dispatch).
    - Outbound message dispatch.
    - Conversation audit log.

    Architecture: WhatsApp is a real channel. All actions here are subject to
    the same RBAC and audit trail as web UI actions.
    """

    # ------------------------------------------------------------------
    # Identity mapping
    # ------------------------------------------------------------------

    def register_identity(
        self,
        employee_id: str,
        phone_e164: str,
        actor: str = "system",
    ) -> WhatsAppIdentityMap:
        """
        Register phone ↔ employee mapping. Issues OTP for verification.
        One active mapping per phone — existing must be revoked first.
        """
        if not phone_e164.startswith("+"):
            raise ValueError("phone_e164 must be in E.164 format (e.g. +923001234567)")

        existing_employee = _phone_index.get(phone_e164)
        if existing_employee and existing_employee != employee_id:
            existing_map = _identity_maps.get(existing_employee)
            if existing_map and existing_map.status == "active":
                raise ValueError(f"Phone {phone_e164} is already mapped to another employee. Revoke that mapping first.")

        otp = _generate_otp()
        mapping = WhatsAppIdentityMap(
            mapping_id=str(uuid.uuid4()),
            employee_id=employee_id,
            phone_e164=phone_e164,
            status="pending",
            otp_code=otp,
            otp_expires_at=_otp_expiry(),
        )
        _identity_maps[employee_id] = mapping
        _phone_index[phone_e164] = employee_id
        emit_canonical_event(
            _outbox,
            legacy_event_name="WhatsAppIdentityRegistered",
            data={"employee_id": employee_id, "phone_e164": phone_e164},
            source="whatsapp-service",
            tenant_id=DEFAULT_TENANT_ID,
            registry=_registry,
        )
        # In production: dispatch OTP via WhatsApp Business API
        return mapping

    def verify_identity(
        self,
        employee_id: str,
        otp_code: str,
        verified_by: str = "system",
    ) -> WhatsAppIdentityMap:
        """Verify OTP and activate the identity mapping."""
        mapping = _identity_maps.get(employee_id)
        if mapping is None:
            raise ValueError(f"No identity mapping found for employee {employee_id}")
        if mapping.status == "active":
            return mapping
        if mapping.otp_code != otp_code:
            raise ValueError("Invalid OTP code")
        if _is_expired(mapping.otp_expires_at or ""):
            raise ValueError("OTP has expired. Request a new registration.")

        mapping.status = "active"
        mapping.otp_code = None
        mapping.otp_expires_at = None
        mapping.verified_at = _now()
        mapping.verified_by = verified_by
        mapping.updated_at = _now()
        emit_canonical_event(
            _outbox,
            legacy_event_name="WhatsAppIdentityVerified",
            data={"employee_id": employee_id, "phone_e164": mapping.phone_e164},
            source="whatsapp-service",
            tenant_id=DEFAULT_TENANT_ID,
            registry=_registry,
        )
        return mapping

    def revoke_identity(self, employee_id: str, actor: str = "system") -> dict:
        mapping = _identity_maps.get(employee_id)
        if mapping is None:
            raise ValueError(f"No identity mapping found for employee {employee_id}")
        mapping.status = "revoked"
        mapping.updated_at = _now()
        emit_canonical_event(
            _outbox,
            legacy_event_name="WhatsAppIdentityRevoked",
            data={"employee_id": employee_id, "phone_e164": mapping.phone_e164},
            source="whatsapp-service",
            tenant_id=DEFAULT_TENANT_ID,
            registry=_registry,
        )
        # Don't remove from phone_index; mark revoked so phone is available for re-use
        return {"employee_id": employee_id, "status": "revoked"}

    def get_identity(self, employee_id: str) -> WhatsAppIdentityMap | None:
        return _identity_maps.get(employee_id)

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def get_or_create_session(self, phone_e164: str, role_context: str = "employee") -> WhatsAppSession:
        employee_id = _phone_index.get(phone_e164)
        if not employee_id:
            raise ValueError(f"No identity mapping for phone {phone_e164}. Register first.")
        mapping = _identity_maps.get(employee_id)
        if not mapping or mapping.status != "active":
            raise ValueError(f"Identity not verified for phone {phone_e164}")

        # Return active non-expired session
        for session in _sessions.values():
            if session.employee_id == employee_id and not _is_expired(session.expires_at):
                session.last_activity_at = _now()
                session.expires_at = _session_expiry()
                return session

        # Create new session
        session = WhatsAppSession(
            session_id=str(uuid.uuid4()),
            employee_id=employee_id,
            phone_e164=phone_e164,
            role_context=role_context,
        )
        _sessions[session.session_id] = session
        mapping.last_seen_at = _now()
        emit_canonical_event(
            _outbox,
            legacy_event_name="WhatsAppSessionStarted",
            data={"session_id": session.session_id, "employee_id": employee_id,
                  "role_context": role_context},
            source="whatsapp-service",
            tenant_id=DEFAULT_TENANT_ID,
            registry=_registry,
        )
        return session

    def get_session(self, session_id: str) -> WhatsAppSession | None:
        return _sessions.get(session_id)

    # ------------------------------------------------------------------
    # Inbound message processing
    # ------------------------------------------------------------------

    def process_inbound(self, raw_payload: dict[str, Any]) -> tuple[int, dict]:
        """
        Process inbound WhatsApp message via webhook parser.
        Creates/refreshes session, logs conversation, returns outbound response.
        """
        message = raw_payload.get("message", {}) if isinstance(raw_payload, dict) else {}
        phone = str(message.get("from", "")).strip()

        # Try to get session (may fail if not registered)
        session = None
        employee_id = _phone_index.get(phone)
        if employee_id:
            try:
                session = self.get_or_create_session(phone)
            except ValueError:
                pass

        status, response = receive_message(raw_payload)

        # Log conversation event
        intent = response.get("meta", {}).get("intent") if isinstance(response.get("meta"), dict) else None
        event = WhatsAppConversationEvent(
            event_id=str(uuid.uuid4()),
            session_id=session.session_id if session else "unauthenticated",
            employee_id=employee_id or phone,
            direction="inbound",
            message_type=str(message.get("type", "text")),
            intent=intent,
            payload=raw_payload,
        )
        _conversation_log.append(event)
        emit_canonical_event(
            _outbox,
            legacy_event_name="WhatsAppMessageReceived",
            data={"session_id": event.session_id, "employee_id": event.employee_id,
                  "intent": intent, "message_type": event.message_type},
            source="whatsapp-service",
            tenant_id=DEFAULT_TENANT_ID,
            registry=_registry,
        )

        return status, response

    # ------------------------------------------------------------------
    # Outbound message dispatch
    # ------------------------------------------------------------------

    def send_message(
        self,
        employee_id: str,
        message_type: str,
        text: str,
        extra: dict | None = None,
        actor: str = "system",
    ) -> dict:
        """
        Dispatch outbound message to employee's registered phone.
        In production: calls WhatsApp Business API.
        """
        mapping = _identity_maps.get(employee_id)
        if not mapping or mapping.status != "active":
            raise ValueError(f"No active WhatsApp identity for employee {employee_id}")

        outbound = {
            "to": mapping.phone_e164,
            "type": message_type,
            "text": text,
            **(extra or {}),
        }
        event = WhatsAppConversationEvent(
            event_id=str(uuid.uuid4()),
            session_id="system_dispatch",
            employee_id=employee_id,
            direction="outbound",
            message_type=message_type,
            payload=outbound,
        )
        _conversation_log.append(event)
        emit_canonical_event(
            _outbox,
            legacy_event_name="WhatsAppMessageSent",
            data={"employee_id": employee_id, "message_type": message_type,
                  "phone_e164": mapping.phone_e164},
            source="whatsapp-service",
            tenant_id=DEFAULT_TENANT_ID,
            registry=_registry,
        )
        return {"status": "queued", "to": mapping.phone_e164, "employee_id": employee_id}

    # ------------------------------------------------------------------
    # Conversation log
    # ------------------------------------------------------------------

    def list_conversations(
        self,
        employee_id: str | None = None,
        from_dt: str | None = None,
        to_dt: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> list[WhatsAppConversationEvent]:
        results = list(_conversation_log)
        if employee_id:
            results = [e for e in results if e.employee_id == employee_id]
        if from_dt:
            results = [e for e in results if e.recorded_at >= from_dt]
        if to_dt:
            results = [e for e in results if e.recorded_at <= to_dt]
        if cursor:
            ids = [e.event_id for e in results]
            start = ids.index(cursor) + 1 if cursor in ids else 0
            results = results[start:]
        return results[:limit]
