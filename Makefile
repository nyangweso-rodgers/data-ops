# data-ops/Makefile
# Root Makefile for the entire data-ops monorepo

DAGSTER_DIR := workflows/dagster
ROOT_DIR := $(shell pwd)

# Export ROOT_DIR so nested Makefiles can use it
export ROOT_DIR

.PHONY: help env-check\
		mysql-dev-build mysql-dev-up mysql-dev-stop mysql-dev-down mysql-dev-logs mysql-dev-restart \
		postgres-dev-up postgres-dev-stop postgres-dev-down postgres-dev-logs \
		dagster-local-up-build dagster-local-up dagster-local-stop \
        dagster-local-down dagster-local-logs dagster-local-restart \
        dagster-prod-up dagster-prod-down dagster-prod-logs dagster-build \
		n8n-init-db n8n-up-build n8n-up n8n-stop n8n-down n8n-logs n8n-restart n8n-shell \
		elasticsearch-up elasticsearch-stop elasticsearch-down elasticsearch-logs \
		kibana-up kibana-stop kibana-down kibana-logs \
		neo4j-up neo4j-stop neo4j-down neo4j-logs \
		redis-dev-up redis-dev-stop redis-dev-down redis-dev-logs \
		redisinsight-dev-up redisinsight-dev-stop redisinsight-dev-down redisinsight-dev-logs \
		trino-up trino-stop trino-down trino-logs \
		amundsen-up amundsen-stop amundsen-down amundsen-logs \
		amundsen-frontend-up amundsen-frontend-stop amundsen-frontend-down amundsen-frontend-logs \
		amundsen-metadata-up amundsen-metadata-stop amundsen-metadata-down amundsen-metadata-logs \
		amundsen-search-up amundsen-search-stop amundsen-search-down amundsen-search-logs \
		prefect-server-up prefect-server-stop prefect-server-down prefect-server-logs \
		prefect-worker-up prefect-worker-stop prefect-worker-down prefect-worker-logs \
		prefect-services-up prefect-services-stop prefect-services-down prefect-services-logs \
		superset-dev-build superset-dev-up superset-dev-stop superset-dev-down superset-dev-logs superset-dev-restart superset-shell \
		redash-dev-up-build redash-dev-up redash-dev-stop redash-dev-down redash-dev-logs redash-dev-restart redash-init-db \
		redash-provision redash-provision-dry-run \
		grafana-up-build grafana-up grafana-stop grafana-down grafana-logs grafana-restart \
		prometheus-up prometheus-stop prometheus-down prometheus-logs \
		loki-up loki-stop loki-down loki-logs \
		postgres-db-exporter-up postgres-db-exporter-stop postgres-db-exporter-down postgres-db-exporter-logs \
		grafana-stack-up grafana-stack-stop grafana-stack-down grafana-stack-logs \
        up down logs clean

