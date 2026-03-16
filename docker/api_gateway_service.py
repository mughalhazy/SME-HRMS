from __future__ import annotations

import json
import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer


PORT = int(os.getenv("PORT", "8000"))
ROUTES = {
    "employee-service": os.getenv("EMPLOYEE_SERVICE_URL", "http://employee-service:8001"),
    "attendance-service": os.getenv("ATTENDANCE_SERVICE_URL", "http://attendance-service:8002"),
    "leave-service": os.getenv("LEAVE_SERVICE_URL", "http://leave-service:8003"),
    "payroll-service": os.getenv("PAYROLL_SERVICE_URL", "http://payroll-service:8004"),
    "hiring-service": os.getenv("HIRING_SERVICE_URL", "http://hiring-service:8005"),
    "auth-service": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8006"),
}


def _check_socket(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
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

    def log_message(self, format: str, *args) -> None:
        return

    def _send_json(self, payload: dict[str, object], status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
