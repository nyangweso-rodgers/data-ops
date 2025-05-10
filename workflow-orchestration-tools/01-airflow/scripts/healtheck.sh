#!/bin/bash
set -euo pipefail

# Check if Airflow webserver is responding
if [[ "${1:-}" == "webserver" ]]; then
  curl -f "http://localhost:8080/health" || exit 1
elif [[ "${1:-}" == "scheduler" ]]; then
  # For scheduler, check if it's running by examining process
  pgrep -f "airflow scheduler" >/dev/null || exit 1
fi

# Check database connectivity
export PGPASSWORD="${POSTGRES_PASSWORD}"
psql -h postgres-db -U "${POSTGRES_USER}" -d "${APACHE_AIRFLOW_POSTGRES_DB:-apache_airflow}" -c '\q' || exit 1

exit 0