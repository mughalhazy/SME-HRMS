# Deployment

## Stack Overview

The deployment layer provisions these runtime services:

- employee-service
- attendance-service
- leave-service
- payroll-service
- hiring-service
- auth-service
- notification-service
- audit-service
- workflow-service
- performance-service
- engagement-service
- helpdesk-service
- reporting-analytics-service
- search-service
- expense-service
- integration-service
- automation-service
- travel-service
- project-service
- settings-service
- api-gateway
- frontend-ui
- postgres (shared relational store)
- migrations (one-shot schema migration job)

## Artifacts

- `docker-compose.yml`
- `Dockerfile.services`
- `Dockerfile.api`
- `Dockerfile.ui`
- `.env.example`
- `deployment/config/*`
- `deployment/migrations/*`
- `.github/workflows/test.yml`
- `.github/workflows/build.yml`
- `.github/workflows/deploy.yml`

## Local run

```bash
cp .env.example .env
docker compose up -d --build
curl http://localhost:8000/ready
curl http://localhost:8000/api/v1/settings
curl http://localhost:3000/
```


## Canonical API route mapping

Gateway and runtime handlers are aligned to plural canonical route families for these domains:

- Projects: `/api/v1/projects` → runtime `/projects`
- Integrations: `/api/v1/integrations` → runtime `/integrations`
- Automations: `/api/v1/automations` → runtime `/automations`
- Workflows: `/api/v1/workflows` → runtime `/workflows`

Legacy singular aliases are still accepted by the gateway for compatibility and translated to the canonical plural runtime prefixes.

## Migration support

Compose runs a `migrations` service after PostgreSQL is healthy and before app services become healthy.

## QC validation

```bash
python deployment/qc_validate.py
```

The validator checks a 10-point deployment quality rubric and exits non-zero if score is below 10.
