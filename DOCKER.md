# Local Docker Stack

Local containerization assets are split by service:

- `docker-compose.yml` - local stack orchestration (`api`, optional `frontend`)
- `apps/api/Dockerfile` - FastAPI API image
- `apps/frontend/Dockerfile` - React frontend static image (optional)
- `apps/frontend/nginx.conf` - Nginx SPA fallback config

## Prerequisites

- Docker Desktop / Docker Engine
- Docker Compose v2 (`docker compose`)

## Run backend stack (API)

```bash
docker compose up --build
```

Useful URLs:

- API health: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

## Run full stack including frontend

```bash
docker compose --profile frontend up --build
```

Frontend URL:

- `http://localhost:3000`

## Stop and remove containers

```bash
docker compose down
```

## Optional helper commands

```bash
docker compose config
docker compose build
docker compose ps
docker compose logs -f
```

## Notes

- This setup is local-only and does not include external deployment services.
