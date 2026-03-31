from __future__ import annotations

import importlib.util
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse
from uuid import UUID

from api_contract import error_payload, success_payload
from resilience import Observability

PORT = int(os.getenv("PORT", "8000"))
SERVICE_NAME = os.getenv("SERVICE_NAME", "service")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("service-runtime")
OBSERVABILITY = Observability(SERVICE_NAME)


@dataclass
class Route:
    method: str
    pattern: str
    handler: Callable[[dict[str, str], dict[str, Any], dict[str, Any], dict[str, str]], tuple[int, dict[str, Any]]]


def _qs_dict(raw_query: str) -> dict[str, str]:
    parsed = parse_qs(raw_query, keep_blank_values=False)
    return {key: values[-1] for key, values in parsed.items() if values}


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def _match(pattern: str, path: str) -> dict[str, str] | None:
    names: list[str] = []
    regex = "^" + re.sub(r"\{([^/}]+)\}", lambda m: names.append(m.group(1)) or r"([^/]+)", pattern.rstrip("/")) + "$"
    m = re.match(regex, path.rstrip("/"))
    if not m:
        return None
    return {names[idx]: value for idx, value in enumerate(m.groups())}


def _send(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    trace = str(payload.get("meta", {}).get("request_id", ""))
    handler.send_header("X-Trace-Id", trace)
    handler.send_header("X-Request-Id", trace)
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("X-Frame-Options", "DENY")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _auth_module(module_name: str, filename: str):
    base = Path(__file__).resolve().parents[1] / "services" / "auth-service"
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))
    spec = importlib.util.spec_from_file_location(module_name, base / filename)
    if not spec or not spec.loader:
        raise RuntimeError(f"Unable to load {filename} from auth-service")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def build_service_runtime(service_name: str) -> tuple[list[Route], dict[str, Any]]:
    ctx: dict[str, Any] = {"service": service_name}
    routes: list[Route] = []

    def register(method: str, pattern: str, fn: Callable[[dict[str, str], dict[str, Any], dict[str, Any], dict[str, str]], tuple[int, dict[str, Any]]]) -> None:
        routes.append(Route(method=method, pattern=pattern, handler=fn))

    if service_name == "attendance-service":
        from attendance_service.api import get_attendance_records, post_attendance_records
        from attendance_service.service import Actor, AttendanceService, EmployeeSnapshot, InMemoryEmployeeDirectory

        directory = InMemoryEmployeeDirectory([
            EmployeeSnapshot(employee_id=UUID("11111111-1111-1111-1111-111111111111"), status="active", department_id=UUID("22222222-2222-2222-2222-222222222222"))
        ])
        service = AttendanceService(directory)
        actor = Actor(employee_id=UUID("11111111-1111-1111-1111-111111111111"), role="HRAdmin", department_id=UUID("22222222-2222-2222-2222-222222222222"))

        register("POST", "/attendance/records", lambda p, q, b, h: post_attendance_records(service, actor, b))
        register("GET", "/attendance/records", lambda p, q, b, h: get_attendance_records(service, actor, q))
    elif service_name == "audit-service":
        from audit_service.api import get_audit_records

        register("GET", "/audit/records", lambda p, q, b, h: get_audit_records(q))
    elif service_name == "engagement-service":
        from engagement_api import get_surveys, post_surveys
        from engagement_service import EngagementService

        service = EngagementService()
        register("POST", "/engagement/surveys", lambda p, q, b, h: post_surveys(service, "HRAdmin", h.get("X-Actor-Id", "system"), b))
        register("GET", "/engagement/surveys", lambda p, q, b, h: get_surveys(service, "HRAdmin", h.get("X-Actor-Id", "system"), q))
    elif service_name == "expense-service":
        from expense_api import get_expense_claims, post_expense_claims
        from expense_service import ExpenseService

        service = ExpenseService()
        register("POST", "/expense/claims", lambda p, q, b, h: post_expense_claims(service, h.get("X-Actor-Role", "Employee"), h.get("X-Actor-Id", "system"), b))
        register("GET", "/expense/claims", lambda p, q, b, h: get_expense_claims(service, h.get("X-Actor-Role", "Employee"), h.get("X-Actor-Id", "system"), q))
    elif service_name == "helpdesk-service":
        from helpdesk_api import get_helpdesk_tickets, post_helpdesk_tickets
        from helpdesk_service import HelpdeskService

        service = HelpdeskService()
        register("POST", "/helpdesk/tickets", lambda p, q, b, h: post_helpdesk_tickets(service, h.get("X-Actor-Role", "Employee"), h.get("X-Actor-Id", "system"), b))
        register("GET", "/helpdesk/tickets", lambda p, q, b, h: get_helpdesk_tickets(service, h.get("X-Actor-Role", "Employee"), h.get("X-Actor-Id", "system"), q))
    elif service_name == "integration-service":
        from integration_api import get_webhooks, post_webhook
        from integration_service import IntegrationService

        service = IntegrationService(master_key=os.getenv("INTEGRATION_MASTER_KEY", "m" * 32))
        register("POST", "/integrations/webhooks", lambda p, q, b, h: post_webhook(service, b))
        register("GET", "/integrations/webhooks", lambda p, q, b, h: get_webhooks(service, q))
    elif service_name == "leave-service":
        from leave_api import get_leave_requests, post_leave_requests
        from leave_service import LeaveService

        service = LeaveService()
        register("POST", "/leave/requests", lambda p, q, b, h: post_leave_requests(service, h.get("X-Actor-Role", "Employee"), h.get("X-Actor-Id", "system"), b))
        register("GET", "/leave/requests", lambda p, q, b, h: get_leave_requests(service, h.get("X-Actor-Role", "Employee"), h.get("X-Actor-Id", "system"), q))
    elif service_name == "payroll-service":
        from payroll_api import get_payroll_records, post_payroll_records
        from payroll_service import PayrollService

        service = PayrollService()
        register("POST", "/payroll/records", lambda p, q, b, h: post_payroll_records(service, b, h.get("Authorization")))
        register("GET", "/payroll/records", lambda p, q, b, h: get_payroll_records(service, h.get("Authorization"), q))
    elif service_name == "travel-service":
        from travel_api import get_travel_requests, post_travel_requests
        from travel_service import TravelService

        service = TravelService()
        register("POST", "/travel/requests", lambda p, q, b, h: post_travel_requests(service, h.get("X-Actor-Role", "Employee"), h.get("X-Actor-Id", "system"), b))
        register("GET", "/travel/requests", lambda p, q, b, h: get_travel_requests(service, h.get("X-Actor-Role", "Employee"), h.get("X-Actor-Id", "system"), q))
    elif service_name == "workflow-service":
        from workflow_api import get_workflow_inbox, post_workflow_escalate
        from workflow_service import WorkflowService

        service = WorkflowService()
        register("GET", "/workflows/inbox", lambda p, q, b, h: get_workflow_inbox(service, tenant_id=q.get("tenant_id", "tenant-default"), actor_id=h.get("X-Actor-Id", "system"), actor_role=h.get("X-Actor-Role", "HRAdmin"), query=q))
        register("POST", "/workflows/escalate", lambda p, q, b, h: post_workflow_escalate(service, tenant_id=(b.get("tenant_id") if isinstance(b, dict) else None) or "tenant-default"))
    elif service_name == "notification-service":
        from notification_api import post_notification_event
        from notification_service import NotificationService

        service = NotificationService()
        register("POST", "/notifications/events", lambda p, q, b, h: post_notification_event(service, b))
    elif service_name == "performance-service":
        from performance_api import get_goals, post_goals
        from performance_service import PerformanceService

        service = PerformanceService()
        register("POST", "/performance/goals", lambda p, q, b, h: post_goals(service, h.get("X-Actor-Role", "Employee"), h.get("X-Actor-Id", "system"), b))
        register("GET", "/performance/goals", lambda p, q, b, h: get_goals(service, h.get("X-Actor-Role", "Employee"), h.get("X-Actor-Id", "system"), q))
    elif service_name == "reporting-analytics-service":
        from reporting_analytics import ReportingAnalyticsService
        from reporting_analytics_api import get_reporting_aggregates

        service = ReportingAnalyticsService()
        register("GET", "/reporting/aggregates", lambda p, q, b, h: get_reporting_aggregates(service, q))
    elif service_name == "search-service":
        from search_api import get_search
        from search_service import SearchIndexingService

        service = SearchIndexingService()
        register("GET", "/search", lambda p, q, b, h: get_search(service, q))
    elif service_name == "automation-service":
        from automation_api import get_rules, post_rule
        from automation_service import AutomationService

        service = AutomationService()
        register("POST", "/automations/rules", lambda p, q, b, h: post_rule(service, b))
        register("GET", "/automations/rules", lambda p, q, b, h: get_rules(service, q))
    elif service_name == "project-service":
        from project_service import ProjectService

        service = ProjectService()

        def create_project(_: dict[str, str], __: dict[str, Any], body: dict[str, Any], ___: dict[str, str]) -> tuple[int, dict[str, Any]]:
            created = service.create_project(body)
            return 201, success_payload(created, OBSERVABILITY.trace_id(None))

        def list_projects(_: dict[str, str], q: dict[str, Any], __: dict[str, Any], ___: dict[str, str]) -> tuple[int, dict[str, Any]]:
            listing = service.list_projects(tenant_id=q.get("tenant_id", "tenant-default"))
            return 200, success_payload({"items": listing}, OBSERVABILITY.trace_id(None))

        register("POST", "/projects", create_project)
        register("GET", "/projects", list_projects)
    elif service_name == "hiring-service":
        from services.hiring_service import HiringService
        from services.hiring_service.api import get_job_postings, post_job_postings

        service = HiringService()
        register("POST", "/hiring/job-postings", lambda p, q, b, h: post_job_postings(service, b))
        register("GET", "/hiring/job-postings", lambda p, q, b, h: get_job_postings(service, q))
    elif service_name == "auth-service":
        auth_service_mod = _auth_module("auth_service_runtime", "service.py")
        auth_api_mod = _auth_module("auth_api_runtime", "api.py")

        service = auth_service_mod.AuthService(token_secret=os.getenv("AUTH_TOKEN_SECRET", "test-secret-for-hardening-1234567890"))

        register("POST", "/auth/login", lambda p, q, b, h: auth_api_mod.post_auth_login(service, b))
        register("GET", "/auth/me", lambda p, q, b, h: auth_api_mod.get_auth_me(service, h.get("Authorization")))
    else:
        LOGGER.warning("No explicit runtime routes for service=%s", service_name)

    ctx["routes"] = [f"{route.method} {route.pattern}" for route in routes]
    return routes, ctx


