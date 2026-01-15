# dagster_pipeline/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
# gcc, g++, libpq-dev (compilation tools)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml first (for Docker layer caching)
# This layer will only rebuild if pyproject.toml changes
COPY pyproject.toml README.md ./

# Install Python dependencies
# Note: We need to copy a minimal package structure for pip to recognize it
COPY dagster_pipeline/__init__.py /app/dagster_pipeline/__init__.py

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Now copy the full pipeline code
# This layer rebuilds whenever code changes, but dependencies are cached
COPY dagster_pipeline/ /app/dagster_pipeline/

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