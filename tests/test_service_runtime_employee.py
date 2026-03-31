from __future__ import annotations

from docker.service_runtime import build_service_runtime


def _route_map(service_name: str):
    routes, context = build_service_runtime(service_name)
    return {(route.method, route.pattern): route for route in routes}, context


def test_employee_service_runtime_boots_with_declared_routes() -> None:
    route_map, context = _route_map("employee-service")

    assert ("GET", "/employees") in route_map
    assert ("GET", "/departments") in route_map
    assert "GET /employees" in context["routes"]
    assert "GET /departments" in context["routes"]


def test_employee_service_employees_endpoint_returns_real_payload() -> None:
    route_map, _ = _route_map("employee-service")

    status, payload = route_map[("GET", "/employees")].handler({}, {}, {}, {})
    assert status == 200
    assert payload["status"] == "success"
    assert payload["data"]["count"] >= 1
    assert any(item["employee_id"] == "emp-hr-admin" for item in payload["data"]["items"])

    filtered_status, filtered_payload = route_map[("GET", "/employees")].handler({}, {"department_id": "dep-eng"}, {}, {})
    assert filtered_status == 200
    assert filtered_payload["data"]["count"] == 1
    assert filtered_payload["data"]["items"][0]["department_id"] == "dep-eng"


def test_employee_service_departments_endpoint_uses_employee_domain_seed() -> None:
    route_map, _ = _route_map("employee-service")

    status, payload = route_map[("GET", "/departments")].handler({}, {}, {}, {})
    assert status == 200
    assert payload["status"] == "success"
    assert payload["data"]["count"] >= 3
    assert any(item["department_id"] == "dep-hr" for item in payload["data"]["items"])

    active_status, active_payload = route_map[("GET", "/departments")].handler({}, {"status": "Active"}, {}, {})
    assert active_status == 200
    assert all(item["status"] == "Active" for item in active_payload["data"]["items"])
