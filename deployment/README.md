# Deployment Layer

This directory contains deterministic deployment configuration:
- `config/` environment and gateway/postgres bootstrap configuration.
- `migrations/` SQL migrations for canonical HRMS entities.
- `scripts/run-migrations.sh` migration runner executed by compose.
- `frontend/` static UI artifact used by `Dockerfile.ui`.
- `qc_validate.py` automated QC scoring (target 10/10).
