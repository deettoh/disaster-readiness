# Worker Dockerfile for RQ background job processing.

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=2.3.1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring

WORKDIR /app

RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock ./
RUN poetry install --only main,worker --no-root

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/apps/worker/src:/app/ai/classification/src \
    PATH=/app/.venv/bin:$PATH \
    REDIS_URL=redis://redis:6379/0 \
    QUEUE_NAME=image-processing \
    WORKER_API_BASE_URL=http://api:8000/api/v1 \
    WORKER_REDACTED_OUTPUT_DIR=/app/data/processed/redacted

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY apps/worker/src ./apps/worker/src
COPY ai/classification/src ./ai/classification/src
COPY ai/classification/models ./ai/classification/models

CMD ["python", "-m", "worker.runner"]
