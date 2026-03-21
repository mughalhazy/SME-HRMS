from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest

MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / 'api-gateway' / 'tenant.py'
SPEC = importlib.util.spec_from_file_location('api_gateway_tenant', MODULE_PATH)
module = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


class GatewayTenantContextTests(unittest.TestCase):
    def test_gateway_resolves_tenant_and_route_context(self) -> None:
        context = module.resolve_gateway_context(
            '/api/v1/leave/requests',
            {
                'x-tenant-id': 'tenant-acme',
                'x-request-id': 'req-123',
                'x-actor-id': 'user-456',
            },
        )
        self.assertEqual(context.route.upstream_service, 'leave-service')
        self.assertEqual(context.tenant_id, 'tenant-acme')
        self.assertEqual(context.request_id, 'req-123')
        self.assertEqual(context.actor_id, 'user-456')

    def test_gateway_builds_upstream_headers_with_tenant_context(self) -> None:
        context = module.resolve_gateway_context('/api/v1/payroll/records', {'x-tenant': 'tenant-beta', 'x-trace-id': 'trace-1'})
        headers = module.build_upstream_headers(context, {'authorization': 'Bearer token'})
        self.assertEqual(headers['x-tenant-id'], 'tenant-beta')
        self.assertEqual(headers['x-request-id'], 'trace-1')
        self.assertEqual(headers['x-trace-id'], 'trace-1')
        self.assertEqual(headers['authorization'], 'Bearer token')


if __name__ == '__main__':
    unittest.main()
