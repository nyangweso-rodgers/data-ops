# workflows/dagster/Makefile
# Dagster-specific commands

# Docker Compose file combinations
COMPOSE_BASE := docker-compose-dagster.base.yml
COMPOSE_DEV := -f $(COMPOSE_BASE) -f docker-compose-dagster.dev.yml
COMPOSE_PROD := -f $(COMPOSE_BASE) -f docker-compose-dagster.prod.yml

# Docker Compose command with root .env file
# Use relative path to avoid Windows path issues
DOCKER_COMPOSE := docker-compose --env-file ../../.env --env-file ../../ports.env

# Host port registry (single source of truth) - make reads it for the URLs below
include ../../ports.env

.PHONY: help dev-up-build dev-up dev-stop dev-down dev-logs dev-restart \
        prod-up prod-down prod-logs build clean env-info

# Default target
help:
	@echo "Dagster Commands:"
	@echo ""
	@echo "Development (metadata DB per DAGSTER_PG_DB_* in .env - local postgres or RDS):"
	@echo "  make dev-up-build   - Build and start dev Dagster"
	@echo "  make dev-up         - Start dev Dagster"
	@echo "  make dev-stop       - Stop dev Dagster"
	@echo "  make dev-down       - Stop and remove dev Dagster"
	@echo "  make dev-logs       - View dev logs"
	@echo "  make dev-restart    - Restart dev"
	@echo ""
	@echo "Production:"
	@echo "  make prod-up        - Start production Dagster (RDS)"
	@echo "  make prod-down      - Stop production Dagster"
	@echo "  make prod-logs      - View production logs"
	@echo ""
	@echo "Other:"
	@echo "  make build          - Rebuild Docker image"
	@echo "  make lock           - Re-resolve uv.lock after editing pyproject.toml"
	@echo "  make sync           - Create/update the local .venv from uv.lock (editor, tests)"
	@echo "  make clean          - Remove dev containers and volumes"
	@echo "  make env-info       - Show environment file location"

# Show which .env file is being used
env-info:
	@echo "Using .env file from: ../../.env"
	@if [ -f ../../.env ]; then \
		echo "✓ File exists"; \
		echo ""; \
		echo "Dagster-related variables:"; \
		grep -E "^DAGSTER_" ../../.env || echo "No DAGSTER_ variables found"; \
	else \
		echo "❌ File not found!"; \
	fi

# ──────────────────────────────────────────────────────────────
# Development
# ──────────────────────────────────────────────────────────────
dev-up-build:
	@echo "Building and starting dev Dagster..."
	@echo "Using .env from: ../../.env"
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d --build
	@echo "✓ Dagster UI: http://localhost:$(DAGSTER_HOST_PORT)"

dev-up:
	@echo "Starting dev Dagster..."
	@echo "Using .env from: ../../.env"
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d
	@echo "✓ Dagster UI: http://localhost:$(DAGSTER_HOST_PORT)"

dev-stop:
	@echo "Stopping dev Dagster..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) stop

dev-down:
	@echo "Stopping and removing dev Dagster..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) down

dev-logs:
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) logs -f

dev-restart: dev-down dev-up

# ──────────────────────────────────────────────────────────────
# Production
# ──────────────────────────────────────────────────────────────
prod-up:
	@echo "Starting production Dagster (RDS)..."
	@echo "Using .env from: ../../.env"
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) up -d
	@echo "✓ Dagster started"

prod-down:
	@echo "Stopping production Dagster..."
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) down

prod-logs:
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) logs -f

# ──────────────────────────────────────────────────────────────
# Build and Clean
# ──────────────────────────────────────────────────────────────
build:
	@echo "Rebuilding Docker images..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) build --no-cache
	@echo "✓ Build complete"

clean:
	@echo "Cleaning up dev environment..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) down -v
	@echo "✓ Cleaned up dev environment"

# ──────────────────────────────────────────────────────────────
# Python dependencies (uv) - pyproject.toml + uv.lock in this folder
# ──────────────────────────────────────────────────────────────
.PHONY: lock sync

lock:
	@uv lock
	@echo "✓ uv.lock updated - rebuild the image to apply it"

sync:
	@uv sync
