# dagster_pipeline/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install Dagster and dependencies
RUN pip install dagster dagster-webserver dagster-postgres sqlalchemy clickhouse-connect

# Copy your pipeline code
COPY ./etl-pipeline.py /app/

# Expose Dagit port
EXPOSE 3004

# Run dagster-webserver with the file specified
CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3004", "-f", "etl-pipeline.py"]