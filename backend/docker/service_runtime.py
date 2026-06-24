from __future__ import annotations

import asyncio
import importlib.util
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse
from uuid import UUID

import uvicorn

from api_contract import error_payload, success_payload
from core.country_resolver import CountryResolver, seed_dev_defaults
from resilience import Observability
from structured_logging import configure_logging


PORT = int(os.getenv("PORT", "8000"))
SERVICE_NAME = os.getenv("SERVICE_NAME", "service")

configure_logging(service="service-runtime")
LOGGER = logging.getLogger("service-runtime")
OBSERVABILITY = Observability(SERVICE_NAME)

_COUNTRY_RESOLVER: CountryResolver = CountryResolver()


def _bootstrap_country_resolver() -> None:
    """Populate the shared CountryResolver from COUNTRY_ORG_MAPPINGS env var at startup.

    Format: COUNTRY_ORG_MAPPINGS=org_id:country_code:adapter_key[,...]
    Example: COUNTRY_ORG_MAPPINGS=ORG_DEFAULT:PK:pakistan,ORG_ACME:PK:pakistan

    Falls back to dev seed (PakistanAdapter for ORG_DEFAULT) if env var is not set.
    """
    mappings_env = os.getenv("COUNTRY_ORG_MAPPINGS", "")
    if not mappings_env:
        seed_dev_defaults(_COUNTRY_RESOLVER)
        LOGGER.info("country_resolver: using dev defaults — set COUNTRY_ORG_MAPPINGS for production")
        return

    try:
        from country.pakistan import PakistanAdapter
        _COUNTRY_RESOLVER.register_adapter("pakistan", PakistanAdapter)
        LOGGER.info("country_resolver: registered pakistan adapter")
    except ImportError:
        LOGGER.warning("country_resolver: PakistanAdapter not found — pakistan adapter not registered")

    for entry in mappings_env.split(","):
        parts = entry.strip().split(":")
        if len(parts) != 3:
            LOGGER.warning("country_resolver: invalid COUNTRY_ORG_MAPPINGS entry '%s' (expected org_id:country_code:adapter_key)", entry)
            continue
        org_id, country_code, adapter_key = (p.strip() for p in parts)
        try:
            _COUNTRY_RESOLVER.register_mapping(org_id, country_code, adapter_key)
            LOGGER.info("country_resolver: registered org_id=%s country=%s adapter=%s", org_id, country_code, adapter_key)
        except Exception as exc:
            LOGGER.error("country_resolver: failed to register '%s': %s", entry, exc)

CANONICAL_PLURAL_ROUTE_PREFIXES: dict[str, str] = {
    "project-service": "/projects",
    "integration-service": "/integrations",
    "automation-service": "/automations",
    "workflow-service": "/workflows",
}


@dataclass
class Route:
    method: str
    pattern: str
    handler: Callable[[dict[str, str], dict[str, Any], dict[str, Any], dict[str, str]], tuple[int, dict[str, Any]]]


def _qs_dict(raw_query: str) -> dict[str, str]:
    parsed = parse_qs(raw_query, keep_blank_values=False)
    return {key: values[-1] for key, values in parsed.items() if values}



def _match(pattern: str, path: str) -> dict[str, str] | None:
    names: list[str] = []
    regex = "^" + re.sub(r"\{([^/}]+)\}", lambda m: names.append(m.group(1)) or r"([^/]+)", pattern.rstrip("/")) + "$"
    m = re.match(regex, path.rstrip("/"))
    if not m:
        return None
    return {names[idx]: value for idx, value in enumerate(m.groups())}


