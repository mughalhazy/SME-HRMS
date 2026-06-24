from __future__ import annotations

from services.ai.anomaly_engine import AnomalyEngine
from services.decision_engine import DecisionEngine


def test_anomaly_engine_detects_all_required_anomaly_types_with_explanations() -> None:
    engine = AnomalyEngine()

    salary = engine.detect_salary_spike(current_salary=135000, historical_average_salary=100000)
    overtime = engine.detect_overtime_anomaly(current_overtime_hours=42, historical_average_overtime_hours=8)
    deductions = engine.detect_missing_deductions(expected_deduction_amount=1200, actual_deduction_amount=0)
    ghost = engine.detect_ghost_employee(
        is_active_employee=False,
        has_duplicate_identity=True,
        days_since_last_attendance=90,
    )

    anomalies = [salary, overtime, deductions, ghost]
    expected_types = {
        "salary_spike",
        "overtime_anomaly",
        "missing_deductions",
        "ghost_employee",
    }

    assert {a["anomaly_type"] for a in anomalies} == expected_types
    for anomaly in anomalies:
        assert isinstance(anomaly["risk_score"], int)
        assert isinstance(anomaly["confidence"], int)
        assert anomaly["explanation"].startswith("WHY_FLAGGED:")
        assert f"anomaly_type: {anomaly['anomaly_type']}" in anomaly["explanation"]


def test_decision_engine_generates_cards_from_anomaly_engine_output() -> None:
    anomaly_engine = AnomalyEngine()
    decision_engine = DecisionEngine(default_ttl_hours=2)

    anomaly = anomaly_engine.detect_ghost_employee(
        is_active_employee=False,
        has_duplicate_identity=True,
        days_since_last_attendance=90,
    )

    cards = decision_engine.generate_from_ai_payroll_guardian([anomaly])

    assert len(cards) == 1
    assert cards[0].trigger.startswith("ghost_employee")
    assert cards[0].recommended_action == "Place payroll hold and escalate for immediate review"
