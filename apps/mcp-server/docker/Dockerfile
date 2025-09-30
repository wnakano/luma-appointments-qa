# ---------- Builder ----------
FROM python:3.11-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app/mcp-server

COPY ./mcp-server/pyproject.toml ./pyproject.toml
COPY ./mcp-server/uv.lock ./uv.lock

RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev curl \
  && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/mcp-server/.venv /app/.venv

WORKDIR /app

COPY ./mcp-server/src .
COPY ./utils ./utils

RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
