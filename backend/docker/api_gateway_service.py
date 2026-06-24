from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import socket
import sys
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

import uvicorn

from api_contract import error_payload, success_payload
from jwt_utils import verify_hs256_jwt
from rate_limiting import SlidingWindowRateLimiter
from resilience import CentralErrorLogger, CircuitBreaker, CircuitBreakerOpenError, Observability, run_with_retry
from structured_logging import configure_logging, set_correlation_id

CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent
GATEWAY_PACKAGE_DIR = REPO_ROOT / "api-gateway"
if str(GATEWAY_PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(GATEWAY_PACKAGE_DIR))

from routes import RouteNotFoundError, iter_routes, resolve_route, translate_to_upstream_path

PORT = int(os.getenv("PORT", "8000"))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("GATEWAY_REQUEST_TIMEOUT_SECONDS", "5.0"))
GATEWAY_ROUTES_CONFIG = Path(os.getenv("GATEWAY_ROUTES_CONFIG", str(REPO_ROOT / "deployment" / "config" / "gateway-routes.json")))

# --- Structured logging ---
configure_logging(service="api-gateway")
LOGGER = logging.getLogger("api-gateway")
ERROR_LOGGER = CentralErrorLogger("api-gateway")
OBSERVABILITY = Observability("api-gateway")

# --- Rate limiting: 200 req/min per IP by default ---
_RATE_LIMIT = int(os.getenv("GATEWAY_RATE_LIMIT", "200"))
_RATE_WINDOW = float(os.getenv("GATEWAY_RATE_WINDOW_SECONDS", "60"))
RATE_LIMITER = SlidingWindowRateLimiter(requests_per_window=_RATE_LIMIT, window_seconds=_RATE_WINDOW)

# --- JWT enforcement ---
_JWT_SECRET_STR = os.getenv("JWT_SECRET", "")
JWT_SECRET: bytes = _JWT_SECRET_STR.encode() if _JWT_SECRET_STR else b""
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "sme-hrms.api")
JWT_ISSUER = os.getenv("JWT_ISSUER", "sme-hrms.auth-service")
# Routes exempt from JWT verification
_AUTH_EXEMPT_PREFIXES = ("/health", "/ready", "/metrics", "/openapi.json", "/docs", "/api/v1/auth/")

# --- CORS ---
_CORS_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*")
_CORS_METHODS = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
_CORS_HEADERS = "Authorization, Content-Type, X-Trace-Id, X-Request-Id, X-Tenant-Id, Idempotency-Key"

# --- Body size limit ---
MAX_REQUEST_BODY_BYTES = int(os.getenv("MAX_REQUEST_BODY_BYTES", str(1 * 1024 * 1024)))  # 1 MB

# --- Route-level RBAC: path prefix → roles allowed (empty tuple = any authenticated user) ---
_ROUTE_ROLE_MAP: dict[str, tuple[str, ...]] = {
    "/api/v1/payroll": ("Admin", "PayrollAdmin", "Manager"),
    "/api/v1/audit":   ("Admin",),
    "/api/v1/hiring":  ("Admin", "Manager", "Recruiter"),
    "/api/v1/reporting": ("Admin", "Manager"),
}

# --- Idempotency cache ---
import threading as _threading

class _IdempotencyCache:
    """In-process TTL cache for idempotent request replay."""

    def __init__(self, ttl_seconds: float = 86400.0, max_size: int = 10_000) -> None:
        self._store: dict[str, tuple[float, tuple]] = {}
        self._lock = _threading.RLock()
        self._ttl = ttl_seconds
        self._max = max_size

    def get(self, key: str) -> tuple | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if time.time() < entry[0]:
                return entry[1]
            del self._store[key]
        return None

    def set(self, key: str, value: tuple) -> None:
        with self._lock:
            if len(self._store) >= self._max:
                oldest = min(self._store, key=lambda k: self._store[k][0])
                del self._store[oldest]
            self._store[key] = (time.time() + self._ttl, value)

_IDEMPOTENCY_CACHE = _IdempotencyCache()

# --- Prometheus-compatible metrics accumulator ---
_METRICS_LOCK = __import__("threading").Lock()
_REQUEST_COUNT: dict[str, int] = {}   # "method:status" → count
_REQUEST_DURATION_SUM: dict[str, float] = {}  # "method" → total seconds
_REQUEST_ERRORS: int = 0


