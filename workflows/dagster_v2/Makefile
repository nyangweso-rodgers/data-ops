# workflows/dagster/Makefile
# Simple command shortcuts for Dagster

# Docker Compose file combinations
COMPOSE_BASE := docker-compose-dagster.base.yml
COMPOSE_LOCAL := -f $(COMPOSE_BASE) -f docker-compose-dagster.local.yml
COMPOSE_PROD := -f $(COMPOSE_BASE) -f docker-compose-dagster.prod.yml

.PHONY: help local-up-build local-up local-stop local-down local-logs local-restart \
        prod-up prod-down prod-logs build clean

# Default target
help:
	@echo "Dagster Commands:"
	@echo ""
	@echo "Local Development:"
	@echo "  make local-up-build - Build and start local Dagster"
	@echo "  make local-up       - Start local Dagster"
	@echo "  make local-stop     - Stop local Dagster"
	@echo "  make local-down     - Stop and remove local Dagster"
	@echo "  make local-logs     - View local logs"
	@echo "  make local-restart  - Restart local"
	@echo ""
	@echo "Production:"
	@echo "  make prod-up        - Start production Dagster (RDS)"
	@echo "  make prod-down      - Stop production Dagster"
	@echo "  make prod-logs      - View production logs"
	@echo ""
	@echo "Other:"
	@echo "  make build          - Rebuild Docker image"
	@echo "  make clean          - Remove all containers and volumes"

# Local development
local-up-build:
	@echo "Building and starting local Dagster..."
	@docker-compose $(COMPOSE_LOCAL) up -d --build
	@echo "✓ Dagster UI: http://localhost:3004"

local-up:
	@echo "Starting local Dagster..."
	@docker-compose $(COMPOSE_LOCAL) up -d
	@echo "✓ Dagster UI: http://localhost:3004"

local-stop:
	@echo "Stopping local Dagster..."
	@docker-compose $(COMPOSE_LOCAL) stop

local-down:
	@echo "Stopping and removing local Dagster..."
	@docker-compose $(COMPOSE_LOCAL) down

local-logs:
	@docker-compose $(COMPOSE_LOCAL) logs -f

local-restart: local-down local-up

# Production
prod-up:
	@echo "Starting production Dagster (RDS)..."
	@docker-compose $(COMPOSE_PROD) up -d
	@echo "✓ Dagster started"

prod-down:
	@echo "Stopping production Dagster..."
	@docker-compose $(COMPOSE_PROD) down

prod-logs:
	@docker-compose $(COMPOSE_PROD) logs -f

# Build
build:
	@echo "Rebuilding Docker images..."
	@docker-compose -f $(COMPOSE_BASE) build --no-cache
	@echo "✓ Build complete"

# Clean up
clean:
	@echo "Cleaning up local environment..."
	@docker-compose $(COMPOSE_LOCAL) down -v
	@echo "✓ Cleaned up local environment"