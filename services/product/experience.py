from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Tier = Literal["SMB", "MID", "ENTERPRISE"]

_TIER_FEATURES: dict[Tier, set[str]] = {
    "SMB": {
        "payroll",
        "compliance",
        "attendance",
    },
    "MID": {
        "payroll",
        "compliance",
        "attendance",
        "performance",
        "recruitment",
        "analytics",
    },
    "ENTERPRISE": {
        "payroll",
        "compliance",
        "attendance",
        "performance",
        "recruitment",
        "analytics",
        "governance",
        "advanced_compliance",
        "workflows",
    },
}

_SME_LITE_ALLOWED: set[str] = {
    "payroll",
    "compliance",
    "attendance",
}


@dataclass(slots=True, frozen=True)
class FinancialWellnessHook:
    provider: str
    endpoint: str
    method: str
    placeholder: bool


class ExperienceLayerService:
    """Feature-mode resolver aligned to docs/specs/experience-layer.md."""

    def _tier_features(self, tier: Tier) -> set[str]:
        if tier not in _TIER_FEATURES:
            raise ValueError("tier must be SMB, MID, or ENTERPRISE")
        return set(_TIER_FEATURES[tier])

    def resolve_feature_flags(
        self,
        *,
        tier: Tier,
        sme_lite_mode: bool = False,
        payroll_managed_mode: bool = False,
        admin_override_controls: bool = False,
    ) -> dict[str, bool]:
        features = self._tier_features(tier)

        if sme_lite_mode:
            features &= _SME_LITE_ALLOWED

        flags = {feature: True for feature in sorted(features)}
        flags["sme_lite_mode"] = sme_lite_mode
        flags["payroll_managed_mode"] = payroll_managed_mode
        flags["payroll_admin_override_controls"] = self.can_admin_override_payroll(
            tier=tier,
            payroll_managed_mode=payroll_managed_mode,
            admin_override_controls=admin_override_controls,
        )
        flags["financial_wellness_hooks"] = tier in {"MID", "ENTERPRISE"}

        return flags

    def can_admin_override_payroll(self, *, tier: Tier, payroll_managed_mode: bool, admin_override_controls: bool) -> bool:
        if tier not in {"MID", "ENTERPRISE"}:
            return False
        return payroll_managed_mode and admin_override_controls

    def loan_api_hook(self) -> FinancialWellnessHook:
        return FinancialWellnessHook(
            provider="managed-loan-provider",
            endpoint="/api/v1/financial-wellness/loan",
            method="POST",
            placeholder=False,
        )

    def ewa_api_hook(self) -> FinancialWellnessHook:
        return FinancialWellnessHook(
            provider="managed-ewa-provider",
            endpoint="/api/v1/financial-wellness/ewa",
            method="POST",
            placeholder=False,
        )
