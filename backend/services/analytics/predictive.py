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

        factors = {
            'engagement_inverse': {'value': engagement, 'weight': 0.45, 'contribution': round((100 - engagement) * 0.45, 2)},
            'tenure_months': {'value': tenure, 'weight': 1.1, 'contribution': round(min(tenure, 24) * 1.1, 2)},
            'absenteeism_rate': {'value': absenteeism, 'weight': 0.25, 'contribution': round(absenteeism * 0.25, 2)},
            'overtime_ratio': {'value': overtime, 'weight': 12.0, 'contribution': round(overtime * 12.0, 2)},
        }
        risk = _clamp(sum(f['contribution'] for f in factors.values()))
        confidence = _clamp(62 + min(tenure, 18) * 1.5)
        top = sorted(factors.items(), key=lambda x: x[1]['contribution'], reverse=True)[:2]
        explanation = (
            f"Risk driven primarily by {top[0][0].replace('_', ' ')} "
            f"(contributes {top[0][1]['contribution']:.1f} pts)"
            + (f" and {top[1][0].replace('_', ' ')} ({top[1][1]['contribution']:.1f} pts)." if len(top) > 1 else '.')
        )
        top_factor = top[0][0].replace('_', ' ')
        suggested_action = (
            f"Review {top_factor} for this employee and consider retention intervention "
            "if risk exceeds 70. Flag for manager review if over 40."
        )
        return {
            'model': 'attrition_risk',
            'prediction': round(risk, 2),
            'confidence': round(confidence, 2),
            'explanation': explanation,
            'suggested_action': suggested_action,
            'supporting_signals': factors,
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
        net_change = round(projected_headcount - current, 2)
        direction = 'growth' if net_change >= 0 else 'reduction'
        explanation = (
            f"Projected headcount of {round(projected_headcount, 0):.0f} based on "
            f"{growth:.1f}% annual {direction} applied over {months:.0f} months "
            f"(net change: {net_change:+.1f} headcount)."
        )
        action_verb = "scale up hiring" if net_change > 0 else "plan workforce reduction"
        suggested_action = (
            f"Based on {growth:.1f}% growth over {months:.0f} months, {action_verb} "
            f"by approximately {abs(net_change):.0f} headcount. Review budget alignment."
        )
        return {
            'model': 'workforce_forecast',
            'prediction': round(projected_headcount, 2),
            'confidence': round(confidence, 2),
            'explanation': explanation,
            'suggested_action': suggested_action,
            'supporting_signals': {
                'current_headcount': {'value': current, 'weight': None, 'contribution': round(current, 2)},
                'planned_growth_rate_pct': {'value': growth, 'weight': None, 'contribution': round(net_change, 2)},
                'forecast_months': {'value': months, 'weight': None, 'contribution': None},
            },
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

        factors = {
            'policy_violations': {'value': violations, 'weight': 6, 'contribution': round(violations * 6, 2)},
            'overdue_filings': {'value': overdue, 'weight': 12, 'contribution': round(overdue * 12, 2)},
            'audit_findings': {'value': findings, 'weight': 15, 'contribution': round(findings * 15, 2)},
        }
        risk = _clamp(sum(f['contribution'] for f in factors.values()))
        confidence = _clamp(68 + min(violations + overdue + findings, 20) * 1.1)
        top = sorted(factors.items(), key=lambda x: x[1]['contribution'], reverse=True)[:2]
        explanation = (
            f"Compliance risk driven by {top[0][0].replace('_', ' ')} "
            f"(contributes {top[0][1]['contribution']:.0f} pts)"
            + (f" and {top[1][0].replace('_', ' ')} ({top[1][1]['contribution']:.0f} pts)." if len(top) > 1 else '.')
        )
        top_compliance_factor = top[0][0].replace('_', ' ')
        suggested_action = (
            f"Prioritise resolution of {top_compliance_factor}. "
            "Escalate to compliance officer if risk exceeds 60. "
            "Block payroll finalization if risk exceeds 80."
        )
        return {
            'model': 'compliance_risk',
            'prediction': round(risk, 2),
            'confidence': round(confidence, 2),
            'explanation': explanation,
            'suggested_action': suggested_action,
            'supporting_signals': factors,
        }
