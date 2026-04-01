from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Tier = Literal["SMB", "Mid", "Enterprise"]

_TIER_FEATURES: dict[Tier, set[str]] = {
    "SMB": {
        "core_hr",
        "attendance",
        "leave",
        "basic_payroll",
    },
    "Mid": {
        "core_hr",
        "attendance",
        "leave",
        "basic_payroll",
        "performance",
        "recruitment",
        "analytics",
    },
    "Enterprise": {
        "core_hr",
        "attendance",
        "leave",
        "basic_payroll",
        "performance",
        "recruitment",
        "analytics",
        "governance",
        "advanced_compliance",
        "workflows",
    },
}

_SME_LITE_DISABLED: set[str] = {
    "performance",
    "recruitment",
    "analytics",
    "governance",
    "advanced_compliance",
    "workflows",
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
            raise ValueError("tier must be SMB, Mid, or Enterprise")
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
            features -= _SME_LITE_DISABLED

        flags = {feature: True for feature in sorted(features)}
        flags["sme_lite_mode"] = sme_lite_mode
        flags["payroll_managed_mode"] = payroll_managed_mode
        flags["payroll_admin_override_controls"] = payroll_managed_mode and admin_override_controls
        flags["financial_wellness_hooks"] = tier in {"Mid", "Enterprise"}

        return flags

    def can_admin_override_payroll(self, *, tier: Tier, payroll_managed_mode: bool, admin_override_controls: bool) -> bool:
        if tier not in {"Mid", "Enterprise"}:
            return False
        return payroll_managed_mode and admin_override_controls

    def loan_api_hook(self) -> FinancialWellnessHook:
        return FinancialWellnessHook(
            provider="placeholder-loan-provider",
            endpoint="/api/v1/financial-wellness/loan",
            method="POST",
            placeholder=True,
        )

    def ewa_api_hook(self) -> FinancialWellnessHook:
        return FinancialWellnessHook(
            provider="placeholder-ewa-provider",
            endpoint="/api/v1/financial-wellness/ewa",
            method="POST",
            placeholder=True,
        )
