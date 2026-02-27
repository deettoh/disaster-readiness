FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=2.3.1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONPATH=/app/apps/worker/src \
    REDIS_URL=redis://redis:6379/0 \
    QUEUE_NAME=image-processing

WORKDIR /app

RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root

COPY apps/worker/src ./apps/worker/src

CMD ["python", "-m", "worker.runner"]
