# SME-HRMS

## Deployment Layer

This repository includes a deterministic deployment layer aligned to canonical service and data architecture docs.

### Runtime topology

#### Standalone services (individual containers)
- employee-service (8001)
- attendance-service (8002)
- leave-service (8003)
- payroll-service (8004)
- hiring-service (8005)
- auth-service (8006)
- notification-service (8007)
- audit-service (8008)
- workflow-service (8009)
- performance-service (8010)
- engagement-service (8011)
- helpdesk-service (8012)
- reporting-analytics-service (8013)
- search-service (8014)
- expense-service (8015)
- integration-service (8016)
- automation-service (8017)
- travel-service (8018)
- project-service (8019)
- settings-service (8020)
- api-gateway (8000)
- frontend-ui (3000)

#### Internal modules (not separate compose services)
- `background_jobs.py` and `background_jobs_api.py` stay internal service modules (asynchronous workers/service-level handlers) and are **not** exposed as a public API gateway route.
- Shared contracts/resilience/middleware/util modules remain in-process dependencies for service containers.


### Canonical route conventions

The public gateway route prefixes use plural domain nouns for collection-style services:

- `/api/v1/projects`
- `/api/v1/integrations`
- `/api/v1/automations`
- `/api/v1/workflows`

Gateway routes are now canonical-only for these domains (`/api/v1/projects`, `/api/v1/integrations`, `/api/v1/automations`, `/api/v1/workflows`); singular aliases were removed during final convergence hardening.

### Key deployment artifacts
- `docker-compose.yml`
- `Dockerfile.services`
- `Dockerfile.api`
- `Dockerfile.ui`
- `start.sh`
- `.env.example`
- `deployment/`

## Run locally

```bash
cp .env.example .env
docker compose up -d --build
```

### Verify startup

```bash
curl http://localhost:8000/ready
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/settings
curl http://localhost:3000/
```

### Useful commands

```bash
# Full status, including health
docker compose ps

# Follow logs
docker compose logs -f api-gateway

# Tear down
docker compose down -v
```

See `docs/deployment.md` for migration and QC validation instructions.
