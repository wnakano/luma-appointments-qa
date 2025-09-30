FROM python:3.11-slim


WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY ./ui-service/pyproject.toml ./
RUN pip install uv && uv pip install --system -r pyproject.toml

COPY ./ui-service/src/ .
COPY ./utils ./utils

# RUN useradd -m -u 1000 chatbot && chown -R chatbot:chatbot /app
# USER chatbot

ENV PATH="/app/.venv/bin:${PATH}"
EXPOSE 8501


CMD ["streamlit", "run", "app.py"]
