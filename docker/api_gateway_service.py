from __future__ import annotations

import json
import logging
import os
import socket
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from api_contract import error_payload, success_payload
from resilience import CentralErrorLogger, CircuitBreaker, CircuitBreakerOpenError, Observability, run_with_retry


PORT = int(os.getenv("PORT", "8000"))
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("api-gateway")
ERROR_LOGGER = CentralErrorLogger("api-gateway")
OBSERVABILITY = Observability("api-gateway")

ROUTES = {
    "employee-service": os.getenv("EMPLOYEE_SERVICE_URL", "http://employee-service:8001"),
    "attendance-service": os.getenv("ATTENDANCE_SERVICE_URL", "http://attendance-service:8002"),
    "leave-service": os.getenv("LEAVE_SERVICE_URL", "http://leave-service:8003"),
    "payroll-service": os.getenv("PAYROLL_SERVICE_URL", "http://payroll-service:8004"),
    "hiring-service": os.getenv("HIRING_SERVICE_URL", "http://hiring-service:8005"),
    "auth-service": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8006"),
    "notification-service": os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8007"),
    "audit-service": os.getenv("AUDIT_SERVICE_URL", "http://audit-service:8008"),
    "workflow-service": os.getenv("WORKFLOW_SERVICE_URL", "http://workflow-service:8009"),
    "engagement-service": os.getenv("ENGAGEMENT_SERVICE_URL", "http://engagement-service:8011"),
    "helpdesk-service": os.getenv("HELPDESK_SERVICE_URL", "http://helpdesk-service:8012"),
    "reporting-analytics-service": os.getenv("REPORTING_ANALYTICS_SERVICE_URL", "http://reporting-analytics-service:8013"),
    "search-service": os.getenv("SEARCH_SERVICE_URL", "http://search-service:8014"),
    "expense-service": os.getenv("EXPENSE_SERVICE_URL", "http://expense-service:8015"),
    "integration-service": os.getenv("INTEGRATION_SERVICE_URL", "http://integration-service:8016"),
    "automation-service": os.getenv("AUTOMATION_SERVICE_URL", "http://automation-service:8017"),
}
BREAKERS = {service: CircuitBreaker(failure_threshold=2, recovery_timeout=1.0) for service in ROUTES}


def _check_socket(host: str, port: int) -> bool:
    with socket.create_connection((host, port), timeout=0.5):
        return True


def _error_payload(code: str, message: str, trace_id: str, details: list[dict] | None = None) -> dict[str, object]:
    return error_payload(code, message, trace_id, details)


def _check_service_health(service: str, url: str, trace_id: str) -> dict[str, object]:
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 80
    breaker = BREAKERS[service]

    try:
        breaker.call(
            lambda: run_with_retry(
                lambda: _check_socket(host, port),
                attempts=3,
                base_delay=0.05,
                timeout_seconds=0.5,
                retryable=lambda exc: isinstance(exc, OSError),
            )
        )
        return {"status": "ok", "target": url}
    except CircuitBreakerOpenError as exc:
        ERROR_LOGGER.log("ready-check", exc, trace_id=trace_id, details={"service": service, "url": url, "degraded": True})
        return {"status": "degraded", "target": url, "reason": "circuit_open"}
    except Exception as exc:  # noqa: BLE001
        ERROR_LOGGER.log("ready-check", exc, trace_id=trace_id, details={"service": service, "url": url})
        return {"status": "degraded", "target": url, "reason": type(exc).__name__}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        started = time.perf_counter()
        trace_id = OBSERVABILITY.trace_id(self.headers.get("X-Trace-Id") or self.headers.get("X-Request-Id"))
        try:
            if self.path == '/health':
                self._send_json(success_payload({'service': 'api-gateway', 'service_status': 'ok', 'routes': ROUTES, 'metrics': OBSERVABILITY.metrics.snapshot()}, trace_id))
                return

            if self.path == '/ready':
                checks = {svc: _check_service_health(svc, url, trace_id) for svc, url in ROUTES.items()}
                overall_status = 'ok' if all(item['status'] == 'ok' for item in checks.values()) else 'degraded'
                self._send_json(success_payload({'service': 'api-gateway', 'service_status': overall_status, 'connectivity': checks}, trace_id))
                return

            self._send_json(success_payload({'service': 'api-gateway', 'message': 'route placeholder'}, trace_id))
        except Exception:  # noqa: BLE001
            LOGGER.exception("Unhandled gateway error path=%s trace_id=%s", self.path, trace_id)
            OBSERVABILITY.logger.error("request.error", trace_id=trace_id, message=self.path, context={"method": "GET"})
            self._send_json(_error_payload("INTERNAL_SERVER_ERROR", "Unexpected server failure", trace_id), status=500)
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            OBSERVABILITY.track("api_gateway_request", trace_id=trace_id, started_at=started, success=getattr(self, "_last_status", 500) < 500, context={"path": self.path, "method": "GET", "status": getattr(self, "_last_status", 500)})
            LOGGER.info("request path=%s method=GET status=%s duration_ms=%s trace_id=%s", self.path, getattr(self, "_last_status", 500), duration_ms, trace_id)

    def log_message(self, format: str, *args) -> None:
        return

    def _send_json(self, payload: dict[str, object], status: int = 200) -> None:
        self._last_status = status
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        trace_id = str(payload.get("meta", {}).get("request_id", ""))
        self.send_header("X-Trace-Id", trace_id)
        self.send_header("X-Request-Id", trace_id)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
