from __future__ import annotations

from typing import Any


class PredictiveAnalyticsError(ValueError):
    """Raised when predictive analytics payloads are invalid."""


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


class PredictiveAnalyticsService:
    """Predictive workforce models aligned to docs/canon/decision-system.md."""

    @staticmethod
    def _to_float(name: str, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise PredictiveAnalyticsError(f'{name} must be numeric') from exc

    @classmethod
    def predict_attrition_risk(
        cls,
        *,
        engagement_score: Any,
        tenure_months: Any,
        absenteeism_rate: Any,
        overtime_ratio: Any,
    ) -> dict[str, float | str]:
        engagement = cls._to_float('engagement_score', engagement_score)
        tenure = cls._to_float('tenure_months', tenure_months)
        absenteeism = cls._to_float('absenteeism_rate', absenteeism_rate)
        overtime = cls._to_float('overtime_ratio', overtime_ratio)

        if engagement < 0 or engagement > 100:
            raise PredictiveAnalyticsError('engagement_score must be between 0 and 100')
        if tenure < 0:
            raise PredictiveAnalyticsError('tenure_months must be >= 0')
        if absenteeism < 0 or absenteeism > 100:
            raise PredictiveAnalyticsError('absenteeism_rate must be between 0 and 100')
        if overtime < 0:
            raise PredictiveAnalyticsError('overtime_ratio must be >= 0')

        risk = _clamp((100 - engagement) * 0.45 + min(tenure, 24) * 1.1 + absenteeism * 0.25 + overtime * 12)
        confidence = _clamp(62 + min(tenure, 18) * 1.5)
        return {
            'model': 'attrition_risk',
            'prediction': round(risk, 2),
            'confidence': round(confidence, 2),
        }

    @classmethod
    def predict_workforce_forecast(
        cls,
        *,
        current_headcount: Any,
        planned_growth_rate: Any,
        forecast_months: Any,
    ) -> dict[str, float | str]:
        current = cls._to_float('current_headcount', current_headcount)
        growth = cls._to_float('planned_growth_rate', planned_growth_rate)
        months = cls._to_float('forecast_months', forecast_months)

        if current < 0:
            raise PredictiveAnalyticsError('current_headcount must be >= 0')
        if growth < -100:
            raise PredictiveAnalyticsError('planned_growth_rate must be >= -100')
        if months <= 0:
            raise PredictiveAnalyticsError('forecast_months must be > 0')

        projected_headcount = max(0.0, current * (1 + (growth / 100.0) * (months / 12.0)))
        confidence = _clamp(58 + min(months, 12) * 2.2 - min(abs(growth), 30) * 0.6)
        return {
            'model': 'workforce_forecast',
            'prediction': round(projected_headcount, 2),
            'confidence': round(confidence, 2),
        }

    @classmethod
    def predict_compliance_risk(
        cls,
        *,
        policy_violations: Any,
        overdue_filings: Any,
        audit_findings: Any,
    ) -> dict[str, float | str]:
        violations = cls._to_float('policy_violations', policy_violations)
        overdue = cls._to_float('overdue_filings', overdue_filings)
        findings = cls._to_float('audit_findings', audit_findings)

        if violations < 0 or overdue < 0 or findings < 0:
            raise PredictiveAnalyticsError('policy_violations, overdue_filings, and audit_findings must be >= 0')

        risk = _clamp(violations * 6 + overdue * 12 + findings * 15)
        confidence = _clamp(68 + min(violations + overdue + findings, 20) * 1.1)
        return {
            'model': 'compliance_risk',
            'prediction': round(risk, 2),
            'confidence': round(confidence, 2),
        }
