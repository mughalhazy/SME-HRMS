from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


class GovernanceError(ValueError):
    """Raised when a governance decision violates policy constraints."""


@dataclass
class GovernanceAction:
    user: str
    action: str
    timestamp: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {
            "user": self.user,
            "action": self.action,
            "timestamp": self.timestamp,
            "reason": self.reason,
        }


class GovernanceService:
    """Governance lifecycle aligned to docs/canon/decision-system.md."""

    def __init__(self) -> None:
        self.audit_trail: list[GovernanceAction] = []

    def create_payroll_approval(self, *, user: str, reason: str = "") -> dict[str, object]:
        approval = {
            "status": "pending",
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self._audit(user=user, action="payroll_approval_created", reason=reason or "created")
        return approval

    def review_payroll_approval(self, approval: dict[str, object], *, user: str, decision: str, reason: str) -> dict[str, object]:
        if approval.get("status") != "pending":
            raise GovernanceError("payroll_approval_must_be_pending")
        normalized = decision.strip().lower()
        if normalized not in {"approved", "rejected"}:
            raise GovernanceError("invalid_payroll_approval_decision")

        approval["status"] = normalized
        approval["updated_at"] = self._now()
        self._audit(user=user, action=f"payroll_approval_{normalized}", reason=reason)
        return approval

    def submit_compliance(self, approval: dict[str, object], *, user: str, reason: str = "") -> dict[str, str]:
        if approval.get("status") != "approved":
            raise GovernanceError("compliance_submission_requires_approved_payroll")
        self._audit(user=user, action="compliance_submitted", reason=reason or "submission approved")
        return {"status": "submitted"}

    def override_anomaly(self, anomaly: dict[str, object], *, user: str, reason: str) -> dict[str, object]:
        if not reason.strip():
            raise GovernanceError("anomaly_override_reason_required")
        anomaly["override"] = True
        anomaly["override_reason"] = reason
        anomaly["override_user"] = user
        anomaly["override_at"] = self._now()
        self._audit(user=user, action="anomaly_override", reason=reason)
        return anomaly

    def update_decision(self, decision_card: dict[str, object], *, user: str, reason: str, **changes: object) -> dict[str, object]:
        if decision_card.get("lifecycle_state") == "expire":
            raise GovernanceError("expired_decision_cards_are_immutable")
        decision_card.update(changes)
        decision_card["lifecycle_state"] = "update"
        decision_card["updated_at"] = self._now()
        self._audit(user=user, action="decision_updated", reason=reason)
        return decision_card

    def expire_decision(self, decision_card: dict[str, object], *, user: str, reason: str) -> dict[str, object]:
        decision_card["lifecycle_state"] = "expire"
        decision_card["updated_at"] = self._now()
        self._audit(user=user, action="decision_expired", reason=reason)
        return decision_card

    def _audit(self, *, user: str, action: str, reason: str) -> None:
        self.audit_trail.append(
            GovernanceAction(
                user=user,
                action=action,
                timestamp=self._now(),
                reason=reason,
            )
        )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
