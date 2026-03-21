import importlib.util
import pathlib
import unittest


MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "api-gateway" / "routes.py"
SPEC = importlib.util.spec_from_file_location("api_gateway_routes", MODULE_PATH)
import sys
api_gateway_routes = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = api_gateway_routes
SPEC.loader.exec_module(api_gateway_routes)


class ApiGatewayRouteTests(unittest.TestCase):
    def test_gateway_exposes_expected_route_groups(self) -> None:
        names = [route.name for route in api_gateway_routes.iter_routes()]
        self.assertEqual(names, ["employees", "departments", "performance", "attendance", "leave", "payroll", "hiring", "auth", "workflows", "audit", "notifications", "integrations", "jobs"])

    def test_resolve_each_route_prefix(self) -> None:
        cases = {
            "/api/v1/employees": "employee-service",
            "/api/v1/departments": "employee-service",
            "/api/v1/performance/goals": "performance-service",
            "/api/v1/attendance/records": "attendance-service",
            "/api/v1/leave/requests": "leave-service",
            "/api/v1/payroll/run": "payroll-service",
            "/api/v1/hiring/candidates": "hiring-service",
            "/api/v1/audit/records": "audit-service",
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                route = api_gateway_routes.resolve_route(path)
                self.assertEqual(route.upstream_service, expected)

    def test_unknown_route_raises(self) -> None:
        route = api_gateway_routes.resolve_route("/api/v1/auth/login")
        self.assertEqual(route.upstream_service, "auth-service")

        workflow_route = api_gateway_routes.resolve_route("/api/v1/workflows/123")
        self.assertEqual(workflow_route.upstream_service, "workflow-service")

        notification_route = api_gateway_routes.resolve_route("/api/v1/notifications/send")
        self.assertEqual(notification_route.upstream_service, "notification-service")

        with self.assertRaises(api_gateway_routes.RouteNotFoundError):
            api_gateway_routes.resolve_route("/api/v1/unknown")


if __name__ == "__main__":
    unittest.main()
