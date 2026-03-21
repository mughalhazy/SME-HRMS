from __future__ import annotations

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, TypeVar
from uuid import uuid4

from audit_service.service import emit_audit_record

LOGGER = logging.getLogger("sme_hrms.resilience")

T = TypeVar("T")


def new_trace_id() -> str:
    return uuid4().hex


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StructuredLogger:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.records: list[dict[str, Any]] = []
        self._lock = Lock()

    def log(
        self,
        level: str,
        event: str,
        *,
        trace_id: str | None = None,
        message: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = {
            "timestamp": utc_now().isoformat(),
            "level": level.upper(),
            "service": self.service_name,
            "event": event,
            "trace_id": trace_id or new_trace_id(),
            "message": message or event,
            "context": context or {},
        }
        with self._lock:
            self.records.append(record)
        LOGGER.log(getattr(logging, record["level"], logging.INFO), json.dumps(record, sort_keys=True))
        return record

    def info(self, event: str, *, trace_id: str | None = None, message: str | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.log("INFO", event, trace_id=trace_id, message=message, context=context)

    def error(self, event: str, *, trace_id: str | None = None, message: str | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.log("ERROR", event, trace_id=trace_id, message=message, context=context)

    def audit(self, action: str, *, trace_id: str | None = None, actor: str | dict[str, Any] | None = None, entity: str | None = None, entity_id: str | None = None, outcome: str = "success", context: dict[str, Any] | None = None) -> dict[str, Any]:
        audit_context = {"actor": actor, "entity": entity, "entity_id": entity_id, "outcome": outcome, **(context or {})}
        actor_payload = actor if isinstance(actor, dict) else {
            'id': actor or str((context or {}).get('actor_id') or 'system'),
            'type': str((context or {}).get('actor_type') or 'system'),
            'role': (context or {}).get('actor_role'),
            'department_id': (context or {}).get('actor_department_id'),
        }
        record = emit_audit_record(
            service_name=self.service_name,
            tenant_id=str((context or {}).get('tenant_id') or 'tenant-default'),
            actor=actor_payload,
            action=action,
            entity=entity or str((context or {}).get('entity') or 'Unknown'),
            entity_id=str(entity_id or (context or {}).get('entity_id') or 'unknown'),
            before=(context or {}).get('before') or {},
            after=(context or {}).get('after') or {},
            trace_id=trace_id or new_trace_id(),
            source={key: value for key, value in (context or {}).items() if key not in {'tenant_id', 'before', 'after', 'actor_type', 'actor_role', 'actor_department_id'}},
        )
        audit_context['audit_record'] = record
        return self.log("INFO", "audit", trace_id=trace_id, message=action, context=audit_context)


@dataclass
class RequestMetric:
    trace_id: str
    operation: str
    latency_ms: float
    success: bool
    recorded_at: str
    context: dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.request_count = 0
        self.error_count = 0
        self._latencies_ms: list[float] = []
        self.request_metrics: list[RequestMetric] = []
        self._lock = Lock()

    def record_request(self, operation: str, *, trace_id: str, latency_ms: float, success: bool, context: dict[str, Any] | None = None) -> None:
        with self._lock:
            self.request_count += 1
            if not success:
                self.error_count += 1
            self._latencies_ms.append(latency_ms)
            self.request_metrics.append(
                RequestMetric(
                    trace_id=trace_id,
                    operation=operation,
                    latency_ms=round(latency_ms, 3),
                    success=success,
                    recorded_at=utc_now().isoformat(),
                    context=context or {},
                )
            )

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            latency_avg = sum(self._latencies_ms) / len(self._latencies_ms) if self._latencies_ms else 0.0
            latency_max = max(self._latencies_ms) if self._latencies_ms else 0.0
            return {
                "service": self.service_name,
                "request_count": self.request_count,
                "error_count": self.error_count,
                "error_rate": round((self.error_count / self.request_count), 4) if self.request_count else 0.0,
                "latency_ms": {
                    "avg": round(latency_avg, 3),
                    "max": round(latency_max, 3),
                },
                "recent_requests": [asdict(metric) for metric in self.request_metrics[-20:]],
            }


class Observability:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = StructuredLogger(service_name)
        self.metrics = MetricsCollector(service_name)

    def trace_id(self, incoming: str | None = None) -> str:
        return incoming or new_trace_id()

    def track(self, operation: str, *, trace_id: str, started_at: float, success: bool, context: dict[str, Any] | None = None) -> float:
        latency_ms = (time.perf_counter() - started_at) * 1000
        self.metrics.record_request(operation, trace_id=trace_id, latency_ms=latency_ms, success=success, context=context)
        self.logger.info(
            "request.completed",
            trace_id=trace_id,
            message=operation,
            context={"success": success, "latency_ms": round(latency_ms, 3), **(context or {})},
        )
        return latency_ms

    def health_status(self, *, checks: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "service": self.service_name,
            "status": "ok",
            "checks": checks or {},
            "metrics": self.metrics.snapshot(),
        }


class CircuitBreakerOpenError(RuntimeError):
    """Raised when a circuit breaker rejects an operation while open."""


class OperationTimeoutError(TimeoutError):
    """Raised when a protected operation exceeds its timeout budget."""


@dataclass
class LoggedFailure:
    service: str
    operation: str
    error_type: str
    message: str
    trace_id: str
    occurred_at: str
    details: dict[str, Any] = field(default_factory=dict)


class CentralErrorLogger:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.failures: list[LoggedFailure] = []
        self.structured_logger = StructuredLogger(service_name)
        self._lock = Lock()

    def log(self, operation: str, error: Exception, *, trace_id: str | None = None, details: dict[str, Any] | None = None) -> LoggedFailure:
        trace = trace_id or new_trace_id()
        failure = LoggedFailure(
            service=self.service_name,
            operation=operation,
            error_type=type(error).__name__,
            message=str(error),
            trace_id=trace,
            occurred_at=utc_now().isoformat(),
            details=details or {},
        )
        with self._lock:
            self.failures.append(failure)
        self.structured_logger.error(
            "error",
            trace_id=trace,
            message=operation,
            context={
                "error_type": failure.error_type,
                "message": failure.message,
                "details": failure.details,
            },
        )
        return failure


@dataclass
class DeadLetter:
    dead_letter_id: str
    workflow: str
    operation: str
    reason: str
    payload: dict[str, Any]
    trace_id: str
    created_at: str
    retryable: bool = True
    recovered_at: str | None = None


class DeadLetterQueue:
    def __init__(self):
        self.entries: list[DeadLetter] = []
        self._lock = Lock()

    def push(self, workflow: str, operation: str, payload: dict[str, Any], reason: str, *, trace_id: str | None = None, retryable: bool = True) -> DeadLetter:
        entry = DeadLetter(
            dead_letter_id=uuid4().hex,
            workflow=workflow,
            operation=operation,
            reason=reason,
            payload=payload,
            trace_id=trace_id or new_trace_id(),
            created_at=utc_now().isoformat(),
            retryable=retryable,
        )
        with self._lock:
            self.entries.append(entry)
        return entry

    def recover(self, predicate: Callable[[DeadLetter], bool], retry: Callable[[DeadLetter], bool]) -> list[DeadLetter]:
        recovered: list[DeadLetter] = []
        with self._lock:
            for entry in self.entries:
                if entry.recovered_at is not None or not entry.retryable or not predicate(entry):
                    continue
                if retry(entry):
                    entry.recovered_at = utc_now().isoformat()
                    recovered.append(entry)
        return recovered


@dataclass
class IdempotentResult:
    key: str
    fingerprint: str
    status_code: int
    payload: dict[str, Any]


class IdempotencyStore:
    def __init__(self):
        self._entries: dict[str, IdempotentResult] = {}
        self._lock = Lock()

    def get(self, key: str) -> IdempotentResult | None:
        with self._lock:
            return self._entries.get(key)

    def record(self, key: str, fingerprint: str, status_code: int, payload: dict[str, Any]) -> IdempotentResult:
        with self._lock:
            result = IdempotentResult(key=key, fingerprint=fingerprint, status_code=status_code, payload=payload)
            self._entries[key] = result
            return result

    def replay_or_conflict(self, key: str, fingerprint: str) -> IdempotentResult | None:
        with self._lock:
            existing = self._entries.get(key)
            if existing and existing.fingerprint != fingerprint:
                raise ValueError("idempotency key reuse with different payload")
            return existing


class CircuitBreaker:
    def __init__(self, *, failure_threshold: int = 3, recovery_timeout: float = 5.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.opened_at: float | None = None
        self._lock = Lock()

    def call(self, func: Callable[[], T]) -> T:
        with self._lock:
            if self.opened_at is not None:
                if (time.monotonic() - self.opened_at) < self.recovery_timeout:
                    raise CircuitBreakerOpenError("circuit breaker is open")
                self.opened_at = None
                self.failure_count = 0

        try:
            result = func()
        except Exception:
            with self._lock:
                self.failure_count += 1
                if self.failure_count >= self.failure_threshold:
                    self.opened_at = time.monotonic()
            raise

        with self._lock:
            self.failure_count = 0
            self.opened_at = None
        return result


def run_with_timeout(func: Callable[[], T], timeout_seconds: float) -> T:
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func)
        try:
            return future.result(timeout=timeout_seconds)
        except FutureTimeoutError as exc:
            future.cancel()
            raise OperationTimeoutError(f"operation exceeded timeout of {timeout_seconds} seconds") from exc


def run_with_retry(
    func: Callable[[], T],
    *,
    attempts: int = 3,
    base_delay: float = 0.05,
    timeout_seconds: float = 1.0,
    retryable: Callable[[Exception], bool] | None = None,
    on_retry: Callable[[int, Exception, float], None] | None = None,
) -> T:
    retryable = retryable or (lambda exc: True)
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return run_with_timeout(func, timeout_seconds)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt >= attempts or not retryable(exc):
                raise
            delay = base_delay * (2 ** (attempt - 1))
            if on_retry is not None:
                on_retry(attempt, exc, delay)
            time.sleep(delay)
    assert last_error is not None
    raise last_error
