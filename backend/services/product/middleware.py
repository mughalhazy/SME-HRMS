from __future__ import annotations

from services.product.tier_enforcer import TierEnforcer


def enforce_workflow_access(*, tier: str, workflow: str, sme_lite_mode: bool = False) -> None:
    """Runtime middleware-style guard for product workflow access."""
    enforcer = TierEnforcer(tier=tier, sme_lite_mode=sme_lite_mode)  # type: ignore[arg-type]
    enforcer.ensure_feature_access(workflow)

