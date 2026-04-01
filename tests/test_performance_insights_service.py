from __future__ import annotations

from services.performance import PerformanceInsightsService


def _sample_payload() -> dict:
    return {
        "employee": {
            "goals_attainment": 82,
            "quality_score": 78,
            "delivery_timeliness": 74,
        },
        "manager": {
            "feedback_sentiment": 80,
            "coaching_frequency": 72,
            "blocker_resolution": 76,
        },
        "skills": {
            "skill_coverage": 70,
            "learning_velocity": 75,
            "critical_skill_gap": 20,
        },
    }


def test_insights_generated_with_text_and_scores() -> None:
    service = PerformanceInsightsService()

    result = service.generate(_sample_payload())

    assert "employee_performance_summary" in result
    assert "manager_insights" in result
    assert "skill_signals" in result
    assert isinstance(result["overall_score"], float)

    assert result["employee_performance_summary"]["text"]
    assert result["manager_insights"]["text"]
    assert result["skill_signals"]["text"]

    assert 0 <= result["employee_performance_summary"]["score"] <= 100
    assert 0 <= result["manager_insights"]["score"] <= 100
    assert 0 <= result["skill_signals"]["score"] <= 100
    assert 0 <= result["overall_score"] <= 100


def test_scoring_is_consistent_for_same_payload() -> None:
    service = PerformanceInsightsService()
    payload = _sample_payload()

    first = service.generate(payload)
    second = service.generate(payload)

    assert first["overall_score"] == second["overall_score"]
    assert first["employee_performance_summary"]["score"] == second["employee_performance_summary"]["score"]
    assert first["manager_insights"]["score"] == second["manager_insights"]["score"]
    assert first["skill_signals"]["score"] == second["skill_signals"]["score"]


def test_scoring_clamps_extreme_values() -> None:
    service = PerformanceInsightsService()

    result = service.generate(
        {
            "employee": {"goals_attainment": 300, "quality_score": -5, "delivery_timeliness": 50},
            "manager": {"feedback_sentiment": 110, "coaching_frequency": -20, "blocker_resolution": 50},
            "skills": {"skill_coverage": -1, "learning_velocity": 300, "critical_skill_gap": 140},
        }
    )

    assert result["employee_performance_summary"]["evidence"]["goals_attainment"] == 100.0
    assert result["employee_performance_summary"]["evidence"]["quality_score"] == 0.0
    assert result["manager_insights"]["evidence"]["feedback_sentiment"] == 100.0
    assert result["skill_signals"]["evidence"]["critical_skill_gap"] == 100.0
