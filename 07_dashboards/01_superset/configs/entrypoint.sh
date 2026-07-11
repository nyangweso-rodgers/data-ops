#!/bin/bash
# entrypoint.sh

echo "APACHE_SUPERSET_ADMIN_USERNAME: ${APACHE_SUPERSET_ADMIN_USERNAME}"
echo "APACHE_SUPERSET_ADMIN_PASSWORD: ${APACHE_SUPERSET_ADMIN_PASSWORD}"
echo "APACHE_SUPERSET_PORT: ${APACHE_SUPERSET_PORT}"

# Apply database migrations
superset db upgrade

# Check if the admin user exists; create or reset if needed
if ! superset fab list-users | grep -q "^${APACHE_SUPERSET_ADMIN_USERNAME}$"; then
  superset fab create-admin \
    --username "${APACHE_SUPERSET_ADMIN_USERNAME}" \
    --firstname "Admin" \
    --lastname "User" \
    --email "${APACHE_SUPERSET_ADMIN_USERNAME}@example.com" \
    --password "${APACHE_SUPERSET_ADMIN_PASSWORD}"
  echo "Created admin user ${APACHE_SUPERSET_ADMIN_USERNAME}."
else
  superset fab reset-password \
    --username "${APACHE_SUPERSET_ADMIN_USERNAME}" \
    --password "${APACHE_SUPERSET_ADMIN_PASSWORD}"
  echo "Reset password for admin user ${APACHE_SUPERSET_ADMIN_USERNAME}."
fi

# Initialize roles and permissions
superset init

# Start Superset
exec superset run -h 0.0.0.0 -p "${APACHE_SUPERSET_PORT}" --with-threads --reload