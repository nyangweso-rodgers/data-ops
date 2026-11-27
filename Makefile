# data-ops/Makefile
# Root Makefile for the entire data-ops monorepo

DAGSTER_DIR := workflows/dagster
AIRFLOW_DIR := workflows/airflow
GRAFANA_DIR := 07_dashboards/grafana
METABASE_DIR := 07_dashboards/metabase
REDASH_DIR := 07_dashboards/redash
SUPERSET_DIR := 07_dashboards/superset
CLICKHOUSE_DIR := 06_data_warehouse/clickhouse
KAFKA_DIR := 03_streaming/kafka
AMUNDSEN_DIR := metadata/amundsen
N8N_DIR := workflows/n8n
PREFECT_DIR := workflows/prefect
ELASTICSEARCH_DIR := 01-databases/elasticsearch
MONGODB_DIR := 01-databases/mongodb
REDIS_DIR := 01-databases/redis
TRINO_DIR := 01-databases/trino
NIFI_DIR := workflows/nifi
AIRBYTE_DIR := workflows/airbyte
OPEN_METADATA_DIR := metadata/open-metadata
NEO4J_DIR := 01-databases/neo4j
DOCUSAURUS_DIR := 10_documentation/docusaurus-site
ML_FLOW_DIR := ml-models/ml-flow
OPEN_WEBUI_DIR := ai/open-webui
POSTGRES_DIR := 01-databases/postgres
MYSQL_DIR := 01-databases/mysql
WEB_APPS_DIR := web-apps
ROOT_DIR := $(shell pwd)

# Export ROOT_DIR so nested Makefiles can use it
export ROOT_DIR

# Host port registry (single source of truth). Make reads it for URLs; compose
# loads it after .env so it always wins. Stack Makefiles pass --env-file explicitly;
# COMPOSE_ENV_FILES covers the plain `docker-compose` calls made from the root.
# (Not read from inside .env - export it in your shell to run docker-compose by hand.)
include ports.env
export COMPOSE_ENV_FILES := .env,ports.env

.PHONY: help env-check ports py-sync py-lock py-lint \
		dagster-local-up-build dagster-local-up dagster-local-stop \
        dagster-local-down dagster-local-logs dagster-local-restart \
        dagster-prod-up dagster-prod-down dagster-prod-logs dagster-build \
		airflow-dev-up-build airflow-dev-up airflow-dev-stop airflow-dev-down airflow-dev-logs \
		airflow-dev-restart airflow-dev-shell airflow-dags airflow-import-errors airflow-test airflow-test-dags \
		airflow-prod-up airflow-prod-down airflow-prod-logs airflow-build airflow-clean \
		metabase-provision metabase-provision-dry-run redash-provision redash-provision-dry-run \
		prometheus-up prometheus-stop prometheus-down prometheus-logs \
		loki-up loki-stop loki-down loki-logs \
		postgres-db-exporter-up postgres-db-exporter-stop postgres-db-exporter-down postgres-db-exporter-logs \
        up down logs clean

