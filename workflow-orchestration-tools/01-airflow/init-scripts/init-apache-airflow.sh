#!/bin/bash

# Load the root .env file (from host's project root)
set -a
source /opt/airflow/root.env  # Will mount this path in docker-compose
set +a

# Wait for Postgres to be ready
until psql -h postgres-db -U "${POSTGRES_USER}" -d "apache_airflow" -c '\q' 2>/dev/null; do
  echo "Waiting for Postgres to be ready..."
  sleep 2
done

# Initialize the database if not already initialized
if [ ! -f "/opt/airflow/airflow.db.init" ]; then
    echo "Initializing the Airflow database..."
    airflow db migrate
    touch "/opt/airflow/airflow.db.init"
fi

# Create admin user with .env variables
if [ -z "$(airflow users get-user -u "${APACHE_AIRFLOW_ADMIN_USERNAME}" 2>/dev/null)" ]; then
    echo "Creating admin user: ${APACHE_AIRFLOW_ADMIN_USERNAME}"
    airflow users create \
        --username "${APACHE_AIRFLOW_ADMIN_USERNAME}" \
        --password "${APACHE_AIRFLOW_ADMIN_USERNAME}" \
        --role "${APCHE_AIRFLOW_ADMIN_ROLE:-Admin}" \
        --email "${APACHE_AIRFLOW_ADMIN_EMAIL:-admin@example.com}"
fi

# Start the requested Airflow component
exec airflow "$@"