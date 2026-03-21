from __future__ import annotations

import json
import logging
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from api_contract import error_payload, success_payload
from resilience import Observability


SERVICE_NAME = os.getenv("SERVICE_NAME", "service")
PORT = int(os.getenv("PORT", "8000"))
DATABASE_URL = os.getenv("DATABASE_URL", "")


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("common-service")
OBSERVABILITY = Observability(SERVICE_NAME)


def _error_payload(code: str, message: str, trace_id: str, details: list[dict] | None = None) -> dict[str, object]:
    return error_payload(code, message, trace_id, details)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        started = time.perf_counter()
        trace_id = OBSERVABILITY.trace_id(self.headers.get("X-Trace-Id") or self.headers.get("X-Request-Id"))
        try:
            if self.path in ("/health", "/ready"):
                payload = success_payload({
                    'service': SERVICE_NAME,
                    'service_status': 'ok',
                    'database_configured': bool(DATABASE_URL),
                    'metrics': OBSERVABILITY.metrics.snapshot(),
                }, trace_id)
                self._send_json(payload)
                return

            if self.path == "/":
                self._send_json(success_payload({'service': SERVICE_NAME, 'message': 'running'}, trace_id))
                return

            self._send_json(_error_payload("NOT_FOUND", "Resource not found", trace_id), status=404)
        except Exception:  # noqa: BLE001
            LOGGER.exception("Unhandled error while serving path=%s trace_id=%s", self.path, trace_id)
            OBSERVABILITY.logger.error("request.error", trace_id=trace_id, message=self.path, context={"method": "GET"})
            self._send_json(_error_payload("INTERNAL_SERVER_ERROR", "Unexpected server failure", trace_id), status=500)
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            OBSERVABILITY.track("common_service_request", trace_id=trace_id, started_at=started, success=getattr(self, "_last_status", 500) < 500, context={"path": self.path, "method": "GET", "status": getattr(self, "_last_status", 500)})
            LOGGER.info("request path=%s method=GET status=%s duration_ms=%s trace_id=%s", self.path, getattr(self, "_last_status", 500), duration_ms, trace_id)

    def log_message(self, format: str, *args) -> None:  # silence default logs
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
