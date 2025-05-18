# dagster_pipeline/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install curl and Dagster dependencies
RUN apt-get update && apt-get install -y curl \
    && pip install --upgrade pip \
    && pip install dagster==1.5.9 dagster-webserver==1.5.9 dagster-postgres==0.21.9 sqlalchemy clickhouse-connect

# Copy your pipeline code
COPY ./etl-pipeline.py /app/

# Expose Dagit port
EXPOSE 3004

# Run dagster-webserver with the file specified
#CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3004", "-f", "etl-pipeline.py"]

# or
# No CMD - let docker-compose override it