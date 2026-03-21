from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, TypeVar
from uuid import uuid4

from audit_service.service import emit_audit_record

LOGGER = logging.getLogger("sme_hrms.resilience")
SENSITIVE_FIELD_NAMES = {
    "password",
    "password_hash",
    "refresh_token",
    "refresh_token_hash",
    "token_hash",
    "access_token",
    "authorization",
    "secret",
    "bank_account",
    "bank_account_number",
    "routing_number",
    "tax_id",
    "ssn",
}
DEPENDENCY_ERROR_TYPES = {
    "ConnectionError",
    "ConnectionResetError",
    "ConnectionRefusedError",
    "ConnectionAbortedError",
    "TimeoutError",
    "OperationTimeoutError",
    "CircuitBreakerOpenError",
}

T = TypeVar("T")


def new_trace_id() -> str:
    return uuid4().hex


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def sanitize_log_context(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            if key.lower() in SENSITIVE_FIELD_NAMES:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_log_context(item)
        return sanitized
    if isinstance(value, list):
        return [sanitize_log_context(item) for item in value]
    return value


def normalize_status(value: Any, *, success: bool | None = None, default: str | None = None) -> str:
    if value is not None:
        return str(value)
    if success is not None:
        return "success" if success else "error"
    return default or "ok"


def infer_tenant_id(context: dict[str, Any] | None) -> str | None:
    if not context:
        return None
    tenant_id = context.get("tenant_id")
    return str(tenant_id) if tenant_id not in (None, "") else None


def infer_correlation_id(request_id: str, context: dict[str, Any] | None) -> str:
    if context:
        correlation_id = context.get("correlation_id") or context.get("trace_id") or context.get("request_id")
        if correlation_id:
            return str(correlation_id)
    return request_id


def classify_error(error: Exception, *, details: dict[str, Any] | None = None) -> str:
    payload = details or {}
    explicit = payload.get("category") or payload.get("error_category")
    if explicit:
        return str(explicit)
    code = str(getattr(error, "code", "") or payload.get("code") or "").upper()
    status_code = getattr(error, "status_code", payload.get("status"))
    name = type(error).__name__
    if code.startswith("VALIDATION") or code in {"BAD_REQUEST", "INVALID_REQUEST", "INVALID_PAYLOAD", "TENANT_SCOPE_VIOLATION"}:
        return "validation"
    if status_code in {400, 401, 403, 404, 409, 422}:
        return "validation"
    if name in DEPENDENCY_ERROR_TYPES:
        return "dependency"
    return "system"


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
        action: str | None = None,
        status: str | None = None,
        tenant_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        sanitized_context = sanitize_log_context(context or {})
        request_id = trace_id or str(sanitized_context.get("request_id") or sanitized_context.get("trace_id") or new_trace_id())
        record = {
            "timestamp": utc_now().isoformat(),
            "level": level.upper(),
            "service": self.service_name,
            "event": event,
            "action": action or str(sanitized_context.get("action") or event),
            "status": normalize_status(status or sanitized_context.get("status") or sanitized_context.get("status_code"), default="ok"),
            "tenant_id": tenant_id or infer_tenant_id(sanitized_context),
            "request_id": request_id,
            "trace_id": request_id,
            "correlation_id": correlation_id or infer_correlation_id(request_id, sanitized_context),
            "message": message or event,
            "context": sanitized_context,
        }
        with self._lock:
            self.records.append(record)
            if len(self.records) > 500:
                self.records.pop(0)
        LOGGER.log(getattr(logging, record["level"], logging.INFO), json.dumps(record, sort_keys=True))
        return record

    def info(
        self,
        event: str,
        *,
        trace_id: str | None = None,
        message: str | None = None,
        context: dict[str, Any] | None = None,
        action: str | None = None,
        status: str | None = None,
        tenant_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        return self.log(
            "INFO",
            event,
            trace_id=trace_id,
            message=message,
            context=context,
            action=action,
            status=status,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )

    def error(
        self,
        event: str,
        *,
        trace_id: str | None = None,
        message: str | None = None,
        context: dict[str, Any] | None = None,
        action: str | None = None,
        status: str | None = None,
        tenant_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        return self.log(
            "ERROR",
            event,
            trace_id=trace_id,
            message=message,
            context=context,
            action=action,
            status=status or "error",
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )

    def audit(
        self,
        action: str,
        *,
        trace_id: str | None = None,
        actor: str | dict[str, Any] | None = None,
        entity: str | None = None,
        entity_id: str | None = None,
        outcome: str = "success",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        sanitized_context = sanitize_log_context(context or {})
        audit_context = {
            "actor": actor,
            "entity": entity,
            "entity_id": entity_id,
            "outcome": outcome,
            **sanitized_context,
        }
        actor_payload = actor if isinstance(actor, dict) else {
            "id": actor or str((sanitized_context or {}).get("actor_id") or "system"),
            "type": str((sanitized_context or {}).get("actor_type") or "system"),
            "role": (sanitized_context or {}).get("actor_role"),
            "department_id": (sanitized_context or {}).get("actor_department_id"),
        }
        request_id = trace_id or new_trace_id()
        record = emit_audit_record(
            service_name=self.service_name,
            tenant_id=str((sanitized_context or {}).get("tenant_id") or "tenant-default"),
            actor=actor_payload,
            action=action,
            entity=entity or str((sanitized_context or {}).get("entity") or "Unknown"),
            entity_id=str(entity_id or (sanitized_context or {}).get("entity_id") or "unknown"),
            before=(sanitized_context or {}).get("before") or {},
            after=(sanitized_context or {}).get("after") or {},
            trace_id=request_id,
            source={key: value for key, value in (sanitized_context or {}).items() if key not in {"tenant_id", "before", "after", "actor_type", "actor_role", "actor_department_id"}},
        )
        audit_context["audit_record"] = record
        return self.log(
            "INFO",
            "audit",
            trace_id=request_id,
            message=action,
            context=audit_context,
            action=action,
            status=outcome,
            tenant_id=str((sanitized_context or {}).get("tenant_id") or "tenant-default"),
        )


@dataclass
class RequestMetric:
    trace_id: str
    request_id: str
    correlation_id: str
    tenant_id: str | None
    operation: str
    latency_ms: float
    success: bool
    status: str
    recorded_at: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceRecord:
    request_id: str
    correlation_id: str
    tenant_id: str | None
    service: str
    action: str
    status: str
    stage: str
    recorded_at: str
    context: dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.request_count = 0
        self.error_count = 0
        self._latencies_ms: list[float] = []
        self.request_metrics: list[RequestMetric] = []
        self.operation_metrics: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "errors": 0, "latency_total_ms": 0.0, "latency_max_ms": 0.0})
        self.job_metrics: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "errors": 0})
        self.workflow_metrics: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "errors": 0})
        self.event_metrics: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "errors": 0})
        self.error_categories: dict[str, int] = defaultdict(int)
        self.tenant_metrics: dict[str, dict[str, int]] = defaultdict(lambda: {"requests": 0, "errors": 0})
        self.trace_records: list[TraceRecord] = []
        self._lock = Lock()

    def record_request(self, operation: str, *, trace_id: str, latency_ms: float, success: bool, context: dict[str, Any] | None = None) -> None:
        sanitized_context = sanitize_log_context(context or {})
        tenant_id = infer_tenant_id(sanitized_context)
        correlation_id = infer_correlation_id(trace_id, sanitized_context)
        status = normalize_status(sanitized_context.get("status") or sanitized_context.get("status_code"), success=success)
        error_category = sanitized_context.get("error_category")
        with self._lock:
            self.request_count += 1
            if not success:
                self.error_count += 1
            self._latencies_ms.append(latency_ms)
            self.request_metrics.append(
                RequestMetric(
                    trace_id=trace_id,
                    request_id=trace_id,
                    correlation_id=correlation_id,
                    tenant_id=tenant_id,
                    operation=operation,
                    latency_ms=round(latency_ms, 3),
                    success=success,
                    status=status,
                    recorded_at=utc_now().isoformat(),
                    context=sanitized_context,
                )
            )
            if len(self.request_metrics) > 50:
                self.request_metrics.pop(0)
            bucket = self.operation_metrics[operation]
            bucket["count"] += 1
            bucket["latency_total_ms"] += latency_ms
            bucket["latency_max_ms"] = max(float(bucket["latency_max_ms"]), latency_ms)
            if not success:
                bucket["errors"] += 1
            if tenant_id:
                self.tenant_metrics[tenant_id]["requests"] += 1
                if not success:
                    self.tenant_metrics[tenant_id]["errors"] += 1
            if error_category:
                self.error_categories[str(error_category)] += 1
            self._record_specialized_metric(self.job_metrics, sanitized_context.get("job_type"), success)
            self._record_specialized_metric(self.workflow_metrics, sanitized_context.get("workflow_definition") or sanitized_context.get("workflow_code") or sanitized_context.get("workflow_id"), success)
            self._record_specialized_metric(self.event_metrics, sanitized_context.get("event_name") or sanitized_context.get("event_type"), success)

    def record_trace(
        self,
        *,
        request_id: str,
        correlation_id: str,
        tenant_id: str | None,
        action: str,
        status: str,
        stage: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        with self._lock:
            self.trace_records.append(
                TraceRecord(
                    request_id=request_id,
                    correlation_id=correlation_id,
                    tenant_id=tenant_id,
                    service=self.service_name,
                    action=action,
                    status=status,
                    stage=stage,
                    recorded_at=utc_now().isoformat(),
                    context=sanitize_log_context(context or {}),
                )
            )
            if len(self.trace_records) > 100:
                self.trace_records.pop(0)

    @staticmethod
    def _record_specialized_metric(store: dict[str, dict[str, int]], key: Any, success: bool) -> None:
        if not key:
            return
        bucket = store[str(key)]
        bucket["count"] += 1
        if not success:
            bucket["errors"] += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            latency_avg = sum(self._latencies_ms) / len(self._latencies_ms) if self._latencies_ms else 0.0
            latency_max = max(self._latencies_ms) if self._latencies_ms else 0.0
            operations = {
                operation: {
                    "count": values["count"],
                    "error_count": values["errors"],
                    "error_rate": round((values["errors"] / values["count"]), 4) if values["count"] else 0.0,
                    "latency_ms": {
                        "avg": round(values["latency_total_ms"] / values["count"], 3) if values["count"] else 0.0,
                        "max": round(values["latency_max_ms"], 3),
                    },
                }
                for operation, values in self.operation_metrics.items()
            }
            return {
                "service": self.service_name,
                "request_count": self.request_count,
                "error_count": self.error_count,
                "error_rate": round((self.error_count / self.request_count), 4) if self.request_count else 0.0,
                "latency_ms": {
                    "avg": round(latency_avg, 3),
                    "max": round(latency_max, 3),
                },
                "operations": operations,
                "job_metrics": dict(self.job_metrics),
                "workflow_metrics": dict(self.workflow_metrics),
                "event_metrics": dict(self.event_metrics),
                "error_categories": dict(self.error_categories),
                "tenant_metrics": dict(self.tenant_metrics),
                "recent_requests": [asdict(metric) for metric in self.request_metrics[-20:]],
                "recent_traces": [asdict(trace) for trace in self.trace_records[-20:]],
            }


class Observability:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = StructuredLogger(service_name)
        self.metrics = MetricsCollector(service_name)

    def trace_id(self, incoming: str | None = None) -> str:
        return incoming or new_trace_id()

    def record_trace(
        self,
        action: str,
        *,
        request_id: str,
        context: dict[str, Any] | None = None,
        status: str | None = None,
        stage: str = "service",
    ) -> None:
        sanitized_context = sanitize_log_context(context or {})
        tenant_id = infer_tenant_id(sanitized_context)
        correlation_id = infer_correlation_id(request_id, sanitized_context)
        self.metrics.record_trace(
            request_id=request_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            action=action,
            status=normalize_status(status or sanitized_context.get("status"), default="ok"),
            stage=stage,
            context=sanitized_context,
        )

    def track(self, operation: str, *, trace_id: str, started_at: float, success: bool, context: dict[str, Any] | None = None) -> float:
        latency_ms = (time.perf_counter() - started_at) * 1000
        enriched_context = {"service": self.service_name, **(context or {})}
        status = normalize_status(enriched_context.get("status") or enriched_context.get("status_code"), success=success)
        self.metrics.record_request(operation, trace_id=trace_id, latency_ms=latency_ms, success=success, context=enriched_context)
        self.record_trace(operation, request_id=trace_id, context=enriched_context, status=status, stage=str(enriched_context.get("trace_stage") or "service"))
        self.logger.info(
            "request.completed",
            trace_id=trace_id,
            message=operation,
            action=operation,
            status=status,
            tenant_id=infer_tenant_id(enriched_context),
            correlation_id=infer_correlation_id(trace_id, enriched_context),
            context={"success": success, "latency_ms": round(latency_ms, 3), **enriched_context},
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
    error_category: str
    message: str
    trace_id: str
    correlation_id: str
    tenant_id: str | None
    occurred_at: str
    details: dict[str, Any] = field(default_factory=dict)


class CentralErrorLogger:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.failures: list[LoggedFailure] = []
        self.structured_logger = StructuredLogger(service_name)
        self._lock = Lock()

    def log(self, operation: str, error: Exception, *, trace_id: str | None = None, details: dict[str, Any] | None = None) -> LoggedFailure:
        payload = sanitize_log_context(details or {})
        trace = trace_id or new_trace_id()
        category = classify_error(error, details=payload)
        correlation_id = infer_correlation_id(trace, payload)
        tenant_id = infer_tenant_id(payload)
        failure = LoggedFailure(
            service=self.service_name,
            operation=operation,
            error_type=type(error).__name__,
            error_category=category,
            message=str(error),
            trace_id=trace,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            occurred_at=utc_now().isoformat(),
            details=payload,
        )
        with self._lock:
            self.failures.append(failure)
        self.structured_logger.error(
            "error.captured",
            trace_id=trace,
            message=operation,
            action=operation,
            status="error",
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            context={
                "error_type": failure.error_type,
                "error_category": failure.error_category,
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
