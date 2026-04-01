from services.experience_layer_service import ExperienceLayerService
from services.finance.ewa import loan_request, salary_advance


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


def test_financial_wellness_hooks_and_placeholder_apis_are_callable() -> None:
    service = ExperienceLayerService()

    loan = service.loan_api_hook()
    ewa = service.ewa_api_hook()

    assert loan.placeholder is True
    assert loan.endpoint == "/api/v1/financial-wellness/loan"
    assert ewa.placeholder is True
    assert ewa.endpoint == "/api/v1/financial-wellness/ewa"

    loan_response = loan_request(employee_id="E-100", amount=15000)
    ewa_response = salary_advance(employee_id="E-100", amount=5000)

    assert loan_response["status"] == "accepted_placeholder"
    assert ewa_response["status"] == "accepted_placeholder"


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
