from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass
class DecisionCard:
    trigger: str
    impact: str
    confidence: float
    action: str
    expires_at: str
    status: str = "active"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    audit_history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trigger": self.trigger,
            "impact": self.impact,
            "confidence": self.confidence,
            "action": self.action,
            "expires_at": self.expires_at,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "audit_history": list(self.audit_history),
        }


class DecisionEngine:
    """Canonical decision-card manager for anomaly and compliance issue routing."""

    def __init__(self, default_ttl_hours: int = 24) -> None:
        self.default_ttl_hours = default_ttl_hours

    def generate_from_anomalies(self, anomalies: list[dict[str, Any]]) -> list[DecisionCard]:
        cards: list[DecisionCard] = []
        for anomaly in anomalies:
            anomaly_type = str(anomaly.get("type", "unknown_anomaly"))
            summary = str(anomaly.get("summary", "Anomaly detected by AI Payroll Guardian"))
            risk_score = float(anomaly.get("risk_score", 0))
            confidence = float(anomaly.get("confidence", 0))

            cards.append(
                self.create_card(
                    trigger=f"{anomaly_type}: {summary}",
                    impact=self._impact_for_risk(risk_score, anomaly),
                    confidence=confidence,
                    action=self._action_for_anomaly(anomaly_type, risk_score),
                )
            )
        return cards


    def generate_from_ai_payroll_guardian(self, anomalies: list[dict[str, Any]]) -> list[DecisionCard]:
        """Generate decision cards from explainable anomaly-engine output."""
        normalized: list[dict[str, Any]] = []
        for anomaly in anomalies:
            anomaly_type = str(anomaly.get("anomaly_type", anomaly.get("type", "unknown_anomaly")))
            explanation = str(anomaly.get("explanation", "")).strip()
            lines = explanation.splitlines()
            has_canonical_summary = explanation.startswith("WHY_FLAGGED:") and len(lines) >= 3
            summary = (
                lines[2].replace("- summary:", "").strip()
                if has_canonical_summary
                else str(anomaly.get("summary", "Anomaly detected by AI Payroll Guardian"))
            )
            normalized.append(
                {
                    "type": anomaly_type,
                    "summary": summary,
                    "risk_score": float(anomaly.get("risk_score", 0)),
                    "confidence": float(anomaly.get("confidence", 0)),
                    "estimate": anomaly.get("estimate"),
                }
            )
        return self.generate_from_anomalies(normalized)

    def generate_from_compliance_issues(self, issues: list[dict[str, Any]]) -> list[DecisionCard]:
        cards: list[DecisionCard] = []
        for issue in issues:
            code = str(issue.get("code", "COMPLIANCE_ISSUE"))
            message = str(issue.get("message", "Compliance issue detected"))
            severity = str(issue.get("severity", "medium")).lower()
            confidence = float(issue.get("confidence", 100.0))

            cards.append(
                self.create_card(
                    trigger=f"{code}: {message}",
                    impact=self._impact_for_severity(severity, issue),
                    confidence=confidence,
                    action=self._action_for_compliance_issue(severity, code),
                )
            )
        return cards

    def create_card(self, trigger: str, impact: str, confidence: float, action: str) -> DecisionCard:
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(hours=self.default_ttl_hours)).isoformat()
        card = DecisionCard(
            trigger=trigger,
            impact=impact,
            confidence=confidence,
            action=action,
            expires_at=expires_at,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
        )
        card.audit_history.append(
            {
                "event": "create",
                "timestamp": now.isoformat(),
                "snapshot": {
                    "trigger": trigger,
                    "impact": impact,
                    "confidence": confidence,
                    "action": action,
                    "expires_at": expires_at,
                    "status": card.status,
                },
            }
        )
        return card

    def update_card(self, card: DecisionCard, **changes: Any) -> DecisionCard:
        if card.status == "expired":
            compliance_note = changes.get("compliance_note")
            if compliance_note:
                card.audit_history.append(
                    {
                        "event": "compliance_annotation",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "note": str(compliance_note),
                    }
                )
                return card
            raise ValueError("Expired decision cards are immutable except for compliance annotations")

        before = card.to_dict()
        for field_name in ("trigger", "impact", "confidence", "action", "expires_at"):
            if field_name in changes:
                setattr(card, field_name, changes[field_name])

        card.updated_at = datetime.now(timezone.utc).isoformat()
        card.audit_history.append(
            {
                "event": "update",
                "timestamp": card.updated_at,
                "before": before,
                "after": card.to_dict(),
            }
        )
        return card

    def expire_card(self, card: DecisionCard, reason: str = "expired") -> DecisionCard:
        if card.status == "expired":
            return card

        card.status = "expired"
        card.updated_at = datetime.now(timezone.utc).isoformat()
        card.audit_history.append(
            {
                "event": "expire",
                "timestamp": card.updated_at,
                "reason": reason,
            }
        )
        return card

    @staticmethod
    def _impact_for_risk(risk_score: float, anomaly: dict[str, Any]) -> str:
        if risk_score >= 70:
            severity = "high"
        elif risk_score >= 40:
            severity = "medium"
        else:
            severity = "low"

        estimate = anomaly.get("estimate")
        if estimate is None:
            return f"{severity} payroll integrity impact"
        return f"{severity} payroll integrity impact (estimated {estimate})"

    @staticmethod
    def _impact_for_severity(severity: str, issue: dict[str, Any]) -> str:
        estimate = issue.get("estimate")
        if estimate is None:
            return f"{severity} compliance impact"
        return f"{severity} compliance impact (estimated {estimate})"

    @staticmethod
    def _action_for_anomaly(anomaly_type: str, risk_score: float) -> str:
        if anomaly_type == "ghost_employee" or risk_score >= 70:
            return "Place payroll hold and escalate for immediate review"
        if risk_score >= 40:
            return "Queue anomaly for analyst review within SLA"
        return "Log anomaly and monitor for recurrence"

    @staticmethod
    def _action_for_compliance_issue(severity: str, code: str) -> str:
        if severity == "high":
            return f"Block payroll release until {code} is resolved"
        if severity == "medium":
            return f"Assign compliance analyst to remediate {code}"
        return f"Document {code} and monitor next payroll cycle"