help:
	@echo "Data-Ops Monorepo Commands:"
	@echo ""
	@echo "Postgres (localhost:$(POSTGRES_HOST_PORT), user/password from .env, data in volume postgres-data):"
	@echo "  make postgres-dev-up-build  - Pull image and start Postgres"
	@echo "  make postgres-dev-up        - Start Postgres"
	@echo "  make postgres-dev-stop      - Stop Postgres"
	@echo "  make postgres-dev-down      - Stop and remove the Postgres container (data volume kept)"
	@echo "  make postgres-dev-logs      - Follow Postgres logs"
	@echo "  make postgres-dev-restart   - Recreate the Postgres container"
	@echo "  make postgres-dev-psql      - psql in the postgres container"
	@echo "  make postgres-prod-up       - Start production Postgres"
	@echo "  make postgres-prod-down     - Stop production Postgres"
	@echo "  make postgres-prod-logs     - Follow production logs"
	@echo "  make postgres-pull          - Pull the pinned image"
	@echo ""
	@echo "MySQL (localhost:$(MYSQL_HOST_PORT), root password from .env):"
	@echo "  make mysql-dev-up-build     - Pull image and start MySQL"
	@echo "  make mysql-dev-up           - Start MySQL"
	@echo "  make mysql-dev-stop         - Stop MySQL"
	@echo "  make mysql-dev-down         - Stop and remove the MySQL container (data volume kept)"
	@echo "  make mysql-dev-logs         - Follow MySQL logs"
	@echo "  make mysql-dev-restart      - Recreate the MySQL container"
	@echo "  make mysql-dev-cli          - mysql client as root"
	@echo "  make mysql-prod-up          - Start production MySQL"
	@echo "  make mysql-prod-down        - Stop production MySQL"
	@echo "  make mysql-prod-logs        - Follow production logs"
	@echo "  make mysql-pull             - Pull the pinned image"
	@echo ""
	@echo "MongoDB (mongodb://localhost:$(MONGODB_HOST_PORT), root user from .env):"
	@echo "  make mongodb-dev-up-build   - Pull image and start MongoDB"
	@echo "  make mongodb-dev-up         - Start MongoDB"
	@echo "  make mongodb-dev-stop       - Stop MongoDB"
	@echo "  make mongodb-dev-down       - Stop and remove the MongoDB container (data volume kept)"
	@echo "  make mongodb-dev-logs       - Follow MongoDB logs"
	@echo "  make mongodb-dev-restart    - Recreate the MongoDB container"
	@echo "  make mongodb-dev-shell      - mongosh as the root user"
	@echo "  make mongodb-prod-up        - Start production MongoDB"
	@echo "  make mongodb-prod-down      - Stop production MongoDB"
	@echo "  make mongodb-prod-logs      - Follow production logs"
	@echo "  make mongodb-pull           - Pull the pinned image"
	@echo ""
	@echo "Elasticsearch (http://localhost:$(ELASTICSEARCH_HOST_PORT), Kibana: http://localhost:$(KIBANA_HOST_PORT)):"
	@echo "  make elasticsearch-dev-up-build - Pull images and start Elasticsearch + Kibana"
	@echo "  make elasticsearch-dev-up       - Start Elasticsearch + Kibana"
	@echo "  make elasticsearch-dev-stop     - Stop Elasticsearch + Kibana"
	@echo "  make elasticsearch-dev-down     - Stop and remove the containers (data volume kept)"
	@echo "  make elasticsearch-dev-logs     - Follow logs"
	@echo "  make elasticsearch-dev-restart  - Recreate the containers"
	@echo "  make elasticsearch-dev-health   - Cluster health"
	@echo "  make elasticsearch-prod-up      - Start production Elasticsearch"
	@echo "  make elasticsearch-prod-down    - Stop production Elasticsearch"
	@echo "  make elasticsearch-prod-logs    - Follow production logs"
	@echo "  make elasticsearch-pull         - Pull the pinned images"
	@echo ""
	@echo "Redis (localhost:$(REDIS_HOST_PORT), RedisInsight: http://localhost:$(REDISINSIGHT_HOST_PORT)):"
	@echo "  make redis-dev-up-build     - Pull images and start Redis + RedisInsight"
	@echo "  make redis-dev-up           - Start Redis + RedisInsight"
	@echo "  make redis-dev-stop         - Stop Redis + RedisInsight"
	@echo "  make redis-dev-down         - Stop and remove the containers (data volumes kept)"
	@echo "  make redis-dev-logs         - Follow logs"
	@echo "  make redis-dev-restart      - Recreate the containers"
	@echo "  make redis-dev-cli          - redis-cli in the redis container"
	@echo "  make redis-prod-up          - Start production Redis"
	@echo "  make redis-prod-down        - Stop production Redis"
	@echo "  make redis-prod-logs        - Follow production logs"
	@echo "  make redis-pull             - Pull the pinned images"
	@echo ""
	@echo "Neo4j (Browser: http://localhost:$(NEO4J_HTTP_HOST_PORT), Bolt: localhost:$(NEO4J_BOLT_HOST_PORT), NEO4J_USER / NEO4J_PASSWORD from .env):"
	@echo "  make neo4j-dev-up-build     - Pull image and start Neo4j"
	@echo "  make neo4j-dev-up           - Start Neo4j"
	@echo "  make neo4j-dev-stop         - Stop Neo4j"
	@echo "  make neo4j-dev-down         - Stop and remove the Neo4j container (data volume kept)"
	@echo "  make neo4j-dev-logs         - Follow Neo4j logs"
	@echo "  make neo4j-dev-restart      - Recreate the Neo4j container"
	@echo "  make neo4j-dev-shell        - cypher-shell in the neo4j container"
	@echo "  make neo4j-prod-up          - Start production Neo4j"
	@echo "  make neo4j-prod-down        - Stop production Neo4j"
	@echo "  make neo4j-prod-logs        - Follow production logs"
	@echo "  make neo4j-pull             - Pull the pinned image"
	@echo ""
	@echo "Trino (http://localhost:$(TRINO_HOST_PORT), catalogs from 01-databases/trino/etc/catalog):"
	@echo "  make trino-dev-up-build     - Pull image and start Trino"
	@echo "  make trino-dev-up           - Start Trino"
	@echo "  make trino-dev-stop         - Stop Trino"
	@echo "  make trino-dev-down         - Stop and remove the Trino container (stateless, no data volume)"
	@echo "  make trino-dev-logs         - Follow Trino logs"
	@echo "  make trino-dev-restart      - Recreate the Trino container (reloads catalog configs)"
	@echo "  make trino-dev-cli          - Trino CLI in the container"
	@echo "  make trino-prod-up          - Start production Trino"
	@echo "  make trino-prod-down        - Stop production Trino"
	@echo "  make trino-prod-logs        - Follow production logs"
	@echo "  make trino-pull             - Pull the pinned image"
	@echo ""
	@echo "Web apps (Next.js in web-apps/apps/, Docker runs the production image;"
	@echo "hot-reload dev runs natively: cd web-apps && pnpm dev:portal):"
	@echo "  Per app - <app> = web-portal (:$(WEB_PORTAL_HOST_PORT)), survey-app (:$(SURVEY_APP_HOST_PORT)), web-portal-starter (:$(WEB_PORTAL_STARTER_HOST_PORT)), data-portal (:$(DATA_PORTAL_HOST_PORT)):"
	@echo "  make <app>-dev-up           - Build if changed and start"
	@echo "  make <app>-dev-up-build     - Rebuild image (no cache) and start"
	@echo "  make <app>-dev-stop         - Stop"
	@echo "  make <app>-dev-down         - Stop and remove the container"
	@echo "  make <app>-dev-logs         - Follow logs"
	@echo "  make <app>-dev-restart      - Recreate the container"
	@echo "  make <app>-dev-shell        - Shell in the container"
	@echo "  make <app>-prod-up          - Start production"
	@echo "  make <app>-prod-down        - Stop and remove production container"
	@echo "  make <app>-prod-logs        - Follow production logs"
	@echo "  make <app>-build            - Rebuild image (no cache)"
	@echo "  All apps at once: make web-apps-dev-up | web-apps-dev-down | web-apps-dev-logs | web-apps-prod-up | ..."
	@echo "  e.g. make web-portal-dev-up   /   make survey-app-dev-logs"
	@echo ""
	@echo "Kafka"
	@echo ""
	@echo "Grafana"
	@echo ""
	@echo ""
	@echo "Metabase"
	@echo ""
	@echo ""
	@echo "Redash"
	@echo ""
	@echo ""
	@echo "Superset"
	@echo ""
	
	@echo "Airflow:"
	@echo "  make airflow-dev-up-build   - Build and start Airflow (webserver + scheduler)"
	@echo "  make airflow-dev-up         - Start Airflow"
	@echo "  make airflow-dev-stop       - Stop Airflow"
	@echo "  make airflow-dev-down       - Stop and remove Airflow"
	@echo "  make airflow-dev-logs       - Follow Airflow logs"
	@echo "  make airflow-dev-restart    - Recreate Airflow containers"
	@echo "  make airflow-dev-shell      - Bash shell in the scheduler"
	@echo "  make airflow-dags           - List DAGs"
	@echo "  make airflow-import-errors  - Show DAG import errors"
	@echo "  make airflow-test           - Run unit tests locally"
	@echo "  make airflow-test-dags      - Run all tests (incl. DAG integrity) in the scheduler"
	@echo "  make airflow-prod-up        - Start production Airflow"
	@echo "  make airflow-prod-down      - Stop production Airflow"
	@echo "  make airflow-prod-logs      - View production logs"
	@echo "  make airflow-build          - Rebuild the Airflow image (no cache)"
	@echo "  make airflow-clean          - Remove dev containers and volumes"
	@echo ""
	
	@echo "Dagster:"
	@echo "  make dagster-local-up-build - Build and start local Dagster"
	@echo "  make dagster-local-up       - Start local Dagster"
	@echo "  make dagster-local-stop     - Stop local Dagster"
	@echo "  make dagster-local-down     - Stop and remove local Dagster"
	@echo "  make dagster-local-logs     - View local Dagster logs"
	@echo "  make dagster-local-restart  - Restart local Dagster"
	@echo "  make dagster-prod-up        - Start production Dagster"
	@echo "  make dagster-prod-down      - Stop production Dagster"
	@echo "  make dagster-prod-logs      - View production logs"
	@echo "  make dagster-build          - Rebuild Dagster images"
	@echo ""
	
	@echo "Maestro (planned - not set up yet)"
	@echo ""

	@echo "n8n (UI: http://localhost:$(N8N_HOST_PORT)):"
	@echo "  make n8n-dev-up-build       - Pull images and start n8n"
	@echo "  make n8n-dev-up             - Start n8n"
	@echo "  make n8n-dev-stop           - Stop n8n"
	@echo "  make n8n-dev-down           - Stop and remove n8n containers"
	@echo "  make n8n-dev-logs           - Follow n8n logs"
	@echo "  make n8n-dev-restart        - Recreate n8n containers"
	@echo "  make n8n-dev-shell          - Shell in the n8n container"
	@echo "  make n8n-init-db            - Create the n8n database in the local postgres container"
	@echo "  make n8n-prod-up            - Start production n8n"
	@echo "  make n8n-prod-down          - Stop production n8n"
	@echo "  make n8n-prod-logs          - Follow production logs"
	@echo "  make n8n-pull               - Pull the pinned images"
	@echo ""

	@echo "NiFi (UI: https://localhost:$(NIFI_HOST_PORT)/nifi, login NIFI_USER / NIFI_PASSWORD from .env):"
	@echo "  make nifi-dev-up-build      - Build images and start NiFi; connections are provisioned on start"
	@echo "  make nifi-dev-up            - Start NiFi; connections are provisioned on start"
	@echo "  make nifi-dev-stop          - Stop NiFi"
	@echo "  make nifi-dev-down          - Stop and remove NiFi containers"
	@echo "  make nifi-dev-logs          - Follow NiFi logs"
	@echo "  make nifi-dev-restart       - Recreate NiFi (needed after changing NIFI_CONN_* in .env)"
	@echo "  make nifi-provision         - Re-apply workflows/nifi configs/ + schemas/ + pipelines/"
	@echo "  make nifi-provision-dry-run - Show what provisioning would change"
	@echo "  make nifi-prod-up           - Start production NiFi"
	@echo "  make nifi-prod-down         - Stop production NiFi"
	@echo "  make nifi-prod-logs         - Follow production logs"
	@echo "  make nifi-build             - Rebuild NiFi images (no cache)"
	@echo ""

	@echo "Prefect (UI: http://localhost:$(PREFECT_HOST_PORT)):"
	@echo "  make prefect-dev-up-build   - Build images and start Prefect"
	@echo "  make prefect-dev-up         - Start Prefect"
	@echo "  make prefect-dev-stop       - Stop Prefect"
	@echo "  make prefect-dev-down       - Stop and remove Prefect containers"
	@echo "  make prefect-dev-logs       - Follow Prefect logs"
	@echo "  make prefect-dev-restart    - Recreate Prefect containers"
	@echo "  make prefect-prod-up        - Start production Prefect"
	@echo "  make prefect-prod-down      - Stop production Prefect"
	@echo "  make prefect-prod-logs      - Follow production logs"
	@echo "  make prefect-build          - Rebuild Prefect images (no cache)"
	@echo "  make prefect-lock           - Re-resolve uv.lock after editing pyproject.toml"
	@echo "  make prefect-sync           - Create/update the local .venv from uv.lock (editor, tests)"
	@echo ""
	
	@echo "Stacks (dev/prod/base convention):"
	@echo "  metabase, redash, superset, grafana, clickhouse, kafka, amundsen,"
	@echo "  airbyte, open-metadata, docusaurus, ml-flow, open-webui (+ollama)"
	@echo "  (Databases in 01-databases/ have their own sections at the top.)"
	@echo "  Each has <dir>/Makefile + docker-compose-<stack>.{base,dev,prod}.yml."
	@echo "  make <stack>-<target> runs <target> in that stack's Makefile:"
	@echo "  make <stack>-dev-up-build   - Build/pull and start (dev)"
	@echo "  make <stack>-dev-up         - Start (dev)"
	@echo "  make <stack>-dev-stop       - Stop (dev)"
	@echo "  make <stack>-dev-down       - Stop and remove (dev)"
	@echo "  make <stack>-dev-logs       - Follow logs (dev)"
	@echo "  make <stack>-dev-restart    - Recreate (dev)"
	@echo "  make <stack>-prod-up        - Start production"
	@echo "  make <stack>-prod-down      - Stop production"
	@echo "  make <stack>-prod-logs      - Follow production logs"
	@echo "  make <stack>-help           - List all targets for that stack (incl. extras below)"
	@echo "  Extras: superset-dev-shell, redash-init-db, redash-prod-init-db,"
	@echo "          clickhouse-dev-client, kafka-dev-topics,"
	@echo "          open-webui-dev-pull-model MODEL=<name>, open-webui-dev-models"
	@echo ""
	@echo "Provisioning:"
	@echo "  make metabase-provision     - Provision Metabase connections"
	@echo "  make metabase-provision-dry-run - Preview Metabase changes"
	@echo "  make redash-provision       - Provision Redash data sources + dashboards"
	@echo "  make redash-provision-dry-run - Preview data-source changes, secrets redacted"
	@echo ""
	@echo "Grafana stack extras (via root docker-compose.yml):"
	@echo "  make prometheus-up         - Start Prometheus"
	@echo "  make prometheus-stop        - Stop Prometheus"
	@echo "  make prometheus-down        - Remove Prometheus"
	@echo "  make prometheus-logs        - View Prometheus logs"
	@echo "  make loki-up                - Start Loki"
	@echo "  make loki-stop              - Stop Loki"
	@echo "  make loki-down              - Remove Loki"
	@echo "  make loki-logs              - View Loki logs"
	@echo "  make postgres-db-exporter-up   - Start Postgres exporter"
	@echo "  make postgres-db-exporter-stop - Stop Postgres exporter"
	@echo "  make postgres-db-exporter-down - Remove Postgres exporter"
	@echo "  make postgres-db-exporter-logs - View Postgres exporter logs"
	@echo ""
	@echo "Python (uv):"
	@echo "  make py-sync                - Create/update the root .venv (provisioning scripts + dev tools)"
	@echo "  make py-lock                - Re-resolve uv.lock for the root and every Python project"
	@echo "  make py-lint                - ruff check the repo (shared config in pyproject.toml)"
	@echo ""
	@echo "Ports:"
	@echo "  make ports                  - List host ports (ports.env) and where they're published;"
	@echo "                                fails on duplicates, hardcoded/defaulted or unregistered ports"

