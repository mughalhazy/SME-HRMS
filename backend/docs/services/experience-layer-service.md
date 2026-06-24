# experience-layer-service

Tenant tier and feature-flag resolver: maps SMB / MID / ENTERPRISE tiers to permitted feature sets, enforces SME-Lite mode restrictions, and provides financial-wellness integration hook descriptors.

## Scope
> NOTE (2026-06-13): this doc's filename/title use `experience-layer-service`; `docs/system/service-manifest.md` and `docs/canon/service-map.md` register the same service as `experience-layer` (no `-service` suffix). Same service, naming variant only — not a separate service. See OIG-2/OIG-9 naming-note in `service-manifest.md` for the related `analytics-service`/`reporting-analytics-service` and `whatsapp-access-service`/`whatsapp-service` variants.
- Add-on service (`experience-layer`, `services/product/experience.py`).
- `services/experience_layer_service.py` is a 3-line re-export stub — the implementation lives in `services/product/experience.py` (102 lines).
- No HTTP surface — imported directly at the service layer and by QC / test suites.
- Complements `docs/specs/experience-layer.md` (which covers UX principles, decision-first design, and API interaction model). This doc covers the implementation behaviour.


## Core responsibilities
- Resolve which features are active for a given `Tier` + mode combination.
- Enforce `sme_lite_mode` — restricts any tier to the SME-Lite-allowed feature subset (payroll / compliance / attendance only).
- Determine whether admin payroll-override controls are available for a tenant.
- Return `FinancialWellnessHook` descriptors so the EWA / loan integration can discover the correct endpoint and provider.

## Tier feature matrix

| Feature | SMB | MID | ENTERPRISE |
|---|---|---|---|
| payroll | ✅ | ✅ | ✅ |
| compliance | ✅ | ✅ | ✅ |
| attendance | ✅ | ✅ | ✅ |
| performance | — | ✅ | ✅ |
| recruitment | — | ✅ | ✅ |
| analytics | — | ✅ | ✅ |
| governance | — | — | ✅ |
| advanced_compliance | — | — | ✅ |
| workflows | — | — | ✅ |

When `sme_lite_mode=True` any tier is further restricted to `{payroll, compliance, attendance}`.

## `resolve_feature_flags()` output schema
```yaml
payroll: bool
compliance: bool
attendance: bool
performance: bool        # MID and above (unless sme_lite_mode)
recruitment: bool
analytics: bool
governance: bool         # ENTERPRISE only
advanced_compliance: bool
workflows: bool
sme_lite_mode: bool      # reflects input param
payroll_managed_mode: bool   # reflects input param
payroll_admin_override_controls: bool  # true only when tier in {MID, ENTERPRISE} AND payroll_managed_mode AND admin_override_controls
financial_wellness_hooks: bool   # true for MID and ENTERPRISE
```

## `FinancialWellnessHook`
Immutable dataclass (`slots=True, frozen=True`) returned by `loan_api_hook()` and `ewa_api_hook()`.

```yaml
provider: string         # integration provider identity
endpoint: string         # e.g. /api/v1/financial-wellness/ewa
method: string           # HTTP method (POST)
integration_mode: string # "live" | "sandbox"
```

## Related modules (`services/product/`)
- `experience.py` — `ExperienceLayerService`, `FinancialWellnessHook`, `Tier` (the canonical implementation)
- `middleware.py` — request-context middleware consumed by the API gateway layer
- `tier_enforcer.py` — enforcement guard that raises on feature access denied for the current tier

## Events published / subscribed
- None.

## Dependencies
- No external service dependencies — pure Python with no I/O.
- `docs/specs/experience-layer.md` is the UX behavioural spec this implementation aligns to.

## Notes
- `Tier` is a `Literal["SMB", "MID", "ENTERPRISE"]` — any other value raises `ValueError`.
- `can_admin_override_payroll()` requires **both** `payroll_managed_mode=True` **and** `admin_override_controls=True`; tier alone is insufficient.
- `governance` feature is ENTERPRISE-only — aligns with `GovernanceService` (`services/governance/service.py`) being a gated capability.
