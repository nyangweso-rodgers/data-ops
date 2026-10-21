-- Superset application database
-- Stores Superset's own metadata (dashboards, charts, database connections, users).
-- Superset creates its tables here via Alembic migrations on first boot;
-- it does NOT create the database itself, so it must exist beforehand.
-- NOTE: docker-entrypoint-initdb.d scripts only run on a fresh (empty) data volume.
CREATE DATABASE local_superset;