# Use the official Postgres image from Docker Hub
FROM postgres:latest
#image: postgres:14-alpine

# Set environment variables (optional, can also be passed via docker-compose.yml)
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=mypassword

# Add custom initialization scripts to create multiple databases
COPY ./init-scripts/init-sales-database.sql /docker-entrypoint-initdb.d/
COPY ./init-scripts/init-users-database.sql /docker-entrypoint-initdb.d/

# Set PostgreSQL configuration options
CMD ["postgres", "-c", "max_replication_slots=10", "-c", "wal_level=logical", "-c", "max_wal_senders=10"]

# Expose the port Postgres will listen on
EXPOSE 5432