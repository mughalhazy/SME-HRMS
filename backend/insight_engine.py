from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExplainableInsight:
    insight_type: str
    summary: str
    score: int
    confidence: int
    evidence: list[tuple[str, str, str]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "insight_type": self.insight_type,
            "summary": self.summary,
            "score": self.score,
            "confidence": self.confidence,
            "explanation": InsightEngine.format_explanation(
                insight_type=self.insight_type,
                summary=self.summary,
                evidence=self.evidence,
                score=self.score,
                confidence=self.confidence,
            ),
        }


class InsightEngine:
    """Generate explainable HR insights aligned with docs/canon/decision-system.md."""

    @staticmethod
    def _clamp(value: float, low: int = 0, high: int = 100) -> int:
        return max(low, min(high, int(round(value))))

    @staticmethod
    def _threshold_level(score: int) -> str:
        if score >= 70:
            return "high"
        if score >= 40:
            return "medium"
        return "low"

    @classmethod
    def format_explanation(
        cls,
        *,
        insight_type: str,
        summary: str,
        evidence: list[tuple[str, str, str]],
        score: int,
        confidence: int,
    ) -> str:
        lines = [
            "WHY_FLAGGED:",
            f"- anomaly_type: {insight_type}",
            f"- summary: {summary}",
            "- evidence:",
        ]
        for metric, value, expected in evidence:
            lines.append(f"  - {metric}: {value} (expected: {expected})")
        lines.extend(
            [
                f"- risk_score: {score}",
                f"- confidence: {confidence}%",
                f"- threshold_level: {cls._threshold_level(score)}",
            ]
        )
        return "\n".join(lines)

    def generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        attrition = self._attrition_risk(payload.get("attrition", {})).to_dict()
        overtime = self._overtime_trends(payload.get("overtime", {})).to_dict()
        payroll = self._payroll_anomalies(payload.get("payroll", {})).to_dict()

        return {
            "attrition_risk": attrition,
            "overtime_trends": overtime,
            "payroll_anomalies": payroll,
        }

    def _attrition_risk(self, data: dict[str, Any]) -> ExplainableInsight:
        tenure_months = max(0.0, float(data.get("tenure_months", 0)))
        engagement_score = max(0.0, min(100.0, float(data.get("engagement_score", 0))))
        manager_changes = max(0.0, float(data.get("manager_changes_last_year", 0)))

        risk = (max(0.0, 24 - tenure_months) * 1.4) + ((100 - engagement_score) * 0.55) + (manager_changes * 8)
        score = self._clamp(risk)
        confidence = self._clamp(60 + (manager_changes * 4) + ((100 - engagement_score) * 0.2))

        return ExplainableInsight(
            insight_type="attrition_risk",
            summary="Attrition risk is elevated by low engagement and workforce stability signals.",
            score=score,
            confidence=confidence,
            evidence=[
                ("engagement_score", f"{engagement_score:.1f}", ">= 70.0"),
                ("tenure_months", f"{tenure_months:.1f}", ">= 24.0"),
                ("manager_changes_last_year", f"{manager_changes:.0f}", "<= 1"),
            ],
        )

    def _overtime_trends(self, data: dict[str, Any]) -> ExplainableInsight:
        current_hours = max(0.0, float(data.get("current_month_hours", 0)))
        baseline_hours = max(1.0, float(data.get("baseline_month_hours", 1)))
        affected_team_pct = max(0.0, min(100.0, float(data.get("affected_team_percent", 0))))

        ratio = current_hours / baseline_hours
        trend_score = ((ratio - 1.0) * 45) + (affected_team_pct * 0.4)
        score = self._clamp(trend_score)
        confidence = self._clamp(55 + ((ratio - 1.0) * 20) + (affected_team_pct * 0.25))

        return ExplainableInsight(
            insight_type="overtime_trends",
            summary="Overtime trend exceeds expected baseline and should be reviewed for burnout/cost risk.",
            score=score,
            confidence=confidence,
            evidence=[
                ("current_month_hours", f"{current_hours:.1f}", f"{baseline_hours:.1f}"),
                ("overtime_ratio", f"{ratio:.2f}x", "<= 1.20x"),
                ("affected_team_percent", f"{affected_team_pct:.1f}%", "<= 20.0%"),
            ],
        )

    def _payroll_anomalies(self, data: dict[str, Any]) -> ExplainableInsight:
        anomaly_count = max(0.0, float(data.get("anomaly_count", 0)))
        payroll_records = max(1.0, float(data.get("payroll_records", 1)))
        unresolved_count = max(0.0, float(data.get("unresolved_count", 0)))

        anomaly_rate = (anomaly_count / payroll_records) * 100
        unresolved_rate = (unresolved_count / max(1.0, anomaly_count)) * 100 if anomaly_count else 0.0

        score = self._clamp((anomaly_rate * 1.8) + (unresolved_rate * 0.6))
        confidence = self._clamp(58 + (anomaly_rate * 0.9) + (unresolved_rate * 0.25))

        return ExplainableInsight(
            insight_type="payroll_anomalies",
            summary="Payroll anomalies indicate elevated integrity risk in the current cycle.",
            score=score,
            confidence=confidence,
            evidence=[
                ("anomaly_rate", f"{anomaly_rate:.2f}%", "<= 2.00%"),
                ("unresolved_rate", f"{unresolved_rate:.2f}%", "<= 25.00%"),
                ("anomaly_count", f"{anomaly_count:.0f}", "near 0"),
            ],
        )
