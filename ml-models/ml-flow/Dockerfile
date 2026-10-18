# ml-models/ml-flow/Dockerfile - MLflow tracking server
FROM python:3.10-slim

# uv (pinned) - installs exactly what uv.lock specifies
COPY --from=ghcr.io/astral-sh/uv:0.8.13 /uv /uvx /bin/

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

# Overridden by docker-compose (backend store / artifacts come from env there)
CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"]
