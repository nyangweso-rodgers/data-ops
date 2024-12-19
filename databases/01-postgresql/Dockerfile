# Use the official Postgres image from Docker Hub
FROM postgres:latest

# Set environment variables (optional, can also be passed via docker-compose.yml)
ENV POSTGRES_USER=admin
ENV POSTGRES_PASSWORD=mypassword
#ENV POSTGRES_DB=mydb

# You can also add custom initialization scripts if needed
# COPY ./init.sql /docker-entrypoint-initdb.d/

# Copy the custom initialization scripts into the container
COPY ./init-scripts/ /docker-entrypoint-initdb.d/

# Expose the port Postgres will listen on
EXPOSE 5432