def _build_response(status: int, payload: dict[str, Any]) -> tuple[int, bytes, list[tuple[bytes, bytes]]]:
    body = json.dumps(payload).encode("utf-8")
    trace = str(payload.get("meta", {}).get("request_id", "")).encode()
    headers = [
        (b"content-type", b"application/json"),
        (b"x-trace-id", trace),
        (b"x-request-id", trace),
        (b"x-content-type-options", b"nosniff"),
        (b"x-frame-options", b"DENY"),
        (b"cache-control", b"no-store"),
        (b"content-length", str(len(body)).encode()),
    ]
    return status, body, headers


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

        service = PayrollService(country_resolver=_COUNTRY_RESOLVER)
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
    elif service_name == "settings-service":
        settings_state: dict[str, Any] = {
            "tenant_id": os.getenv("DEFAULT_TENANT_ID", "tenant-default"),
            "attendance_policy": {"workdays": ["MON", "TUE", "WED", "THU", "FRI"], "timezone": "UTC"},
            "leave_policy": {"annual_days": 20, "carry_forward_limit_days": 5},
            "payroll": {"currency": "USD", "pay_schedule": "monthly", "pay_day": 30},
        }

        def get_settings(_: dict[str, str], __: dict[str, Any], ___: dict[str, Any], ____: dict[str, str]) -> tuple[int, dict[str, Any]]:
            return 200, success_payload({"settings": settings_state}, OBSERVABILITY.trace_id(None))

        def put_settings(_: dict[str, str], __: dict[str, Any], body: dict[str, Any], ___: dict[str, str]) -> tuple[int, dict[str, Any]]:
            if not isinstance(body, dict):
                return 400, error_payload("INVALID_PAYLOAD", "Expected JSON object body", OBSERVABILITY.trace_id(None))
            settings_state.update(body)
            return 200, success_payload({"settings": settings_state}, OBSERVABILITY.trace_id(None))

        register("GET", "/settings", get_settings)
        register("PUT", "/settings", put_settings)
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
    elif service_name == "compliance-service":
        from compliance_api import (
            post_compliance_submission, get_compliance_submission,
            list_compliance_submissions, validate_compliance_submission,
            generate_compliance_report, submit_compliance,
            retry_compliance_submission, get_compliance_report, get_compliance_audit,
        )
        from services.compliance_service import ComplianceService

        service = ComplianceService(resolver=_COUNTRY_RESOLVER)
        register("POST", "/compliance/submissions", lambda p, q, b, h: post_compliance_submission(service, b, h.get("Authorization")))
        register("GET", "/compliance/submissions/{submission_id}", lambda p, q, b, h: get_compliance_submission(service, p["submission_id"], h.get("Authorization")))
        register("GET", "/compliance/submissions", lambda p, q, b, h: list_compliance_submissions(service, h.get("Authorization"), q))
        register("POST", "/compliance/submissions/{submission_id}/validate", lambda p, q, b, h: validate_compliance_submission(service, p["submission_id"], b, h.get("Authorization")))
        register("POST", "/compliance/submissions/{submission_id}/generate", lambda p, q, b, h: generate_compliance_report(service, p["submission_id"], b, h.get("Authorization")))
        register("POST", "/compliance/submissions/{submission_id}/submit", lambda p, q, b, h: submit_compliance(service, p["submission_id"], b, h.get("Authorization")))
        register("POST", "/compliance/submissions/{submission_id}/retry", lambda p, q, b, h: retry_compliance_submission(service, p["submission_id"], b, h.get("Authorization")))
        register("GET", "/compliance/submissions/{submission_id}/report", lambda p, q, b, h: get_compliance_report(service, p["submission_id"], h.get("Authorization")))
        register("GET", "/compliance/audit", lambda p, q, b, h: get_compliance_audit(service, h.get("Authorization"), q))
    elif service_name == "bank-service":
        from banking_api import (
            post_disbursement, get_disbursement, list_disbursements,
            execute_disbursement, list_payments, post_reconciliation,
            get_reconciliation, post_raast_payout, get_bank_accounts,
            post_bank_account, patch_bank_account,
        )
        from bank_service import BankService

        service = BankService(resolver=_COUNTRY_RESOLVER)
        register("POST", "/banking/disbursements", lambda p, q, b, h: post_disbursement(service, b, h.get("Authorization")))
        register("GET", "/banking/disbursements/{disbursement_id}", lambda p, q, b, h: get_disbursement(service, p["disbursement_id"], h.get("Authorization")))
        register("GET", "/banking/disbursements", lambda p, q, b, h: list_disbursements(service, h.get("Authorization"), q))
        register("POST", "/banking/disbursements/{disbursement_id}/execute", lambda p, q, b, h: execute_disbursement(service, p["disbursement_id"], b, h.get("Authorization")))
        register("GET", "/banking/payments", lambda p, q, b, h: list_payments(service, h.get("Authorization"), q))
        register("POST", "/banking/reconcile", lambda p, q, b, h: post_reconciliation(service, b, h.get("Authorization")))
        register("GET", "/banking/reconciliation/{reconciliation_id}", lambda p, q, b, h: get_reconciliation(service, p["reconciliation_id"], h.get("Authorization")))
        register("POST", "/banking/raast/payout", lambda p, q, b, h: post_raast_payout(service, b, h.get("Authorization")))
        register("GET", "/banking/accounts", lambda p, q, b, h: get_bank_accounts(service, h.get("Authorization"), q))
        register("POST", "/banking/accounts", lambda p, q, b, h: post_bank_account(service, b, h.get("Authorization")))
        register("PATCH", "/banking/accounts/{account_id}", lambda p, q, b, h: patch_bank_account(service, p["account_id"], b, h.get("Authorization")))
    elif service_name == "whatsapp-service":
        from whatsapp_api import (
            post_webhook, post_identity_register, post_identity_verify,
            delete_identity, get_identity, post_send_message, get_conversations, get_session,
        )
        from whatsapp_service import WhatsAppService

        service = WhatsAppService()
        register("POST", "/whatsapp/webhook", lambda p, q, b, h: post_webhook(service, b, h.get("Authorization")))
        register("POST", "/whatsapp/identity/register", lambda p, q, b, h: post_identity_register(service, b, h.get("Authorization")))
        register("POST", "/whatsapp/identity/verify", lambda p, q, b, h: post_identity_verify(service, b, h.get("Authorization")))
        register("DELETE", "/whatsapp/identity/{employee_id}", lambda p, q, b, h: delete_identity(service, p["employee_id"], h.get("Authorization")))
        register("GET", "/whatsapp/identity/{employee_id}", lambda p, q, b, h: get_identity(service, p["employee_id"], h.get("Authorization")))
        register("POST", "/whatsapp/send", lambda p, q, b, h: post_send_message(service, b, h.get("Authorization")))
        register("GET", "/whatsapp/conversations", lambda p, q, b, h: get_conversations(service, h.get("Authorization"), q))
        register("GET", "/whatsapp/sessions/{session_id}", lambda p, q, b, h: get_session(service, p["session_id"], h.get("Authorization")))
    elif service_name == "decision-service":
        from decision_api import (
            list_decision_cards, get_decision_card, acknowledge_card,
            override_card, dismiss_card, list_anomalies, trigger_scan,
            post_copilot_query, get_compliance_readiness,
        )

        register("GET", "/decisions/cards", lambda p, q, b, h: list_decision_cards(h.get("Authorization"), q))
        register("GET", "/decisions/cards/{card_id}", lambda p, q, b, h: get_decision_card(p["card_id"], h.get("Authorization")))
        register("POST", "/decisions/cards/{card_id}/acknowledge", lambda p, q, b, h: acknowledge_card(p["card_id"], b, h.get("Authorization")))
        register("POST", "/decisions/cards/{card_id}/override", lambda p, q, b, h: override_card(p["card_id"], b, h.get("Authorization")))
        register("POST", "/decisions/cards/{card_id}/dismiss", lambda p, q, b, h: dismiss_card(p["card_id"], b, h.get("Authorization")))
        register("GET", "/decisions/anomalies", lambda p, q, b, h: list_anomalies(h.get("Authorization"), q))
        register("POST", "/decisions/scan", lambda p, q, b, h: trigger_scan(b, h.get("Authorization")))
        register("POST", "/decisions/copilot", lambda p, q, b, h: post_copilot_query(b, h.get("Authorization")))
        register("POST", "/decisions/compliance-readiness", lambda p, q, b, h: get_compliance_readiness(b))
    elif service_name == "auth-service":
        auth_service_mod = _auth_module("auth_service_runtime", "service.py")
        auth_api_mod = _auth_module("auth_api_runtime", "api.py")

        service = auth_service_mod.AuthService(token_secret=os.getenv("AUTH_TOKEN_SECRET", "test-secret-for-hardening-1234567890"))

        register("POST", "/auth/login", lambda p, q, b, h: auth_api_mod.post_auth_login(service, b))
        register("GET", "/auth/me", lambda p, q, b, h: auth_api_mod.get_auth_me(service, h.get("Authorization")))
    elif service_name == "employee-service":
        from employee_service import EmployeeService
        from employee_api import (
            post_departments, get_departments, get_department, patch_department,
            post_roles, get_roles, get_role, patch_role,
            post_employees, get_employees, get_employee, patch_employee,
            post_employee_terminate, post_employee_transfer,
        )

        service = EmployeeService()

        register("POST", "/departments", lambda p, q, b, h: post_departments(service, b))
        register("GET", "/departments", lambda p, q, b, h: get_departments(service, q))
        register("GET", "/departments/{department_id}", lambda p, q, b, h: get_department(service, p["department_id"]))
        register("PATCH", "/departments/{department_id}", lambda p, q, b, h: patch_department(service, p["department_id"], b))
        register("POST", "/roles", lambda p, q, b, h: post_roles(service, b))
        register("GET", "/roles", lambda p, q, b, h: get_roles(service, q))
        register("GET", "/roles/{role_id}", lambda p, q, b, h: get_role(service, p["role_id"]))
        register("PATCH", "/roles/{role_id}", lambda p, q, b, h: patch_role(service, p["role_id"], b))
        register("POST", "/employees", lambda p, q, b, h: post_employees(service, b))
        register("GET", "/employees", lambda p, q, b, h: get_employees(service, q))
        register("GET", "/employees/{employee_id}", lambda p, q, b, h: get_employee(service, p["employee_id"]))
        register("PATCH", "/employees/{employee_id}", lambda p, q, b, h: patch_employee(service, p["employee_id"], b))
        register("POST", "/employees/{employee_id}/terminate", lambda p, q, b, h: post_employee_terminate(service, p["employee_id"], b))
        register("POST", "/employees/{employee_id}/transfer", lambda p, q, b, h: post_employee_transfer(service, p["employee_id"], b))
    else:
        LOGGER.warning("No explicit runtime routes for service=%s", service_name)

    if service_name in CANONICAL_PLURAL_ROUTE_PREFIXES:
        canonical_prefix = CANONICAL_PLURAL_ROUTE_PREFIXES[service_name]
        if not any(route.pattern.startswith(canonical_prefix) for route in routes):
            raise RuntimeError(f"Service '{service_name}' must expose canonical runtime prefix '{canonical_prefix}'.")

    ctx["routes"] = [f"{route.method} {route.pattern}" for route in routes]
    return routes, ctx


