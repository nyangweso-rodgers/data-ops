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
		n8n-init-db n8n-up-build n8n-up n8n-down n8n-logs n8n-restart n8n-shell \
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
	@echo "  make n8n-up             - Start n8n"
	@echo "  make n8n-down           - Stop n8n"
	@echo "  make n8n-restart        - Restart n8n"
	@echo "  make n8n-shell          - Access n8n shell"
	@echo ""
	@echo "PostgreSQL:"
	@echo "  make postgres-up            - Start PostgreSQL"
	@echo "  make postgres-down          - Stop PostgreSQL"
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

n8n-down:
	@echo "⏸️  Stopping n8n..."
	@docker-compose stop n8n
	@echo "✓ n8n stopped"

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

