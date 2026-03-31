from __future__ import annotations

import importlib.util
import io
import pathlib
import sys
from types import SimpleNamespace


MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "docker" / "api_gateway_service.py"
SPEC = importlib.util.spec_from_file_location("api_gateway_service_forwarding", MODULE_PATH)
gateway = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = gateway
SPEC.loader.exec_module(gateway)


class _FakeHeaders(dict):
    def items(self):  # type: ignore[override]
        return super().items()


class _FakeUpstreamResponse:
    def __init__(self, payload: bytes = b'{"ok":true}') -> None:
        self.status = 200
        self._payload = payload
        self.headers = {"Content-Type": "application/json"}

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeUpstreamResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None


class _FakeHandler(SimpleNamespace):
    def __init__(self, body: bytes | None = None) -> None:
        headers = _FakeHeaders()
        if body:
            headers["Content-Length"] = str(len(body))
            headers["Content-Type"] = "application/json"
        super().__init__(
            headers=headers,
            rfile=io.BytesIO(body or b""),
            client_address=("127.0.0.1", 8080),
            upstream_calls=[],
            json_calls=[],
        )

    def _read_request_body(self) -> bytes | None:
        return gateway.Handler._read_request_body(self)

    def _build_upstream_headers(self, trace_id: str) -> dict[str, str]:
        return gateway.Handler._build_upstream_headers(self, trace_id)

    def _send_upstream_response(self, status: int, body: bytes, headers, trace_id: str) -> None:  # noqa: ANN001
        self.upstream_calls.append({"status": status, "body": body, "headers": headers, "trace_id": trace_id})

    def _send_json(self, payload: dict[str, object], status: int = 200) -> None:
        self.json_calls.append({"status": status, "payload": payload})


def test_gateway_translates_public_paths_before_proxying(monkeypatch) -> None:
    monkeypatch.setitem(gateway.SERVICE_URLS, "settings-service", "http://settings.internal")
    monkeypatch.setitem(gateway.SERVICE_URLS, "attendance-service", "http://attendance.internal")
    monkeypatch.setitem(gateway.SERVICE_URLS, "helpdesk-service", "http://helpdesk.internal")
    monkeypatch.setitem(gateway.SERVICE_URLS, "project-service", "http://project.internal")
    monkeypatch.setitem(gateway.SERVICE_URLS, "workflow-service", "http://workflow.internal")

    forwarded: list[tuple[str, str]] = []

    def fake_urlopen(request, timeout):  # noqa: ANN001
        forwarded.append((request.get_method(), request.full_url))
        return _FakeUpstreamResponse()

    monkeypatch.setattr(gateway, "urlopen", fake_urlopen)

    scenarios = [
        ("GET", "/api/v1/settings", "http://settings.internal/settings"),
        ("GET", "/api/v1/attendance/records?from=2026-01-01", "http://attendance.internal/attendance/records?from=2026-01-01"),
        ("POST", "/api/v1/helpdesk/tickets", "http://helpdesk.internal/helpdesk/tickets"),
        ("PATCH", "/api/v1/project", "http://project.internal/projects"),
        ("GET", "/api/v1/workflow/inbox", "http://workflow.internal/workflows/inbox"),
    ]

    for method, path_with_query, expected_url in scenarios:
        handler = _FakeHandler(body=b'{"ok":1}' if method in {"POST", "PATCH"} else None)
        gateway.Handler._proxy_request(handler, method=method, path_with_query=path_with_query, trace_id="trace-proxy")
        assert not handler.json_calls
        assert handler.upstream_calls and handler.upstream_calls[-1]["status"] == 200
        assert forwarded[-1] == (method, expected_url)

