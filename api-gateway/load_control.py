from __future__ import annotations

from dataclasses import asdict, dataclass, field
from threading import Condition, Lock
from time import monotonic
from typing import Any, Callable, Mapping

from resilience import Observability
from tenant_support import normalize_tenant_id


@dataclass(frozen=True)
class LimitWindow:
    limit: int
    window_ms: int


@dataclass(frozen=True)
class ThrottleConfig:
    max_concurrent: int
    max_queue: int
    queue_timeout_ms: int = 200


@dataclass(frozen=True)
class GatewayTrafficPolicy:
    tenant_burst: LimitWindow = field(default_factory=lambda: LimitWindow(limit=120, window_ms=1_000))
    tenant_sustained: LimitWindow = field(default_factory=lambda: LimitWindow(limit=2_000, window_ms=60_000))
    user_burst: LimitWindow = field(default_factory=lambda: LimitWindow(limit=30, window_ms=1_000))
    user_sustained: LimitWindow = field(default_factory=lambda: LimitWindow(limit=300, window_ms=60_000))
    abusive_client_burst: LimitWindow = field(default_factory=lambda: LimitWindow(limit=90, window_ms=1_000))
    request_timeout_ms: int = 1_500
    collapse_ttl_ms: int = 250
    throttle: ThrottleConfig = field(default_factory=lambda: ThrottleConfig(max_concurrent=48, max_queue=96, queue_timeout_ms=200))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None, *, fallback: 'GatewayTrafficPolicy | None' = None) -> 'GatewayTrafficPolicy':
        base = fallback or cls()
        source = dict(payload or {})

        def _window(key: str, current: LimitWindow) -> LimitWindow:
            raw = dict(source.get(key) or {})
            return LimitWindow(limit=int(raw.get('limit', current.limit)), window_ms=int(raw.get('window_ms', current.window_ms)))

        throttle_raw = dict(source.get('throttle') or {})
        throttle = ThrottleConfig(
            max_concurrent=int(throttle_raw.get('max_concurrent', base.throttle.max_concurrent)),
            max_queue=int(throttle_raw.get('max_queue', base.throttle.max_queue)),
            queue_timeout_ms=int(throttle_raw.get('queue_timeout_ms', base.throttle.queue_timeout_ms)),
        )
        return cls(
            tenant_burst=_window('tenant_burst', base.tenant_burst),
            tenant_sustained=_window('tenant_sustained', base.tenant_sustained),
            user_burst=_window('user_burst', base.user_burst),
            user_sustained=_window('user_sustained', base.user_sustained),
            abusive_client_burst=_window('abusive_client_burst', base.abusive_client_burst),
            request_timeout_ms=int(source.get('request_timeout_ms', base.request_timeout_ms)),
            collapse_ttl_ms=int(source.get('collapse_ttl_ms', base.collapse_ttl_ms)),
            throttle=throttle,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GatewayTrafficPolicyStore:
    def __init__(self, default_policy: GatewayTrafficPolicy | None = None) -> None:
        self.default_policy = default_policy or GatewayTrafficPolicy()
        self._tenant_policies: dict[str, GatewayTrafficPolicy] = {}
        self._lock = Lock()

    def upsert_tenant_policy(self, tenant_id: str, payload: Mapping[str, Any]) -> GatewayTrafficPolicy:
        tenant = normalize_tenant_id(tenant_id)
        with self._lock:
            current = self._tenant_policies.get(tenant, self.default_policy)
            policy = GatewayTrafficPolicy.from_mapping(payload, fallback=current)
            self._tenant_policies[tenant] = policy
            return policy

    def get_policy(self, tenant_id: str | None) -> GatewayTrafficPolicy:
        tenant = normalize_tenant_id(tenant_id)
        with self._lock:
            return self._tenant_policies.get(tenant, self.default_policy)


@dataclass
class _CounterWindow:
    count: int
    reset_at_ms: int


class GatewayRateLimiter:
    def __init__(self, policy_store: GatewayTrafficPolicyStore | None = None, *, observability: Observability | None = None) -> None:
        self.policy_store = policy_store or GatewayTrafficPolicyStore()
        self.observability = observability or Observability('api-gateway')
        self._windows: dict[str, _CounterWindow] = {}
        self._lock = Lock()

    def evaluate(
        self,
        *,
        tenant_id: str,
        actor_id: str | None,
        client_id: str,
        route_key: str,
        method: str,
        now_ms: int | None = None,
    ) -> dict[str, Any]:
        tenant = normalize_tenant_id(tenant_id)
        policy = self.policy_store.get_policy(tenant)
        timestamp = int(now_ms if now_ms is not None else monotonic() * 1000)
        principal = actor_id or 'anonymous'

        checks = [
            ('tenant_burst', policy.tenant_burst, f'tenant:{tenant}'),
            ('tenant_sustained', policy.tenant_sustained, f'tenant:{tenant}'),
            ('user_burst', policy.user_burst, f'user:{tenant}:{principal}'),
            ('user_sustained', policy.user_sustained, f'user:{tenant}:{principal}'),
            ('abusive_client_burst', policy.abusive_client_burst, f'client:{tenant}:{client_id}'),
        ]

        with self._lock:
            for scope, limit_window, subject_key in checks:
                bucket_key = f'{scope}:{method}:{route_key}:{subject_key}'
                decision = self._increment(bucket_key, limit_window, now_ms=timestamp)
                if not decision['allowed']:
                    self.observability.logger.info(
                        'gateway.rate_limit.exceeded',
                        context={
                            'tenant_id': tenant,
                            'actor_id': actor_id,
                            'client_id': client_id,
                            'route_key': route_key,
                            'method': method,
                            'scope': scope,
                            'limit': limit_window.limit,
                            'window_ms': limit_window.window_ms,
                        },
                    )
                    return {
                        'allowed': False,
                        'scope': scope,
                        'tenant_id': tenant,
                        'headers': decision['headers'],
                        'retry_after_ms': decision['retry_after_ms'],
                    }

        return {
            'allowed': True,
            'tenant_id': tenant,
            'policy': policy.to_dict(),
        }

    def _increment(self, key: str, limit_window: LimitWindow, *, now_ms: int) -> dict[str, Any]:
        current = self._windows.get(key)
        if current is None or current.reset_at_ms <= now_ms:
            current = _CounterWindow(count=0, reset_at_ms=now_ms + limit_window.window_ms)
            self._windows[key] = current
        current.count += 1
        remaining = max(0, limit_window.limit - current.count)
        allowed = current.count <= limit_window.limit
        return {
            'allowed': allowed,
            'headers': {
                'X-RateLimit-Limit': str(limit_window.limit),
                'X-RateLimit-Remaining': str(remaining),
                'X-RateLimit-Reset': str(max(0, (current.reset_at_ms - now_ms + 999) // 1000)),
            },
            'retry_after_ms': max(0, current.reset_at_ms - now_ms),
        }


@dataclass
class _CollapsedEntry:
    ready: bool = False
    value: Any = None
    error: Exception | None = None
    completed_at: float | None = None
    in_flight: bool = False


class GatewayRequestCollapser:
    def __init__(self, policy_store: GatewayTrafficPolicyStore | None = None, *, observability: Observability | None = None) -> None:
        self.policy_store = policy_store or GatewayTrafficPolicyStore()
        self.observability = observability or Observability('api-gateway')
        self._entries: dict[str, _CollapsedEntry] = {}
        self._condition = Condition(Lock())

    def execute(
        self,
        *,
        tenant_id: str,
        cache_key: str,
        supplier: Callable[[], Any],
    ) -> Any:
        tenant = normalize_tenant_id(tenant_id)
        ttl_seconds = self.policy_store.get_policy(tenant).collapse_ttl_ms / 1000
        full_key = f'{tenant}:{cache_key}'
        now = monotonic()
        execute_supplier = False

        with self._condition:
            entry = self._entries.get(full_key)
            if entry and entry.ready and entry.completed_at is not None and (now - entry.completed_at) <= ttl_seconds:
                self.observability.logger.info('gateway.request_collapsed.cache_hit', context={'tenant_id': tenant, 'cache_key': cache_key})
                if entry.error:
                    raise entry.error
                return entry.value
            if entry and entry.in_flight:
                self.observability.logger.info('gateway.request_collapsed.joined', context={'tenant_id': tenant, 'cache_key': cache_key})
                while entry.in_flight:
                    self._condition.wait(timeout=ttl_seconds or 0.1)
                if entry.error:
                    raise entry.error
                return entry.value
            entry = _CollapsedEntry(in_flight=True)
            self._entries[full_key] = entry
            execute_supplier = True

        if execute_supplier:
            try:
                value = supplier()
            except Exception as exc:  # noqa: BLE001
                with self._condition:
                    entry.in_flight = False
                    entry.ready = True
                    entry.error = exc
                    entry.completed_at = monotonic()
                    self._condition.notify_all()
                raise
            with self._condition:
                entry.in_flight = False
                entry.ready = True
                entry.value = value
                entry.completed_at = monotonic()
                self._condition.notify_all()
            return value

        raise RuntimeError('request collapser reached an invalid state')