help:
	@echo "Data-Ops Monorepo Commands:"
	@echo ""
	@echo "  make mysql-dev-build           - Build and start MySQL (detached)"
	@echo "  make mysql-dev-up              - Start MySQL (detached)"
	@echo "  make mysql-dev-stop            - Stop MySQL"
	@echo "  make mysql-dev-down            - Remove MySQL"
	@echo "  make mysql-dev-restart         - Restart MySQL"
	@echo ""
	@echo "  make postgres-dev-up       - Start development PostgreSQL"
	@echo "  make postgres-dev-stop     - Stop development PostgreSQL"
	@echo "  make postgres-dev-down     - Remove development PostgreSQL"
	@echo "  make postgres-dev-logs     - View development PostgreSQL logs"
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
	@echo "n8n:"
	@echo "  make n8n-init-db        - Initialize n8n database"
	@echo "  make n8n-up-build       - Build and start n8n"
	@echo "  make n8n-up             - Start n8n"
	@echo "  make n8n-stop           - Stop n8n"
	@echo "  make n8n-down           - Stop and remove n8n"
	@echo "  make n8n-logs           - View n8n logs"
	@echo "  make n8n-restart        - Restart n8n"
	@echo "  make n8n-shell          - Access n8n shell"
	@echo ""
	@echo "PostgreSQL:"
	@echo "  make postgres-up            - Start PostgreSQL"
	@echo "  make postgres-down          - Stop PostgreSQL"
	@echo ""
	@echo "Superset:"
	@echo "  make superset-dev-build     - Build and start Superset"
	@echo "  make superset-dev-up        - Start Superset"
	@echo "  make superset-dev-stop      - Stop Superset"
	@echo "  make superset-dev-down      - Remove Superset"
	@echo "  make superset-dev-logs      - View Superset logs"
	@echo "  make superset-dev-restart   - Restart Superset"
	@echo "  make superset-shell         - Access Superset shell"
	@echo ""
	@echo "Redash:"
	@echo "  make redash-dev-build       - Build and start Redash (server/scheduler/worker)"
	@echo "  make redash-dev-up          - Start Redash"
	@echo "  make redash-dev-stop        - Stop Redash"
	@echo "  make redash-dev-down        - Remove Redash"
	@echo "  make redash-dev-logs        - View Redash logs"
	@echo "  make redash-dev-restart     - Restart Redash"
	@echo "  make redash-init-db         - Run Redash's one-time schema migration (create_db)"
	@echo "  make redash-provision       - Provision Redash data sources + dashboards"
	@echo "  make redash-provision-dry-run - Preview data-source changes, secrets redacted"
	@echo ""
	@echo "Grafana:"
	@echo "  make grafana-up-build       - Build and start Grafana"
	@echo "  make grafana-up             - Start Grafana"
	@echo "  make grafana-stop           - Stop Grafana"
	@echo "  make grafana-down           - Remove Grafana"
	@echo "  make grafana-logs           - View Grafana logs"
	@echo "  make grafana-restart        - Restart Grafana"
	@echo "  make prometheus-up          - Start Prometheus"
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
	@echo "  make grafana-stack-up       - Start Grafana + Prometheus + Loki + exporter"
	@echo "  make grafana-stack-stop     - Stop the full Grafana stack"
	@echo "  make grafana-stack-down     - Remove the full Grafana stack"
	@echo "  make grafana-stack-logs     - View logs for the full Grafana stack"
	@echo ""
	@echo "Elasticsearch:"
	@echo "  make elasticsearch-up       - Start Elasticsearch"
	@echo "  make elasticsearch-stop     - Stop Elasticsearch"
	@echo "  make elasticsearch-down     - Remove Elasticsearch"
	@echo "  make elasticsearch-logs     - View Elasticsearch logs"
	@echo ""
	@echo "Kibana:"
	@echo "  make kibana-up              - Start Kibana"
	@echo "  make kibana-stop            - Stop Kibana"
	@echo "  make kibana-down            - Remove Kibana"
	@echo "  make kibana-logs            - View Kibana logs"
	@echo ""
	@echo "Neo4j:"
	@echo "  make neo4j-up               - Start Neo4j"
	@echo "  make neo4j-stop             - Stop Neo4j"
	@echo "  make neo4j-down             - Remove Neo4j"
	@echo "  make neo4j-logs             - View Neo4j logs"
	@echo ""
	@echo "Redis:"
	@echo "  make redis-dev-up           - Start Redis"
	@echo "  make redis-dev-stop         - Stop Redis"
	@echo "  make redis-dev-down         - Remove Redis"
	@echo "  make redis-dev-logs         - View Redis logs"
	@echo ""
	@echo "RedisInsight:"
	@echo "  make redisinsight-dev-up    - Start RedisInsight"
	@echo "  make redisinsight-dev-stop  - Stop RedisInsight"
	@echo "  make redisinsight-dev-down  - Stop and remove RedisInsight"
	@echo "  make redisinsight-dev-logs  - View RedisInsight logs"
	@echo ""
	@echo "Trino:"
	@echo "  make trino-up               - Start Trino"
	@echo "  make trino-stop             - Stop Trino"
	@echo "  make trino-down             - Remove Trino"
	@echo "  make trino-logs             - View Trino logs"
	@echo ""
	@echo "Amundsen (full stack):"
	@echo "  make amundsen-up            - Start all Amundsen services"
	@echo "  make amundsen-stop          - Stop all Amundsen services"
	@echo "  make amundsen-down          - Remove all Amundsen services"
	@echo "  make amundsen-logs          - View all Amundsen logs"
	@echo "  make amundsen-frontend-up   - Start Amundsen frontend"
	@echo "  make amundsen-frontend-stop - Stop Amundsen frontend"
	@echo "  make amundsen-frontend-down - Remove Amundsen frontend"
	@echo "  make amundsen-frontend-logs - View Amundsen frontend logs"
	@echo "  make amundsen-metadata-up   - Start Amundsen metadata service"
	@echo "  make amundsen-metadata-stop - Stop Amundsen metadata service"
	@echo "  make amundsen-metadata-down - Remove Amundsen metadata service"
	@echo "  make amundsen-metadata-logs - View Amundsen metadata logs"
	@echo "  make amundsen-search-up     - Start Amundsen search service"
	@echo "  make amundsen-search-stop   - Stop Amundsen search service"
	@echo "  make amundsen-search-down   - Remove Amundsen search service"
	@echo "  make amundsen-search-logs   - View Amundsen search logs"
	@echo ""
	@echo "Prefect:"
	@echo "  make prefect-server-up      - Start Prefect server"
	@echo "  make prefect-server-stop    - Stop Prefect server"
	@echo "  make prefect-server-down    - Remove Prefect server"
	@echo "  make prefect-server-logs    - View Prefect server logs"
	@echo "  make prefect-worker-up      - Start Prefect worker"
	@echo "  make prefect-worker-stop    - Stop Prefect worker"
	@echo "  make prefect-worker-down    - Remove Prefect worker"
	@echo "  make prefect-worker-logs    - View Prefect worker logs"
	@echo "  make prefect-services-up    - Start all Prefect services"
	@echo "  make prefect-services-stop  - Stop all Prefect services"
	@echo "  make prefect-services-down  - Remove all Prefect services"
	@echo "  make prefect-services-logs  - View all Prefect logs"
	@echo ""
	@echo "Full stack:"
	@echo "  make up                     - Start all services"
	@echo "  make down                   - Stop all services"
	@echo "  make logs                   - View all logs"
	@echo "  make clean                  - Clean up everything"

