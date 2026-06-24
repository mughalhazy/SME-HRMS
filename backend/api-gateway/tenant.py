from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
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
    actor_role: str | None = None
    actor_employee_id: str | None = None
    subject_type: str | None = None


def resolve_gateway_context(request_path: str, headers: Mapping[str, str] | None = None) -> GatewayRequestContext:
    headers = headers or {}
    tenant_id = normalize_tenant_id(headers.get('x-tenant-id') or headers.get('x-tenant'))
    return GatewayRequestContext(
        route=resolve_route(request_path),
        tenant_id=tenant_id,
        request_id=headers.get('x-request-id') or headers.get('x-trace-id'),
        actor_id=headers.get('x-actor-id'),
        actor_role=headers.get('x-actor-role'),
        actor_employee_id=headers.get('x-actor-employee-id'),
        subject_type=headers.get('x-auth-subject-type'),
    )


def build_upstream_headers(context: GatewayRequestContext, headers: Mapping[str, str] | None = None) -> dict[str, str]:
    upstream = dict(headers or {})
    upstream['x-tenant-id'] = context.tenant_id
    if context.request_id:
        upstream.setdefault('x-request-id', context.request_id)
        upstream.setdefault('x-trace-id', context.request_id)
    if context.actor_id:
        upstream.setdefault('x-actor-id', context.actor_id)
    if context.actor_role:
        upstream.setdefault('x-actor-role', context.actor_role)
    if context.actor_employee_id:
        upstream.setdefault('x-actor-employee-id', context.actor_employee_id)
    if context.subject_type:
        upstream.setdefault('x-auth-subject-type', context.subject_type)
    upstream.setdefault('x-authenticated-tenant-id', context.tenant_id)
    auth_context = {
        'tenant_id': context.tenant_id,
        'actor_id': context.actor_id,
        'actor_role': context.actor_role,
        'actor_employee_id': context.actor_employee_id,
        'subject_type': context.subject_type or 'user',
        'upstream_service': context.route.upstream_service,
    }
    upstream.setdefault('x-auth-context', json.dumps({key: value for key, value in auth_context.items() if value is not None}, separators=(',', ':')))
    return upstream
