# Use the official Postgres image from Docker Hub
FROM postgres:latest

# Set environment variables (optional, can also be passed via docker-compose.yml)
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=mypassword
#ENV POSTGRES_DB=users

# Add custom initialization script to create multiple databases
COPY ./init-scripts/init-databases-and-tables.sql /docker-entrypoint-initdb.d/

# Expose the port Postgres will listen on
EXPOSE 5432