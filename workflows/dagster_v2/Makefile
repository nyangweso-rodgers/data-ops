# workflows/dagster_v2/Makefile
# Dagster-specific commands

# Docker Compose file combinations
COMPOSE_BASE := docker-compose-dagster.base.yml
COMPOSE_LOCAL := -f $(COMPOSE_BASE) -f docker-compose-dagster.local.yml
COMPOSE_LOCAL_RDS := -f $(COMPOSE_BASE) -f docker-compose-dagster.local-rds.yml
COMPOSE_PROD := -f $(COMPOSE_BASE) -f docker-compose-dagster.prod.yml

# Docker Compose command with root .env file
# Use relative path to avoid Windows path issues
DOCKER_COMPOSE := docker-compose --env-file ../../.env

.PHONY: help local-up-build local-up local-stop local-down local-logs local-restart \
        local-rds-up-build local-rds-up local-rds-stop local-rds-down local-rds-logs local-rds-restart \
        prod-up prod-down prod-logs build clean env-info

# Default target
help:
	@echo "Dagster Commands:"
	@echo ""
	@echo "Local Development (local postgres):"
	@echo "  make local-up-build - Build and start local Dagster"
	@echo "  make local-up       - Start local Dagster"
	@echo "  make local-stop     - Stop local Dagster"
	@echo "  make local-down     - Stop and remove local Dagster"
	@echo "  make local-logs     - View local logs"
	@echo "  make local-restart  - Restart local"
	@echo ""
	@echo "Local + RDS (real AWS RDS instead of local postgres container):"
	@echo "  make local-rds-up-build - Build and start local Dagster (using RDS)"
	@echo "  make local-rds-up       - Start local Dagster (using RDS)"
	@echo "  make local-rds-stop     - Stop local Dagster (RDS mode)"
	@echo "  make local-rds-down     - Stop and remove local Dagster (RDS mode)"
	@echo "  make local-rds-logs     - View logs for local Dagster (RDS mode)"
	@echo "  make local-rds-restart  - Restart local Dagster (RDS mode)"
	@echo ""
	@echo "Production:"
	@echo "  make prod-up        - Start production Dagster (RDS)"
	@echo "  make prod-down      - Stop production Dagster"
	@echo "  make prod-logs      - View production logs"
	@echo ""
	@echo "Other:"
	@echo "  make build          - Rebuild Docker image"
	@echo "  make clean          - Remove all containers and volumes"
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
# Local development (with local postgres)
# ──────────────────────────────────────────────────────────────
local-up-build:
	@echo "Building and starting local Dagster..."
	@echo "Using .env from: ../../.env"
	@$(DOCKER_COMPOSE) $(COMPOSE_LOCAL) up -d --build
	@echo "✓ Dagster UI: http://localhost:3004"

local-up:
	@echo "Starting local Dagster..."
	@echo "Using .env from: ../../.env"
	@$(DOCKER_COMPOSE) $(COMPOSE_LOCAL) up -d
	@echo "✓ Dagster UI: http://localhost:3004"

local-stop:
	@echo "Stopping local Dagster..."
	@$(DOCKER_COMPOSE) $(COMPOSE_LOCAL) stop

local-down:
	@echo "Stopping and removing local Dagster..."
	@$(DOCKER_COMPOSE) $(COMPOSE_LOCAL) down

local-logs:
	@$(DOCKER_COMPOSE) $(COMPOSE_LOCAL) logs -f

local-restart: local-down local-up

# ──────────────────────────────────────────────────────────────
# Local + RDS (real AWS RDS instead of local postgres container)
# ──────────────────────────────────────────────────────────────
local-rds-up-build:
	@echo "Building and starting local Dagster (using RDS)..."
	@echo "Using .env from: ../../.env"
	@$(DOCKER_COMPOSE) $(COMPOSE_LOCAL_RDS) up -d --build
	@echo "✓ Dagster UI: http://localhost:3004 (connected to RDS)"

local-rds-up:
	@echo "Starting local Dagster (using RDS)..."
	@echo "Using .env from: ../../.env"
	@$(DOCKER_COMPOSE) $(COMPOSE_LOCAL_RDS) up -d
	@echo "✓ Dagster UI: http://localhost:3004 (connected to RDS)"

local-rds-stop:
	@echo "Stopping local Dagster (RDS mode)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_LOCAL_RDS) stop

local-rds-down:
	@echo "Stopping and removing local Dagster (RDS mode)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_LOCAL_RDS) down

local-rds-logs:
	@$(DOCKER_COMPOSE) $(COMPOSE_LOCAL_RDS) logs -f

local-rds-restart: local-rds-down local-rds-up

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
	@echo "Cleaning up local environment..."
	@$(DOCKER_COMPOSE) $(COMPOSE_LOCAL) down -v
	@echo "✓ Cleaned up local environment"