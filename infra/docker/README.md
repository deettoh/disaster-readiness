# Local Docker Stack

This folder contains local containerization assets for the app:

- `api.Dockerfile` - FastAPI API image
- `worker.Dockerfile` - RQ worker image
- `frontend.Dockerfile` - React frontend static image (optional)
- `frontend.nginx.conf` - Nginx SPA fallback config
- `docker-compose.yml` - local stack orchestration (`redis`, `api`, `worker`, optional `frontend`)

## Prerequisites

- Docker Desktop / Docker Engine
- Docker Compose v2 (`docker compose`)

## Run backend stack (API + worker + Redis)

```bash
make docker-up
```

Useful URLs:

- API health: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

## Run full stack including frontend

```bash
make docker-up-frontend
```

Frontend URL:

- `http://localhost:3000`

## Stop and remove containers

```bash
make docker-down
```

## Optional helper commands

```bash
make docker-config
make docker-build
make docker-ps
make docker-logs
```

## Direct docker compose commands (equivalent)

```bash
docker compose -f infra/docker/docker-compose.yml up --build
docker compose -f infra/docker/docker-compose.yml --profile frontend up --build
docker compose -f infra/docker/docker-compose.yml down
```

## Notes

- This setup is local-only and does not include external deployment services.
- Worker queue defaults are wired to local Redis (`redis://redis:6379/0`).
