from services.experience_layer_service import ExperienceLayerService
from services.finance.ewa import FinancialWellnessService, loan_request, salary_advance
from services.product.tier_enforcer import TierAccessError, TierEnforcer


def test_sme_lite_mode_limits_features_to_payroll_compliance_attendance() -> None:
    service = ExperienceLayerService()

    standard = service.resolve_feature_flags(tier="MID", sme_lite_mode=False)
    lite = service.resolve_feature_flags(tier="MID", sme_lite_mode=True)

    assert standard["performance"] is True
    assert standard["analytics"] is True

    assert lite["payroll"] is True
    assert lite["compliance"] is True
    assert lite["attendance"] is True
    assert "performance" not in lite
    assert "analytics" not in lite
    assert lite["sme_lite_mode"] is True


def test_payroll_as_a_service_controls_require_managed_mode() -> None:
    service = ExperienceLayerService()

    disabled = service.resolve_feature_flags(
        tier="ENTERPRISE",
        payroll_managed_mode=False,
        admin_override_controls=True,
    )
    enabled = service.resolve_feature_flags(
        tier="ENTERPRISE",
        payroll_managed_mode=True,
        admin_override_controls=True,
    )

    assert disabled["payroll_admin_override_controls"] is False
    assert enabled["payroll_admin_override_controls"] is True


def test_financial_wellness_hooks_and_live_apis_are_callable() -> None:
    service = ExperienceLayerService()

    loan = service.loan_api_hook()
    ewa = service.ewa_api_hook()

    assert loan.integration_mode == "live"
    assert loan.endpoint == "/api/v1/financial-wellness/loan"
    assert ewa.integration_mode == "live"
    assert ewa.endpoint == "/api/v1/financial-wellness/ewa"

    loan_response = loan_request(employee_id="E-100", amount=15000)
    ewa_response = salary_advance(employee_id="E-100", amount=5000)

    assert loan_response["status"] == "accepted"
    assert loan_response["amount"] == "15000.00"
    assert "created_at" in loan_response
    assert ewa_response["status"] == "accepted"
    assert ewa_response["amount"] == "5000.00"
    assert "created_at" in ewa_response


def test_tier_logic_gates_features_consistently() -> None:
    service = ExperienceLayerService()

    smb = service.resolve_feature_flags(tier="SMB")
    mid = service.resolve_feature_flags(tier="MID")
    enterprise = service.resolve_feature_flags(tier="ENTERPRISE")

    assert "performance" not in smb
    assert mid["performance"] is True
    assert enterprise["advanced_compliance"] is True

    assert service.can_admin_override_payroll(
        tier="SMB",
        payroll_managed_mode=True,
        admin_override_controls=True,
    ) is False
    assert service.can_admin_override_payroll(
        tier="MID",
        payroll_managed_mode=True,
        admin_override_controls=True,
    ) is True


def test_tier_enforcer_blocks_advanced_features_for_smb_and_sme_lite() -> None:
    smb = TierEnforcer(tier="SMB")
    smb.ensure_feature_access("payroll")
    try:
        smb.ensure_feature_access("analytics")
        raise AssertionError("Expected TierAccessError")
    except TierAccessError:
        pass

    lite = TierEnforcer(tier="ENTERPRISE", sme_lite_mode=True)
    try:
        lite.ensure_feature_access("workflows")
        raise AssertionError("Expected TierAccessError")
    except TierAccessError:
        pass


def test_financial_wellness_salary_advance_flow_integrates_deduction() -> None:
    service = FinancialWellnessService()
    request = service.request_salary_advance(employee_id="E-100", amount=3000, currency="PKR")
    assert request["status"] == "PendingApproval"

    approved = service.approve_salary_advance(request_id=str(request["request_id"]), approver_id="mgr-1")
    assert approved["status"] == "Approved"

    deduction = service.payroll_deduction_for_employee(employee_id="E-100", max_deduction=1000)
    assert str(deduction) == "1000.00"