# Environment check
# ──────────────────────────────────────────────────────────────
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
# MySQL Commands
# ──────────────────────────────────────────────────────────────
mysql-dev-build:
	@echo "🔨 Building and starting MySQL (detached)..."
	@docker-compose up -d --build mysql
	@echo "✓ MySQL started in background"

mysql-dev-up:
	@echo "🚀 Starting MySQL..."
	@docker-compose up -d mysql
	@echo "✓ MySQL started"

mysql-dev-stop:
	@echo "⏸️  Stopping MySQL..."
	@docker-compose stop mysql
	@echo "✓ MySQL stopped"

mysql-dev-down:
	@echo "🗑️  Removing MySQL..."
	@docker-compose rm -sf mysql
	@echo "✓ MySQL removed"

mysql-dev-restart:
	@echo "🔄 Restarting MySQL..."
	@docker-compose restart mysql
	@echo "✓ MySQL restarted"

# ──────────────────────────────────────────────────────────────
# Postgres Commands
# ──────────────────────────────────────────────────────────────
postgres-dev-up:
	@echo "🚀 Starting PostgreSQL..."
	@docker-compose up -d postgres
	@echo "✓ PostgreSQL started"

postgres-dev-stop:
	@docker-compose stop postgres

postgres-dev-down:
	@docker-compose rm -sf postgres

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
# n8n Commands
# ──────────────────────────────────────────────────────────────
n8n-up-build:
	@echo "🚀 Building and starting n8n..."
	@docker-compose up -d --build n8n
	@echo "✓ n8n started at http://localhost:5678"

n8n-up:
	@echo "🚀 Starting n8n..."
	@docker-compose up -d n8n
	@echo "✓ n8n started"

n8n-stop:
	@echo "⏸️  Stopping n8n..."
	@docker-compose stop n8n
	@echo "✓ n8n stopped"

n8n-down:
	@echo "🗑️  Removing n8n..."
	@docker-compose rm -sf n8n
	@echo "✓ n8n removed"

n8n-logs:
	@docker-compose logs -f n8n

n8n-restart:
	@echo "🔄 Restarting n8n..."
	@docker-compose restart n8n
	@echo "✓ n8n restarted"

n8n-shell:
	@docker-compose exec n8n /bin/sh

n8n-init-db:
	@echo "🗄️  Initializing n8n database..."
	@docker exec -i postgres psql -U postgres < workflows/n8n/init-n8n-db.sql
	@echo "✓ n8n database initialized"

# ──────────────────────────────────────────────────────────────
# MetaBase Commands
# ──────────────────────────────────────────────────────────────
metabase-dev-up-build:
	@echo "🚀 Building and starting Metabase..."
	@docker-compose up -d --build metabase
	@echo "✓ Metabase started at http://localhost:3000"

