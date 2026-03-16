# Deployment

This repository includes a containerized deployment baseline and a CI/CD workflow.

## Docker

Build image:

```bash
docker build -t sme-hrms:latest .
```

Run containerized test workload:

```bash
docker run --rm sme-hrms:latest
```

Use Compose:

```bash
docker compose up --build
```

## CI/CD pipeline

The workflow is defined in `.github/workflows/ci-cd.yml` and runs on every pull request and on pushes to `main`:

1. Installs Python 3.12 and dependencies.
2. Runs `python -m unittest discover -s tests -v`.
3. Builds a Docker image.
4. Pushes the image to GHCR (`ghcr.io/<owner>/sme-hrms`) only when the event is a push to `main`.

### Required repository settings

- Ensure GitHub Packages permissions are enabled for the repository.
- If publishing to a different container registry, update the image reference in:
  - `docker-compose.yml`
  - `.github/workflows/ci-cd.yml`
