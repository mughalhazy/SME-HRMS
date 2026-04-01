from services.governance import GovernanceError, GovernanceService


def test_payroll_approval_flow_pending_to_approved_or_rejected() -> None:
    governance = GovernanceService()

    approval = governance.create_payroll_approval(user="payroll_analyst")
    assert approval["status"] == "pending"

    approved = governance.review_payroll_approval(
        approval,
        user="finance_manager",
        decision="approved",
        reason="Validated payroll anomalies",
    )
    assert approved["status"] == "approved"

    rejected_flow = governance.create_payroll_approval(user="payroll_analyst")
    rejected = governance.review_payroll_approval(
        rejected_flow,
        user="finance_manager",
        decision="rejected",
        reason="Deduction mismatch unresolved",
    )
    assert rejected["status"] == "rejected"


def test_compliance_submission_requires_prior_approval() -> None:
    governance = GovernanceService()

    approval = governance.create_payroll_approval(user="payroll_analyst")

    try:
        governance.submit_compliance(approval, user="compliance_officer")
    except GovernanceError as exc:
        assert "requires_approved_payroll" in str(exc)
    else:
        raise AssertionError("Expected compliance submission to be blocked before approval")

    governance.review_payroll_approval(
        approval,
        user="finance_manager",
        decision="approved",
        reason="Controls satisfied",
    )
    result = governance.submit_compliance(approval, user="compliance_officer", reason="Quarterly filing")
    assert result["status"] == "submitted"


def test_anomaly_override_requires_reason_and_is_audited() -> None:
    governance = GovernanceService()
    anomaly = {"anomaly_type": "ghost_employee", "risk_score": 95}

    try:
        governance.override_anomaly(anomaly, user="payroll_admin", reason="")
    except GovernanceError as exc:
        assert "reason_required" in str(exc)
    else:
        raise AssertionError("Expected override without reason to fail")

    updated = governance.override_anomaly(anomaly, user="payroll_admin", reason="Verified contractor conversion")
    assert updated["override"] is True
    assert updated["override_reason"] == "Verified contractor conversion"


def test_audit_trail_captures_user_action_timestamp_and_reason() -> None:
    governance = GovernanceService()
    decision = {"lifecycle_state": "create"}

    approval = governance.create_payroll_approval(user="ops_user", reason="Payroll batch opened")
    governance.review_payroll_approval(approval, user="ops_reviewer", decision="approved", reason="All checks passed")
    governance.update_decision(decision, user="ops_user", reason="New evidence attached", confidence=92)
    governance.expire_decision(decision, user="ops_user", reason="Payroll cycle closed")

    assert len(governance.audit_trail) >= 4
    for record in governance.audit_trail:
        payload = record.to_dict()
        assert payload["user"]
        assert payload["action"]
        assert payload["timestamp"]
        assert payload["reason"]
