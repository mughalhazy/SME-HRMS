from services.decision_engine import DecisionCard, DecisionEngine


def test_decision_card_schema_fields_exist() -> None:
    card = DecisionCard(
        trigger="salary_spike: salary +35% without promotion",
        impact="high payroll integrity impact (estimated 12000)",
        confidence=92.5,
        action="Place payroll hold and escalate for immediate review",
        expires_at="2026-04-02T00:00:00+00:00",
    )

    payload = card.to_dict()

    assert payload["trigger"] == card.trigger
    assert payload["impact"] == card.impact
    assert payload["confidence"] == card.confidence
    assert payload["action"] == card.action
    assert payload["expires_at"] == card.expires_at


def test_generation_from_anomalies_and_compliance_issues() -> None:
    engine = DecisionEngine(default_ttl_hours=2)

    anomaly_cards = engine.generate_from_anomalies(
        [
            {
                "type": "ghost_employee",
                "summary": "Payroll issued to inactive employee",
                "risk_score": 88,
                "confidence": 96,
                "estimate": 5400,
            }
        ]
    )
    compliance_cards = engine.generate_from_compliance_issues(
        [
            {
                "code": "MISSING_TAX",
                "message": "Tax deduction missing",
                "severity": "high",
                "confidence": 100,
                "estimate": 2500,
            }
        ]
    )

    assert len(anomaly_cards) == 1
    assert anomaly_cards[0].trigger.startswith("ghost_employee")
    assert anomaly_cards[0].action == "Place payroll hold and escalate for immediate review"

    assert len(compliance_cards) == 1
    assert compliance_cards[0].trigger.startswith("MISSING_TAX")
    assert "Block payroll release" in compliance_cards[0].action


def test_lifecycle_create_update_expire_and_immutability() -> None:
    engine = DecisionEngine(default_ttl_hours=1)

    card = engine.create_card(
        trigger="missing_deductions: retirement deduction absent",
        impact="medium payroll integrity impact",
        confidence=84,
        action="Queue anomaly for analyst review within SLA",
    )
    assert card.status == "active"
    assert card.audit_history[0]["event"] == "create"

    updated = engine.update_card(card, confidence=89, action="Assign payroll analyst for immediate validation")
    assert updated.confidence == 89
    assert updated.action == "Assign payroll analyst for immediate validation"
    assert updated.audit_history[-1]["event"] == "update"

    expired = engine.expire_card(updated, reason="payroll period closed")
    assert expired.status == "expired"
    assert expired.audit_history[-1]["event"] == "expire"

    annotated = engine.update_card(expired, compliance_note="Regulator note attached")
    assert annotated.audit_history[-1]["event"] == "compliance_annotation"

    try:
        engine.update_card(expired, confidence=10)
    except ValueError as exc:
        assert "immutable" in str(exc)
    else:
        raise AssertionError("Expected immutability error for expired card updates")