ROUTES, CONTEXT = build_service_runtime(SERVICE_NAME)


class Handler(BaseHTTPRequestHandler):
    def _serve(self, method: str) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        trace_id = OBSERVABILITY.trace_id(self.headers.get("X-Trace-Id") or self.headers.get("X-Request-Id"))

        if path in ("/health", "/ready"):
            payload = success_payload(
                {
                    "service": SERVICE_NAME,
                    "service_status": "ok",
                    "runtime": "domain",
                    "routes": CONTEXT.get("routes", []),
                    "metrics": OBSERVABILITY.metrics.snapshot(),
                },
                trace_id,
            )
            _send(self, 200, payload)
            return

        if path == "/":
            payload = success_payload({"service": SERVICE_NAME, "message": "domain runtime active", "routes": CONTEXT.get("routes", [])}, trace_id)
            _send(self, 200, payload)
            return

        body = _read_json(self) if method in ("POST", "PATCH", "PUT", "DELETE") else {}
        query = _qs_dict(parsed.query)
        headers = {k: v for k, v in self.headers.items()}

        for route in ROUTES:
            if route.method != method:
                continue
            path_params = _match(route.pattern, path)
            if path_params is None:
                continue
            status, payload = route.handler(path_params, query, body, headers)
            _send(self, status, payload)
            return

        _send(self, 404, error_payload("NOT_FOUND", "Resource not found", trace_id, details=[{"path": path, "method": method}], service=SERVICE_NAME))

    def do_GET(self) -> None:  # noqa: N802
        self._serve("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._serve("POST")

    def do_PATCH(self) -> None:  # noqa: N802
        self._serve("PATCH")

    def do_PUT(self) -> None:  # noqa: N802
        self._serve("PUT")

    def do_DELETE(self) -> None:  # noqa: N802
        self._serve("DELETE")

    def log_message(self, fmt: str, *args: Any) -> None:
        return


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
