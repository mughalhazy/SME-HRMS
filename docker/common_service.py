from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


SERVICE_NAME = os.getenv("SERVICE_NAME", "service")
PORT = int(os.getenv("PORT", "8000"))
DATABASE_URL = os.getenv("DATABASE_URL", "")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
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

        self._send_json({"error": "not_found"}, status=404)

    def log_message(self, format: str, *args) -> None:  # silence default logs
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
