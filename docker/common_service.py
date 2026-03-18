from __future__ import annotations

import json
import logging
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from uuid import uuid4


SERVICE_NAME = os.getenv("SERVICE_NAME", "service")
PORT = int(os.getenv("PORT", "8000"))
DATABASE_URL = os.getenv("DATABASE_URL", "")


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("common-service")


def _error_payload(code: str, message: str, trace_id: str, details: list[dict] | None = None) -> dict[str, object]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "traceId": trace_id,
        }
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        started = time.perf_counter()
        trace_id = self.headers.get("X-Trace-Id", uuid4().hex)
        try:
            if self.path in ("/health", "/ready"):
                payload = {
                    "service": SERVICE_NAME,
                    "status": "ok",
                    "database_configured": bool(DATABASE_URL),
                }
                self._send_json(payload)
                return

            if self.path == "/":
                self._send_json({"service": SERVICE_NAME, "message": "running"})
                return

            self._send_json(_error_payload("NOT_FOUND", "Resource not found", trace_id), status=404)
        except Exception:  # noqa: BLE001
            LOGGER.exception("Unhandled error while serving path=%s trace_id=%s", self.path, trace_id)
            self._send_json(_error_payload("INTERNAL_SERVER_ERROR", "Unexpected server failure", trace_id), status=500)
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            LOGGER.info("request path=%s method=GET status=%s duration_ms=%s trace_id=%s", self.path, getattr(self, "_last_status", 500), duration_ms, trace_id)

    def log_message(self, format: str, *args) -> None:  # silence default logs
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
