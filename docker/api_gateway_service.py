from __future__ import annotations

import json
import logging
import os
import socket
import time
from http.server import BaseHTTPRequestHandler, HTTPServer


PORT = int(os.getenv("PORT", "8000"))
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("api-gateway")

ROUTES = {
    "employee-service": os.getenv("EMPLOYEE_SERVICE_URL", "http://employee-service:8001"),
    "attendance-service": os.getenv("ATTENDANCE_SERVICE_URL", "http://attendance-service:8002"),
    "leave-service": os.getenv("LEAVE_SERVICE_URL", "http://leave-service:8003"),
    "payroll-service": os.getenv("PAYROLL_SERVICE_URL", "http://payroll-service:8004"),
    "hiring-service": os.getenv("HIRING_SERVICE_URL", "http://hiring-service:8005"),
    "auth-service": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8006"),
    "notification-service": os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8007"),
}


def _check_socket(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        started = time.perf_counter()
        try:
            if self.path == "/health":
                self._send_json({"service": "api-gateway", "status": "ok", "routes": ROUTES})
                return

            if self.path == "/ready":
                checks: dict[str, bool] = {}
                for svc, url in ROUTES.items():
                    hostport = url.replace("http://", "").split("/")[0]
                    host, port = hostport.split(":")
                    checks[svc] = _check_socket(host, int(port))
                self._send_json({"service": "api-gateway", "status": "ok" if all(checks.values()) else "degraded", "connectivity": checks})
                return

            self._send_json({"service": "api-gateway", "message": "route placeholder"})
        except Exception:
            LOGGER.exception("Unhandled gateway error path=%s", self.path)
            self._send_json({"error": {"code": "INTERNAL_ERROR", "message": "Unexpected server failure", "details": [], "traceId": "gateway"}}, status=500)
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            LOGGER.info("request path=%s method=GET status=%s duration_ms=%s", self.path, getattr(self, "_last_status", 500), duration_ms)

    def log_message(self, format: str, *args) -> None:
        return

    def _send_json(self, payload: dict[str, object], status: int = 200) -> None:
        self._last_status = status
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