def _record_metric(method: str, status: int, duration_s: float) -> None:
    key = f"{method}:{status}"
    with _METRICS_LOCK:
        global _REQUEST_ERRORS
        _REQUEST_COUNT[key] = _REQUEST_COUNT.get(key, 0) + 1
        _REQUEST_DURATION_SUM[method] = _REQUEST_DURATION_SUM.get(method, 0.0) + duration_s
        if status >= 500:
            _REQUEST_ERRORS += 1


def _build_metrics_text() -> bytes:
    lines: list[str] = [
        "# HELP gateway_requests_total Total requests by method and status",
        "# TYPE gateway_requests_total counter",
    ]
    with _METRICS_LOCK:
        for key, count in sorted(_REQUEST_COUNT.items()):
            method, status = key.split(":", 1)
            lines.append(f'gateway_requests_total{{method="{method}",status="{status}"}} {count}')
        lines.append("# HELP gateway_request_duration_seconds_total Total request duration by method")
        lines.append("# TYPE gateway_request_duration_seconds_total counter")
        for method, total in sorted(_REQUEST_DURATION_SUM.items()):
            lines.append(f'gateway_request_duration_seconds_total{{method="{method}"}} {total:.6f}')
        lines.append(f"# HELP gateway_errors_total Total 5xx responses")
        lines.append(f"# TYPE gateway_errors_total counter")
        lines.append(f"gateway_errors_total {_REQUEST_ERRORS}")
    return ("\n".join(lines) + "\n").encode()

HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailer", "transfer-encoding", "upgrade", "host", "content-length",
}


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


# ---------------------------------------------------------------------------
# OpenAPI spec (generated from ROUTES)
# ---------------------------------------------------------------------------

def _build_openapi_spec() -> dict[str, Any]:
    paths: dict[str, Any] = {}
    for r in iter_routes():
        path_item: dict[str, Any] = {}
        for method in ("get", "post", "put", "patch", "delete"):
            path_item[method] = {
                "tags": [r.name],
                "summary": f"{method.upper()} {r.path_prefix}",
                "operationId": f"{method}_{r.name.replace('-', '_')}",
                "security": [{"BearerAuth": []}],
                "responses": {
                    "200": {"description": "Success"},
                    "400": {"description": "Bad request"},
                    "401": {"description": "Unauthorised"},
                    "403": {"description": "Forbidden"},
                    "404": {"description": "Not found"},
                    "429": {"description": "Rate limit exceeded"},
                    "502": {"description": "Bad gateway"},
                },
            }
        full_prefix = f"/api/v1{r.path_prefix}"
        paths[full_prefix] = path_item
        paths[f"{full_prefix}/{{id}}"] = {
            m: {**path_item[m], "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}]}
            for m in path_item
        }

    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Meridian HCM API",
            "version": "1.0.0",
            "description": "SME Human Resource Management System REST API",
            "contact": {"email": "support@meridian-hcm.internal"},
        },
        "servers": [{"url": "/", "description": "API gateway"}],
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            }
        },
        "paths": paths,
    }


_OPENAPI_SPEC: dict[str, Any] | None = None


def _get_openapi_spec() -> dict[str, Any]:
    global _OPENAPI_SPEC
    if _OPENAPI_SPEC is None:
        _OPENAPI_SPEC = _build_openapi_spec()
    return _OPENAPI_SPEC


_DOCS_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>Meridian HCM API Docs</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" rel="stylesheet">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({ url: "/openapi.json", dom_id: "#swagger-ui",
      presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset] });
  </script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Health / ready helpers
# ---------------------------------------------------------------------------

def _check_socket(host: str, port: int) -> bool:
    with socket.create_connection((host, port), timeout=0.5):
        return True


