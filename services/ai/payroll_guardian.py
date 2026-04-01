from __future__ import annotations

from typing import Any


class PayrollGuardian:
    """Decision helpers aligned to docs/canon/decision-system.md."""

    @staticmethod
    def _threshold_level(risk_score: int) -> str:
        if risk_score >= 70:
            return "high"
        if risk_score >= 40:
            return "medium"
        return "low"

    @classmethod
    def _why_flagged(
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
                f"- threshold_level: {cls._threshold_level(risk_score)}",
            ]
        )
        return "\n".join(lines)

    @staticmethod
    def _clamp(value: float, low: int = 0, high: int = 100) -> int:
        return max(low, min(high, int(round(value))))

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

        risk_score = self._clamp(adjusted_spike_pct * 2)
        confidence = self._clamp(55 + adjusted_spike_pct)
        summary = "Salary increase is materially above historical baseline."

        reason = self._why_flagged(
            anomaly_type="salary_spike",
            summary=summary,
            evidence=[
                ("current_salary", f"{current_salary:.2f}", f"{baseline:.2f}"),
                ("spike_percent", f"{spike_pct:.1f}%", "<= 20.0%"),
            ],
            risk_score=risk_score,
            confidence=confidence,
        )
        return {"risk_score": risk_score, "confidence": confidence, "reason": reason}

    def detect_overtime_spike(
        self,
        *,
        current_overtime_hours: float,
        historical_average_overtime_hours: float,
    ) -> dict[str, Any]:
        baseline = historical_average_overtime_hours if historical_average_overtime_hours > 0 else 1
        ratio = current_overtime_hours / baseline
        overage = max(0.0, current_overtime_hours - baseline)

        risk_score = self._clamp(((ratio - 1.0) * 35) + (overage * 1.2))
        confidence = self._clamp(50 + ((ratio - 1.0) * 25))

        reason = self._why_flagged(
            anomaly_type="overtime_anomaly",
            summary="Overtime total deviates from historical work pattern.",
            evidence=[
                ("current_overtime_hours", f"{current_overtime_hours:.2f}", f"{baseline:.2f}"),
                ("overtime_ratio", f"{ratio:.2f}x", "<= 1.50x"),
            ],
            risk_score=risk_score,
            confidence=confidence,
        )
        return {"risk_score": risk_score, "confidence": confidence, "reason": reason}

    def detect_missing_tax(
        self,
        *,
        expected_tax_amount: float,
        actual_tax_amount: float,
    ) -> dict[str, Any]:
        expected = max(expected_tax_amount, 0.0)
        actual = max(actual_tax_amount, 0.0)
        gap = max(0.0, expected - actual)
        missing_pct = (gap / expected * 100) if expected > 0 else 0.0

        risk_score = self._clamp((missing_pct * 0.9) + (15 if gap > 0 else 0))
        confidence = self._clamp(60 + (missing_pct * 0.35))

        reason = self._why_flagged(
            anomaly_type="missing_deductions",
            summary="Expected statutory tax deduction is absent or materially reduced.",
            evidence=[
                ("actual_tax", f"{actual:.2f}", f"{expected:.2f}"),
                ("tax_gap", f"{gap:.2f}", "0.00"),
            ],
            risk_score=risk_score,
            confidence=confidence,
        )
        return {"risk_score": risk_score, "confidence": confidence, "reason": reason}

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
        confidence = self._clamp(45 + (risk_score * 0.5))

        reason = self._why_flagged(
            anomaly_type="ghost_employee",
            summary="Payroll record indicates inactive, duplicate, or non-attending employee signals.",
            evidence=[
                ("employee_active", str(is_active_employee).lower(), "true"),
                ("days_since_last_attendance", str(days_since_last_attendance), "<= 30"),
            ],
            risk_score=risk_score,
            confidence=confidence,
        )
        return {"risk_score": risk_score, "confidence": confidence, "reason": reason}
