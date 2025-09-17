# Use the official Postgres image from Docker Hub
FROM postgres:14.18

# Add custom initialization scripts to create multiple databases
COPY ./init-scripts/init-users-db.sql /docker-entrypoint-initdb.d/

# Set PostgreSQL configuration options
CMD ["postgres", "-c", "max_replication_slots=10", "-c", "wal_level=logical", "-c", "max_wal_senders=10"]

# Expose the port Postgres will listen on
EXPOSE 5432