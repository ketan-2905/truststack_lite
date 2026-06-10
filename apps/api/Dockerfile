# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps: curl for healthcheck, libpq for psycopg, build tools for argon2.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl gcc libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better layer caching. A stub package is
# created so setuptools can build metadata before the real source is copied;
# the editable install then picks up the real source after COPY.
COPY pyproject.toml ./
RUN mkdir -p app && touch app/__init__.py \
    && pip install --upgrade pip \
    && pip install -e ".[dev]"

# Copy application source (overlays the stub for the editable install).
COPY . .

EXPOSE 8000

# Default command runs the API. Overridden by the worker service.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
