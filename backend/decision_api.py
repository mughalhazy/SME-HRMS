from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from api_contract import error_payload, success_payload
from event_contract import EventRegistry, emit_canonical_event
from tenant_support import DEFAULT_TENANT_ID
from services.decision_engine import DecisionCard, DecisionEngine
from services.governance.service import GovernanceService, GovernanceError
from services.ai.payroll_guardian import PayrollGuardian
from services.ai.anomaly_engine import AnomalyEngine
from services.ai.hr_copilot import HRCopilot, AccessContext
from services.compliance_service import ComplianceService

SERVICE_NAME = "decision-service"

_ERROR_STATUS = {
    "NOT_FOUND": 404,
    "VALIDATION_ERROR": 422,
    "FORBIDDEN": 403,
    "PRECONDITION_FAILED": 412,
    "CONFLICT": 409,
}


def _ok(data: Any, status: int = 200) -> tuple[int, dict]:
    return status, success_payload(data, str(uuid.uuid4()), service=SERVICE_NAME)


def _err(code: str, message: str) -> tuple[int, dict]:
    return _ERROR_STATUS.get(code, 400), error_payload(code, message, str(uuid.uuid4()), service=SERVICE_NAME)


# ---------------------------------------------------------------------------
# In-process card store (replace with DB repository in production)
# ---------------------------------------------------------------------------

_cards: dict[str, dict[str, Any]] = {}   # card_id → card dict
_engine = DecisionEngine()
_guardian = PayrollGuardian()
_anomaly_engine = AnomalyEngine()
_governance = GovernanceService()
_compliance_service = ComplianceService()
_outbox: list[dict] = []
_registry = EventRegistry()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _risk_level(risk_score: float) -> str:
    if risk_score >= 70:
        return "high"
    if risk_score >= 40:
        return "medium"
    return "low"


def _store_card(card: DecisionCard, extra: dict | None = None) -> dict:
    card_id = str(uuid.uuid4())
    data = card.to_dict()
    data["card_id"] = card_id
    data.update(extra or {})
    _cards[card_id] = data
    return data


# ---------------------------------------------------------------------------
# GET /api/v1/decisions/cards
# ---------------------------------------------------------------------------

def list_decision_cards(
    authorization: str | None = None,
    query: dict[str, Any] | None = None,
) -> tuple[int, dict]:
    params = query or {}
    results = list(_cards.values())

    domain = params.get("domain")
    status = params.get("status")
    risk_level = params.get("risk_level")
    employee_id = params.get("employee_id")
    period = params.get("period")
    limit = int(params.get("limit", 50))

    if domain:
        results = [c for c in results if c.get("domain") == domain]
    if status:
        results = [c for c in results if c.get("status") == status]
    if risk_level:
        results = [c for c in results if _risk_level(c.get("confidence", 0)) == risk_level]
    if employee_id:
        results = [c for c in results if c.get("employee_id") == employee_id]
    if period:
        results = [c for c in results if c.get("period") == period]

    cursor = params.get("cursor")
    if cursor:
        ids = sorted(_cards.keys())
        start = ids.index(cursor) + 1 if cursor in ids else 0
        results = [c for c in results if c.get("card_id") in ids[start:]]

    return _ok({"items": results[:limit], "count": len(results[:limit])})


# ---------------------------------------------------------------------------
# GET /api/v1/decisions/cards/{card_id}
# ---------------------------------------------------------------------------

def get_decision_card(
    card_id: str,
    authorization: str | None = None,
) -> tuple[int, dict]:
    card = _cards.get(card_id)
    if card is None:
        return _err("NOT_FOUND", f"Decision card {card_id} not found")
    return _ok(card)


# ---------------------------------------------------------------------------
# POST /api/v1/decisions/cards/{card_id}/acknowledge
# ---------------------------------------------------------------------------

