from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

API_VERSION_PREFIX = "/api/v1"


@dataclass(frozen=True)
class Route:
    name: str
    path_prefix: str
    upstream_service: str
    legacy_aliases: tuple[str, ...] = ()
    upstream_path_prefix: str | None = None
    expects_versioned_paths: bool = False

    @property
    def full_path_prefix(self) -> str:
        return f"{API_VERSION_PREFIX}{self.path_prefix}"

    @property
    def legacy_path_prefix(self) -> str:
        return self.path_prefix

    @property
    def legacy_prefixes(self) -> tuple[str, ...]:
        return (self.path_prefix, *self.legacy_aliases)

    @property
    def normalized_upstream_prefix(self) -> str:
        return self.upstream_path_prefix or self.path_prefix


ROUTES: tuple[Route, ...] = (
    Route(name="employees", path_prefix="/employees", upstream_service="employee-service"),
    Route(name="departments", path_prefix="/departments", upstream_service="employee-service"),
    Route(name="performance", path_prefix="/performance", upstream_service="performance-service"),
    Route(name="attendance", path_prefix="/attendance", upstream_service="attendance-service"),
    Route(name="leave", path_prefix="/leave", upstream_service="leave-service"),
    Route(name="travel", path_prefix="/travel", upstream_service="travel-service"),
    Route(name="projects", path_prefix="/projects", upstream_service="project-service", legacy_aliases=("/project",)),
    Route(name="payroll", path_prefix="/payroll", upstream_service="payroll-service"),
    Route(name="hiring", path_prefix="/hiring", upstream_service="hiring-service"),
    Route(name="auth", path_prefix="/auth", upstream_service="auth-service"),
    Route(name="workflows", path_prefix="/workflows", upstream_service="workflow-service", legacy_aliases=("/workflow",)),
    Route(name="audit", path_prefix="/audit", upstream_service="audit-service"),
    Route(name="notifications", path_prefix="/notifications", upstream_service="notification-service"),
    Route(name="engagement", path_prefix="/engagement", upstream_service="engagement-service"),
    Route(name="helpdesk", path_prefix="/helpdesk", upstream_service="helpdesk-service"),
    Route(name="reporting", path_prefix="/reporting", upstream_service="reporting-analytics-service"),
    Route(name="search", path_prefix="/search", upstream_service="search-service"),
    Route(name="expense", path_prefix="/expense", upstream_service="expense-service"),
    Route(name="integrations", path_prefix="/integrations", upstream_service="integration-service", legacy_aliases=("/integration",)),
    Route(name="automations", path_prefix="/automations", upstream_service="automation-service", legacy_aliases=("/automation",)),
    Route(name="settings", path_prefix="/settings", upstream_service="settings-service"),
    Route(name="jobs", path_prefix="/jobs", upstream_service="api-gateway"),
)


class RouteNotFoundError(LookupError):
    """Raised when no API gateway route matches a request path."""


def iter_routes() -> Iterable[Route]:
    return ROUTES


def _matches_prefix(request_path: str, prefix: str) -> bool:
    return request_path == prefix or request_path.startswith(f"{prefix}/")


def resolve_route(request_path: str) -> Route:
    normalized = request_path.rstrip("/") or "/"
    for route in ROUTES:
        if _matches_prefix(normalized, route.full_path_prefix):
            return route

    for route in ROUTES:
        versioned_legacy_aliases = tuple(f"{API_VERSION_PREFIX}{alias}" for alias in route.legacy_aliases)
        for legacy_prefix in (*route.legacy_prefixes, *versioned_legacy_aliases):
            if _matches_prefix(normalized, legacy_prefix):
                return route

    raise RouteNotFoundError(f"No API gateway route registered for '{request_path}'.")


def is_legacy_route(request_path: str) -> bool:
    normalized = request_path.rstrip("/") or "/"
    for route in ROUTES:
        versioned_legacy_aliases = tuple(f"{API_VERSION_PREFIX}{alias}" for alias in route.legacy_aliases)
        for legacy_prefix in (*route.legacy_prefixes, *versioned_legacy_aliases):
            if _matches_prefix(normalized, legacy_prefix) and not _matches_prefix(normalized, route.full_path_prefix):
                return True
    return False


def translate_to_upstream_path(route: Route, request_path: str) -> str:
    normalized = request_path.rstrip("/") or "/"
    versioned_legacy_aliases = tuple(f"{API_VERSION_PREFIX}{alias}" for alias in route.legacy_aliases)
    candidate_prefixes: tuple[str, ...] = (route.full_path_prefix, *route.legacy_prefixes, *versioned_legacy_aliases)

    matched_prefix: str | None = None
    for prefix in candidate_prefixes:
        if _matches_prefix(normalized, prefix):
            matched_prefix = prefix
            break

    if not matched_prefix:
        raise RouteNotFoundError(f"Route '{route.name}' does not match request path '{request_path}'.")

    suffix = normalized[len(matched_prefix):]
    if suffix and not suffix.startswith("/"):
        suffix = f"/{suffix}"

    if route.expects_versioned_paths:
        if normalized.startswith(API_VERSION_PREFIX):
            return normalized
        return f"{API_VERSION_PREFIX}{normalized if normalized.startswith('/') else f'/{normalized}'}"

    return f"{route.normalized_upstream_prefix}{suffix}"
