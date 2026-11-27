-- General-purpose local database for ad-hoc work and experiments.
-- NOTE: docker-entrypoint-initdb.d scripts only run on a fresh (empty) data volume.
-- On an already-running container, apply manually:
--   docker exec postgres psql -U postgres -d postgres -f /docker-entrypoint-initdb.d/init-local-postgres-db.sql
-- Postgres has no CREATE DATABASE IF NOT EXISTS, so \gexec keeps this safe to re-run.
SELECT 'CREATE DATABASE local_postgres'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'local_postgres')\gexec