# Environment check
# ──────────────────────────────────────────────────────────────
ports:
	@bash scripts/check_ports.sh

# ──────────────────────────────────────────────────────────────
# Python (uv)
# Root pyproject.toml = repo tooling + host-side scripts. Each service keeps its own
# pyproject.toml + uv.lock (separate resolutions - see pyproject.toml header).
# ──────────────────────────────────────────────────────────────
PY_PROJECTS := $(AIRFLOW_DIR) $(DAGSTER_DIR) $(PREFECT_DIR) $(ML_FLOW_DIR) $(NIFI_DIR)

py-sync:
	@uv sync

py-lock:
	@uv lock
	@for d in $(PY_PROJECTS); do echo "→ $$d"; (cd $$d && uv lock) || exit 1; done
	@echo "✓ all uv.lock files resolved - rebuild affected images to apply"

py-lint:
	@uv run ruff check .

env-check:
	@if [ ! -f .env ]; then \
		echo "❌ Error: .env file not found in root directory"; \
		echo "Please create .env file from .env.example"; \
		exit 1; \
	fi
	@echo "✓ .env file found"
	@if ! grep -q "DAGSTER_PG_DB_HOST" .env; then \
		echo "⚠️  Warning: DAGSTER_PG_DB_HOST not found in .env"; \
	fi