ROUTES, CONTEXT = build_service_runtime(SERVICE_NAME)


# ---------------------------------------------------------------------------
# Synchronous dispatch — called via asyncio.to_thread from the ASGI app
# ---------------------------------------------------------------------------

def _dispatch(
    method: str,
    path: str,
    query_string: str,
    headers: dict[str, str],
    raw_body: bytes,
) -> tuple[int, bytes, list[tuple[bytes, bytes]]]:
    trace_id = OBSERVABILITY.trace_id(headers.get("x-trace-id") or headers.get("x-request-id"))

    if path in ("/health", "/ready"):
        return _build_response(200, success_payload(
            {
                "service": SERVICE_NAME,
                "service_status": "ok",
                "runtime": "domain",
                "routes": CONTEXT.get("routes", []),
                "metrics": OBSERVABILITY.metrics.snapshot(),
            },
            trace_id,
        ))

    if path == "/":
        return _build_response(200, success_payload(
            {"service": SERVICE_NAME, "message": "domain runtime active", "routes": CONTEXT.get("routes", [])},
            trace_id,
        ))

    if method in ("POST", "PATCH", "PUT", "DELETE") and raw_body:
        try:
            body: dict[str, Any] = json.loads(raw_body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            body = {}
    else:
        body = {}

    query = _qs_dict(query_string)

    for route in ROUTES:
        if route.method != method:
            continue
        path_params = _match(route.pattern, path)
        if path_params is None:
            continue
        status, payload = route.handler(path_params, query, body, headers)
        return _build_response(status, payload)

    return _build_response(
        404,
        error_payload("NOT_FOUND", "Resource not found", trace_id, details=[{"path": path, "method": method}], service=SERVICE_NAME),
    )


# ---------------------------------------------------------------------------
# ASGI application
# ---------------------------------------------------------------------------

async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
    if scope["type"] == "lifespan":
        while True:
            event = await receive()
            if event["type"] == "lifespan.startup":
                _bootstrap_country_resolver()
                await send({"type": "lifespan.startup.complete"})
            elif event["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                break
        return

    if scope["type"] != "http":
        return

    raw_body = b""
    while True:
        message = await receive()
        raw_body += message.get("body", b"")
        if not message.get("more_body", False):
            break

    method = scope["method"]
    path = scope["path"]
    query_string = scope.get("query_string", b"").decode()
    headers = {k.decode(): v.decode() for k, v in scope.get("headers", [])}

    status, resp_body, resp_headers = await asyncio.to_thread(
        _dispatch, method, path, query_string, headers, raw_body
    )

    await send({"type": "http.response.start", "status": status, "headers": resp_headers})
    await send({"type": "http.response.body", "body": resp_body})


if __name__ == "__main__":
    import sys
    from typing import Any as _Any
    ssl_cert = os.getenv("SSL_CERT_FILE", "")
    ssl_key = os.getenv("SSL_KEY_FILE", "")
    uvicorn_kwargs: dict[str, _Any] = {
        "host": "0.0.0.0",
        "port": PORT,
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
        "access_log": False,
    }
    if ssl_cert and ssl_key:
        uvicorn_kwargs["ssl_certfile"] = ssl_cert
        uvicorn_kwargs["ssl_keyfile"] = ssl_key
    uvicorn.run("service_runtime:app", **uvicorn_kwargs)
