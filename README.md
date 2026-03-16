# SME-HRMS

## Attendance service implementation

This repository now includes a reference `attendance-service` implementation aligned to canonical docs in `docs/canon/`.

### Key coverage
- Attendance record capture/update/list/read.
- Validation/approval/period lock lifecycle (`Captured` → `Validated` → `Approved` → `Locked`).
- Role-aware authorization aligned with the RBAC matrix (`Admin`, `Manager`, `Employee`).
- Event emission for `AttendanceCaptured`, `AttendanceValidated`, `AttendanceApproved`, `AttendanceLocked`, and `AttendancePeriodClosed`.
- API adapter helpers with canonical error envelope support.

### Run tests

```bash
python -m unittest discover -s tests -v
```

## Deployment baseline

- `Dockerfile` builds a Python 3.12 container for the repository.
- `docker-compose.yml` defines a runnable `hrms` service.
- `.github/workflows/ci-cd.yml` runs tests on PRs and builds/publishes an image on `main`.

See `docs/deployment.md` for usage details.
