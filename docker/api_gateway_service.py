from __future__ import annotations

import json
import logging
import os
import socket
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from api_contract import error_payload, success_payload
from resilience import CentralErrorLogger, CircuitBreaker, CircuitBreakerOpenError, Observability, run_with_retry

CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent
GATEWAY_PACKAGE_DIR = REPO_ROOT / "api-gateway"
if str(GATEWAY_PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(GATEWAY_PACKAGE_DIR))

from routes import RouteNotFoundError, iter_routes, resolve_route, translate_to_upstream_path


PORT = int(os.getenv("PORT", "8000"))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("GATEWAY_REQUEST_TIMEOUT_SECONDS", "5.0"))
GATEWAY_ROUTES_CONFIG = Path(os.getenv("GATEWAY_ROUTES_CONFIG", str(REPO_ROOT / "deployment" / "config" / "gateway-routes.json")))

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("api-gateway")
ERROR_LOGGER = CentralErrorLogger("api-gateway")
OBSERVABILITY = Observability("api-gateway")


def _load_route_targets(config_path: Path) -> dict[str, str]:
    with config_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    route_targets = payload.get("routes")
    if not isinstance(route_targets, dict):
        raise ValueError(f"Invalid gateway config at {config_path}: 'routes' must be an object")
    return {str(name): str(target).rstrip("/") for name, target in route_targets.items()}


def _service_env_name(service: str) -> str:
    return f"{service.replace('-', '_').upper()}_URL"


ROUTE_TARGETS = _load_route_targets(GATEWAY_ROUTES_CONFIG)
SERVICE_URLS: dict[str, str] = {}
for route in iter_routes():
    configured_target = ROUTE_TARGETS.get(route.name)
    env_target = os.getenv(_service_env_name(route.upstream_service))
    if env_target:
        SERVICE_URLS[route.upstream_service] = env_target.rstrip("/")
    elif configured_target:
        SERVICE_URLS[route.upstream_service] = configured_target

BREAKERS = {service: CircuitBreaker(failure_threshold=2, recovery_timeout=1.0) for service in SERVICE_URLS}
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


def _check_socket(host: str, port: int) -> bool:
    with socket.create_connection((host, port), timeout=0.5):
        return True


def _error_payload(code: str, message: str, trace_id: str, details: list[dict] | None = None) -> dict[str, object]:
    return error_payload(code, message, trace_id, details)


