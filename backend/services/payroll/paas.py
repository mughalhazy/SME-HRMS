from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from payroll_service import PayrollService, ServiceError
from services.product.tier_enforcer import TierEnforcer


@dataclass(slots=True)
class AuditEntry:
    action: str
    actor_id: str
    actor_mode: str
    at: datetime
    details: dict[str, Any]


class PayrollManagedService:
    def __init__(self, payroll_service: PayrollService):
        self.payroll = payroll_service
        self.audit_log: list[AuditEntry] = []

    def run_payroll(
        self,
        *,
        tier: str,
        actor_id: str,
        actor_mode: str,
        period_start: str,
        period_end: str,
        authorization: str | None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        TierEnforcer(tier=tier).ensure_feature_access("payroll")  # type: ignore[arg-type]
        status, payload = self.payroll.run_payroll(period_start, period_end, authorization, trace_id=trace_id)
        self.audit_log.append(AuditEntry("paas_run_payroll", actor_id, actor_mode, datetime.now(timezone.utc), {"status": status}))
        return {"status_code": status, "result": payload.get("data", payload), "mode": actor_mode, "managed": True}

    def admin_override(
        self,
        *,
        tier: str,
        actor_id: str,
        payroll_record_id: str,
        authorization: str | None,
        payment_date: str | None = None,
        reason: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        TierEnforcer(tier=tier).ensure_tier_at_least("MID")  # type: ignore[arg-type]
        if not reason:
            raise ServiceError("VALIDATION_ERROR", "override reason is required", 422)
        status, payload = self.payroll.mark_paid(payroll_record_id, authorization, payment_date=payment_date, trace_id=trace_id)
        self.audit_log.append(
            AuditEntry("paas_admin_override", actor_id, "admin", datetime.now(timezone.utc), {"record_id": payroll_record_id, "reason": reason})
        )
        return {"status_code": status, "result": payload.get("data", payload), "override": True}

