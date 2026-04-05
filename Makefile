# data-ops/Makefile
# Root Makefile for the entire data-ops monorepo

DAGSTER_DIR := workflows/dagster_v2
ROOT_DIR := $(shell pwd)

# Export ROOT_DIR so nested Makefiles can use it
export ROOT_DIR

.PHONY: help env-check\
		mysql-build mysql-up mysql-stop mysql-down mysql-logs mysql-restart \
		postgres-up postgres-stop postgres-down postgres-logs \
		dagster-local-up-build dagster-local-up dagster-local-stop \
        dagster-local-down dagster-local-logs dagster-local-restart \
        dagster-local-rds-up-build dagster-local-rds-up dagster-local-rds-stop \
        dagster-local-rds-down dagster-local-rds-logs dagster-local-rds-restart \
        dagster-prod-up dagster-prod-down dagster-prod-logs dagster-build \
		n8n-init-db n8n-up-build n8n-up n8n-down n8n-logs n8n-restart n8n-shell \
        up down logs clean

help:
	@echo "Data-Ops Monorepo Commands:"
	@echo ""
	@echo "  make mysql-build           - Build and start MySQL (detached)"
	@echo "  make mysql-up              - Start MySQL (attached, shows logs)"
	@echo "  make mysql-stop            - Stop MySQL"
	@echo "  make mysql-down            - Remove MySQL"
	@echo "  make mysql-logs            - View MySQL logs"
	@echo "  make mysql-restart         - Restart MySQL"
	@echo ""
	@echo "  make postgres-up           - Start PostgreSQL"
	@echo "  make postgres-stop         - Stop PostgreSQL"
	@echo "  make postgres-down         - Remove PostgreSQL"
	@echo "  make postgres-logs         - View PostgreSQL logs"
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
	@echo "  make n8n-logs           - View n8n logs"
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
mysql-build:
	@echo "🔨 Building and starting MySQL (detached)..."
	@docker-compose up -d --build mysql
	@echo "✓ MySQL started in background"

mysql-up:
	@echo "🚀 Starting MySQL (attached)..."
	@docker-compose up mysql

mysql-stop:
	@echo "⏸️  Stopping MySQL..."
	@docker-compose stop mysql
	@echo "✓ MySQL stopped"

mysql-down:
	@echo "🗑️  Removing MySQL..."
	@docker-compose rm -sf mysql
	@echo "✓ MySQL removed"

mysql-logs:
	@docker-compose logs -f mysql

mysql-restart:
	@echo "🔄 Restarting MySQL..."
	@docker-compose restart mysql
	@echo "✓ MySQL restarted"

# ──────────────────────────────────────────────────────────────
# Postgres Commands
# ──────────────────────────────────────────────────────────────
postgres-up:
	@echo "🚀 Starting PostgreSQL..."
	@docker-compose up -d postgres
	@echo "✓ PostgreSQL started"

postgres-stop:
	@docker-compose stop postgres

postgres-down:
	@docker-compose rm -sf postgres

postgres-logs:
	@docker-compose logs -f postgres

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

dagster-local-logs:
	@$(MAKE) -C $(DAGSTER_DIR) local-logs

dagster-local-restart:
	@$(MAKE) -C $(DAGSTER_DIR) local-restart

# ──────────────────────────────────────────────────────────────
# Dagster - Local + RDS (real AWS RDS instead of local postgres container)
# ──────────────────────────────────────────────────────────────

dagster-local-rds-up-build:
	@$(MAKE) -C $(DAGSTER_DIR) local-rds-up-build

dagster-local-rds-up:
	@$(MAKE) -C $(DAGSTER_DIR) local-rds-up

dagster-local-rds-stop:
	@$(MAKE) -C $(DAGSTER_DIR) local-rds-stop

dagster-local-rds-down:
	@$(MAKE) -C $(DAGSTER_DIR) local-rds-down

dagster-local-rds-logs:
	@$(MAKE) -C $(DAGSTER_DIR) local-rds-logs

dagster-local-rds-restart:
	@$(MAKE) -C $(DAGSTER_DIR) local-rds-restart

# ──────────────────────────────────────────────────────────────
# Dagster - Production
# ──────────────────────────────────────────────────────────────
dagster-prod-up:
	@$(MAKE) -C $(DAGSTER_DIR) prod-up

dagster-prod-down:
	@$(MAKE) -C $(DAGSTER_DIR) prod-down

dagster-prod-logs:
	@$(MAKE) -C $(DAGSTER_DIR) prod-logs

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
# Full Stack Commands
# ──────────────────────────────────────────────────────────────
up:
	@docker-compose up -d

down:
	@docker-compose down

logs:
	@docker-compose logs -f

clean:
	@$(MAKE) -C $(DAGSTER_DIR) clean
	@docker-compose down -v
	@echo "✓ All services cleaned"