# Meridian HCM

Multi-tenant SaaS Human Capital Management platform for SMEs.

## Architecture

- **Backend**: 24 Python microservices + API Gateway (custom ASGI runtime, uvicorn)
- **Frontend**: Next.js 15 app (`backend/ui/`)
- **Database**: Single PostgreSQL 16 instance (shared across services)
- **Gateway**: Port 8000 — JWT enforcement, RBAC, rate limiting, 25 upstream routes

## Structure

```
backend/          Python microservices, gateway, shared libs
backend/ui/       Next.js 15 frontend app
docs/             Authority documentation
frontend/         HTML wireframes (archive)
```

## Running Locally

```bash
cd backend
cp .env.example .env
docker compose up
```

API gateway: http://localhost:8000
Frontend: http://localhost:3000
API docs: http://localhost:8000/docs

## Documentation

See `docs/` for full authority documentation:

- `docs/00_authority/` — Project charter, feature scope, domain model
- `docs/01_backend/` — Service catalog, API contract, architecture
- `docs/06_decisions/` — Architecture decision records
- `docs/08_reports/` — Audit and gap reports
