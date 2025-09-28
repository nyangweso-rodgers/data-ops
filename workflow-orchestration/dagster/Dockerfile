# dagster_pipeline/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install \
    dagster==1.11.9 \
    dagster-webserver==1.11.9 \
    dagster-postgres==0.27.9 \
    sqlalchemy \
    clickhouse-connect \
    psycopg2-binary \
    mysql-connector-python==8.0.33 \
    pandas \
    pyyaml

# Copy your pipeline code
COPY dagster_pipeline/ /app/dagster_pipeline/

# Create storage directories for Dagster
RUN mkdir -p /app/dagster_home/storage/logs
RUN mkdir -p /app/dagster_home/storage/runs
RUN mkdir -p /app/dagster_home/storage/events
RUN mkdir -p /app/dagster_home/storage/schedules

# Set Python path
ENV PYTHONPATH=/app

# Expose Dagit port
EXPOSE 3004

# Default command (will be overridden in docker-compose)
CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3004"]