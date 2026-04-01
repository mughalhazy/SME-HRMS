from __future__ import annotations

from dataclasses import dataclass

from country.pakistan import PakistanAdapter


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
    def __init__(self) -> None:
        self._mappings: dict[str, OrgCountryMapping] = {
            "ORG_PK_001": OrgCountryMapping("ORG_PK_001", "PK", "pakistan")
        }
        self._adapters = {"pakistan": PakistanAdapter}

    def resolve(self, organization_id: str):
        mapping = self._mappings.get(organization_id)
        if mapping is None:
            raise CountryResolverError("ORG_COUNTRY_NOT_FOUND", f"No country mapping found for organization_id={organization_id}")
        adapter_cls = self._adapters.get(mapping.adapter_key)
        if adapter_cls is None:
            raise CountryResolverError(
                "COUNTRY_ADAPTER_NOT_REGISTERED",
                f"No adapter registered for adapter_key={mapping.adapter_key}",
            )
        return adapter_cls()