metabase-dev-up:
	@echo "🚀 Starting Metabase..."
	@docker-compose up -d metabase
	@echo "✓ Metabase started at http://localhost:3000"

metabase-dev-stop:
	@echo "⏸️  Stopping Metabase..."
	@docker-compose stop metabase
	@echo "✓ Metabase stopped"

metabase-dev-down:
	@echo "🗑️  Removing Metabase..."
	@docker-compose rm -sf metabase
	@echo "✓ Metabase removed"

metabase-provision:
	@echo "🔌 Provisioning Metabase database connections..."
	@python 07_dashboards/04_metabase/provisioning/provision_metabase.py

metabase-provision-dry-run:
	@python 07_dashboards/04_metabase/provisioning/provision_metabase.py --dry-run

# ──────────────────────────────────────────────────────────────
# Superset Commands
# ──────────────────────────────────────────────────────────────
superset-dev-build:
	@echo "🔨 Building and starting Superset (detached)..."
	@docker-compose up -d --build apache-superset
	@echo "✓ Superset started at http://localhost:8088"

superset-dev-up:
	@echo "🚀 Starting Superset..."
	@docker-compose up -d apache-superset
	@echo "✓ Superset started at http://localhost:8088"

superset-dev-stop:
	@echo "⏸️  Stopping Superset..."
	@docker-compose stop apache-superset
	@echo "✓ Superset stopped"

superset-dev-down:
	@echo "🗑️  Removing Superset..."
	@docker-compose rm -sf apache-superset
	@echo "✓ Superset removed"

superset-dev-logs:
	@docker-compose logs -f apache-superset

superset-dev-restart:
	@echo "🔄 Restarting Superset..."
	@docker-compose restart apache-superset
	@echo "✓ Superset restarted"

superset-shell:
	@docker-compose exec apache-superset bash

# ──────────────────────────────────────────────────────────────
# Redash Commands
# ──────────────────────────────────────────────────────────────
redash-dev-build:
	@echo "🔨 Building and starting Redash (detached)..."
	@docker-compose up -d --build redash-server redash-scheduler redash-worker
	@echo "✓ Redash started at http://localhost:$${REDASH_PORT:-5001}"

redash-dev-up:
	@echo "🚀 Starting Redash..."
	@docker-compose up -d redash-server redash-scheduler redash-worker
	@echo "✓ Redash started at http://localhost:$${REDASH_PORT:-5001}"
	@echo "  First time only: run 'make redash-init-db' before opening the UI."

redash-dev-stop:
	@echo "⏸️  Stopping Redash..."
	@docker-compose stop redash-server redash-scheduler redash-worker
	@echo "✓ Redash stopped"

redash-dev-down:
	@echo "🗑️  Removing Redash..."
	@docker-compose rm -sf redash-server redash-scheduler redash-worker
	@echo "✓ Redash removed"

redash-dev-logs:
	@docker-compose logs -f redash-server redash-scheduler redash-worker

redash-dev-restart:
	@echo "🔄 Restarting Redash..."
	@docker-compose restart redash-server redash-scheduler redash-worker
	@echo "✓ Redash restarted"

redash-init-db:
	@echo "🗄️  Running Redash schema migration (create_db)..."
	@docker-compose run --rm redash-server create_db
	@echo "✓ Redash database initialized"

redash-provision:
	@echo "🔌 Provisioning Redash data sources and dashboards..."
	@python 07_dashboards/03_redash/provisioning/provision_redash.py

redash-provision-dry-run:
	@python 07_dashboards/03_redash/provisioning/provision_redash.py --dry-run

# ──────────────────────────────────────────────────────────────
# Grafana Commands
# ──────────────────────────────────────────────────────────────
grafana-up-build:
	@echo "🔨 Building and starting Grafana (detached)..."
	@docker-compose up -d --build grafana
	@echo "✓ Grafana started at http://localhost:3006"

grafana-up:
	@echo "🚀 Starting Grafana..."
	@docker-compose up -d grafana
	@echo "✓ Grafana started at http://localhost:3006"

grafana-stop:
	@echo "⏸️  Stopping Grafana..."
	@docker-compose stop grafana
	@echo "✓ Grafana stopped"

grafana-down:
	@echo "🗑️  Removing Grafana..."
	@docker-compose rm -sf grafana
	@echo "✓ Grafana removed"

grafana-logs:
	@docker-compose logs -f grafana

