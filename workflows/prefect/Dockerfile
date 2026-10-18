# Official Prefect image, pinned - keep in sync with prefect== in pyproject.toml
FROM prefecthq/prefect:3.4.20-python3.11

# Set working directory
WORKDIR /app

# No apt packages needed: every locked dependency ships a Linux wheel (psycopg2-binary
# bundles libpq), and the compose healthcheck uses Python instead of curl.

# Install exactly what uv.lock specifies. The base image ships uv and sets
# UV_SYSTEM_PYTHON=1, so this installs into the same environment as Prefect itself.
COPY pyproject.toml uv.lock /app/
RUN uv export --frozen --no-dev --no-hashes -o /tmp/requirements.txt && \
    uv pip install --no-cache -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Optional: Copy custom scripts or configs
# COPY ./my_scripts /app/my_scripts

# Copy flows directory into the image
COPY flows/ /app/flows/
COPY tasks /app/tasks/
COPY deployments /app/deployments/

# Set environment variables (optional, can override in docker-compose.yml)
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app