#!/bin/bash
set -euo pipefail

DB_NAME="${APACHE_AIRFLOW_POSTGRES_DB:-apache_airflow}"
export PGPASSWORD="${POSTGRES_PASSWORD}"

echo "Initializing Airflow environment..."

# Wait for Postgres to be ready with retry logic
max_retries=30
count=0
until psql -h postgres-db -U "${POSTGRES_USER}" -d "postgres" -c '\q' 2>/dev/null || [ "$count" -eq "$max_retries" ]; do
  echo "Waiting for Postgres server to be ready... ($count/$max_retries)"
  sleep 2
  count=$((count + 1))
done

if [ "$count" -eq "$max_retries" ]; then
  echo "Error: Postgres server not ready after $max_retries attempts."
  exit 1
fi
echo "Postgres is ready."

# Create the Airflow metadata database if it doesn't exist
if ! psql -h postgres-db -U "${POSTGRES_USER}" -d "$DB_NAME" -c '\q' 2>/dev/null; then
  echo "Creating database $DB_NAME..."
  psql -h postgres-db -U "${POSTGRES_USER}" -d "postgres" -c "CREATE DATABASE $DB_NAME;" || {
    echo "Error: Failed to create database $DB_NAME."
    exit 1
  }
fi
echo "Database $DB_NAME exists or was created."

# Check if Airflow database is initialized
echo "Checking if Airflow database is initialized..."
if ! psql -h postgres-db -U "${POSTGRES_USER}" -d "$DB_NAME" -c "SELECT 1 FROM ab_user LIMIT 1" 2>/dev/null; then
  echo "Airflow database not initialized or corrupted. Running 'airflow db init'..."
  airflow db init || {
    echo "Error: Failed to initialize database with 'airflow db init'."
    exit 1
  }
  echo "Airflow database initialized successfully."
else
  echo "Airflow database already initialized. Checking for migrations..."
fi

# Always apply migrations to ensure schema is up-to-date
echo "Applying any database migrations..."
airflow db migrate || {
  echo "Error: Failed to apply migrations with 'airflow db migrate'."
  exit 1
}
echo "Database schema up-to-date."

# Create Airflow admin user if it doesn't exist
echo "Checking and creating admin user if necessary..."
if ! airflow users list 2>/dev/null | grep -q "${APACHE_AIRFLOW_ADMIN_USERNAME}"; then
  echo "Creating admin user: ${APACHE_AIRFLOW_ADMIN_USERNAME}"
  airflow users create \
    --username "${APACHE_AIRFLOW_ADMIN_USERNAME}" \
    --firstname "${APACHE_AIRFLOW_FIRST_NAME:-Admin}" \
    --lastname "${APACHE_AIRFLOW_LAST_NAME:-User}" \
    --password "${APACHE_AIRFLOW_ADMIN_PASSWORD}" \
    --role "${APACHE_AIRFLOW_ADMIN_ROLE:-Admin}" \
    --email "${APACHE_AIRFLOW_ADMIN_EMAIL}" || {
      echo "Error: Failed to create admin user."
      exit 1
    }
  echo "Admin user created successfully."
else
  echo "Admin user ${APACHE_AIRFLOW_ADMIN_USERNAME} already exists."
fi

echo "Initialization complete."