grafana-restart:
	@echo "🔄 Restarting Grafana..."
	@docker-compose restart grafana
	@echo "✓ Grafana restarted"

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

grafana-stack-up:
	@echo "Starting full Grafana observability stack..."
	@docker-compose up -d --build grafana prometheus loki postgres-db-exporter
	@echo "✓ Grafana stack started (Grafana: http://localhost:3006)"

grafana-stack-stop:
	@echo "Stopping full Grafana observability stack..."
	@docker-compose stop grafana prometheus loki postgres-db-exporter
	@echo "✓ Grafana stack stopped"

grafana-stack-down:
	@echo "Removing full Grafana observability stack..."
	@docker-compose rm -sf grafana prometheus loki postgres-db-exporter
	@echo "✓ Grafana stack removed"

grafana-stack-logs:
	@docker-compose logs -f grafana prometheus loki postgres-db-exporter

# ──────────────────────────────────────────────────────────────
# Elasticsearch Commands
# ──────────────────────────────────────────────────────────────
elasticsearch-up:
	@echo "Starting Elasticsearch..."
	@docker-compose up -d elasticsearch
	@echo "Elasticsearch started"

elasticsearch-stop:
	@echo "Stopping Elasticsearch..."
	@docker-compose stop elasticsearch
	@echo "Elasticsearch stopped"

elasticsearch-down:
	@echo "Removing Elasticsearch..."
	@docker-compose rm -sf elasticsearch
	@echo "Elasticsearch removed"

elasticsearch-logs:
	@docker-compose logs -f elasticsearch

# ──────────────────────────────────────────────────────────────
# Kibana Commands
# ──────────────────────────────────────────────────────────────
kibana-up:
	@echo "Starting Kibana..."
	@docker-compose up -d kibana
	@echo "Kibana started at http://localhost:5601"

kibana-stop:
	@echo "Stopping Kibana..."
	@docker-compose stop kibana
	@echo "Kibana stopped"

kibana-down:
	@echo "Removing Kibana..."
	@docker-compose rm -sf kibana
	@echo "Kibana removed"

kibana-logs:
	@docker-compose logs -f kibana

# ──────────────────────────────────────────────────────────────
# Neo4j Commands
# ──────────────────────────────────────────────────────────────
neo4j-up:
	@echo "Starting Neo4j..."
	@docker-compose up -d neo4j
	@echo "Neo4j started at http://localhost:7474"

neo4j-stop:
	@echo "Stopping Neo4j..."
	@docker-compose stop neo4j
	@echo "Neo4j stopped"

neo4j-down:
	@echo "Removing Neo4j..."
	@docker-compose rm -sf neo4j
	@echo "Neo4j removed"

neo4j-logs:
	@docker-compose logs -f neo4j

# ──────────────────────────────────────────────────────────────
# Redis Commands
# ──────────────────────────────────────────────────────────────
redis-dev-up:
	@echo "Starting Redis..."
	@docker-compose up -d redis
	@echo "Redis started"

redis-dev-stop:
	@echo "Stopping Redis..."
	@docker-compose stop redis
	@echo "Redis stopped"

redis-dev-down:
	@echo "Removing Redis..."
	@docker-compose rm -sf redis
	@echo "Redis removed"

redis-dev-logs:
	@docker-compose logs -f redis

# ──────────────────────────────────────────────────────────────
# RedisInsight Commands
# ──────────────────────────────────────────────────────────────
redisinsight-dev-up:
	@echo "Starting RedisInsight..."
	@docker-compose up -d redisinsight
	@echo "RedisInsight started at http://localhost:8001"

redisinsight-dev-stop:
	@echo "Stopping RedisInsight..."
	@docker-compose stop redisinsight
	@echo "RedisInsight stopped"

redisinsight-dev-down:
	@echo "Removing RedisInsight..."
	@docker-compose rm -sf redisinsight
	@echo "RedisInsight removed"

redisinsight-dev-logs:
	@docker-compose logs -f redisinsight

# ──────────────────────────────────────────────────────────────
# Trino Commands
# ──────────────────────────────────────────────────────────────
trino-up:
	@echo "Starting Trino..."
	@docker-compose up -d trino
	@echo "Trino started at http://localhost:8080"

trino-stop:
	@echo "Stopping Trino..."
	@docker-compose stop trino
	@echo "Trino stopped"

trino-down:
	@echo "Removing Trino..."
	@docker-compose rm -sf trino
	@echo "Trino removed"

