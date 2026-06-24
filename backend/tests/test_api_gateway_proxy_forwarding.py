from __future__ import annotations

import importlib.util
import json
import pathlib
import sys


MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "docker" / "api_gateway_service.py"
SPEC = importlib.util.spec_from_file_location("api_gateway_service_forwarding", MODULE_PATH)
gateway = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = gateway
SPEC.loader.exec_module(gateway)


class _FakeUpstreamResponse:
    def __init__(self, payload: bytes = b'{"ok":true}') -> None:
        self.status = 200
        self._payload = payload
        self.headers = {"Content-Type": "application/json"}

    def read(self) -> bytes:
        return self._payload

    def get(self, key: str, default: str = "") -> str:
        return self.headers.get(key, default)

    def __enter__(self) -> "_FakeUpstreamResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None


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
        ("PATCH", "/api/v1/projects", "http://project.internal/projects"),
        ("GET", "/api/v1/workflows/inbox", "http://workflow.internal/workflows/inbox"),
    ]

    for method, path_with_query, expected_url in scenarios:
        body = b'{"ok":1}' if method in {"POST", "PATCH"} else b""
        headers: dict[str, str] = {}
        if body:
            headers["Content-Type"] = "application/json"

        status, resp_body, _resp_headers = gateway._dispatch(method, path_with_query, headers, body)

        assert status == 200, f"Expected 200 for {method} {path_with_query}, got {status}: {resp_body}"
        payload = json.loads(resp_body)
        assert payload.get("ok") is True, f"Expected upstream response for {method} {path_with_query}"
        assert forwarded[-1] == (method, expected_url)

