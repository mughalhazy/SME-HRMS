from __future__ import annotations

import importlib.util
import pathlib
import re
import sys
import unittest

MODULE_PATH = pathlib.Path(__file__).resolve().parents[2] / "api-gateway" / "routes.py"
SPEC = importlib.util.spec_from_file_location("api_gateway_routes_contract", MODULE_PATH)
api_gateway_routes = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = api_gateway_routes
SPEC.loader.exec_module(api_gateway_routes)


class GatewayApiStandardsTests(unittest.TestCase):
    def test_all_routes_use_v1_prefix(self) -> None:
        for route in api_gateway_routes.iter_routes():
            with self.subTest(route=route.name):
                self.assertTrue(route.full_path_prefix.startswith("/api/v1/"))

    def test_route_segments_use_noun_style_naming(self) -> None:
        # Lowercase letters and optional internal hyphens are allowed.
        segment_pattern = re.compile(r"^/[a-z]+(?:-[a-z]+)*$")
        for route in api_gateway_routes.iter_routes():
            with self.subTest(route=route.name):
                self.assertRegex(route.path_prefix, segment_pattern)

    def test_gateway_resolves_plural_resource_paths(self) -> None:
        test_cases = {
            "/api/v1/employees/123": "employee-service",
            "/api/v1/departments/123": "employee-service",
            "/api/v1/attendance/records": "attendance-service",
            "/api/v1/notifications/events": "notification-service",
        }
        for path, service in test_cases.items():
            with self.subTest(path=path):
                resolved = api_gateway_routes.resolve_route(path)
                self.assertEqual(resolved.upstream_service, service)


if __name__ == "__main__":
    unittest.main()
