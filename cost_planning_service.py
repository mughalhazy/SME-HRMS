from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from uuid import uuid4

from event_contract import EventRegistry, emit_canonical_event
from tenant_support import normalize_tenant_id


@dataclass(slots=True)
class CostPlan:
    plan_id: str
    tenant_id: str
    owner_employee_id: str
    fiscal_period: str
    amount: float
    status: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CostPlanningService:
    def __init__(self) -> None:
        self.plans: dict[str, CostPlan] = {}
        self.events: list[dict[str, Any]] = []
        self.event_registry = EventRegistry()
        self._lock = RLock()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def submit_plan(self, payload: dict[str, Any], *, correlation_id: str | None = None) -> dict[str, Any]:
        tenant_id = normalize_tenant_id(payload.get("tenant_id"))
        owner_employee_id = str(payload.get("owner_employee_id") or "").strip()
        fiscal_period = str(payload.get("fiscal_period") or "").strip()
        if not owner_employee_id or not fiscal_period:
            raise ValueError("owner_employee_id and fiscal_period are required")

        amount = float(payload.get("amount") or 0)
        now = self._now()
        plan = CostPlan(
            plan_id=str(uuid4()),
            tenant_id=tenant_id,
            owner_employee_id=owner_employee_id,
            fiscal_period=fiscal_period,
            amount=amount,
            status="Submitted",
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self.plans[plan.plan_id] = plan
            plan_payload = plan.to_dict()
            self._emit("CostPlanningPlanSubmitted", plan_payload, tenant_id=tenant_id, correlation_id=correlation_id, aggregate_id=plan.plan_id)
        return plan_payload

    def decide_plan(self, plan_id: str, *, action: str, correlation_id: str | None = None) -> dict[str, Any]:
        with self._lock:
            plan = self.plans[plan_id]
            if action == "approve":
                plan.status = "Approved"
                event_name = "CostPlanningPlanApproved"
            elif action == "reject":
                plan.status = "Rejected"
                event_name = "CostPlanningPlanRejected"
            else:
                raise ValueError("action must be approve or reject")
            plan.updated_at = self._now()
            self.plans[plan_id] = plan
            plan_payload = plan.to_dict()
            self._emit(event_name, plan_payload, tenant_id=plan.tenant_id, correlation_id=correlation_id, aggregate_id=plan.plan_id)
        return plan_payload

    def _emit(self, legacy_event_name: str, data: dict[str, Any], *, tenant_id: str, correlation_id: str | None, aggregate_id: str) -> None:
        emit_canonical_event(
            self.events,
            legacy_event_name=legacy_event_name,
            source="cost-planning-service",
            tenant_id=tenant_id,
            data=data,
            correlation_id=correlation_id,
            registry=self.event_registry,
            aliases={"aggregate_id": aggregate_id},
        )
