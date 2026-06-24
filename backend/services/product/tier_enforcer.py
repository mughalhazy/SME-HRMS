from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Tier = Literal["SMB", "MID", "ENTERPRISE"]

_TIER_ORDER: dict[Tier, int] = {"SMB": 1, "MID": 2, "ENTERPRISE": 3}
_ALLOWED_BY_TIER: dict[Tier, set[str]] = {
    "SMB": {"payroll", "compliance", "attendance"},
    "MID": {"payroll", "compliance", "attendance", "performance", "recruitment", "analytics"},
    "ENTERPRISE": {"payroll", "compliance", "attendance", "performance", "recruitment", "analytics", "governance", "advanced_compliance", "workflows"},
}


class TierAccessError(PermissionError):
    pass


@dataclass(slots=True, frozen=True)
class TierEnforcer:
    tier: Tier
    sme_lite_mode: bool = False

    def allowed_features(self) -> set[str]:
        base = set(_ALLOWED_BY_TIER[self.tier])
        if self.sme_lite_mode:
            return {"payroll", "compliance", "attendance"}
        return base

    def ensure_feature_access(self, feature: str) -> None:
        if feature not in self.allowed_features():
            raise TierAccessError(f"feature '{feature}' is blocked for tier {self.tier}")

    def ensure_tier_at_least(self, minimum: Tier) -> None:
        if _TIER_ORDER[self.tier] < _TIER_ORDER[minimum]:
            raise TierAccessError(f"tier {self.tier} does not satisfy minimum {minimum}")

