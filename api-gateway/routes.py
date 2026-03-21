from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

API_VERSION_PREFIX = "/api/v1"


@dataclass(frozen=True)
class Route:
    name: str
    path_prefix: str
    upstream_service: str

    @property
    def full_path_prefix(self) -> str:
        return f"{API_VERSION_PREFIX}{self.path_prefix}"


ROUTES: tuple[Route, ...] = (
    Route(name="employees", path_prefix="/employees", upstream_service="employee-service"),
    Route(name="departments", path_prefix="/departments", upstream_service="employee-service"),
    Route(name="attendance", path_prefix="/attendance", upstream_service="attendance-service"),
    Route(name="leave", path_prefix="/leave", upstream_service="leave-service"),
    Route(name="payroll", path_prefix="/payroll", upstream_service="payroll-service"),
    Route(name="hiring", path_prefix="/hiring", upstream_service="hiring-service"),
    Route(name="auth", path_prefix="/auth", upstream_service="auth-service"),
    Route(name="audit", path_prefix="/audit", upstream_service="audit-service"),
    Route(name="notifications", path_prefix="/notifications", upstream_service="notification-service"),
    Route(name="integrations", path_prefix="/integrations", upstream_service="integration-service"),
    Route(name="jobs", path_prefix="/jobs", upstream_service="api-gateway"),
)


class RouteNotFoundError(LookupError):
    """Raised when no API gateway route matches a request path."""


def iter_routes() -> Iterable[Route]:
    return ROUTES


def resolve_route(request_path: str) -> Route:
    normalized = request_path.rstrip("/") or "/"
    for route in ROUTES:
        prefix = route.full_path_prefix
        if normalized == prefix or normalized.startswith(f"{prefix}/"):
            return route
    raise RouteNotFoundError(f"No API gateway route registered for '{request_path}'.")
