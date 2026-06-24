"""
Import smoke test — exits nonzero if any critical module fails to import.
Run before deployment or CI gating to catch broken dependency chains early.

Usage:
    python script/import_smoke.py
"""
import importlib
import sys

MODULES = [
    # Core services
    "payroll_service",
    "bank_service",
    "leave_service",
    "whatsapp_service",
    "notification_service",
    "workflow_service",
    # API surface
    "payroll_api",
    "compliance_api",
    "banking_api",
    "decision_api",
    "whatsapp_api",
    "reporting_analytics_api",
    # Country layer
    "core.country_resolver",
    "country.base",
    "country.pakistan",
    "country.dummy",
    # Service submodules
    "services.compliance_service",
    "services.decision_engine",
]

failures = []
for mod in MODULES:
    try:
        importlib.import_module(mod)
        print(f"  OK  {mod}")
    except Exception as exc:
        print(f"  FAIL {mod}: {exc}")
        failures.append((mod, exc))

print()
if failures:
    print(f"SMOKE FAILED — {len(failures)} module(s) failed to import:")
    for mod, exc in failures:
        print(f"  {mod}: {exc}")
    sys.exit(1)
else:
    print(f"SMOKE PASSED — {len(MODULES)} modules imported successfully.")
    sys.exit(0)
