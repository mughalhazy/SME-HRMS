from __future__ import annotations

from dataclasses import dataclass
from typing import Type


@dataclass(frozen=True)
class OrgCountryMapping:
    organization_id: str
    country_code: str
    adapter_key: str


class CountryResolverError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class CountryResolver:
    """
    Routes an organization_id to its country adapter via registered mappings.

    Architecture rule: no service may import any country module directly.
    All country logic is accessed through this resolver.

    Mappings are data-driven — loaded via register_mapping() at startup
    (from DB, config, or environment). The hardcoded Pakistan seed exists
    only for dev/test and must NOT be relied on in production.

    Usage:
        resolver = CountryResolver()
        resolver.register_adapter("pakistan", PakistanAdapter)
        resolver.register_mapping("ORG_001", "PK", "pakistan")
        adapter = resolver.resolve("ORG_001")
    """

    def __init__(self) -> None:
        self._mappings: dict[str, OrgCountryMapping] = {}
        self._adapters: dict[str, Type] = {}

    # ------------------------------------------------------------------
    # Registration API — called at application startup from config/DB
    # ------------------------------------------------------------------

    def register_adapter(self, adapter_key: str, adapter_cls: Type) -> None:
        """Register a country adapter class under a lookup key."""
        if not adapter_key:
            raise CountryResolverError("INVALID_ADAPTER_KEY", "adapter_key must not be empty")
        self._adapters[adapter_key] = adapter_cls

    def register_mapping(self, organization_id: str, country_code: str, adapter_key: str) -> None:
        """Map an organization_id to a country adapter key."""
        if not organization_id:
            raise CountryResolverError("INVALID_ORG_ID", "organization_id must not be empty")
        if adapter_key not in self._adapters:
            raise CountryResolverError(
                "COUNTRY_ADAPTER_NOT_REGISTERED",
                f"Adapter '{adapter_key}' is not registered. Call register_adapter() first.",
            )
        self._mappings[organization_id] = OrgCountryMapping(organization_id, country_code, adapter_key)

    def list_mappings(self) -> list[OrgCountryMapping]:
        """Return all registered org→country mappings (for health checks / admin)."""
        return list(self._mappings.values())

    # ------------------------------------------------------------------
    # Resolution API — called per request
    # ------------------------------------------------------------------

    def get_adapter(self, organization_id: str):
        mapping = self._mappings.get(organization_id)
        if mapping is None:
            raise CountryResolverError(
                "ORG_COUNTRY_NOT_FOUND",
                f"No country mapping found for organization_id={organization_id}. "
                "Register the mapping at startup via register_mapping().",
            )
        adapter_cls = self._adapters.get(mapping.adapter_key)
        if adapter_cls is None:
            raise CountryResolverError(
                "COUNTRY_ADAPTER_NOT_REGISTERED",
                f"No adapter registered for adapter_key={mapping.adapter_key}",
            )
        return adapter_cls()

    def resolve(self, organization_id: str):
        """Alias for get_adapter — returns a live adapter instance."""
        return self.get_adapter(organization_id)


# ----------------------------------------------------------------------
# Dev / test seed — NOT for production use
# Import here is intentional: only this module may reference country adapters.
# All other services must call CountryResolver.resolve(), never import adapters.
# ----------------------------------------------------------------------

def seed_dev_defaults(resolver: CountryResolver) -> None:
    """
    Seed resolver with Pakistan as the default org mapping.
    Also registers the dummy adapter for architecture tests.
    Call this in dev/test entrypoints only.
    Production startup must load mappings from the database.
    """
    from country.pakistan import PakistanAdapter  # noqa: PLC0415
    from country.dummy import DummyAdapter  # noqa: PLC0415

    resolver.register_adapter("pakistan", PakistanAdapter)
    resolver.register_mapping("ORG_DEFAULT", "PK", "pakistan")

    resolver.register_adapter("dummy", DummyAdapter)
    resolver.register_mapping("ORG_DUMMY", "XX", "dummy")