def _check_service_health(service: str, url: str, trace_id: str) -> dict[str, object]:
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 80
    breaker = BREAKERS.setdefault(service, CircuitBreaker(failure_threshold=2, recovery_timeout=1.0))
    try:
        breaker.call(
            lambda: run_with_retry(
                lambda: _check_socket(host, port),
                attempts=3, base_delay=0.05, timeout_seconds=0.5,
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


# ---------------------------------------------------------------------------
# Synchronous dispatch
# ---------------------------------------------------------------------------

def _parse_traceparent(header: str) -> tuple[str, str] | None:
    """Parse W3C Trace Context traceparent. Returns (trace_id, parent_id) or None."""
    parts = header.split("-")
    if len(parts) != 4 or parts[0] != "00":
        return None
    trace_id, parent_id = parts[1], parts[2]
    if len(trace_id) != 32 or len(parent_id) != 16:
        return None
    return trace_id, parent_id


def _new_traceparent(trace_id: str | None = None) -> tuple[str, str, str]:
    """Generate a W3C traceparent. Returns (traceparent_header, trace_id, span_id)."""
    tid = trace_id or uuid.uuid4().hex
    sid = uuid.uuid4().hex[:16]
    return f"00-{tid}-{sid}-01", tid, sid


def _dispatch(
    method: str,
    path_with_query: str,
    headers: dict[str, str],
    body: bytes,
) -> tuple[int, bytes, list[tuple[bytes, bytes]]]:
    """Process one request; returns (status, body_bytes, asgi_headers)."""
    started = time.perf_counter()

    # --- W3C Trace Context ---
    incoming_tp = headers.get("traceparent", "")
    parsed_tp = _parse_traceparent(incoming_tp) if incoming_tp else None
    existing_trace_id = parsed_tp[0] if parsed_tp else None
    traceparent_out, w3c_trace_id, _span_id = _new_traceparent(existing_trace_id)
    trace_id = OBSERVABILITY.trace_id(
        headers.get("x-trace-id") or headers.get("x-request-id") or w3c_trace_id
    )
    set_correlation_id(trace_id)

    _cors_headers = [
        (b"access-control-allow-origin", _CORS_ORIGINS.encode()),
        (b"access-control-allow-methods", _CORS_METHODS.encode()),
        (b"access-control-allow-headers", _CORS_HEADERS.encode()),
        (b"access-control-max-age", b"86400"),
        (b"traceparent", traceparent_out.encode()),
    ]

    def _json_response(payload: dict[str, object], status: int = 200) -> tuple[int, bytes, list[tuple[bytes, bytes]]]:
        resp_body = json.dumps(payload).encode("utf-8")
        rid = str(payload.get("meta", {}).get("request_id", ""))
        resp_headers = [
            (b"content-type", b"application/json"),
            (b"x-trace-id", rid.encode()),
            (b"x-request-id", rid.encode()),
            (b"x-content-type-options", b"nosniff"),
            (b"x-frame-options", b"DENY"),
            (b"cache-control", b"no-store"),
            (b"content-length", str(len(resp_body)).encode()),
        ] + _cors_headers
        return status, resp_body, resp_headers

    def _error(code: str, message: str, status: int, details: list[dict] | None = None, extra_headers: list[tuple[bytes, bytes]] | None = None) -> tuple[int, bytes, list[tuple[bytes, bytes]]]:
        result = _json_response(error_payload(code, message, trace_id, details), status)
        if extra_headers:
            return result[0], result[1], result[2] + extra_headers
        return result

    try:
        parsed = urlparse(path_with_query)
        path = parsed.path

        # --- CORS preflight ---
        if method == "OPTIONS":
            return 204, b"", _cors_headers + [(b"content-length", b"0")]

        # --- Rate limiting ---
        client_ip = (
            headers.get("x-forwarded-for", "").split(",")[0].strip()
            or headers.get("x-real-ip", "")
            or "unknown"
        )
        rl = RATE_LIMITER.check(client_ip)
        rate_headers = [
            (b"x-ratelimit-limit", str(rl.limit).encode()),
            (b"x-ratelimit-remaining", str(rl.remaining).encode()),
            (b"x-ratelimit-reset", str(math.ceil(rl.reset_at)).encode()),
        ]
        if not rl.allowed:
            retry_after = str(max(1, math.ceil(rl.reset_at - time.time())))
            return _error(
                "RATE_LIMIT_EXCEEDED",
                "Too many requests. Please slow down.",
                429,
                extra_headers=rate_headers + [(b"retry-after", retry_after.encode())],
            )

        # --- Static / infrastructure routes ---
        if path == "/health":
            status_val, body_val, h = _json_response(success_payload(
                {"service": "api-gateway", "service_status": "ok", "routes": SERVICE_URLS, "metrics": OBSERVABILITY.metrics.snapshot()},
                trace_id,
            ))
            return status_val, body_val, h + rate_headers

        if path == "/ready":
            checks = {svc: _check_service_health(svc, url, trace_id) for svc, url in SERVICE_URLS.items()}
            overall = "ok" if all(item["status"] == "ok" for item in checks.values()) else "degraded"
            status_val, body_val, h = _json_response(success_payload(
                {"service": "api-gateway", "service_status": overall, "connectivity": checks}, trace_id
            ))
            return status_val, body_val, h + rate_headers

        if path == "/openapi.json":
            spec_bytes = json.dumps(_get_openapi_spec(), ensure_ascii=False).encode()
            return 200, spec_bytes, [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(spec_bytes)).encode()),
                (b"cache-control", b"public, max-age=300"),
            ]

        if path == "/docs":
            docs_bytes = _DOCS_HTML.encode()
            return 200, docs_bytes, [
                (b"content-type", b"text/html; charset=utf-8"),
                (b"content-length", str(len(docs_bytes)).encode()),
            ]

        if path == "/metrics":
            metrics_bytes = _build_metrics_text()
            return 200, metrics_bytes, [
                (b"content-type", b"text/plain; version=0.0.4; charset=utf-8"),
                (b"content-length", str(len(metrics_bytes)).encode()),
            ]

        # --- JWT enforcement (skip auth routes and infrastructure paths) ---
        if JWT_SECRET and not any(path.startswith(p) for p in _AUTH_EXEMPT_PREFIXES):
            auth_header = headers.get("authorization", "")
            token = auth_header.removeprefix("Bearer ").strip() if auth_header.lower().startswith("bearer ") else ""
            if not token:
                return _error("UNAUTHORIZED", "Missing or malformed Authorization header.", 401)
            claims = verify_hs256_jwt(token, JWT_SECRET, audience=JWT_AUDIENCE, issuer=JWT_ISSUER)
            if claims is None:
                return _error("UNAUTHORIZED", "Token is invalid or expired.", 401)
        else:
            claims = None

        # --- Per-tenant RBAC ---
        if claims:
            header_tenant = headers.get("x-tenant-id", "")
            jwt_tenant = str(claims.get("tenant_id", ""))
            if header_tenant and jwt_tenant and header_tenant != jwt_tenant:
                return _error("FORBIDDEN", "Tenant header does not match token.", 403)
            user_role = str(claims.get("role", ""))
            for _prefix, _allowed in _ROUTE_ROLE_MAP.items():
                if path.startswith(_prefix):
                    if user_role not in _allowed:
                        return _error("FORBIDDEN", f"Role '{user_role}' is not permitted for this resource.", 403)
                    break

        try:
            route = resolve_route(path)
        except RouteNotFoundError:
            return _error("ROUTE_NOT_FOUND", f"No route for '{path}'.", 404)

        upstream_base_url = SERVICE_URLS.get(route.upstream_service)
        if not upstream_base_url:
            return _error("UPSTREAM_UNAVAILABLE", f"No upstream configured for '{route.upstream_service}'.", 502)

        upstream_path = translate_to_upstream_path(route, path)
        upstream_path_with_query = upstream_path if not parsed.query else f"{upstream_path}?{parsed.query}"
        upstream_url = urljoin(f"{upstream_base_url}/", upstream_path_with_query.lstrip("/"))

        forward_headers: dict[str, str] = {}
        for key, value in headers.items():
            if key.lower() in HOP_BY_HOP_HEADERS:
                continue
            forward_headers[key] = value
        forward_headers.setdefault("X-Trace-Id", trace_id)
        forward_headers.setdefault("X-Request-Id", trace_id)
        forward_headers.setdefault("X-Forwarded-Proto", "https")
        forward_headers["traceparent"] = traceparent_out
        # Propagate verified principal claims downstream
        if claims:
            forward_headers["X-User-Id"] = str(claims.get("sub", ""))
            forward_headers["X-User-Role"] = str(claims.get("role", ""))
            forward_headers["X-Tenant-Id"] = str(claims.get("tenant_id", ""))

        # --- JSON body validation ---
        if body and headers.get("content-type", "").lower().startswith("application/json"):
            try:
                json.loads(body)
            except json.JSONDecodeError as exc:
                return _error("INVALID_JSON", f"Request body is not valid JSON: {exc.msg}", 400)

        # --- Idempotency key ---
        idem_key_header = headers.get("idempotency-key", "")
        idem_cache_key = f"{client_ip}:{idem_key_header}" if idem_key_header and method in ("POST", "PATCH", "PUT") else ""
        if idem_cache_key:
            cached = _IDEMPOTENCY_CACHE.get(idem_cache_key)
            if cached is not None:
                c_status, c_body, c_headers = cached
                return c_status, c_body, c_headers + [(b"x-idempotent-replayed", b"true")]

        req = Request(url=upstream_url, data=body if body else None, headers=forward_headers, method=method)
        try:
            with urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as upstream_response:
                resp_body = upstream_response.read()
                status = upstream_response.status
                ct = upstream_response.headers.get("Content-Type", "application/json")
        except HTTPError as exc:
            resp_body = exc.read()
            status = exc.code
            ct = exc.headers.get("Content-Type", "application/json") if exc.headers else "application/json"
        except TimeoutError:
            return _error("UPSTREAM_TIMEOUT", f"Timed out contacting '{route.upstream_service}'.", 504)
        except URLError as exc:
            reason = exc.reason
            if isinstance(reason, TimeoutError):
                return _error("UPSTREAM_TIMEOUT", f"Timed out contacting '{route.upstream_service}'.", 504)
            ERROR_LOGGER.log("gateway-proxy", exc, trace_id=trace_id, details={"upstream": upstream_url})
            return _error("BAD_GATEWAY", f"Unable to connect to '{route.upstream_service}'.", 502)

        resp_headers = [
            (b"content-type", ct.encode()),
            (b"x-trace-id", trace_id.encode()),
            (b"x-request-id", trace_id.encode()),
            (b"x-content-type-options", b"nosniff"),
            (b"x-frame-options", b"DENY"),
            (b"cache-control", b"no-store"),
            (b"content-length", str(len(resp_body)).encode()),
        ] + rate_headers + _cors_headers
        if idem_cache_key:
            _IDEMPOTENCY_CACHE.set(idem_cache_key, (status, resp_body, resp_headers))
        return status, resp_body, resp_headers

    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Unhandled gateway error path=%s trace_id=%s", path_with_query, trace_id)
        OBSERVABILITY.logger.error("request.error", trace_id=trace_id, message=path_with_query, context={"method": method})
        return _error("INTERNAL_SERVER_ERROR", "Unexpected server failure", 500)

    finally:
        duration_s = time.perf_counter() - started
        duration_ms = int(duration_s * 1000)
        LOGGER.info(
            "gateway.request",
            extra={"path": path_with_query, "method": method, "duration_ms": duration_ms, "trace_id": trace_id},
        )


