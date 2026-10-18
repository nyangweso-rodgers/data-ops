# 07_dashboards/grafana/Makefile
# Grafana stack commands (the root Makefile delegates its grafana-* targets here)
# Stack = grafana + prometheus + loki + postgres-db-exporter

# Docker Compose file combinations
COMPOSE_BASE := docker-compose-grafana.base.yml
COMPOSE_DEV := -f $(COMPOSE_BASE) -f docker-compose-grafana.dev.yml
COMPOSE_PROD := -f $(COMPOSE_BASE) -f docker-compose-grafana.prod.yml

# Docker Compose command with root .env file
# Use relative path to avoid Windows path issues
DOCKER_COMPOSE := docker-compose --env-file ../../.env --env-file ../../ports.env

# Host port registry (single source of truth) - make reads it for the URLs below
include ../../ports.env

GRAFANA_URL := http://localhost:$(GRAFANA_HOST_PORT)

.PHONY: help dev-up-build dev-up dev-stop dev-down dev-logs dev-restart \
        prod-up prod-down prod-logs build

# Default target
help:
	@echo "Grafana Stack Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev-up-build   - Build and start the stack"
	@echo "  make dev-up         - Start the stack"
	@echo "  make dev-stop       - Stop the stack"
	@echo "  make dev-down       - Stop and remove the stack"
	@echo "  make dev-logs       - Follow stack logs"
	@echo "  make dev-restart    - Recreate the stack"
	@echo ""
	@echo "Production:"
	@echo "  make prod-up        - Build and start the production stack"
	@echo "  make prod-down      - Stop the production stack"
	@echo "  make prod-logs      - Follow production logs"
	@echo ""
	@echo "Other:"
	@echo "  make build          - Rebuild the Grafana image (no cache)"

# ──────────────────────────────────────────────────────────────
# Development
# ──────────────────────────────────────────────────────────────
dev-up-build:
	@echo "Building and starting Grafana stack (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d --build
	@echo "✓ Grafana: $(GRAFANA_URL)"

dev-up:
	@echo "Starting Grafana stack (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d
	@echo "✓ Grafana: $(GRAFANA_URL)"

dev-stop:
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) stop

dev-down:
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) down

dev-logs:
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) logs -f

dev-restart: dev-down dev-up

# ──────────────────────────────────────────────────────────────
# Production
# ──────────────────────────────────────────────────────────────
# --build so the image always carries the current provisioning/
prod-up:
	@echo "Starting production Grafana stack..."
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) up -d --build
	@echo "✓ Grafana stack started"

prod-down:
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) down

prod-logs:
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) logs -f

# ──────────────────────────────────────────────────────────────
# Build
# ──────────────────────────────────────────────────────────────
build:
	@echo "Rebuilding Grafana image..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) build --no-cache grafana
	@echo "✓ Build complete"
