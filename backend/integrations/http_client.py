from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib import error, request


class IntegrationHTTPError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 3
    backoff_seconds: float = 0.5
    retry_on_statuses: tuple[int, ...] = (408, 429, 500, 502, 503, 504)


class JsonHTTPClient:
    def __init__(self, timeout_seconds: float = 10.0, retry_policy: RetryPolicy | None = None) -> None:
        self.timeout_seconds = timeout_seconds
        self.retry_policy = retry_policy or RetryPolicy()

    def post_json(self, url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
        encoded = json.dumps(payload).encode("utf-8")
        all_headers = {"Content-Type": "application/json", "Accept": "application/json", **(headers or {})}

        last_error: Exception | None = None
        for attempt in range(1, self.retry_policy.attempts + 1):
            req = request.Request(url=url, data=encoded, headers=all_headers, method="POST")
            try:
                with request.urlopen(req, timeout=self.timeout_seconds) as response:
                    raw = response.read().decode("utf-8") or "{}"
                    body = json.loads(raw)
                    return {"status_code": int(response.status), "body": body}
            except error.HTTPError as exc:
                raw_error = exc.read().decode("utf-8") if exc.fp else ""
                parsed: dict[str, Any] = {}
                if raw_error:
                    try:
                        parsed = json.loads(raw_error)
                    except Exception:
                        parsed = {"raw": raw_error}
                last_error = IntegrationHTTPError(
                    status_code=int(exc.code),
                    code=str(parsed.get("code", "HTTP_ERROR")),
                    message=str(parsed.get("message", f"HTTP request failed with status {exc.code}")),
                    details=parsed,
                )
                if int(exc.code) not in self.retry_policy.retry_on_statuses or attempt >= self.retry_policy.attempts:
                    raise last_error
            except error.URLError as exc:
                last_error = IntegrationHTTPError(status_code=0, code="NETWORK_ERROR", message=str(exc.reason), details={})
                if attempt >= self.retry_policy.attempts:
                    raise last_error

            time.sleep(self.retry_policy.backoff_seconds * attempt)

        if last_error:
            raise last_error
        raise IntegrationHTTPError(status_code=0, code="UNKNOWN", message="Unexpected HTTP execution path")
