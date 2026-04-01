from insight_engine import InsightEngine


def test_generate_insights_contains_required_sections() -> None:
    engine = InsightEngine()

    insights = engine.generate(
        {
            "attrition": {
                "tenure_months": 8,
                "engagement_score": 42,
                "manager_changes_last_year": 2,
            },
            "overtime": {
                "current_month_hours": 41,
                "baseline_month_hours": 18,
                "affected_team_percent": 37,
            },
            "payroll": {
                "anomaly_count": 12,
                "payroll_records": 240,
                "unresolved_count": 5,
            },
        }
    )

    assert set(insights) == {"attrition_risk", "overtime_trends", "payroll_anomalies"}


def test_all_insights_are_explainable() -> None:
    engine = InsightEngine()
    insights = engine.generate({})

    for insight in insights.values():
        assert insight["explanation"].startswith("WHY_FLAGGED:")
        assert "- evidence:" in insight["explanation"]
        assert "- threshold_level:" in insight["explanation"]
