FROM mysql:9.2.0

COPY ./init-scripts/init-mysql-db.sql /docker-entrypoint-initdb.d/
COPY ./init-scripts/init-mysql-users.sql /docker-entrypoint-initdb.d/

# Expose the default MySQL port
EXPOSE 3306