FROM python:3.12-slim AS base

# Install curl (for uv installer) and system deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libc6-dev \
    libpq-dev \
    python3-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY ./ai-service/pyproject.toml ./ai-service/uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY ./ai-service/src .
COPY ./utils ./utils

ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

