-- Redash application database
-- Stores Redash's own metadata (queries, dashboards, data source connections, users).
-- Redash does NOT create the database itself, so it must exist beforehand, and
-- (unlike Superset/Metabase) it does not run its schema migrations automatically
-- on boot either -- run `make redash-init-db` once after the first `make redash-dev-up`.
-- NOTE: docker-entrypoint-initdb.d scripts only run on a fresh (empty) data volume.
CREATE DATABASE local_redash;
