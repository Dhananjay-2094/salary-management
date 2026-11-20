# Deployment Guide

## One-container demo deployment

The repository includes a multi-stage `Dockerfile` that builds the React application and serves it from the Python API container. SQLite data lives at `/data/salary_management.sqlite3`. The Compose configuration attaches a named persistent volume at `/data` and seeds 10,000 synthetic employees only when the database is empty.

Prerequisites: Docker Engine with the Docker Compose plugin.

From the repository root:

```sh
docker compose up --build -d
docker compose logs -f salary-management
```

Open `http://localhost:8000`. The app and API share one origin. The first startup creates and seeds the demo database; this can take a few seconds. Stop the service with `docker compose down`. The named volume keeps changes across container restarts.

To deliberately restore the synthetic dataset after making demo changes, run:

```sh
docker compose exec salary-management python -m scripts.seed --reset
```

That command replaces all employee and salary rows in the mounted demo database. Back up `/data/salary_management.sqlite3` before running it if the volume contains changes you want to keep.

## Hosting requirements

Build the root `Dockerfile` as one web service. The host must route HTTP traffic to the container's `PORT` and provide a persistent volume mounted at `/data`. Set:

- `DATABASE_PATH=/data/salary_management.sqlite3`
- `FRONTEND_DIST=/app/frontend-dist`
- `SEED_DEMO_DATA=true` for the initial empty volume; it seeds only when there are no employees.

The container accepts the host's `PORT` environment variable and exposes `/health`. Keep the database volume attached to the same single application instance. SQLite is fine for this assessment demo's 10,000 synthetic employees, but this configuration is not a high-write-concurrency or multi-instance production architecture.

Do not expose the local Compose port publicly without a hosting proxy and TLS. This assignment intentionally has no authentication, so the demo URL should be shared only as appropriate for synthetic data and the assessment audience. Do not add real employee salary data.

## Deployment status

The repository is container-ready, but no cloud provider account or deployment credentials are configured in this workspace. A public deployment still requires selecting a host and attaching persistent storage. Do not treat the local Compose URL as a public deployed URL.
