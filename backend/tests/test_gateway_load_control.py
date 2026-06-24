from __future__ import annotations

import importlib.util
import pathlib
import sys
import threading
import time

MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / 'api-gateway' / 'load_control.py'
SPEC = importlib.util.spec_from_file_location('api_gateway_load_control', MODULE_PATH)
module = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def test_rate_limiter_enforces_per_tenant_and_per_user_burst_limits() -> None:
    store = module.GatewayTrafficPolicyStore()
    store.upsert_tenant_policy(
        'tenant-acme',
        {
            'tenant_burst': {'limit': 2, 'window_ms': 1_000},
            'tenant_sustained': {'limit': 10, 'window_ms': 60_000},
            'user_burst': {'limit': 1, 'window_ms': 1_000},
            'user_sustained': {'limit': 5, 'window_ms': 60_000},
        },
    )
    limiter = module.GatewayRateLimiter(store)

    first = limiter.evaluate(tenant_id='tenant-acme', actor_id='user-1', client_id='ip-1', route_key='GET:/api/v1/search', method='GET', now_ms=100)
    second = limiter.evaluate(tenant_id='tenant-acme', actor_id='user-1', client_id='ip-1', route_key='GET:/api/v1/search', method='GET', now_ms=200)
    third = limiter.evaluate(tenant_id='tenant-acme', actor_id='user-2', client_id='ip-2', route_key='GET:/api/v1/search', method='GET', now_ms=300)

    assert first['allowed'] is True
    assert second['allowed'] is False
    assert second['scope'] == 'user_burst'
    assert third['allowed'] is False
    assert third['scope'] == 'tenant_burst'


def test_rate_limiter_can_block_abusive_client_without_penalizing_other_tenants() -> None:
    store = module.GatewayTrafficPolicyStore()
    store.upsert_tenant_policy('tenant-a', {'abusive_client_burst': {'limit': 1, 'window_ms': 1_000}})
    limiter = module.GatewayRateLimiter(store)

    allowed = limiter.evaluate(tenant_id='tenant-a', actor_id='user-1', client_id='shared-ip', route_key='GET:/health', method='GET', now_ms=100)
    blocked = limiter.evaluate(tenant_id='tenant-a', actor_id='user-2', client_id='shared-ip', route_key='GET:/health', method='GET', now_ms=150)
    other_tenant = limiter.evaluate(tenant_id='tenant-b', actor_id='user-1', client_id='shared-ip', route_key='GET:/health', method='GET', now_ms=150)

    assert allowed['allowed'] is True
    assert blocked['allowed'] is False
    assert blocked['scope'] == 'abusive_client_burst'
    assert other_tenant['allowed'] is True


def test_request_collapser_reuses_single_supplier_result_for_concurrent_reads() -> None:
    store = module.GatewayTrafficPolicyStore()
    store.upsert_tenant_policy('tenant-default', {'collapse_ttl_ms': 1_000})
    collapser = module.GatewayRequestCollapser(store)
    calls: list[str] = []
    results: list[dict[str, int]] = []

    def supplier() -> dict[str, int]:
        calls.append('call')
        time.sleep(0.05)
        return {'value': 42}

    def invoke() -> None:
        results.append(collapser.execute(tenant_id='tenant-default', cache_key='search:engineering', supplier=supplier))

    first = threading.Thread(target=invoke)
    second = threading.Thread(target=invoke)
    first.start()
    second.start()
    first.join()
    second.join()

    cached = collapser.execute(tenant_id='tenant-default', cache_key='search:engineering', supplier=supplier)

    assert len(calls) == 1
    assert results == [{'value': 42}, {'value': 42}]
    assert cached == {'value': 42}
