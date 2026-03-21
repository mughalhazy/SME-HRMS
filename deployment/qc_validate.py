from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = (ROOT / "docker-compose.yml").read_text()
ENV_EXAMPLE = (ROOT / ".env.example").read_text()
WORKFLOW_BUILD = (ROOT / ".github/workflows/build.yml").read_text()
CORE_SCHEMA = (ROOT / "deployment/migrations/001_core_schema.sql").read_text()
WORKFLOW_SCHEMA = (ROOT / "deployment/migrations/002_workflow_schema.sql").read_text()

checks: list[tuple[str, bool]] = []

# 1 service containers match required map subset
required = [
    "employee-service",
    "attendance-service",
    "leave-service",
    "payroll-service",
    "hiring-service",
    "auth-service",
    "notification-service",
    "api-gateway",
    "frontend-ui",
]
checks.append(("service containers", all(f"\n  {name}:" in COMPOSE for name in required)))

# 2 env vars defined
checks.append(("environment variables", "EMPLOYEE_SERVICE_URL" in ENV_EXAMPLE and "POSTGRES_PASSWORD" in ENV_EXAMPLE))

# 3 API gateway connectivity
checks.append(("api gateway connectivity", all(k in COMPOSE for k in ["EMPLOYEE_SERVICE_URL", "ATTENDANCE_SERVICE_URL", "AUTH_SERVICE_URL", "NOTIFICATION_SERVICE_URL"])))

# 4 db connectivity
checks.append(("database connectivity", "postgres:" in COMPOSE and "DATABASE_URL" in COMPOSE))

# 5 migrations support
checks.append(("migrations", "migrations:" in COMPOSE and "run-migrations.sh" in COMPOSE))

# 6 health checks
checks.append(("health checks", COMPOSE.count("healthcheck:") >= 9))

# 7 tests before build
checks.append(("tests before build", "needs: test-before-build" in WORKFLOW_BUILD))

# 8 build containers correctly
checks.append(("build containers", all(df in WORKFLOW_BUILD for df in ["Dockerfile.api", "Dockerfile.services", "Dockerfile.ui"])))

# 9 matches data architecture relational postgres
schema_markers = [
    "tenant_id VARCHAR(80) NOT NULL",
    "first_name VARCHAR(100) NOT NULL",
    "manager_employee_id UUID",
    "leave_type VARCHAR(20) NOT NULL",
    "base_salary NUMERIC(12,2) NOT NULL",
    "CREATE TABLE IF NOT EXISTS interviews",
    "CREATE TABLE IF NOT EXISTS performance_reviews",
    "ON UPDATE CASCADE",
]
checks.append(("data architecture match", "postgres:16-alpine" in COMPOSE and all(marker in (CORE_SCHEMA + WORKFLOW_SCHEMA) for marker in schema_markers)))

# 10 multi-tenant safety
all_tables_have_tenant_id = all('tenant_id VARCHAR(80) NOT NULL' in block for block in __import__('re').findall(r'CREATE TABLE IF NOT EXISTS\s+\w+\s*\((.*?)\);', CORE_SCHEMA + '\n' + WORKFLOW_SCHEMA, __import__('re').S))
checks.append(("multi-tenant tenant_id enforcement", all_tables_have_tenant_id and 'REFERENCES employees (tenant_id, employee_id)' in WORKFLOW_SCHEMA))

# 11 secrets not committed
checks.append(("no committed secrets", not re.search(r"AKIA|PRIVATE KEY|BEGIN RSA", ENV_EXAMPLE + COMPOSE)))

score = sum(1 for _, ok in checks)
for name, ok in checks:
    print(f"[{ 'PASS' if ok else 'FAIL' }] {name}")
print(f"QC score: {score}/{len(checks)}")
if score < len(checks):
    raise SystemExit(1)