def _check_service_health(service: str, url: str, trace_id: str) -> dict[str, object]:
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 80
    breaker = BREAKERS.setdefault(service, CircuitBreaker(failure_threshold=2, recovery_timeout=1.0))

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
        self._dispatch_request("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch_request("POST")

    def do_PUT(self) -> None:  # noqa: N802
        self._dispatch_request("PUT")

    def do_DELETE(self) -> None:  # noqa: N802
        self._dispatch_request("DELETE")

    def _dispatch_request(self, method: str) -> None:
        started = time.perf_counter()
        trace_id = OBSERVABILITY.trace_id(self.headers.get("X-Trace-Id") or self.headers.get("X-Request-Id"))

        try:
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                self._send_json(success_payload({"service": "api-gateway", "service_status": "ok", "routes": SERVICE_URLS, "metrics": OBSERVABILITY.metrics.snapshot()}, trace_id))
                return

            if parsed.path == "/ready":
                checks = {svc: _check_service_health(svc, url, trace_id) for svc, url in SERVICE_URLS.items()}
                overall_status = "ok" if all(item["status"] == "ok" for item in checks.values()) else "degraded"
                self._send_json(success_payload({"service": "api-gateway", "service_status": overall_status, "connectivity": checks}, trace_id))
                return

            self._proxy_request(method=method, path_with_query=self.path, trace_id=trace_id)
        except Exception:  # noqa: BLE001
            LOGGER.exception("Unhandled gateway error path=%s trace_id=%s", self.path, trace_id)
            OBSERVABILITY.logger.error("request.error", trace_id=trace_id, message=self.path, context={"method": method})
            self._send_json(_error_payload("INTERNAL_SERVER_ERROR", "Unexpected server failure", trace_id), status=500)
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            status = getattr(self, "_last_status", 500)
            OBSERVABILITY.track("api_gateway_request", trace_id=trace_id, started_at=started, success=status < 500, context={"path": self.path, "method": method, "status": status})
            LOGGER.info("request path=%s method=%s status=%s duration_ms=%s trace_id=%s", self.path, method, status, duration_ms, trace_id)

    def log_message(self, format: str, *args) -> None:
        return

    def _proxy_request(self, method: str, path_with_query: str, trace_id: str) -> None:
        parsed = urlparse(path_with_query)
        path = parsed.path
        try:
            route = resolve_route(path)
        except RouteNotFoundError:
            self._send_json(_error_payload("ROUTE_NOT_FOUND", f"No route for '{path}'.", trace_id), status=404)
            return

        upstream_base_url = SERVICE_URLS.get(route.upstream_service)
        if not upstream_base_url:
            self._send_json(_error_payload("UPSTREAM_UNAVAILABLE", f"No upstream configured for '{route.upstream_service}'.", trace_id), status=502)
            return

        upstream_path = translate_to_upstream_path(route, path)
        upstream_path_with_query = upstream_path if not parsed.query else f"{upstream_path}?{parsed.query}"
        upstream_url = urljoin(f"{upstream_base_url}/", upstream_path_with_query.lstrip("/"))
        body = self._read_request_body()
        forward_headers = self._build_upstream_headers(trace_id=trace_id)
        if body and "Content-Type" in self.headers:
            forward_headers["Content-Type"] = self.headers["Content-Type"]

        request = Request(url=upstream_url, data=body if body else None, headers=forward_headers, method=method)
        try:
            with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as upstream_response:
                response_body = upstream_response.read()
                self._send_upstream_response(
                    status=upstream_response.status,
                    body=response_body,
                    headers=upstream_response.headers,
                    trace_id=trace_id,
                )
        except HTTPError as exc:
            response_body = exc.read()
            self._send_upstream_response(status=exc.code, body=response_body, headers=exc.headers, trace_id=trace_id)
        except TimeoutError:
            self._send_json(_error_payload("UPSTREAM_TIMEOUT", f"Timed out contacting '{route.upstream_service}'.", trace_id), status=504)
        except URLError as exc:
            reason = exc.reason
            if isinstance(reason, TimeoutError):
                self._send_json(_error_payload("UPSTREAM_TIMEOUT", f"Timed out contacting '{route.upstream_service}'.", trace_id), status=504)
                return
            ERROR_LOGGER.log("gateway-proxy", exc, trace_id=trace_id, details={"upstream": upstream_url})
            self._send_json(_error_payload("BAD_GATEWAY", f"Unable to connect to '{route.upstream_service}'.", trace_id), status=502)

    def _read_request_body(self) -> bytes | None:
        content_length = self.headers.get("Content-Length")
        if not content_length:
            return None
        try:
            length = int(content_length)
        except ValueError:
            return None
        if length <= 0:
            return None
        return self.rfile.read(length)

    def _build_upstream_headers(self, trace_id: str) -> dict[str, str]:
        headers: dict[str, str] = {}
        for key, value in self.headers.items():
            if key.lower() in HOP_BY_HOP_HEADERS:
                continue
            headers[key] = value
        headers.setdefault("X-Trace-Id", trace_id)
        headers.setdefault("X-Request-Id", trace_id)
        headers.setdefault("X-Forwarded-For", self.client_address[0] if self.client_address else "")
        headers.setdefault("X-Forwarded-Proto", "http")
        return headers

    def _send_upstream_response(self, status: int, body: bytes, headers, trace_id: str) -> None:
        self._last_status = status
        self.send_response(status)
        forwarded_content_type = headers.get("Content-Type") if headers else None
        if forwarded_content_type:
            self.send_header("Content-Type", forwarded_content_type)
        self.send_header("X-Trace-Id", trace_id)
        self.send_header("X-Request-Id", trace_id)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

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
