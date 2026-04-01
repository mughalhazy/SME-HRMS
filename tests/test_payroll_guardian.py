from __future__ import annotations

from services.ai.payroll_guardian import PayrollGuardian


def test_detect_salary_spike_high_risk_for_35_percent_without_promotion() -> None:
    guardian = PayrollGuardian()

    result = guardian.detect_salary_spike(
        current_salary=135000,
        historical_average_salary=100000,
        promotion_event=False,
    )

    assert result["risk_score"] == 70
    assert result["confidence"] == 90
    assert "anomaly_type: salary_spike" in result["reason"]
    assert "threshold_level: high" in result["reason"]


def test_detect_overtime_spike_flags_large_jump() -> None:
    guardian = PayrollGuardian()

    result = guardian.detect_overtime_spike(
        current_overtime_hours=42,
        historical_average_overtime_hours=8,
    )

    assert result["risk_score"] >= 70
    assert result["confidence"] >= 80
    assert "anomaly_type: overtime_anomaly" in result["reason"]


def test_detect_missing_tax_flags_absent_deduction() -> None:
    guardian = PayrollGuardian()

    result = guardian.detect_missing_tax(expected_tax_amount=1200, actual_tax_amount=0)

    assert result["risk_score"] >= 90
    assert result["confidence"] >= 90
    assert "anomaly_type: missing_deductions" in result["reason"]


def test_detect_ghost_employee_high_risk_for_inactive_record() -> None:
    guardian = PayrollGuardian()

    result = guardian.detect_ghost_employee(
        is_active_employee=False,
        has_duplicate_identity=True,
        days_since_last_attendance=90,
    )

    assert result["risk_score"] == 100
    assert result["confidence"] == 95
    assert "anomaly_type: ghost_employee" in result["reason"]
    assert "threshold_level: high" in result["reason"]
