from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

DEFAULT_TENANT_ID = 'tenant-default'
TENANT_HEADER_CANDIDATES = ('x-tenant-id', 'x-tenant', 'tenant_id')


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str = DEFAULT_TENANT_ID
    actor_id: str | None = None
    actor_type: str = 'user'


def normalize_tenant_id(value: str | None) -> str:
    tenant_id = (value or DEFAULT_TENANT_ID).strip()
    return tenant_id or DEFAULT_TENANT_ID


def resolve_tenant_id(*sources: Any, default: str = DEFAULT_TENANT_ID) -> str:
    for source in sources:
        if source is None:
            continue
        if isinstance(source, str):
            normalized = normalize_tenant_id(source)
            if normalized:
                return normalized
        if isinstance(source, Mapping):
            for key in TENANT_HEADER_CANDIDATES:
                value = source.get(key)
                if isinstance(value, str) and value.strip():
                    return normalize_tenant_id(value)
    return normalize_tenant_id(default)


def assert_tenant_access(resource_tenant_id: str, actor_tenant_id: str, *, code: str = 'TENANT_SCOPE_VIOLATION') -> None:
    if normalize_tenant_id(resource_tenant_id) != normalize_tenant_id(actor_tenant_id):
        raise PermissionError(code)
