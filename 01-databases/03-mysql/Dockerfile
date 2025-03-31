FROM mysql:9.2.0

COPY ./init-scripts/init-open-metadata-db.sql /docker-entrypoint-initdb.d/

# Expose the default MySQL port
EXPOSE 3306