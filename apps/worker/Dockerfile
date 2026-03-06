# Worker Dockerfile for RQ background job processing.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=2.3.1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONPATH=/app/apps/worker/src:/app/ai/classification/src \
    REDIS_URL=redis://redis:6379/0 \
    QUEUE_NAME=image-processing \
    WORKER_API_BASE_URL=http://api:8000/api/v1 \
    WORKER_REDACTED_OUTPUT_DIR=/app/data/processed/redacted

WORKDIR /app

RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root

COPY apps/worker/src ./apps/worker/src
COPY ai/classification/src ./ai/classification/src
COPY ai/classification/models ./ai/classification/models

CMD ["python", "-m", "worker.runner"]