# ---------------------------------------------------------------------------
# ASGI application
# ---------------------------------------------------------------------------

async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
    if scope["type"] == "lifespan":
        while True:
            event = await receive()
            if event["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif event["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                break
        return

    if scope["type"] != "http":
        return

    body = b""
    while True:
        message = await receive()
        body += message.get("body", b"")
        if len(body) > MAX_REQUEST_BODY_BYTES:
            while message.get("more_body", False):
                message = await receive()
            _413_body = b'{"error":{"code":"REQUEST_TOO_LARGE","message":"Request body exceeds limit."}}'
            await send({
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(_413_body)).encode()),
                    (b"connection", b"close"),
                ],
            })
            await send({"type": "http.response.body", "body": _413_body})
            return
        if not message.get("more_body", False):
            break

    method = scope["method"]
    path = scope["path"]
    qs = scope.get("query_string", b"").decode()
    path_with_query = f"{path}?{qs}" if qs else path
    headers = {k.decode(): v.decode() for k, v in scope.get("headers", [])}

    # Inject client IP from ASGI scope if not already in headers
    if "x-forwarded-for" not in headers:
        client = scope.get("client")
        if client:
            headers["x-forwarded-for"] = client[0]

    _t0 = time.perf_counter()
    status, resp_body, resp_headers = await asyncio.to_thread(
        _dispatch, method, path_with_query, headers, body
    )
    _record_metric(method, status, time.perf_counter() - _t0)

    await send({"type": "http.response.start", "status": status, "headers": resp_headers})
    await send({"type": "http.response.body", "body": resp_body})


if __name__ == "__main__":
    ssl_cert = os.getenv("SSL_CERT_FILE", "")
    ssl_key = os.getenv("SSL_KEY_FILE", "")
    uvicorn_kwargs: dict[str, Any] = {
        "host": "0.0.0.0",
        "port": PORT,
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
        "access_log": False,
    }
    if ssl_cert and ssl_key:
        uvicorn_kwargs["ssl_certfile"] = ssl_cert
        uvicorn_kwargs["ssl_keyfile"] = ssl_key
        LOGGER.info("TLS enabled", extra={"cert": ssl_cert})
    uvicorn.run("api_gateway_service:app", **uvicorn_kwargs)
