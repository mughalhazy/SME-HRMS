# SME-HRMS

## Deployment Layer

This repository includes a deterministic deployment layer aligned to canonical service and data architecture docs.

### Included services
- employee-service
- attendance-service
- leave-service
- payroll-service
- hiring-service
- auth-service
- api-gateway
- frontend-ui

### Key deployment artifacts
- `docker-compose.yml`
- `Dockerfile.services`
- `Dockerfile.api`
- `Dockerfile.ui`
- `.env.example`
- `deployment/`
- `.github/workflows/test.yml`
- `.github/workflows/build.yml`
- `.github/workflows/deploy.yml`

See `docs/deployment.md` for startup, migration, and QC validation instructions.
