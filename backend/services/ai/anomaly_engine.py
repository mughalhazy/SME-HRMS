from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AnomalySignal:
    anomaly_type: str
    summary: str
    evidence: list[tuple[str, str, str]]
    risk_score: int
    confidence: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "anomaly_type": self.anomaly_type,
            "risk_score": self.risk_score,
            "confidence": self.confidence,
            "explanation": AnomalyEngine.format_explanation(
                anomaly_type=self.anomaly_type,
                summary=self.summary,
                evidence=self.evidence,
                risk_score=self.risk_score,
                confidence=self.confidence,
            ),
        }


class AnomalyEngine:
    """Explainable payroll anomaly detector aligned with docs/canon/decision-system.md."""

    @staticmethod
    def _clamp(value: float, low: int = 0, high: int = 100) -> int:
        return max(low, min(high, int(round(value))))

    @staticmethod
    def threshold_level(risk_score: int) -> str:
        if risk_score >= 70:
            return "high"
        if risk_score >= 40:
            return "medium"
        return "low"

    @classmethod
    def format_explanation(
        cls,
        *,
        anomaly_type: str,
        summary: str,
        evidence: list[tuple[str, str, str]],
        risk_score: int,
        confidence: int,
    ) -> str:
        lines = [
            "WHY_FLAGGED:",
            f"- anomaly_type: {anomaly_type}",
            f"- summary: {summary}",
            "- evidence:",
        ]
        for metric, value, expected in evidence:
            lines.append(f"  - {metric}: {value} (expected: {expected})")
        lines.extend(
            [
                f"- risk_score: {risk_score}",
                f"- confidence: {confidence}%",
                f"- threshold_level: {cls.threshold_level(risk_score)}",
            ]
        )
        return "\n".join(lines)

    def detect_salary_spike(
        self,
        *,
        current_salary: float,
        historical_average_salary: float,
        promotion_event: bool = False,
    ) -> dict[str, Any]:
        baseline = historical_average_salary if historical_average_salary > 0 else 1
        spike_pct = ((current_salary - baseline) / baseline) * 100
        adjusted_spike_pct = max(0.0, spike_pct - (10.0 if promotion_event else 0.0))

        signal = AnomalySignal(
            anomaly_type="salary_spike",
            summary="Salary increase is materially above historical baseline.",
            evidence=[
                ("current_salary", f"{current_salary:.2f}", f"{baseline:.2f}"),
                ("spike_percent", f"{spike_pct:.1f}%", "<= 20.0%"),
            ],
            risk_score=self._clamp(adjusted_spike_pct * 2),
            confidence=self._clamp(55 + adjusted_spike_pct),
        )
        return signal.to_dict()

    def detect_overtime_anomaly(
        self,
        *,
        current_overtime_hours: float,
        historical_average_overtime_hours: float,
    ) -> dict[str, Any]:
        baseline = historical_average_overtime_hours if historical_average_overtime_hours > 0 else 1
        ratio = current_overtime_hours / baseline
        overage = max(0.0, current_overtime_hours - baseline)

        signal = AnomalySignal(
            anomaly_type="overtime_anomaly",
            summary="Overtime total deviates from historical work pattern.",
            evidence=[
                ("current_overtime_hours", f"{current_overtime_hours:.2f}", f"{baseline:.2f}"),
                ("overtime_ratio", f"{ratio:.2f}x", "<= 1.50x"),
            ],
            risk_score=self._clamp(((ratio - 1.0) * 35) + (overage * 1.2)),
            confidence=self._clamp(50 + ((ratio - 1.0) * 25)),
        )
        return signal.to_dict()

    def detect_missing_deductions(
        self,
        *,
        expected_deduction_amount: float,
        actual_deduction_amount: float,
    ) -> dict[str, Any]:
        expected = max(expected_deduction_amount, 0.0)
        actual = max(actual_deduction_amount, 0.0)
        gap = max(0.0, expected - actual)
        missing_pct = (gap / expected * 100) if expected > 0 else 0.0

        signal = AnomalySignal(
            anomaly_type="missing_deductions",
            summary="Expected payroll deductions are absent or materially reduced.",
            evidence=[
                ("actual_deductions", f"{actual:.2f}", f"{expected:.2f}"),
                ("deduction_gap", f"{gap:.2f}", "0.00"),
            ],
            risk_score=self._clamp((missing_pct * 0.9) + (15 if gap > 0 else 0)),
            confidence=self._clamp(60 + (missing_pct * 0.35)),
        )
        return signal.to_dict()

    def detect_ghost_employee(
        self,
        *,
        is_active_employee: bool,
        has_duplicate_identity: bool,
        days_since_last_attendance: int,
    ) -> dict[str, Any]:
        inactivity_score = max(0, days_since_last_attendance - 30)
        risk = 0
        if not is_active_employee:
            risk += 55
        if has_duplicate_identity:
            risk += 25
        risk += min(20, int(inactivity_score / 2))

        risk_score = self._clamp(risk)
        signal = AnomalySignal(
            anomaly_type="ghost_employee",
            summary="Payroll record indicates inactive, duplicate, or non-attending employee signals.",
            evidence=[
                ("employee_active", str(is_active_employee).lower(), "true"),
                ("days_since_last_attendance", str(days_since_last_attendance), "<= 30"),
            ],
            risk_score=risk_score,
            confidence=self._clamp(45 + (risk_score * 0.5)),
        )
        return signal.to_dict()