# ──────────────────────────────────────────────────────────────
# Dagster - Local development
# ──────────────────────────────────────────────────────────────
dagster-local-up-build:
	@$(MAKE) -C $(DAGSTER_DIR) local-up-build

dagster-local-up:
	@$(MAKE) -C $(DAGSTER_DIR) local-up

dagster-local-stop:
	@$(MAKE) -C $(DAGSTER_DIR) local-stop

dagster-local-down:
	@$(MAKE) -C $(DAGSTER_DIR) local-down

dagster-local-restart:
	@$(MAKE) -C $(DAGSTER_DIR) local-restart

# ──────────────────────────────────────────────────────────────
# Dagster - Production
# ──────────────────────────────────────────────────────────────
dagster-prod-up:
	@$(MAKE) -C $(DAGSTER_DIR) prod-up

dagster-prod-down:
	@$(MAKE) -C $(DAGSTER_DIR) prod-down

dagster-build:
	@$(MAKE) -C $(DAGSTER_DIR) build

# ──────────────────────────────────────────────────────────────
# Airflow - Development (see workflows/airflow/Makefile)
# ──────────────────────────────────────────────────────────────
airflow-dev-up-build:
	@$(MAKE) -C $(AIRFLOW_DIR) dev-up-build

airflow-dev-up:
	@$(MAKE) -C $(AIRFLOW_DIR) dev-up

