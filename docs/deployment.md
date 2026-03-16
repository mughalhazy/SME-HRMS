# Deployment

## Stack Overview

The deployment layer provisions these runtime services:

- employee-service
- attendance-service
- leave-service
- payroll-service
- hiring-service
- auth-service
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
curl http://localhost:3000/
```

## Migration support

Compose runs a `migrations` service after PostgreSQL is healthy and before app services become healthy.

## QC validation

```bash
python deployment/qc_validate.py
```

The validator checks a 10-point deployment quality rubric and exits non-zero if score is below 10.
