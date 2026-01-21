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
# PostgreSQL Commands
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

# PostgreSQL commands
postgres-up:
	@docker-compose up -d postgres

postgres-down:
	@docker-compose stop postgres

# Full stack
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