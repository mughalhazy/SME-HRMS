"""
S7-G05 — Import health: all top-level service and API modules must import without error.

If any module fails to import, the test fails with the exact import error message.
This is the first line of defence against broken dependency chains.
"""
import importlib
import pytest

# Core services
CORE_SERVICES = [
    "payroll_service",
    "bank_service",
    "leave_service",
    "whatsapp_service",
    "notification_service",
    "workflow_service",
    "automation_service",
    "travel_service",
    "engagement_service",
    "expense_service",
    "helpdesk_service",
    "performance_service",
    "search_service",
    "integration_service",
    "project_service",
    "cost_planning_service",
]

# API surface modules
API_MODULES = [
    "payroll_api",
    "compliance_api",
    "banking_api",
    "decision_api",
    "whatsapp_api",
    "reporting_analytics_api",
    "leave_api",
    "travel_api",
    "automation_api",
    "engagement_api",
    "expense_api",
    "helpdesk_api",
    "notification_api",
    "performance_api",
    "workflow_api",
    "search_api",
    "integration_api",
]

# Country layer
COUNTRY_MODULES = [
    "core.country_resolver",
    "country.base",
    "country.pakistan",
    "country.dummy",
]

# Key services subdirectory modules
SERVICE_MODULES = [
    "services.compliance_service",
    "services.decision_engine",
]


@pytest.mark.parametrize("module", CORE_SERVICES)
def test_core_service_imports(module):
    importlib.import_module(module)


@pytest.mark.parametrize("module", API_MODULES)
def test_api_module_imports(module):
    importlib.import_module(module)


@pytest.mark.parametrize("module", COUNTRY_MODULES)
def test_country_module_imports(module):
    importlib.import_module(module)


@pytest.mark.parametrize("module", SERVICE_MODULES)
def test_service_submodule_imports(module):
    importlib.import_module(module)