trino-logs:
	@docker-compose logs -f trino

# ──────────────────────────────────────────────────────────────
# Amundsen Commands
# ──────────────────────────────────────────────────────────────
amundsen-frontend-up:
	@echo "Starting Amundsen frontend..."
	@docker-compose up -d amundsen-frontend
	@echo "Amundsen frontend started at http://localhost:5000"

amundsen-frontend-stop:
	@echo "Stopping Amundsen frontend..."
	@docker-compose stop amundsen-frontend
	@echo "Amundsen frontend stopped"

amundsen-frontend-down:
	@echo "Removing Amundsen frontend..."
	@docker-compose rm -sf amundsen-frontend
	@echo "Amundsen frontend removed"

amundsen-frontend-logs:
	@docker-compose logs -f amundsen-frontend

amundsen-metadata-up:
	@echo "Starting Amundsen metadata service..."
	@docker-compose up -d amundsen-metadata
	@echo "Amundsen metadata service started"

amundsen-metadata-stop:
	@echo "Stopping Amundsen metadata service..."
	@docker-compose stop amundsen-metadata
	@echo "Amundsen metadata service stopped"

amundsen-metadata-down:
	@echo "Removing Amundsen metadata service..."
	@docker-compose rm -sf amundsen-metadata
	@echo "Amundsen metadata service removed"

amundsen-metadata-logs:
	@docker-compose logs -f amundsen-metadata

amundsen-search-up:
	@echo "Starting Amundsen search service..."
	@docker-compose up -d amundsen-search
	@echo "Amundsen search service started"

amundsen-search-stop:
	@echo "Stopping Amundsen search service..."
	@docker-compose stop amundsen-search
	@echo "Amundsen search service stopped"

amundsen-search-down:
	@echo "Removing Amundsen search service..."
	@docker-compose rm -sf amundsen-search
	@echo "Amundsen search service removed"

amundsen-search-logs:
	@docker-compose logs -f amundsen-search

amundsen-up:
	@echo "Starting all Amundsen services..."
	@docker-compose up -d amundsen-frontend amundsen-metadata amundsen-search
	@echo "Amundsen stack started (frontend: http://localhost:5000)"

amundsen-stop:
	@echo "Stopping all Amundsen services..."
	@docker-compose stop amundsen-frontend amundsen-metadata amundsen-search
	@echo "Amundsen stack stopped"

amundsen-down:
	@echo "Removing all Amundsen services..."
	@docker-compose rm -sf amundsen-frontend amundsen-metadata amundsen-search
	@echo "Amundsen stack removed"

amundsen-logs:
	@docker-compose logs -f amundsen-frontend amundsen-metadata amundsen-search

# ──────────────────────────────────────────────────────────────
# Prefect Commands
# ──────────────────────────────────────────────────────────────
prefect-server-up:
	@echo "Starting Prefect server..."
	@docker-compose up -d prefect-server
	@echo "Prefect server started at http://localhost:4200"

prefect-server-stop:
	@echo "Stopping Prefect server..."
	@docker-compose stop prefect-server
	@echo "Prefect server stopped"

prefect-server-down:
	@echo "Removing Prefect server..."
	@docker-compose rm -sf prefect-server
	@echo "Prefect server removed"

prefect-server-logs:
	@docker-compose logs -f prefect-server

prefect-worker-up:
	@echo "Starting Prefect worker..."
	@docker-compose up -d prefect-worker
	@echo "Prefect worker started"

prefect-worker-stop:
	@echo "Stopping Prefect worker..."
	@docker-compose stop prefect-worker
	@echo "Prefect worker stopped"

prefect-worker-down:
	@echo "Removing Prefect worker..."
	@docker-compose rm -sf prefect-worker
	@echo "Prefect worker removed"

prefect-worker-logs:
	@docker-compose logs -f prefect-worker

prefect-services-up:
	@echo "Starting all Prefect services..."
	@docker-compose up -d prefect-server prefect-worker
	@echo "Prefect services started (UI: http://localhost:4200)"

prefect-services-stop:
	@echo "Stopping all Prefect services..."
	@docker-compose stop prefect-server prefect-worker
	@echo "Prefect services stopped"

prefect-services-down:
	@echo "Removing all Prefect services..."
	@docker-compose rm -sf prefect-server prefect-worker
	@echo "Prefect services removed"

prefect-services-logs:
	@docker-compose logs -f prefect-server prefect-worker

