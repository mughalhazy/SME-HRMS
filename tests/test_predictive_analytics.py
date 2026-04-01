from __future__ import annotations

import pytest

from services.analytics.predictive import PredictiveAnalyticsError, PredictiveAnalyticsService


def test_predictive_models_generate_predictions_with_confidence() -> None:
    attrition = PredictiveAnalyticsService.predict_attrition_risk(
        engagement_score=52,
        tenure_months=8,
        absenteeism_rate=6,
        overtime_ratio=1.3,
    )
    forecast = PredictiveAnalyticsService.predict_workforce_forecast(
        current_headcount=120,
        planned_growth_rate=15,
        forecast_months=12,
    )
    compliance = PredictiveAnalyticsService.predict_compliance_risk(
        policy_violations=3,
        overdue_filings=1,
        audit_findings=2,
    )

    for result, model in (
        (attrition, 'attrition_risk'),
        (forecast, 'workforce_forecast'),
        (compliance, 'compliance_risk'),
    ):
        assert result['model'] == model
        assert isinstance(result['prediction'], float)
        assert 0 <= result['confidence'] <= 100


def test_predictive_models_validate_inputs() -> None:
    with pytest.raises(PredictiveAnalyticsError):
        PredictiveAnalyticsService.predict_attrition_risk(
            engagement_score=120,
            tenure_months=4,
            absenteeism_rate=2,
            overtime_ratio=0.8,
        )

    with pytest.raises(PredictiveAnalyticsError):
        PredictiveAnalyticsService.predict_workforce_forecast(
            current_headcount=10,
            planned_growth_rate=5,
            forecast_months=0,
        )

    with pytest.raises(PredictiveAnalyticsError):
        PredictiveAnalyticsService.predict_compliance_risk(
            policy_violations=-1,
            overdue_filings=0,
            audit_findings=0,
        )
