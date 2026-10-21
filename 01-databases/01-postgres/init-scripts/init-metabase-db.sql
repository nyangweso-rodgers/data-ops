-- Metabase application database
-- Stores Metabase's own config/metadata (dashboards, questions, users, settings).
-- Metabase creates its tables here via Liquibase migrations on first boot;
-- it does NOT create the database itself, so it must exist beforehand.
-- NOTE: docker-entrypoint-initdb.d scripts only run on a fresh (empty) data volume.
CREATE DATABASE local_metabase;