airflow-dev-stop:
	@$(MAKE) -C $(AIRFLOW_DIR) dev-stop

airflow-dev-down:
	@$(MAKE) -C $(AIRFLOW_DIR) dev-down

airflow-dev-logs:
	@$(MAKE) -C $(AIRFLOW_DIR) dev-logs

airflow-dev-restart:
	@$(MAKE) -C $(AIRFLOW_DIR) dev-restart

airflow-dev-shell:
	@$(MAKE) -C $(AIRFLOW_DIR) dev-shell

airflow-dags:
	@$(MAKE) -C $(AIRFLOW_DIR) dags

airflow-import-errors:
	@$(MAKE) -C $(AIRFLOW_DIR) import-errors

airflow-test:
	@$(MAKE) -C $(AIRFLOW_DIR) test

airflow-test-dags:
	@$(MAKE) -C $(AIRFLOW_DIR) test-dags

# ──────────────────────────────────────────────────────────────
# Airflow - Production
# ──────────────────────────────────────────────────────────────
airflow-prod-up:
	@$(MAKE) -C $(AIRFLOW_DIR) prod-up

airflow-prod-down:
	@$(MAKE) -C $(AIRFLOW_DIR) prod-down

airflow-prod-logs:
	@$(MAKE) -C $(AIRFLOW_DIR) prod-logs

