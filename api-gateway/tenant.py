from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
import sys

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from tenant_support import DEFAULT_TENANT_ID, normalize_tenant_id
from routes import Route, resolve_route


@dataclass(frozen=True)
class GatewayRequestContext:
    route: Route
    tenant_id: str
    request_id: str | None
    actor_id: str | None


def resolve_gateway_context(request_path: str, headers: Mapping[str, str] | None = None) -> GatewayRequestContext:
    headers = headers or {}
    tenant_id = normalize_tenant_id(headers.get('x-tenant-id') or headers.get('x-tenant'))
    return GatewayRequestContext(
        route=resolve_route(request_path),
        tenant_id=tenant_id,
        request_id=headers.get('x-request-id') or headers.get('x-trace-id'),
        actor_id=headers.get('x-actor-id'),
    )


def build_upstream_headers(context: GatewayRequestContext, headers: Mapping[str, str] | None = None) -> dict[str, str]:
    upstream = dict(headers or {})
    upstream['x-tenant-id'] = context.tenant_id
    if context.request_id:
        upstream.setdefault('x-request-id', context.request_id)
        upstream.setdefault('x-trace-id', context.request_id)
    if context.actor_id:
        upstream.setdefault('x-actor-id', context.actor_id)
    return upstream
