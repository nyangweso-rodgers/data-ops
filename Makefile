# data-ops/Makefile
# Root Makefile for the entire data-ops monorepo

DAGSTER_DIR := workflows/dagster_v2

.PHONY: help dagster-local-up-build dagster-local-up dagster-local-stop \
        dagster-local-down dagster-local-logs dagster-local-restart \
        dagster-prod-up dagster-prod-down dagster-prod-logs dagster-build \
        postgres-up postgres-down up down logs clean

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
	@echo "PostgreSQL:"
	@echo "  make postgres-up            - Start PostgreSQL"
	@echo "  make postgres-down          - Stop PostgreSQL"
	@echo ""
	@echo "Full stack:"
	@echo "  make up                     - Start all services"
	@echo "  make down                   - Stop all services"
	@echo "  make logs                   - View all logs"
	@echo "  make clean                  - Clean up everything"

# Dagster commands (delegate to workflows/dagster_v2/Makefile)
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