def acknowledge_card(
    card_id: str,
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    card = _cards.get(card_id)
    if card is None:
        return _err("NOT_FOUND", f"Decision card {card_id} not found")
    if card.get("status") not in ("open", "active"):
        return _err("PRECONDITION_FAILED", f"Card {card_id} cannot be acknowledged in status '{card.get('status')}'")

    actor = payload.get("actor", "api")
    card["status"] = "acknowledged"
    card["acknowledged_by"] = actor
    card["acknowledged_at"] = _now()
    _governance._audit(user=actor, action="decision_card_acknowledged", reason=f"card_id={card_id}")
    emit_canonical_event(
        _outbox,
        legacy_event_name="DecisionCardAcknowledged",
        data={"card_id": card_id, "actor": actor},
        source="decision-service",
        tenant_id=card.get("employee_id") or DEFAULT_TENANT_ID,
        registry=_registry,
    )
    return _ok(card)


# ---------------------------------------------------------------------------
# POST /api/v1/decisions/cards/{card_id}/override
# ---------------------------------------------------------------------------

def override_card(
    card_id: str,
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    """Human-in-loop override. Requires actor identity and non-empty reason."""
    card = _cards.get(card_id)
    if card is None:
        return _err("NOT_FOUND", f"Decision card {card_id} not found")

    actor = payload.get("actor", "").strip()
    reason = payload.get("reason", "").strip()
    if not actor:
        return _err("VALIDATION_ERROR", "actor is required for override")
    if not reason:
        return _err("VALIDATION_ERROR", "reason is required for override — human-in-loop gate enforced")

    try:
        anomaly_ref = {"card_id": card_id, "status": card.get("status"), "impact": card.get("impact")}
        _governance.override_anomaly(anomaly_ref, user=actor, reason=reason)
    except GovernanceError as exc:
        return _err("PRECONDITION_FAILED", str(exc))

    card["status"] = "overridden"
    card["override_actor"] = actor
    card["override_reason"] = reason
    card["override_at"] = _now()
    emit_canonical_event(
        _outbox,
        legacy_event_name="DecisionCardOverridden",
        data={"card_id": card_id, "actor": actor, "reason": reason},
        source="decision-service",
        tenant_id=card.get("employee_id") or DEFAULT_TENANT_ID,
        registry=_registry,
    )
    return _ok(card)


# ---------------------------------------------------------------------------
# POST /api/v1/decisions/cards/{card_id}/dismiss
# ---------------------------------------------------------------------------

def dismiss_card(
    card_id: str,
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    card = _cards.get(card_id)
    if card is None:
        return _err("NOT_FOUND", f"Decision card {card_id} not found")

    actor = payload.get("actor", "api")
    reason = payload.get("reason", "dismissed by operator")
    card["status"] = "dismissed"
    card["dismissed_by"] = actor
    card["dismissed_reason"] = reason
    card["dismissed_at"] = _now()
    _governance._audit(user=actor, action="decision_card_dismissed", reason=reason)
    emit_canonical_event(
        _outbox,
        legacy_event_name="DecisionCardDismissed",
        data={"card_id": card_id, "actor": actor, "reason": reason},
        source="decision-service",
        tenant_id=card.get("employee_id") or DEFAULT_TENANT_ID,
        registry=_registry,
    )
    return _ok(card)


# ---------------------------------------------------------------------------
# GET /api/v1/decisions/anomalies
# ---------------------------------------------------------------------------

def list_anomalies(
    authorization: str | None = None,
    query: dict[str, Any] | None = None,
) -> tuple[int, dict]:
    """Return anomaly signals from stored decision cards."""
    params = query or {}
    anomaly_type = params.get("type")
    period = params.get("period")
    risk_level = params.get("risk_level")
    limit = int(params.get("limit", 50))

    cards = list(_cards.values())
    if anomaly_type:
        cards = [c for c in cards if anomaly_type in c.get("trigger", "")]
    if period:
        cards = [c for c in cards if c.get("period") == period]
    if risk_level:
        cards = [c for c in cards if _risk_level(c.get("confidence", 0)) == risk_level]

    return _ok({"items": cards[:limit], "count": len(cards[:limit])})


# ---------------------------------------------------------------------------
# POST /api/v1/decisions/scan
# ---------------------------------------------------------------------------

def trigger_scan(
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    """
    On-demand anomaly scan for a pay period.
    Accepts payroll_batch and generates Decision Cards via PayrollGuardian + DecisionEngine.
    """
    payroll_batch = payload.get("payroll_batch", {})
    period = payload.get("period", "")
    actor = payload.get("actor", "api")

    employees = payroll_batch.get("employees", [])
    if not employees:
        return _err("VALIDATION_ERROR", "payroll_batch.employees is required for scan")

    raw_anomalies: list[dict] = []
    for emp in employees:
        employee_id = str(emp.get("employee_id", ""))

        # 1. Salary spike
        current_salary = float(emp.get("current_salary", 0))
        historical_avg = float(emp.get("historical_average_salary", current_salary))
        promotion = bool(emp.get("promotion_event", False))
        spike = _guardian.detect_salary_spike(
            current_salary=current_salary,
            historical_average_salary=historical_avg,
            promotion_event=promotion,
        )
        if spike.get("risk_score", 0) >= 30:
            spike.update({"employee_id": employee_id, "period": period, "anomaly_type": "salary_spike"})
            raw_anomalies.append(spike)

        # 2. Overtime spike (correct method name: detect_overtime_spike)
        overtime_hours = float(emp.get("overtime_hours", 0))
        baseline_overtime = float(emp.get("baseline_overtime_hours", 1))
        if overtime_hours > 0:
            ot = _guardian.detect_overtime_spike(
                current_overtime_hours=overtime_hours,
                historical_average_overtime_hours=baseline_overtime,
            )
            if ot.get("risk_score", 0) >= 30:
                ot.update({"employee_id": employee_id, "period": period, "anomaly_type": "overtime_anomaly"})
                raw_anomalies.append(ot)

        # 3. Missing tax deduction
        expected_tax = float(emp.get("expected_tax", 0))
        actual_tax = float(emp.get("actual_tax", 0))
        if expected_tax > 0:
            tax = _guardian.detect_missing_tax(
                expected_tax_amount=expected_tax,
                actual_tax_amount=actual_tax,
            )
            if tax.get("risk_score", 0) >= 30:
                tax.update({"employee_id": employee_id, "period": period, "anomaly_type": "missing_deductions"})
                raw_anomalies.append(tax)

        # 4. Ghost employee
        is_active = bool(emp.get("is_active_employee", True))
        has_duplicate = bool(emp.get("has_duplicate_identity", False))
        days_inactive = int(emp.get("days_since_last_attendance", 0))
        if not is_active or has_duplicate or days_inactive > 30:
            ghost = _guardian.detect_ghost_employee(
                is_active_employee=is_active,
                has_duplicate_identity=has_duplicate,
                days_since_last_attendance=days_inactive,
            )
            if ghost.get("risk_score", 0) >= 30:
                ghost.update({"employee_id": employee_id, "period": period, "anomaly_type": "ghost_employee"})
                raw_anomalies.append(ghost)

    cards_created = []
    if raw_anomalies:
        for anomaly in raw_anomalies:
            emit_canonical_event(
                _outbox,
                legacy_event_name="AnomalyDetected",
                data={"employee_id": anomaly.get("employee_id", ""), "period": period,
                      "anomaly_type": anomaly.get("anomaly_type", ""), "risk_score": anomaly.get("risk_score", 0)},
                source="decision-service",
                tenant_id=anomaly.get("employee_id") or DEFAULT_TENANT_ID,
                registry=_registry,
            )
        new_cards = _engine.generate_from_ai_payroll_guardian(raw_anomalies)
        for card in new_cards:
            emp_id = raw_anomalies[len(cards_created)].get("employee_id", "") if len(cards_created) < len(raw_anomalies) else ""
            stored = _store_card(card, extra={
                "domain": "payroll",
                "employee_id": emp_id,
                "period": period,
                "risk_level": _risk_level(card.confidence),
            })
            emit_canonical_event(
                _outbox,
                legacy_event_name="DecisionCardCreated",
                data={"card_id": stored["card_id"], "employee_id": emp_id, "period": period,
                      "risk_level": stored.get("risk_level"), "domain": "payroll"},
                source="decision-service",
                tenant_id=emp_id or DEFAULT_TENANT_ID,
                registry=_registry,
            )
            cards_created.append(stored)

    _governance._audit(
        user=actor,
        action="anomaly_scan_completed",
        reason=f"period={period}, employees_scanned={len(employees)}, anomalies={len(raw_anomalies)}",
    )

    return _ok({
        "period": period,
        "employees_scanned": len(employees),
        "anomalies_detected": len(raw_anomalies),
        "cards_created": len(cards_created),
        "cards": cards_created,
    }, status=201)


# ---------------------------------------------------------------------------
# POST /api/v1/decisions/copilot
# (G20 - HR Copilot explainable Q&A)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Human-in-loop payroll gate (G22)
# Call this before marking payroll as Processed/Paid for a period.
# Returns (blocked: bool, open_high_risk_count: int, card_ids: list)
# Usage in payroll_service.py mark_paid():
#   from decision_api import check_payroll_gate
#   blocked, count, ids = check_payroll_gate(period, organization_id)
#   if blocked: raise ServiceError("HUMAN_IN_LOOP_GATE", f"{count} open High-risk cards require review", 409)
# ---------------------------------------------------------------------------

def check_payroll_gate(period: str, organization_id: str) -> tuple[bool, int, list[str]]:
    """
    Human-in-loop gate: checks for open High-risk Decision Cards for the given period/org.
    Returns (blocked, open_high_risk_count, card_ids).
    Payroll finalization must be blocked if blocked=True.
    """
    open_high_risk = [
        c for c in _cards.values()
        if c.get("period") == period
        and c.get("status") in ("open", "active")
        and _risk_level(c.get("confidence", 0)) == "high"
    ]
    return bool(open_high_risk), len(open_high_risk), [c["card_id"] for c in open_high_risk]


# ---------------------------------------------------------------------------
# Decision expiry sweep (S8-G06)
# Enforces expires_at on all stored decision cards.
# Must be called on a schedule — register via background_jobs_api.py.
# BEHAVIOR SPEC §06: decision expiry must be enforced, not decorative.
# ---------------------------------------------------------------------------

def expire_overdue_decisions() -> dict:
    """
    Sweep all stored decision cards and expire any that have passed their expires_at timestamp.
    Returns a summary of how many cards were expired.

    Register this as a recurring background job (e.g. every 15 minutes).
    """
    now = _now()
    expired_ids: list[str] = []
    skipped: int = 0

    for card_id, card_data in list(_cards.items()):
        expires_at = card_data.get("expires_at")
        status = card_data.get("status", "active")

        # Only act on non-terminal cards that have passed their expiry time
        if status in ("expired", "resolved", "overridden"):
            skipped += 1
            continue
        if expires_at and expires_at < now:
            # Reconstruct a minimal DecisionCard to call expire_card() cleanly
            from services.decision_engine import DecisionCard, DecisionSeverity
            card_obj = DecisionCard(
                trigger=str(card_data.get("trigger", "")),
                impact=str(card_data.get("impact", "")),
                confidence=float(card_data.get("confidence", 0)),
                recommended_action=str(card_data.get("recommended_action", "")),
                reversibility=str(card_data.get("reversibility", "reversible")),
                expires_at=str(expires_at),
                source_domain=str(card_data.get("source_domain", "system")),
                severity=DecisionSeverity(card_data.get("severity", "passive")),
                status=status,
                audit_history=list(card_data.get("audit_history", [])),
            )
            _engine.expire_card(card_obj, reason="ttl_exceeded")
            # Write back the expired state to the store
            card_data["status"] = "expired"
            card_data["updated_at"] = now
            card_data["audit_history"] = card_obj.audit_history
            _cards[card_id] = card_data
            expired_ids.append(card_id)
            emit_canonical_event(
                _outbox,
                legacy_event_name="DecisionCardExpired",
                data={"card_id": card_id, "reason": "ttl_exceeded",
                      "employee_id": card_data.get("employee_id", "")},
                source="decision-service",
                tenant_id=card_data.get("employee_id") or DEFAULT_TENANT_ID,
                registry=_registry,
            )

    return {
        "expired_count": len(expired_ids),
        "skipped_count": skipped,
        "expired_card_ids": expired_ids,
        "swept_at": now,
    }


def post_copilot_query(
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    """
    HR Copilot: explainable answers to HR queries (salary breakdown, leave balance, tax explanation).
    Requires actor_role for access control.
    """
    query = payload.get("query", "").strip()
    employee_id = payload.get("employee_id", "").strip()
    actor_role = payload.get("actor_role", "").strip()
    payroll_data = payload.get("payroll_data", {})
    compliance_data = payload.get("compliance_data", {})

    if not query or not employee_id or not actor_role:
        return _err("VALIDATION_ERROR", "query, employee_id, and actor_role are required")

    try:
        copilot = HRCopilot(payroll_data=payroll_data, compliance_data=compliance_data)
        result = copilot.answer_query(
            query=query,
            employee_id=employee_id,
            context=AccessContext(actor_role=actor_role),
        )
    except PermissionError as exc:
        return _err("FORBIDDEN", str(exc))
    except ValueError as exc:
        return _err("VALIDATION_ERROR", str(exc))

    return _ok({"query": query, "employee_id": employee_id, **result})


# ---------------------------------------------------------------------------
# MN-G06: GET /decisions/compliance-readiness
# Proactive compliance readiness check — returns a Decision Card if employee
# records will block payroll, or a clean signal if all are ready.
# Aligned to §11B UX pattern: "3 employees have missing EOBI numbers".
# ---------------------------------------------------------------------------

def get_compliance_readiness(payload: dict[str, Any]) -> tuple[int, dict]:
    """
    POST /decisions/compliance-readiness

    Body: {organization_id, legal_entity_id, period, payroll_input: {employee_records: [...]}}

    Returns a Decision Card if compliance violations are found, or a clean-all-clear
    response if every employee is ready for payroll finalization.
    """
    organization_id = str(payload.get("organization_id") or "").strip()
    legal_entity_id = str(payload.get("legal_entity_id") or "").strip()
    period = str(payload.get("period") or "").strip()
    payroll_input = payload.get("payroll_input", {})

    if not organization_id or not legal_entity_id or not period:
        return _err("VALIDATION_ERROR", "organization_id, legal_entity_id, and period are required")

    try:
        card = _compliance_service.get_compliance_readiness_card(
            organization_id=organization_id,
            legal_entity_id=legal_entity_id,
            period=period,
            payroll_input=payroll_input,
        )
    except Exception as exc:
        return _err("VALIDATION_ERROR", str(exc))

    if card is None:
        return _ok({
            "compliance_ready": True,
            "period": period,
            "message": "All employee records pass compliance validation. Payroll can proceed.",
            "affected_count": 0,
        })

    return _ok({
        "compliance_ready": False,
        "decision_card": card,
    })