airflow-build:
	@$(MAKE) -C $(AIRFLOW_DIR) build

airflow-clean:
	@$(MAKE) -C $(AIRFLOW_DIR) clean

# ──────────────────────────────────────────────────────────────
# Stack delegation
# ──────────────────────────────────────────────────────────────
# Each stack has its own Makefile + docker-compose-<stack>.{base,dev,prod}.yml.
# `make <stack>-<target>` runs `<target>` in that stack's Makefile, e.g.
#   make superset-dev-up   -> make -C 07_dashboards/superset dev-up
#   make kafka-prod-logs   -> make -C 03_streaming/kafka prod-logs
# Explicit root targets (e.g. metabase-provision) take precedence over these rules.
# (Pattern rules must NOT be listed in .PHONY, or make skips them.)
metabase-%:
	@$(MAKE) -C $(METABASE_DIR) $*

redash-%:
	@$(MAKE) -C $(REDASH_DIR) $*

superset-%:
	@$(MAKE) -C $(SUPERSET_DIR) $*

grafana-%:
	@$(MAKE) -C $(GRAFANA_DIR) $*

clickhouse-%:
	@$(MAKE) -C $(CLICKHOUSE_DIR) $*

kafka-%:
	@$(MAKE) -C $(KAFKA_DIR) $*

amundsen-%:
	@$(MAKE) -C $(AMUNDSEN_DIR) $*

n8n-%:
	@$(MAKE) -C $(N8N_DIR) $*

prefect-%:
	@$(MAKE) -C $(PREFECT_DIR) $*

elasticsearch-%:
	@$(MAKE) -C $(ELASTICSEARCH_DIR) $*

mongodb-%:
	@$(MAKE) -C $(MONGODB_DIR) $*

redis-%:
	@$(MAKE) -C $(REDIS_DIR) $*

trino-%:
	@$(MAKE) -C $(TRINO_DIR) $*

nifi-%:
	@$(MAKE) -C $(NIFI_DIR) $*

airbyte-%:
	@$(MAKE) -C $(AIRBYTE_DIR) $*

open-metadata-%:
	@$(MAKE) -C $(OPEN_METADATA_DIR) $*

