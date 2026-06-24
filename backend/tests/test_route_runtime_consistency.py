from __future__ import annotations

import importlib.util
import pathlib
import sys

from docker.service_runtime import build_service_runtime


MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "api-gateway" / "routes.py"
SPEC = importlib.util.spec_from_file_location("api_gateway_routes_runtime_consistency", MODULE_PATH)
api_gateway_routes = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = api_gateway_routes
SPEC.loader.exec_module(api_gateway_routes)


def _runtime_patterns(service_name: str) -> set[str]:
    routes, _ = build_service_runtime(service_name)
    return {route.pattern for route in routes}


def test_gateway_canonical_routes_translate_to_runtime_plural_paths() -> None:
    canonical_cases = {
        "/api/v1/projects": "/projects",
        "/api/v1/integrations/webhooks": "/integrations/webhooks",
        "/api/v1/automations/rules": "/automations/rules",
        "/api/v1/workflows/inbox": "/workflows/inbox",
    }

    for public_path, expected_upstream in canonical_cases.items():
        route = api_gateway_routes.resolve_route(public_path)
        translated = api_gateway_routes.translate_to_upstream_path(route, public_path)
        assert translated == expected_upstream


def test_gateway_rejects_removed_singular_aliases() -> None:
    removed_aliases = [
        "/api/v1/project",
        "/api/v1/integration/webhooks",
        "/api/v1/automation/rules",
        "/api/v1/workflow/inbox",
    ]

    for legacy_path in removed_aliases:
        try:
            api_gateway_routes.resolve_route(legacy_path)
        except api_gateway_routes.RouteNotFoundError:
            continue
        raise AssertionError(f"Expected removed alias to be unresolved: {legacy_path}")


def test_runtime_handlers_expose_plural_route_prefixes_only() -> None:
    project_patterns = _runtime_patterns("project-service")
    integration_patterns = _runtime_patterns("integration-service")
    automation_patterns = _runtime_patterns("automation-service")
    workflow_patterns = _runtime_patterns("workflow-service")

    assert "/projects" in project_patterns
    assert "/integrations/webhooks" in integration_patterns
    assert "/automations/rules" in automation_patterns
    assert "/workflows/inbox" in workflow_patterns

    assert "/project" not in project_patterns
    assert "/integration/webhooks" not in integration_patterns
    assert "/automation/rules" not in automation_patterns
    assert "/workflow/inbox" not in workflow_patterns
