from services.experience_layer_service import ExperienceLayerService


def test_sme_lite_mode_simplifies_feature_set() -> None:
    service = ExperienceLayerService()

    standard = service.resolve_feature_flags(tier="Mid", sme_lite_mode=False)
    lite = service.resolve_feature_flags(tier="Mid", sme_lite_mode=True)

    assert standard["performance"] is True
    assert standard["analytics"] is True
    assert "performance" not in lite
    assert "analytics" not in lite
    assert lite["sme_lite_mode"] is True


def test_payroll_as_a_service_controls_require_managed_mode() -> None:
    service = ExperienceLayerService()

    disabled = service.resolve_feature_flags(
        tier="Enterprise",
        payroll_managed_mode=False,
        admin_override_controls=True,
    )
    enabled = service.resolve_feature_flags(
        tier="Enterprise",
        payroll_managed_mode=True,
        admin_override_controls=True,
    )

    assert disabled["payroll_admin_override_controls"] is False
    assert enabled["payroll_admin_override_controls"] is True


def test_financial_wellness_hooks_expose_placeholder_contracts() -> None:
    service = ExperienceLayerService()

    loan = service.loan_api_hook()
    ewa = service.ewa_api_hook()

    assert loan.placeholder is True
    assert loan.endpoint == "/api/v1/financial-wellness/loan"
    assert ewa.placeholder is True
    assert ewa.endpoint == "/api/v1/financial-wellness/ewa"


def test_tier_logic_gates_features_consistently() -> None:
    service = ExperienceLayerService()

    smb = service.resolve_feature_flags(tier="SMB")
    mid = service.resolve_feature_flags(tier="Mid")
    enterprise = service.resolve_feature_flags(tier="Enterprise")

    assert "performance" not in smb
    assert mid["performance"] is True
    assert enterprise["advanced_compliance"] is True

    assert service.can_admin_override_payroll(
        tier="SMB",
        payroll_managed_mode=True,
        admin_override_controls=True,
    ) is False
    assert service.can_admin_override_payroll(
        tier="Mid",
        payroll_managed_mode=True,
        admin_override_controls=True,
    ) is True
