# data-ops/Makefile
# Root Makefile for the entire data-ops monorepo

DAGSTER_DIR := workflows/dagster
AIRFLOW_DIR := workflows/airflow
GRAFANA_DIR := 07_dashboards/grafana
METABASE_DIR := 07_dashboards/04_metabase
REDASH_DIR := 07_dashboards/03_redash
SUPERSET_DIR := 07_dashboards/01_superset
CLICKHOUSE_DIR := 06_data_warehouse/clickhouse
KAFKA_DIR := 03_messaging_services/kafka
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
POSTGRES_DIR := 01-databases/01-postgres
MYSQL_DIR := 01-databases/mysql
ROOT_DIR := $(shell pwd)

# Export ROOT_DIR so nested Makefiles can use it
export ROOT_DIR

# Host port registry (single source of truth). Make reads it for URLs; compose
# loads it after .env so it always wins. Stack Makefiles pass --env-file explicitly;
# COMPOSE_ENV_FILES covers the plain `docker-compose` calls made from the root.
# (Not read from inside .env - export it in your shell to run docker-compose by hand.)
include ports.env
export COMPOSE_ENV_FILES := .env,ports.env

.PHONY: help env-check ports \
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
	@echo "Stacks (dev/prod/base convention):"
	@echo "  metabase, redash, superset, grafana, clickhouse, kafka, amundsen, n8n, prefect,"
	@echo "  elasticsearch (+kibana), mongodb, redis (+redisinsight), trino, nifi, airbyte, open-metadata,"
	@echo "  neo4j, docusaurus, ml-flow, open-webui (+ollama), postgres, mysql"
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
	@echo "  Extras: superset-dev-shell, n8n-dev-shell, n8n-init-db, redash-init-db,"
	@echo "          redash-prod-init-db, clickhouse-dev-client, kafka-dev-topics,"
	@echo "          elasticsearch-dev-health, mongodb-dev-shell, redis-dev-cli, trino-dev-cli,"
	@echo "          neo4j-dev-shell, open-webui-dev-pull-model MODEL=<name>, open-webui-dev-models,"
	@echo "          postgres-dev-psql, mysql-dev-cli"
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
	@echo "Ports:"
	@echo "  make ports                  - List host ports (ports.env) and where they're published;"
	@echo "                                fails on duplicates, hardcoded/defaulted or unregistered ports"
	@echo ""
	@echo "Full stack:"
	@echo "  make up                     - Start all services"
	@echo "  make down                   - Stop all services"
	@echo "  make logs                   - View all logs"
	@echo "  make clean                  - Clean up everything"

# Environment check
# ──────────────────────────────────────────────────────────────
ports:
	@bash scripts/check_ports.sh

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
#   make superset-dev-up   -> make -C 07_dashboards/01_superset dev-up
#   make kafka-prod-logs   -> make -C 03_messaging_services/kafka prod-logs
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

# ──────────────────────────────────────────────────────────────
# MetaBase provisioning (runs from the repo root)
# METABASE_URL / REDASH_URL default to the host ports in ports.env (export to override)
# ──────────────────────────────────────────────────────────────
metabase-provision:
	@echo "🔌 Provisioning Metabase database connections..."
	@METABASE_URL="$${METABASE_URL:-http://localhost:$(METABASE_HOST_PORT)}" python 07_dashboards/04_metabase/provisioning/provision_metabase.py

metabase-provision-dry-run:
	@METABASE_URL="$${METABASE_URL:-http://localhost:$(METABASE_HOST_PORT)}" python 07_dashboards/04_metabase/provisioning/provision_metabase.py --dry-run

# ──────────────────────────────────────────────────────────────
# Redash provisioning (runs from the repo root)
# ──────────────────────────────────────────────────────────────
redash-provision:
	@echo "🔌 Provisioning Redash data sources and dashboards..."
	@REDASH_URL="$${REDASH_URL:-http://localhost:$(REDASH_HOST_PORT)}" python 07_dashboards/03_redash/provisioning/provision_redash.py

redash-provision-dry-run:
	@REDASH_URL="$${REDASH_URL:-http://localhost:$(REDASH_HOST_PORT)}" python 07_dashboards/03_redash/provisioning/provision_redash.py --dry-run

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