neo4j-%:
	@$(MAKE) -C $(NEO4J_DIR) $*

docusaurus-%:
	@$(MAKE) -C $(DOCUSAURUS_DIR) $*

ml-flow-%:
	@$(MAKE) -C $(ML_FLOW_DIR) $*

open-webui-%:
	@$(MAKE) -C $(OPEN_WEBUI_DIR) $*

# postgres/mysql Makefiles use project "data-ops" (same as the root compose).
# The explicit postgres-db-exporter-* targets above win over postgres-%.
postgres-%:
	@$(MAKE) -C $(POSTGRES_DIR) $*

mysql-%:
	@$(MAKE) -C $(MYSQL_DIR) $*

# Next.js apps: per-app targets (make web-portal-dev-up, make data-portal-dev-up) + all-apps (make web-apps-dev-up).
# GNU make picks the pattern with the shortest stem, so web-portal-starter-dev-up
# matches web-portal-starter-% (stem "dev-up"), not web-portal-% (stem "starter-dev-up").
web-apps-%:
	@$(MAKE) -C $(WEB_APPS_DIR) $*

web-portal-%:
	@$(MAKE) -C $(WEB_APPS_DIR) web-portal-$*

web-portal-starter-%:
	@$(MAKE) -C $(WEB_APPS_DIR) web-portal-starter-$*

survey-app-%:
	@$(MAKE) -C $(WEB_APPS_DIR) survey-app-$*

data-portal-%:
	@$(MAKE) -C $(WEB_APPS_DIR) data-portal-$*

# ──────────────────────────────────────────────────────────────
# MetaBase provisioning (runs from the repo root)
# METABASE_URL / REDASH_URL default to the host ports in ports.env (export to override)
# ──────────────────────────────────────────────────────────────
metabase-provision:
	@echo "🔌 Provisioning Metabase database connections..."
	@METABASE_URL="$${METABASE_URL:-http://localhost:$(METABASE_HOST_PORT)}" uv run python 07_dashboards/metabase/provisioning/provision_metabase.py

metabase-provision-dry-run:
	@METABASE_URL="$${METABASE_URL:-http://localhost:$(METABASE_HOST_PORT)}" uv run python 07_dashboards/metabase/provisioning/provision_metabase.py --dry-run

# ──────────────────────────────────────────────────────────────
# Redash provisioning (runs from the repo root)
# ──────────────────────────────────────────────────────────────
redash-provision:
	@echo "🔌 Provisioning Redash data sources and dashboards..."
	@REDASH_URL="$${REDASH_URL:-http://localhost:$(REDASH_HOST_PORT)}" uv run python 07_dashboards/redash/provisioning/provision_redash.py

redash-provision-dry-run:
	@REDASH_URL="$${REDASH_URL:-http://localhost:$(REDASH_HOST_PORT)}" uv run python 07_dashboards/redash/provisioning/provision_redash.py --dry-run

# ──────────────────────────────────────────────────────────────
# Prometheus Commands
# ──────────────────────────────────────────────────────────────
prometheus-up:
	@echo "🚀 Starting Prometheus..."
	@docker-compose up -d prometheus
	@echo "✓ Prometheus started at http://localhost:$${PROMETHEUS_PORT:-9090}"

prometheus-stop:
	@docker-compose stop prometheus

prometheus-down:
	@docker-compose rm -sf prometheus

prometheus-logs:
	@docker-compose logs -f prometheus

# ──────────────────────────────────────────────────────────────
# Loki Commands
# ──────────────────────────────────────────────────────────────
loki-up:
	@echo "🚀 Starting Loki..."
	@docker-compose up -d loki
	@echo "✓ Loki started"

loki-stop:
	@docker-compose stop loki

loki-down:
	@docker-compose rm -sf loki

loki-logs:
	@docker-compose logs -f loki

# ──────────────────────────────────────────────────────────────
# Postgres DB Exporter Commands
# ──────────────────────────────────────────────────────────────
postgres-db-exporter-up:
	@echo "🚀 Starting Postgres DB exporter..."
	@docker-compose up -d postgres-db-exporter
	@echo "✓ Postgres DB exporter started at http://localhost:9187"

postgres-db-exporter-stop:
	@docker-compose stop postgres-db-exporter

postgres-db-exporter-down:
	@docker-compose rm -sf postgres-db-exporter

postgres-db-exporter-logs:
	@docker-compose logs -f postgres-db-exporter
