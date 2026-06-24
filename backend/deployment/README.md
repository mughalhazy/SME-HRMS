# Deployment Layer

This directory contains deterministic deployment configuration:
- `config/` environment and gateway/postgres bootstrap configuration.
- `migrations/` SQL migrations for canonical HRMS entities.
- `scripts/run-migrations.sh` migration runner executed by compose.
- `frontend/` static UI artifact used by `Dockerfile.ui`.
- `qc_validate.py` automated QC scoring (target 10/10).

- `re_qc_validate_addon_convergence.py` P50 add-on convergence re-QC gate (must pass 10/10).

- `re_qc_validate_master_certification.py` P51 master add-on certification re-QC gate (must pass 10/10).

## Compose runtime notes

- `docker-compose.yml` starts Postgres, runs one-shot migrations, then starts all domain services, including `settings-service`, before `api-gateway`.
- Service images built from `Dockerfile.services` execute real runtime entrypoints through `docker/service_runtime.py` (`start.sh` provides equivalent all-in-one orchestration for non-compose usage).
