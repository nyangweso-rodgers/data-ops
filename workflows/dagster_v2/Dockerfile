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

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy pipeline code
COPY dagster_pipeline/ /app/dagster_pipeline/

# Create storage directories for Dagster
# Create only the dagster_home directory (no subdirectories needed)
RUN mkdir -p /app/dagster_home

# Set Python path
ENV PYTHONPATH=/app

# Expose Dagit port
EXPOSE 3004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/server_info || exit 1

# Default command (will be overridden in docker-compose)
CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3004"]