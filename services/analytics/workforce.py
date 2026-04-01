from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any


class WorkforceAnalyticsError(ValueError):
    """Raised when workforce analytics payloads are invalid."""


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _threshold_for(score: float) -> str:
    if score >= 70:
        return 'high'
    if score >= 40:
        return 'medium'
    return 'low'


class WorkforceAnalyticsService:
    """Workforce analytics metrics aligned to docs/canon/decision-system.md."""

    def __init__(self, *, tenant_id: str = 'tenant-default') -> None:
        self.tenant_id = tenant_id

    @staticmethod
    def _iso_expiry(days: int = 30) -> str:
        return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat().replace('+00:00', 'Z')

    @staticmethod
    def _validate_positive_int(name: str, value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise WorkforceAnalyticsError(f'{name} must be an integer') from exc
        if parsed < 0:
            raise WorkforceAnalyticsError(f'{name} must be >= 0')
        return parsed

    @staticmethod
    def _validate_percentage(name: str, value: Any) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError) as exc:
            raise WorkforceAnalyticsError(f'{name} must be numeric') from exc
        if parsed < 0 or parsed > 100:
            raise WorkforceAnalyticsError(f'{name} must be between 0 and 100')
        return parsed

    def _decision_payload(self, *, anomaly_type: str, summary: str, evidence: dict[str, dict[str, float]], risk_score: float, confidence: float, impact: str, action: str, reversibility: str = 'reversible') -> dict[str, Any]:
        threshold = _threshold_for(risk_score)
        return {
            'risk_score': round(_clamp(risk_score), 2),
            'confidence': round(_clamp(confidence), 2),
            'threshold_level': threshold,
            'why_flagged': {
                'anomaly_type': anomaly_type,
                'summary': summary,
                'evidence': evidence,
                'risk_score': round(_clamp(risk_score), 2),
                'confidence': round(_clamp(confidence), 2),
                'threshold_level': threshold,
            },
            'decision_card': {
                'trigger': f'{anomaly_type}:{threshold}',
                'impact': impact,
                'confidence': round(_clamp(confidence), 2),
                'recommended_action': action,
                'reversibility': reversibility,
                'expires_at': self._iso_expiry(),
            },
        }

    def calculate_absenteeism(self, *, absent_days: Any, working_days: Any, expected_absence_rate: Any = 3.0) -> dict[str, Any]:
        absent = self._validate_positive_int('absent_days', absent_days)
        working = self._validate_positive_int('working_days', working_days)
        if working <= 0:
            raise WorkforceAnalyticsError('working_days must be > 0')

        expected = self._validate_percentage('expected_absence_rate', expected_absence_rate)
        rate = round((absent / working) * 100, 2)
        risk_score = _clamp((rate / 20.0) * 100)
        confidence = _clamp(50 + min(working, 30) * 1.5)

        metric = self._decision_payload(
            anomaly_type='ghost_employee' if rate >= 25 else 'missing_deductions',
            summary='Absence rate exceeded expected operating baseline.',
            evidence={'absence_rate': {'value': rate, 'expected': expected}},
            risk_score=risk_score,
            confidence=confidence,
            impact=f'Potential productivity loss from {rate}% absenteeism.',
            action='Review attendance exceptions and manager interventions.',
        )
        metric.update({'metric': 'absenteeism_rate', 'value': rate, 'unit': 'percent'})
        return metric

    def calculate_overtime_pattern(self, *, overtime_hours: list[float] | tuple[float, ...], expected_hours: Any = 8.0) -> dict[str, Any]:
        if not overtime_hours:
            raise WorkforceAnalyticsError('overtime_hours must include at least one value')
        series = [float(hours) for hours in overtime_hours]
        if any(hours < 0 for hours in series):
            raise WorkforceAnalyticsError('overtime_hours values must be >= 0')
        expected = float(expected_hours)
        if expected < 0:
            raise WorkforceAnalyticsError('expected_hours must be >= 0')

        avg_hours = round(mean(series), 2)
        spike_ratio = 0.0 if expected == 0 else avg_hours / expected
        risk_score = _clamp((spike_ratio - 1) * 100)
        confidence = _clamp(55 + min(len(series), 26) * 1.5)

        metric = self._decision_payload(
            anomaly_type='overtime_anomaly',
            summary='Average overtime deviated from expected trend baseline.',
            evidence={'avg_overtime_hours': {'value': avg_hours, 'expected': round(expected, 2)}},
            risk_score=risk_score,
            confidence=confidence,
            impact=f'Increased overtime exposure with average {avg_hours}h per cycle.',
            action='Validate staffing gaps and approve/limit overtime requests.',
        )
        metric.update({'metric': 'overtime_pattern', 'value': avg_hours, 'unit': 'hours'})
        return metric

    def calculate_attrition_risk(self, *, engagement_score: Any, tenure_months: Any, absenteeism_rate: Any, overtime_ratio: Any) -> dict[str, Any]:
        engagement = self._validate_percentage('engagement_score', engagement_score)
        tenure = self._validate_positive_int('tenure_months', tenure_months)
        absence = self._validate_percentage('absenteeism_rate', absenteeism_rate)
        overtime = float(overtime_ratio)
        if overtime < 0:
            raise WorkforceAnalyticsError('overtime_ratio must be >= 0')

        engagement_risk = 100 - engagement
        tenure_risk = 100 if tenure <= 6 else 60 if tenure <= 12 else 25
        absence_risk = _clamp(absence * 3)
        overtime_risk = _clamp(overtime * 50)
        risk_score = _clamp(engagement_risk * 0.4 + tenure_risk * 0.25 + absence_risk * 0.2 + overtime_risk * 0.15)
        confidence = _clamp(60 + (20 if tenure >= 3 else 8))

        metric = self._decision_payload(
            anomaly_type='salary_spike',
            summary='Composite attrition predictors crossed risk threshold.',
            evidence={
                'engagement_score': {'value': round(engagement, 2), 'expected': 75.0},
                'absenteeism_rate': {'value': round(absence, 2), 'expected': 3.0},
            },
            risk_score=risk_score,
            confidence=confidence,
            impact='Potential voluntary turnover probability increase.',
            action='Trigger retention check-in and manager action plan.',
            reversibility='partially_reversible',
        )
        metric.update({'metric': 'attrition_risk', 'value': round(risk_score, 2), 'unit': 'risk_score'})
        return metric

    def calculate_burnout_index(self, *, engagement_score: Any, overtime_hours: Any, absent_days: Any, working_days: Any) -> dict[str, Any]:
        engagement = self._validate_percentage('engagement_score', engagement_score)
        overtime = float(overtime_hours)
        if overtime < 0:
            raise WorkforceAnalyticsError('overtime_hours must be >= 0')
        absent = self._validate_positive_int('absent_days', absent_days)
        working = self._validate_positive_int('working_days', working_days)
        if working <= 0:
            raise WorkforceAnalyticsError('working_days must be > 0')

        absence_rate = (absent / working) * 100
        overtime_stress = _clamp((overtime / 20) * 100)
        disengagement = 100 - engagement
        recovery_penalty = _clamp((absence_rate / 10) * 100)
        index = _clamp(overtime_stress * 0.45 + disengagement * 0.35 + recovery_penalty * 0.2)
        confidence = _clamp(65 + min(working, 30))

        metric = self._decision_payload(
            anomaly_type='overtime_anomaly',
            summary='Burnout composite indicates sustained workload strain.',
            evidence={
                'overtime_stress': {'value': round(overtime_stress, 2), 'expected': 40.0},
                'disengagement': {'value': round(disengagement, 2), 'expected': 25.0},
            },
            risk_score=index,
            confidence=confidence,
            impact='Elevated burnout likelihood can reduce productivity and retention.',
            action='Initiate workload rebalance and wellbeing intervention.',
        )
        metric.update({'metric': 'burnout_index', 'value': round(index, 2), 'unit': 'index'})
        return metric
