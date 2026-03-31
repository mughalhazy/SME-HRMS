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


def test_gateway_to_runtime_execution_alignment_for_core_domains() -> None:
    scenarios = [
        {
            "name": "settings",
            "method": "GET",
            "gateway_path": "/api/v1/settings",
            "expected_upstream": "/settings",
            "service": "settings-service",
            "expected_status": 200,
            "expected_payload_status": "success",
        },
        {
            "name": "attendance",
            "method": "GET",
            "gateway_path": "/api/v1/attendance/records?employee_id=11111111-1111-1111-1111-111111111111&from_date=2026-01-01&to_date=2026-01-31",
            "expected_upstream": "/attendance/records?employee_id=11111111-1111-1111-1111-111111111111&from_date=2026-01-01&to_date=2026-01-31",
            "service": "attendance-service",
            "expected_status": 403,
            "expected_payload_status": "error",
        },
        {
            "name": "helpdesk",
            "method": "GET",
            "gateway_path": "/api/v1/helpdesk/tickets",
            "expected_upstream": "/helpdesk/tickets",
            "service": "helpdesk-service",
            "expected_status": 200,
            "expected_payload_status": "success",
        },
        {
            "name": "workflow",
            "method": "GET",
            "gateway_path": "/api/v1/workflows/inbox?tenant_id=tenant-default",
            "expected_upstream": "/workflows/inbox?tenant_id=tenant-default",
            "service": "workflow-service",
            "expected_status": 200,
            "expected_payload_status": "success",
        },
        {
            "name": "project",
            "method": "GET",
            "gateway_path": "/api/v1/projects",
            "expected_upstream": "/projects",
            "service": "project-service",
            "expected_status": 200,
            "expected_payload_status": "success",
        },
        {
            "name": "employee",
            "method": "GET",
            "gateway_path": "/api/v1/employees",
            "expected_upstream": "/employees",
            "service": "employee-service",
            "expected_status": 200,
            "expected_payload_status": "success",
        },
    ]

    for scenario in scenarios:
        gateway_path = scenario["gateway_path"]
        route = api_gateway_routes.resolve_route(gateway_path)
        translated_path = api_gateway_routes.translate_to_upstream_path(route, gateway_path)

        assert translated_path == scenario["expected_upstream"], (
            f"{scenario['name']} translated path mismatch: expected={scenario['expected_upstream']} actual={translated_path}"
        )
        assert route.upstream_service == scenario["service"]

        status, payload = _execute_forwarded_request(
            service_name=scenario["service"],
            method=scenario["method"],
            forwarded_path_with_query=translated_path,
        )

        assert status == scenario["expected_status"], f"{scenario['name']} runtime status mismatch: {status}"
        assert payload["status"] == scenario["expected_payload_status"], (
            f"{scenario['name']} runtime payload status mismatch: {payload['status']}"
        )
        if scenario["expected_payload_status"] == "success":
            assert payload["error"] is None, f"{scenario['name']} runtime payload unexpectedly contained an error"
        else:
            assert payload["error"], f"{scenario['name']} runtime payload should include an error body"
