# Architecture

## Table of Contents

1. [Conventions](#conventions)
2. [Services](#services)
3. [Pending TODOs](#pending-todos)
   - [Cross-cutting](#cross-cutting)
   - [Databases](#databases)
   - [Messaging & warehouse](#messaging--warehouse)
   - [Orchestration & pipelines](#orchestration--pipelines)
   - [Dashboards](#dashboards)
   - [Metadata](#metadata)
   - [ML / AI & docs](#ml--ai--docs)

## Conventions

- **One stack per folder**, each with `docker-compose-<stack>.base.yml` (shared definition), `.dev.yml` (no auto-restart, live-edit mounts) and `.prod.yml` (RDS where a metadata DB exists, required secrets via `${VAR:?}`, restart policies, resource limits, log rotation).
- **Root `docker-compose.yml`** `extends` each stack's base file. Dependencies on services from *other* stacks (postgres, redis, mysql, neo4j, elasticsearch) are declared there, since a base file can't `depends_on` a service it doesn't define.
- **Makefiles:** `make <stack>-<target>` in the root delegates to `<stack-dir>/Makefile` (`dev-up`, `dev-up-build`, `dev-logs`, `prod-up`, ... ; `make <stack>-help` lists all).
- **Ports:** every host port is defined once, in the committed root `ports.env` (`<SERVICE>_HOST_PORT`, values unique). Compose maps `"${<SERVICE>_HOST_PORT:?see ports.env}:<container port>"` with no default, so a missing entry fails fast; the container port is set by the image and stays literal. Makefiles pass `--env-file .env --env-file ports.env` (registry wins) and `include` it for URLs; the root Makefile exports `COMPOSE_ENV_FILES=.env,ports.env` (for plain `docker-compose` by hand, export it in your shell). `make ports` fails on duplicates, hardcoded or defaulted host ports, and unregistered/unused entries.
- **Python (uv):** each Python service has its own `pyproject.toml` + `uv.lock` in its folder (airflow, dagster, prefect, ml-flow) and its image installs from that lock. They are deliberately separate resolutions, not one workspace: Airflow 2.x needs SQLAlchemy<2 while Dagster/Prefect need >=2. The root `pyproject.toml` is only for repo tooling (ruff, pytest, pre-commit), host-side scripts (provisioning) and the shared ruff config that projects `extend`. Airflow's image is the exception: Airflow's own pins come from the base image (`apache-airflow==$AIRFLOW_VERSION`); its `uv.lock` covers the `dataflow` package for local tests. `make py-sync` / `py-lock` / `py-lint` at the root; `make -C <project> lock` / `sync` per project.
- **Names:** every service sets `container_name`, and every service with `build:` also sets `image:` (named after the container). Otherwise Compose generates `<project>-<service>-1` container names and `<project>-<service>` image names.
- **Network:** every container joins the external `data-ops-network` and is reachable by container name.
- **Volumes:** named volumes use a pinned `name:` so root and stack-level runs share data.
- **Prod-only tooling** (admin UIs) is disabled in prod with `profiles: ["tools"]`.
- **Images:** use the official image directly and configure it in compose (`environment`, `command`, mounts, `healthcheck`). Add a Dockerfile only when the image itself must change: plugins/drivers (cp-kafka-connect, nifi, superset, grafana) or your own code/dependencies (airflow, dagster, prefect, ml-flow, docusaurus).

## Services

Host ports live only in [`ports.env`](../ports.env); `make ports` lists them with the file that publishes each. "Root" = included in the root `docker-compose.yml`.

| Stack | Path | Containers | State | Depends on | Prod backend | Root |
| --- | --- | --- | --- | --- | --- | --- |
| postgres | `01-databases/01-postgres` | postgres 14.18 | `postgres-data` | – | self-hosted | ✓ |
| mysql | `01-databases/mysql` | mysql 9.2.0 | `mysql-data` | – | self-hosted | ✓ |
| redis | `01-databases/redis` | redis, redisinsight (tools) | `redis-data` | – | self-hosted | ✓ |
| mongodb | `01-databases/mongodb` | mongo-db-community-server 7.0 | `mongo-db-community-server-volume` | – | self-hosted | – |
| elasticsearch | `01-databases/elasticsearch` | elasticsearch 9.2, kibana | `elasticsearch_data` | – | self-hosted | ✓ |
| neo4j | `01-databases/neo4j` | neo4j 4.4 | `neo4j_data` | – | self-hosted | ✓ |
| trino | `01-databases/trino` | trino 477 | `etc/catalog` | postgres | self-hosted | ✓ |
| kafka | `03_streaming/kafka` ([architecture](../03_streaming/kafka/docs/architecture.md)) | kafka (KRaft, no ZooKeeper), schema-registry, cp-kafka-connect, debezium-connect, kafka-ui (tools; also manages both Connect clusters) | `kafka-data` | postgres (connectors) | self-hosted | ✓ |
| clickhouse | `06_data_warehouse/clickhouse` | clickhouse-server 24.8, tabix (tools) | `clickhouse-server-data` | – | self-hosted | ✓ |
| airflow | `workflows/airflow` | webserver, scheduler (LocalExecutor) | metadata DB | postgres | RDS + S3 task logs | ✓ |
| dagster | `workflows/dagster` | gRPC server, webserver, daemon | metadata DB | postgres | RDS | ✓ |
| prefect | `workflows/prefect` | server, services, worker | metadata DB | postgres, redis | RDS | ✓ |
| n8n | `workflows/n8n` | n8n | `n8n-data` + DB | postgres | RDS | ✓ |
| nifi | `workflows/nifi` | nifi 2.3 | `nifi-vol`, `nifi-flows` | – | self-hosted | – |
| airbyte | `workflows/airbyte` | temporal, server, webapp, worker | DB | postgres | – (see AB1) | – |
| superset | `07_dashboards/superset` | superset | `superset-volume` + DB | postgres, redis (db 1) | RDS | ✓ |
| redash | `07_dashboards/redash` | server, scheduler, worker | DB | postgres, redis (db 2) | RDS | ✓ |
| metabase | `07_dashboards/metabase` | metabase 0.61 | DB | postgres | RDS | ✓ |
| grafana | `07_dashboards/grafana` | grafana, prometheus, loki, postgres-db-exporter | `grafana-vol`, `prometheus-vol`, `loki-vol` | postgres (exporter) | self-hosted, exporter → RDS | ✓ |
| amundsen | `metadata/amundsen` | frontend, search, metadata | – | neo4j, elasticsearch | self-hosted | ✓ |
| open-metadata | `metadata/open-metadata` | migrate job, server 1.6.7 | DB | mysql, elasticsearch | self-hosted | ✓ |
| ml-flow | `ml-models/ml-flow` | mlflow server | `./data` (sqlite + artifacts) | – | RDS + S3 | ✓ |
| open-webui | `ai/open-webui` | open-webui, ollama | `./data`, `ollama-data` + DB | postgres | RDS | ✓ |
| docusaurus | `10_documentation/docusaurus-site` | docusaurus (dev server / static serve) | – | – | static build | ✓ |


**Notes**

- **postgres / mysql** were last started via `make postgres-dev-up` / `make mysql-dev-up`; the root compose (base only, no dev log rotation) sees a different config and would recreate them, so keep using the stack targets (see X1). Their Makefiles run with `-p data-ops` (same project as the root compose). Compose then warns about "orphan containers"; never add `--remove-orphans` to those commands, as it removes every other service. Their data volumes are `external`, so Compose never creates or deletes them (on a fresh machine run `docker volume create postgres-data` / `mysql-data` first). Both run the official images directly (no Dockerfile); `init-scripts/` is mounted and runs only on an empty volume. Postgres runs with `wal_level=logical` for Debezium CDC.
- **redash** doesn't migrate its schema on boot: run `make redash-init-db` (or `redash-prod-init-db`) once per database.
- **neo4j** `NEO4J_AUTH` only applies on first init; rotating `NEO4J_PASSWORD` also requires `ALTER CURRENT USER SET PASSWORD` inside neo4j.
- **docusaurus** dev keeps the image's `node_modules` in an anonymous volume; after dependency changes run `make docusaurus-dev-down` then `make docusaurus-dev-up-build`.

**Not converted yet:** taipy (`07_dashboards/taipy`), ML model services (`ml-models/01_diabetes_predictor`, `ml-models/ocr-pipeline`).

## Pending TODOs

IDs are referenced from comments in the compose files.

### Cross-cutting

- **X1** Fixed `container_name`s clash between the root project and per-stack projects (`make <stack>-dev-up` fails with "container name already in use" if started from root). Apply `-p data-ops` to the remaining stack Makefiles, as postgres/mysql already do.
- **X2** Standalone `make <stack>-dev-up` doesn't wait for cross-stack dependencies (only the root compose declares them). Start dependencies first, or add wait-for logic to entrypoints.
- **X3** Ports published in base can't be removed in prod overrides on older compose. Restrict at the firewall / security group, or require compose ≥ 2.24 and use `ports: !reset []`.
- **X4** `.env` has `REDIS_HOST=localhost` (for host-side scripts). Containers must keep using `redis`; consider a separate `REDIS_CONTAINER_HOST`.
- **X5** Superset, Redash and Prefect use the shared redis container in prod. Move to a managed redis (ElastiCache).
- **X6** Pin unpinned images: `prom/prometheus`, `prometheuscommunity/postgres-exporter`, `spoonest/clickhouse-tabix-web-client`, `ghcr.io/open-webui/open-webui:main`.
- **X7** Convert taipy, customers-api and the ML model services (their host ports are already in `ports.env`). Two of them don't validate standalone: customers-api `depends_on` an undefined `postgres`, and ocr-pipeline's `env_file: ../.env` resolves to `ml-models/.env`, which doesn't exist.
- **X8** Rename dagster's `dagster-local-*` targets to `dagster-dev-*`.
- **X12** Host-side scripts still hardcode host ports: `ml-models/ml-flow/app/test.py` (5005), `metadata/amundsen/test/test_search_service.py` (5003), `ml-models/01_diabetes_predictor/test/test.py` (8000), `07_dashboards/svelte-fastapi-dashboard/frontend` (8000, a non-Docker service). Read them from the environment / `ports.env` instead.
- **X13** Remove the old publish-port vars from `.env` (now superseded by `ports.env`): `APACHE_SUPERSET_PORT`, `REDASH_PORT`, `WEBUI_PORT`, `PROMETHEUS_PORT`, `LOKI_PORT`, `LOCAL_KAFKA_UI_PORT`, `APACHE_AIRFLOW_PORT`. Keep client connection ports (`PG_DB_PORT`, `REDIS_PORT`, `ELASTICSEARCH_PORT`, ...).
- **X10** First build + `dev-up` of every converted stack except postgres/mysql (so far only `docker-compose config` has been validated). Next up: the uv-based images in this order - dagster, prefect, ml-flow (no apt step, so they don't depend on the Debian mirror), then airflow (still needs apt for `mysqlclient`). Smoke-test each: `dagster --version`; a real Prefect flow run (checks the pydantic 2.14 upgrade from the lock); `mlflow --version` + `import psycopg2, boto3`; `airflow version` + `dbt --version` + `import dataflow`.
- **X15** Grafana is the only stack that isn't self-contained: it mounts `../../monitoring-and-observability/{02-prometheus,03-loki}` configs. Move them into `07_dashboards/grafana/` so the stack can be extracted like the others (see README "Take any service and deploy it on its own").
- **X14** `python:3.10-slim` (dagster, ml-flow) is flagged with high-severity CVEs. Move to a newer Python slim image once DG1 is resolved; ml-flow can move now.
- **X11** Add the prod env vars that are still missing from `.env`: `RDS_HOSTNAME`, `RDS_PORT`, `RDS_USERNAME`, `RDS_PASSWORD`, `KAFKA_ADVERTISED_HOST`, `PREFECT_RDS_DB_URL`, `PREFECT_PUBLIC_URL`, `GRAFANA_ROOT_URL`, `NIFI_SINGLE_USER_USERNAME`, `NIFI_SINGLE_USER_PASSWORD`, `MLFLOW_ARTIFACTS_S3_URI`. `WEBHOOK_URL`, `N8N_ENCRYPTION_KEY`, `MB_SITE_URL`, `WEBUI_SECRET_KEY` and the DB passwords exist, but with dev values.

### Databases

**redis**
- **RD1** `--requirepass` is on the command line (visible in `docker inspect`). Move to a mounted `redis.conf`.
- **RD2** No eviction policy, since queues (Redash, Prefect) share the instance with Superset's cache. Split cache (evictable) and queues (`noeviction`).

**elasticsearch**
- **E1** Prod host needs `vm.max_map_count >= 262144` (prod enables `bootstrap.memory_lock`).

**neo4j**
- **NJ2** Upgrade off the 4.4 line together with Amundsen's metadata service.

**trino**
- **T2** Prod mounts `etc/catalog` read-only, which breaks `CATALOG_MANAGEMENT=dynamic`. Drop `:ro` or use static catalogs in prod.
- **T3** No authentication. Configure password/OAuth auth + HTTPS before prod.

### Messaging & warehouse

**kafka**
- **K9** The Debezium Avro connector (`02-postgresdb-avro-for-customers.json`) uses Confluent's `AvroConverter`, which the Debezium image doesn't ship; registering it fails with a class-not-found error. Either use the JSON connector, switch to Apicurio (`ENABLE_APICURIO_CONVERTERS=true`, built into the image), or extend the image with the Confluent Avro converter jars.
- **K10** Replace the BigQuery sink (plugin installed in the cp-kafka-connect `Dockerfile`, configs in `connectors/cp-kafka-connect/configs/sink/bigquery/`) with a ClickHouse sink (configs under `configs/sink/clickhouse/<database>/`) (e.g. `clickhouse/clickhouse-kafka-connect` from Confluent Hub) - there's no BigQuery access to test against.

**clickhouse**
- No service-specific TODOs (see X3 for published ports).

### Orchestration & pipelines

**airflow**
- Create the S3 log bucket (with a lifecycle rule), set `AIRFLOW_REMOTE_LOG_FOLDER`, and grant the containers S3 access (IAM role preferred).

**dagster**
- Prod expects `certs/rds-ca-bundle.pem` for RDS SSL; download it before `make dagster-prod-up`.
- **DG1** Locked to Python 3.10 because `mysql-connector-python==8.0.33` needs `protobuf<=3.20.3`, which Dagster 1.12 only allows on 3.10. Bump the connector (or drop it in favour of `pymysql`, which is also installed) to move the image off `python:3.10-slim` (see X14).
- See X8.

**prefect**
- **P2** Prod needs `PREFECT_RDS_DB_URL` and `PREFECT_PUBLIC_URL` (X11).

**n8n**
- **N1** `N8N_BASIC_AUTH_*` was removed in n8n 1.0 (image is 2.43.7); delete those env vars and rely on n8n's built-in user management.
- **N2** Verify `DB_POSTGRESDB_SSL_ENABLED` is honoured for RDS on the n8n version in use.

**nifi**
- **NF1** Image is HTTPS-only (2.x), but base sets `NIFI_WEB_HTTP_PORT=8443`. Drop it and serve HTTPS with single-user credentials.
- **NF3** `conf/` is a named volume, so image upgrades won't refresh config. Mount only customised files.

**airbyte**
- **AB1** Airbyte 1.x (images are 1.4.1) doesn't support docker-compose; the supported path is `abctl` / Helm. Decide: migrate, or pin an old 0.x compose release.
- **AB2** `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_USERS_DB` are missing from `.env`.
- **AB3** Server/worker use the `users` database. Give Airbyte its own.
- **AB4** Webapp calls `airbyte-server:8001` while the server publishes 8002. Align.

### Dashboards

**superset**
- **S1** `superset_config.py` hardcodes port 5432 and has no `sslmode`. Read both from env for RDS.

**metabase**
- **M1** Verify `MB_DB_CONNECTION_URI` + separate `MB_DB_USER`/`MB_DB_PASS` works on v0.61 against RDS.

**grafana**
- **G1** `prometheus.yml` scrapes `apache-kafka:9999`. The container is `kafka`, and JMX isn't exposed.
- **G2** `scrape_interval: 3600s`. Lower it unless hourly is intentional.
- **G3** Verify the `wget` healthcheck works in `grafana/grafana:12.0.2`.
- **G4** Optional: move Grafana's own DB from sqlite to RDS (block commented in the prod file).
- **G5** `provisioning/datasources/pg-datasource.yml` is empty. Fill in or delete.
- **G6** The Dockerfile only installs 2 plugins + copies provisioning. On 12.0.2 the compose-only alternatives don't fit (`GF_PLUGINS_PREINSTALL_SYNC` installs nothing, `GF_PLUGINS_PREINSTALL` is async, `GF_INSTALL_PLUGINS` is deprecated). When upgrading Grafana, retest `GF_PLUGINS_PREINSTALL_SYNC`; if it works, drop the Dockerfile and mount `provisioning/` (`:ro` in prod). Note: plugins baked into the image only reach `grafana-vol` when the volume is first created.

### Metadata

**amundsen**
- **A1** Frontend runs `TestConfig` with no real auth. Switch the config class and wire auth before exposing it.

**open-metadata**
- **OM1** `PIPELINE_SERVICE_CLIENT_ENDPOINT` points at `apache-airflow-webserver`; the container is `airflow-webserver`.
- **OM2** No Elasticsearch credentials passed, but ES has security enabled. Add `ELASTICSEARCH_USER` / `ELASTICSEARCH_PASSWORD`.
- **OM3** Uses the MySQL root user without SSL. Create a dedicated user.
- **OM4** Optional: restore the `open-metadata-ingestion` service (git history of `docker-compose.open-metadata.yml`) for UI-driven ingestion.

### ML / AI & docs

**ml-flow**
- **MF4** Add a healthcheck (python one-liner; no curl in `python:3.10-slim`).
- **MF5** Prod needs `MLFLOW_ARTIFACTS_S3_URI` and S3 access (IAM role preferred).

**open-webui**
- **OW2** `.env` `WEBUI_URL` says `http://localhost:3000`, but the UI is published on `OPEN_WEBUI_HOST_PORT` (8087). Fix `WEBUI_URL` (and drop `WEBUI_PORT`, see X13).
- **OW3** Drop `WEBUI_JWT_SECRET_KEY` (likely not an Open WebUI setting) and the insecure dev secret fallbacks.
- **OW5** `ai/open-webui/config/branding.json` / `custom_models.json` aren't read by Open WebUI. Set branding via env (`WEBUI_NAME` already is) and add the custom model via the admin UI or `OPENAI_API_BASE_URLS`, then delete `config/`.
- **OW6** Verify `OLLAMA_LLM_MAX_MEMORY` / `OLLAMA_NUM_THREADS` are real Ollama settings; remove if not.
- **OW7** Ollama's API (11434) is unauthenticated and published. Stop publishing it, or firewall it.

**docusaurus**
- **D3** Prod builds at container start and serves via Node. Move to a multi-stage build and serve `build/` from nginx or S3 + CloudFront.
