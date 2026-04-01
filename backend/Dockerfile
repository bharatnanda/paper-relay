FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/appuser \
    XDG_CACHE_HOME=/home/appuser/.cache \
    UV_CACHE_DIR=/home/appuser/.cache/uv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:/root/.local/bin:$PATH"

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.6.10

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -m appuser

COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

COPY --chown=appuser:appuser . .
RUN uv sync --no-dev --no-install-project
RUN mkdir -p /home/appuser/.cache/uv && chown -R appuser:appuser /home/appuser /app

USER appuser

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
