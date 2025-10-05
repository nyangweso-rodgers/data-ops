#!/bin/bash
set -euo pipefail

# Set core environment variables
export AIRFLOW__CORE__SQL_ALCHEMY_CONN="postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres-db/${APACHE_AIRFLOW_POSTGRES_DB:-apache_airflow}"
echo "Airflow SQL Alchemy connection set to: $AIRFLOW__CORE__SQL_ALCHEMY_CONN"
echo "Using Fernet key: $AIRFLOW__CORE__FERNET_KEY"

# Run the initialization script
/opt/airflow/scripts/init.sh

# Print startup information
echo "Starting Airflow ${1:-} service..."

# Execute the command passed to the entrypoint
exec airflow "$@"