# Architecture

## Table of Contents

1. [Compose convention: base / dev / prod](#compose-convention-base--dev--prod)
2. [Known issues backlog](#known-issues-backlog)
   - [Cross-cutting](#cross-cutting)
   - [Kafka](#kafka)
   - [Grafana stack](#grafana-stack)
   - [Superset](#superset)
   - [Redash](#redash)
   - [Metabase](#metabase)
   - [ClickHouse](#clickhouse)
   - [Amundsen](#amundsen)
   - [n8n](#n8n)
   - [Prefect](#prefect)
3. [Required env vars for prod](#required-env-vars-for-prod)

## Compose convention: base / dev / prod

Each stack lives in its own folder with:

| File                               | Purpose                                                                                                   |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `docker-compose-<stack>.base.yml`  | Shared definition. Works on its own, and the root `docker-compose.yml` `extends` it.                       |
| `docker-compose-<stack>.dev.yml`   | Dev override: no auto-restart, debug-friendly logging, source/config mounted for live edits.              |
| `docker-compose-<stack>.prod.yml`  | Prod override: RDS for metadata DBs, required secrets (`${VAR:?}`), restart policies, limits, log rotation. |
| `Makefile`                         | `dev-*`, `prod-*`, `build`/`pull` targets plus stack-specific extras.                                      |

The root `Makefile` delegates `make <stack>-<target>` to the stack Makefile (e.g. `make superset-dev-up`).

**Converted:** airflow, dagster, grafana, metabase, redash, superset, clickhouse, kafka, amundsen, n8n, prefect.

**Rules of thumb**

- A base file must not `depends_on` a service defined in another compose file: standalone validation fails, even with `required: false`. Declare those dependencies in the root `docker-compose.yml`, which defines every service.
- Named volumes use a pinned `name:` so the root project and the stack project share the same data.
- Admin/UI tools that shouldn't run in prod get `profiles: ["tools"]` in the prod override.

## Known issues backlog

Status as of 2026-10-18. All files pass `docker-compose config`, but **none of the converted stacks have been built or started yet.** Most items below will only show up at `up` time.

### Cross-cutting

| #   | Issue                                                                                                                                                                                                              | Impact                                                                                     | Suggested fix                                                                                                         |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| X1  | Containers have fixed `container_name`s. The root project (`data-ops`) and each stack project (folder name) both try to own them.                                                                                  | `make <stack>-dev-up` fails with "container name already in use" if started from root first. | Pick one entry point per stack, or drop `container_name` and rely on service DNS names.                               |
| X2  | Cross-file `depends_on` exists only in the root compose.                                                                                                                                                            | Standalone `make <stack>-dev-up` doesn't wait for postgres/redis/neo4j/elasticsearch.       | Start dependencies first (noted in each dev file header), or add a wait-for step in entrypoints.                        |
| X3  | Ports published in base can't be removed in prod overrides (`!reset` needs a newer compose than we can assume).                                                                                                    | Prometheus, Loki, exporter, ClickHouse, Kafka ports are exposed in prod.                   | Restrict at firewall/security group, or require compose ≥ 2.24 and use `ports: !reset []`.                               |
| X4  | `.env` has `REDIS_HOST=localhost` (for host-side scripts).                                                                                                                                                          | Using `${REDIS_HOST}` inside containers breaks redis connections.                         | Keep containers on the hardcoded `redis` host, or add a separate `REDIS_CONTAINER_HOST`.                                |
| X5  | Superset, Redash and Prefect use the shared redis container in prod.                                                                                                                                               | No managed/HA redis in prod.                                                               | Move to ElastiCache (TODOs in the prod files).                                                                         |
| X6  | Several images are unpinned `:latest`: `prom/prometheus`, `prometheuscommunity/postgres-exporter`, `provectuslabs/kafka-ui`, `debezium/connect`, `debezium/debezium-ui`, `spoonest/clickhouse-tabix-web-client`. | Non-reproducible builds.                                                                   | Pin versions.                                                                                                          |
| X7  | Stacks not yet converted: postgres, mysql, redis, elasticsearch/kibana, neo4j, trino, open-metadata, taipy, docusaurus, ml-flow, ml models, open-webui.                                                             | Inconsistent convention.                                                                   | Convert as they're touched.                                                                                            |
| X8  | Dagster's root targets use `dagster-local-*`; every other stack uses `<stack>-dev-*`.                                                                                                                              | Naming inconsistency.                                                                      | Rename to `dagster-dev-*`.                                                                                              |

### Kafka

| #   | Issue                                                                                                                                       | Impact                                                    | Suggested fix                                                                   |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------- |
| K1  | `kafka-ui` and `debezium-ui` both publish host port `8082`.                                                                                 | Second container fails to start.                          | Move debezium-ui to another host port.                                         |
| K2  | `debezium-ui` maps `8082:8082`, but the app listens on `8080`.                                                                               | UI unreachable.                                           | Map `<host>:8080`.                                                              |
| K3  | `debezium-ui` uses `KAFKA_CONNECT_URIS: http://debezium:8084`, but the container is `debezium-connect`.                                     | UI can't reach Connect.                                   | `http://debezium-connect:8084` (and check Connect actually listens on 8084).     |
| K4  | `KAFKA_DEFAULT_REPLICATION_FACTOR: "2"` and debezium `*_STORAGE_REPLICATION_FACTOR: 2` on a single broker.                                  | Auto-created topics and debezium internal topics fail.    | Set to `1` while there's one broker.                                            |
| K5  | `cp-kafka-connect` mounts `./cp-kafka-connect/plugins/bigquery-keyfile.json`, a path that doesn't exist (connector lives in `01-connectors/01-cp-kafka-connect/`). | Docker creates an empty directory in place of the keyfile. | Fix the path, and keep the keyfile out of git.                                  |
| K6  | `cp-kafka-connect` has `CONNECT_ZOOKEEPER_CONNECT: zookeeper:2181`, but the container is `kafka-zookeeper`.                                  | Wrong host if anything uses it.                           | `kafka-zookeeper:2181`, or remove (Connect doesn't need ZooKeeper).              |
| K7  | Connect converters point at `http://schema-registry:8081`, but the container is `kafka-schema-registry`.                                     | Schema-registry lookups fail.                             | `http://kafka-schema-registry:8081`.                                            |
| K8  | Connect and debezium need postgres, but the dependency was removed from base (it pointed at a non-existent `postgres-db` service).          | Must start postgres manually first.                       | Neither is in the root compose. Add them there with `depends_on: postgres` if needed. |
| K9  | `SCHEMA_REGISTRY_DEBUG` now defaults to `false` in base (dev turns it on).                                                                   | Behaviour change for root-compose runs.                   | None needed. Noted for awareness.                                               |

### Grafana stack

| #   | Issue                                                                                                          | Impact                                    | Suggested fix                                        |
| --- | -------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | ---------------------------------------------------- |
| G1  | `prometheus.yml` scrapes `apache-kafka:9999`, but the container is `kafka` and JMX on 9999 isn't configured.    | Scrape target permanently down.           | Point at `kafka` and enable a JMX exporter, or drop the job. |
| G2  | `scrape_interval: 3600s`.                                                                                      | Hourly metrics only; most dashboards look empty. | Lower (e.g. `30s`) unless that was a deliberate cost choice. |
| G3  | Grafana's healthcheck uses `wget`, which hasn't been verified in `grafana/grafana:12.0.2`.                     | Healthcheck may always fail.              | Verify after first build; switch to `curl` if needed. |
| G4  | Grafana's own DB is sqlite on `grafana-vol`.                                                                   | Single-instance only, backups by volume.  | Optional RDS block is commented in the prod file.    |
| G5  | `provisioning/datasources/pg-datasource.yml` is empty (`apiVersion: 1` only).                                  | No Postgres datasource provisioned.       | Fill in or delete.                                   |

### Superset

| #   | Issue                                                                                     | Impact                               | Suggested fix                                                     |
| --- | ----------------------------------------------------------------------------------------- | ------------------------------------ | ----------------------------------------------------------------- |
| S1  | `superset_config.py` hardcodes port `5432` and has no `sslmode` in `SQLALCHEMY_DATABASE_URI`. | Prod RDS connection is unencrypted / not configurable. | Read port + sslmode from env (e.g. `?sslmode=require`). |

### Redash

| #   | Issue                                                                                                              | Impact                          | Suggested fix                          |
| --- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------- | -------------------------------------- |
| R1  | Default host port `5001` (`REDASH_PORT`) is the same as Amundsen search's default (`SEARCH_PORT`).                  | Port clash if both run on defaults. | Give one of them a different default.  |
| R2  | Redash doesn't migrate its schema on boot.                                                                         | Fresh DB needs a manual step.   | `make redash-init-db` (dev) / `make redash-prod-init-db` (prod), once per database. |

### Metabase

| #   | Issue                                                                                                   | Impact                         | Suggested fix               |
| --- | ------------------------------------------------------------------------------------------------------- | ------------------------------ | --------------------------- |
| M1  | Prod uses `MB_DB_CONNECTION_URI` (with `sslmode=require`) together with separate `MB_DB_USER`/`MB_DB_PASS`. Unverified on v0.61. | Prod may fail to connect to RDS. | Verify on first prod start. |

### ClickHouse

| #   | Issue                                                                                    | Impact                       | Suggested fix                                     |
| --- | ---------------------------------------------------------------------------------------- | ---------------------------- | ------------------------------------------------- |
| C1  | Tabix receives the default user's password via env.                                       | Credentials exposed to a web client. | Disabled in prod (`profiles: ["tools"]`). Keep it dev-only. |
| C2  | Native (9000), HTTP (8123), interserver (9009) and keeper (9181) ports all published.    | Larger attack surface in prod. | See X3.                                         |

### Amundsen

| #   | Issue                                                                                     | Impact                                  | Suggested fix                                         |
| --- | ----------------------------------------------------------------------------------------- | --------------------------------------- | ----------------------------------------------------- |
| A1  | Frontend runs `amundsen_application.config.TestConfig` with no real auth.                  | Not production-ready.                   | Switch config class and wire auth before exposing it.  |
| A2  | neo4j credentials were hardcoded; base now uses `NEO4J_USER` / `NEO4J_PASSWORD` from `.env`. | Behaviour change if `.env` differs from the old hardcoded values. | Confirm the values match the neo4j container.         |

### n8n

| #   | Issue                                                                                     | Impact                                  | Suggested fix                                |
| --- | ----------------------------------------------------------------------------------------- | --------------------------------------- | -------------------------------------------- |
| N1  | `N8N_BASIC_AUTH_*` is likely ignored in n8n 1.x (replaced by built-in user management).   | False sense of protection.              | Verify against the image version; remove if unused. |
| N2  | Prod sets `DB_POSTGRESDB_SSL_ENABLED: "true"`. Unverified for the n8n version in the Dockerfile. | RDS connection may not use TLS.         | Verify on first prod start.                  |
| N3  | `n8n-data` volume changed from `external: true` to `name: n8n-data` in base.              | Compose now creates it if missing instead of erroring. | None needed. Noted for awareness.            |

### Prefect

| #   | Issue                                                                                      | Impact                                         | Suggested fix                                     |
| --- | ------------------------------------------------------------------------------------------ | ---------------------------------------------- | ------------------------------------------------- |
| P1  | Worker used to mount host `/flows` over `/app/flows`. Base now uses the flows baked into the image; dev mounts `./flows`, `./tasks`, `./deployments`. | Behaviour change: prod needs a rebuild to pick up new flows. | None needed. Noted for awareness.                 |
| P2  | Prod needs `PREFECT_RDS_DB_URL` (asyncpg + SSL) and `PREFECT_PUBLIC_URL`. Neither is in `.env` yet. | `make prefect-prod-up` refuses to start.       | Add to `.env` (see below).                        |

## Required env vars for prod

Prod overrides either refuse to start without these (`:?`) or fall back to empty values. "In `.env`" reflects the root `.env` on 2026-10-18; the local (dev) values still need prod equivalents.

| Variable                                      | Used by                                              | In `.env`? |
| --------------------------------------------- | ---------------------------------------------------- | ---------- |
| `RDS_HOSTNAME`, `RDS_PORT`, `RDS_USERNAME`, `RDS_PASSWORD` | metabase, redash, superset, n8n, grafana exporter (also airflow, dagster) | No |
| `METABASE_RDS_DB_NAME`, `REDASH_RDS_DB_NAME`, `SUPERSET_RDS_DB_NAME`, `N8N_RDS_DB_NAME` | optional, default to the service name | No |
| `PREFECT_RDS_DB_URL`, `PREFECT_PUBLIC_URL`    | prefect (required)                                   | No         |
| `KAFKA_ADVERTISED_HOST`                       | kafka (required)                                     | No         |
| `GRAFANA_ROOT_URL`                            | grafana                                              | No         |
| `WEBHOOK_URL`, `N8N_ENCRYPTION_KEY`           | n8n (required)                                       | Yes (dev values) |
| `MB_SITE_URL`                                 | metabase (required)                                  | Yes (dev value)  |
