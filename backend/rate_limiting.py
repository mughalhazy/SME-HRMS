from __future__ import annotations

import threading
import time
from collections import deque
from typing import NamedTuple


class RateLimitResult(NamedTuple):
    allowed: bool
    limit: int
    remaining: int
    reset_at: float  # Unix timestamp


class SlidingWindowRateLimiter:
    """Thread-safe in-process sliding window rate limiter keyed by arbitrary string."""

    def __init__(self, requests_per_window: int = 100, window_seconds: float = 60.0) -> None:
        self._limit = requests_per_window
        self._window = window_seconds
        self._buckets: dict[str, deque[float]] = {}
        self._lock = threading.RLock()

    def check(self, key: str) -> RateLimitResult:
        now = time.time()
        cutoff = now - self._window
        with self._lock:
            bucket = self._buckets.setdefault(key, deque())
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            count = len(bucket)
            reset_at = (bucket[0] + self._window) if bucket else (now + self._window)
            if count >= self._limit:
                return RateLimitResult(
                    allowed=False, limit=self._limit, remaining=0, reset_at=reset_at
                )
            bucket.append(now)
            return RateLimitResult(
                allowed=True,
                limit=self._limit,
                remaining=self._limit - count - 1,
                reset_at=reset_at,
            )

    def purge_expired(self) -> None:
        cutoff = time.time() - self._window
        with self._lock:
            dead = [k for k, dq in self._buckets.items() if not dq or dq[-1] < cutoff]
            for k in dead:
                del self._buckets[k]
