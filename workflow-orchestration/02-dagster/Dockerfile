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
    dagster==1.5.9 \
    dagster-webserver==1.5.9 \
    dagit==1.5.9 \
    dagster-postgres==0.21.9 \
    sqlalchemy \
    clickhouse-connect \
    psycopg2-binary \
    mysql-connector-python==8.0.33
    # && apt-get remove -y gcc && apt-get autoremove -y \ # clean up unnecessary packages
    # && apt-get clean && rm -rf /var/lib/apt/lists/* # clean up apt cache

# Copy your pipeline code
COPY ./dagster-pipeline/etl-pipeline.py /app/dagster-pipeline/

# Expose Dagit port
EXPOSE 3004

# Default command (will be overridden in docker-compose)
CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3004"]