# Backend API (FastAPI)

The `apps/api/` service is the core backend for the Hyperlocal Disaster Readiness platform. It provides RESTful endpoints for hazard report submission, image processing orchestration, hazard/readiness data retrieval, routing, alerts, and weather snapshots.

## Package Layout

```
apps/api/src/app/
├── main.py                 # FastAPI app factory and entrypoint
├── api/
│   ├── router.py           # Top-level versioned router (/api/v1)
│   ├── dependencies.py     # DI wiring (backend selection, rate limits)
│   └── routes/             # Endpoint modules (reports, hazards, readiness, alerts, routing, weather, health)
├── core/
│   ├── config.py           # Pydantic settings (env-driven)
│   ├── logging.py          # Structured logging setup
│   ├── exceptions.py       # Custom exception definitions
│   ├── exception_handlers.py
│   └── upload_validation.py
├── db/
│   ├── models/             # SQLAlchemy ORM models (report, image, grid_cell, readiness_score, alert)
│   └── session.py          # Session factory
├── repositories/           # Data-access layer (SQL/ORM queries)
├── schemas/                # Pydantic request/response schemas
└── services/               # Business logic, orchestration, image processing, routing adapter, weather
```

## API Endpoints

All endpoints live under the `/api/v1` prefix (configurable via `API_PREFIX`).

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/info` | API metadata |
| `POST` | `/api/v1/reports` | Create hazard report metadata |
| `POST` | `/api/v1/reports/{id}/image` | Upload report image (triggers background processing) |
| `GET` | `/api/v1/reports/{id}/status` | Get report processing status |
| `POST` | `/api/v1/reports/{id}/processing-result` | Manual processing result callback |
| `GET` | `/api/v1/hazards` | List hazard predictions (map layer) |
| `GET` | `/api/v1/readiness` | List readiness scores per neighborhood |
| `GET` | `/api/v1/alerts` | List active alerts |
| `GET` | `/api/v1/route` | Compute evacuation route (pgRouting) |
| `GET` | `/api/v1/weather` | Current weather snapshot |

## Key Configuration

Settings are loaded from environment variables (see `.env.example` at project root):

| Variable | Purpose | Default |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL connection string | *(required)* |
| `DATA_BACKEND` | Data source: `mock` or `sql` | `mock` |
| `ROUTING_BACKEND` | Routing source: `mock` or `sql` | `mock` |
| `ROUTING_ALGORITHM` | `dijkstra` or `astar` | `dijkstra` |
| `QUEUE_BACKEND` | Job processing: `mock` or `in_process` | `mock` |
| `WEATHER_BACKEND` | Weather source: `mock` or `live` | `mock` |
| `SUPABASE_URL` | Supabase project URL | — |
| `SUPABASE_SECRET_KEY` | Supabase service key (image uploads) | — |

## Running

### Without Docker

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir apps/api/src
```

### With Docker

```bash
docker compose up --build
```

API docs available at `http://localhost:8000/docs` (Swagger) and `http://localhost:8000/redoc`.

## Image Processing

Image processing (hazard classification + privacy redaction) runs as in-process background jobs inside the API container. Set `QUEUE_BACKEND=in_process` to enable. The pipeline:

1. Validates and accepts uploaded image
2. Runs EfficientNet-B0 hazard classification
3. Runs face (RetinaFace) + plate (YOLOv8) redaction
4. Uploads redacted image to Supabase Storage
5. Writes classification results to `hazard_predictions`
6. Triggers road penalty updates, readiness recomputation, and alert generation

See [`ai/classification/README.md`](../../ai/classification/README.md) and [`ai/redaction/README.md`](../../ai/redaction/README.md) for model details.
