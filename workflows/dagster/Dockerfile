# workflows/dagster/Dockerfile
FROM python:3.10-slim

# uv (pinned) - installs exactly what uv.lock specifies
COPY --from=ghcr.io/astral-sh/uv:0.8.13 /uv /uvx /bin/

WORKDIR /app

# No apt packages needed: every locked dependency ships a Linux wheel (psycopg2-binary
# bundles libpq), and the compose healthchecks use Python instead of curl.

# The environment lives outside /app so compose's code mounts can never hide it
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:$PATH"

# Dependencies first (cached until pyproject.toml / uv.lock change)
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project --no-cache

# Then the pipeline code, installed editable (so compose's dev mount of
# ./dagster_pipeline is what actually runs)
COPY dagster_pipeline/ /app/dagster_pipeline/
RUN uv sync --frozen --no-dev --no-cache

# Create storage directories for Dagster
RUN mkdir -p /app/dagster_home

# Set Python path (redundant with editable install, but kept for clarity)
ENV PYTHONPATH=/app

# Expose ports
## for Webserver
EXPOSE 3004
## for gRPC
EXPOSE 4000

# Default command (will be overridden in docker-compose)
CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3004"]
