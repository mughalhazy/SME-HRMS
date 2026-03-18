from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, TypeVar
from uuid import uuid4

LOGGER = logging.getLogger("sme_hrms.resilience")

T = TypeVar("T")


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

    def log(self, operation: str, error: Exception, *, trace_id: str | None = None, details: dict[str, Any] | None = None) -> LoggedFailure:
        trace = trace_id or uuid4().hex
        failure = LoggedFailure(
            service=self.service_name,
            operation=operation,
            error_type=type(error).__name__,
            message=str(error),
            trace_id=trace,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            details=details or {},
        )
        self.failures.append(failure)
        LOGGER.error(
            "service=%s operation=%s trace_id=%s error_type=%s message=%s details=%s",
            failure.service,
            failure.operation,
            failure.trace_id,
            failure.error_type,
            failure.message,
            failure.details,
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

    def push(self, workflow: str, operation: str, payload: dict[str, Any], reason: str, *, trace_id: str | None = None, retryable: bool = True) -> DeadLetter:
        entry = DeadLetter(
            dead_letter_id=uuid4().hex,
            workflow=workflow,
            operation=operation,
            reason=reason,
            payload=payload,
            trace_id=trace_id or uuid4().hex,
            created_at=datetime.now(timezone.utc).isoformat(),
            retryable=retryable,
        )
        self.entries.append(entry)
        return entry

    def recover(self, predicate: Callable[[DeadLetter], bool], retry: Callable[[DeadLetter], bool]) -> list[DeadLetter]:
        recovered: list[DeadLetter] = []
        for entry in self.entries:
            if entry.recovered_at is not None or not entry.retryable or not predicate(entry):
                continue
            if retry(entry):
                entry.recovered_at = datetime.now(timezone.utc).isoformat()
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
