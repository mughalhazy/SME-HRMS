from __future__ import annotations

import importlib.util
import pathlib
import sys
from urllib.parse import urlsplit

from docker.service_runtime import _match, _qs_dict, build_service_runtime


ROUTES_MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "api-gateway" / "routes.py"
ROUTES_SPEC = importlib.util.spec_from_file_location("api_gateway_routes_e2e_alignment", ROUTES_MODULE_PATH)
api_gateway_routes = importlib.util.module_from_spec(ROUTES_SPEC)
assert ROUTES_SPEC and ROUTES_SPEC.loader
sys.modules[ROUTES_SPEC.name] = api_gateway_routes
ROUTES_SPEC.loader.exec_module(api_gateway_routes)


def _execute_forwarded_request(
    *,
    service_name: str,
    method: str,
    forwarded_path_with_query: str,
    body: dict[str, object] | None = None,
) -> tuple[int, dict[str, object]]:
    parsed = urlsplit(forwarded_path_with_query)
    forwarded_path = parsed.path
    forwarded_query = _qs_dict(parsed.query)

    routes, _ = build_service_runtime(service_name)
    for route in routes:
        if route.method != method:
            continue

        path_params = _match(route.pattern, forwarded_path)
        if path_params is None:
            continue

        return route.handler(path_params, forwarded_query, body or {}, {})

    raise AssertionError(
        f"Gateway forwarded unhandled runtime path: service={service_name}, method={method}, path={forwarded_path_with_query}"
    )


def test_gateway_to_runtime_execution_alignment_for_all_declared_public_routes() -> None:
    route_execution_cases = {
        "employees": {"method": "GET", "gateway_path": "/api/v1/employees", "expected_upstream": "/employees", "service": "employee-service"},
        "departments": {"method": "GET", "gateway_path": "/api/v1/departments", "expected_upstream": "/departments", "service": "employee-service"},
        "performance": {"method": "GET", "gateway_path": "/api/v1/performance/goals", "expected_upstream": "/performance/goals", "service": "performance-service"},
        "attendance": {"method": "GET", "gateway_path": "/api/v1/attendance/records?employee_id=11111111-1111-1111-1111-111111111111&from_date=2026-01-01&to_date=2026-01-31", "expected_upstream": "/attendance/records?employee_id=11111111-1111-1111-1111-111111111111&from_date=2026-01-01&to_date=2026-01-31", "service": "attendance-service"},
        "leave": {"method": "GET", "gateway_path": "/api/v1/leave/requests", "expected_upstream": "/leave/requests", "service": "leave-service"},
        "travel": {"method": "GET", "gateway_path": "/api/v1/travel/requests", "expected_upstream": "/travel/requests", "service": "travel-service"},
        "projects": {"method": "GET", "gateway_path": "/api/v1/projects", "expected_upstream": "/projects", "service": "project-service"},
        "payroll": {"method": "GET", "gateway_path": "/api/v1/payroll/records", "expected_upstream": "/payroll/records", "service": "payroll-service"},
        "hiring": {"method": "GET", "gateway_path": "/api/v1/hiring/job-postings", "expected_upstream": "/hiring/job-postings", "service": "hiring-service"},
        "auth": {"method": "GET", "gateway_path": "/api/v1/auth/me", "expected_upstream": "/auth/me", "service": "auth-service"},
        "workflows": {"method": "GET", "gateway_path": "/api/v1/workflows/inbox?tenant_id=tenant-default", "expected_upstream": "/workflows/inbox?tenant_id=tenant-default", "service": "workflow-service"},
        "audit": {"method": "GET", "gateway_path": "/api/v1/audit/records", "expected_upstream": "/audit/records", "service": "audit-service"},
        "notifications": {"method": "POST", "gateway_path": "/api/v1/notifications/events", "expected_upstream": "/notifications/events", "service": "notification-service", "body": {"event_type": "notification.sent", "tenant_id": "tenant-default", "channel": "email", "recipient": "ops@example.com", "subject": "s", "message": "m"}},
        "engagement": {"method": "GET", "gateway_path": "/api/v1/engagement/surveys", "expected_upstream": "/engagement/surveys", "service": "engagement-service"},
        "helpdesk": {"method": "GET", "gateway_path": "/api/v1/helpdesk/tickets", "expected_upstream": "/helpdesk/tickets", "service": "helpdesk-service"},
        "reporting": {"method": "GET", "gateway_path": "/api/v1/reporting/aggregates", "expected_upstream": "/reporting/aggregates", "service": "reporting-analytics-service"},
        "search": {"method": "GET", "gateway_path": "/api/v1/search", "expected_upstream": "/search", "service": "search-service"},
        "expense": {"method": "GET", "gateway_path": "/api/v1/expense/claims", "expected_upstream": "/expense/claims", "service": "expense-service"},
        "integrations": {"method": "GET", "gateway_path": "/api/v1/integrations/webhooks?tenant_id=tenant-default", "expected_upstream": "/integrations/webhooks?tenant_id=tenant-default", "service": "integration-service"},
        "automations": {"method": "GET", "gateway_path": "/api/v1/automations/rules?tenant_id=tenant-default", "expected_upstream": "/automations/rules?tenant_id=tenant-default", "service": "automation-service"},
        "settings": {"method": "GET", "gateway_path": "/api/v1/settings", "expected_upstream": "/settings", "service": "settings-service"},
    }

    declared_route_names = {route.name for route in api_gateway_routes.iter_routes()}
    assert declared_route_names == set(route_execution_cases)

    for name, scenario in route_execution_cases.items():
        route = api_gateway_routes.resolve_route(scenario["gateway_path"])
        translated_path = api_gateway_routes.translate_to_upstream_path(route, scenario["gateway_path"])

        assert translated_path == scenario["expected_upstream"], (
            f"{name} translated path mismatch: expected={scenario['expected_upstream']} actual={translated_path}"
        )
        assert route.upstream_service == scenario["service"]

        status, payload = _execute_forwarded_request(
            service_name=scenario["service"],
            method=scenario["method"],
            forwarded_path_with_query=translated_path,
            body=scenario.get("body"),
        )

        assert status < 500, f"{name} runtime execution failed with non-executable status={status}"
        assert payload["status"] in {"success", "error"}


def test_every_runtime_service_declared_in_compose_is_bootable_in_domain_runtime() -> None:
    runtime_services = [
        "employee-service",
        "attendance-service",
        "leave-service",
        "payroll-service",
        "hiring-service",
        "auth-service",
        "notification-service",
        "audit-service",
        "workflow-service",
        "performance-service",
        "engagement-service",
        "helpdesk-service",
        "reporting-analytics-service",
        "search-service",
        "expense-service",
        "integration-service",
        "automation-service",
        "travel-service",
        "project-service",
        "settings-service",
    ]

    for service_name in runtime_services:
        routes, context = build_service_runtime(service_name)
        assert routes, f"runtime must expose at least one route for {service_name}"
        assert context.get("routes"), f"runtime context should include route inventory for {service_name}"
