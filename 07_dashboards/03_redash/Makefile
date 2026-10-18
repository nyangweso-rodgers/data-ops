# 07_dashboards/03_redash/Makefile
# Redash commands (the root Makefile delegates redash-* targets here, e.g. make redash-dev-up)

# Docker Compose file combinations
COMPOSE_BASE := docker-compose-redash.base.yml
COMPOSE_DEV := -f $(COMPOSE_BASE) -f docker-compose-redash.dev.yml
COMPOSE_PROD := -f $(COMPOSE_BASE) -f docker-compose-redash.prod.yml

# Docker Compose command with root .env file
# Use relative path to avoid Windows path issues
DOCKER_COMPOSE := docker-compose --env-file ../../.env --env-file ../../ports.env

# Host port registry (single source of truth) - make reads it for the URLs below
include ../../ports.env

URL := http://localhost:$(REDASH_HOST_PORT)

.PHONY: help dev-up-build dev-up dev-stop dev-down dev-logs dev-restart \
        prod-up prod-down prod-logs pull init-db prod-init-db

# Default target
help:
	@echo "Redash Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev-up-build   - Build/pull and start"
	@echo "  make dev-up         - Start"
	@echo "  make dev-stop       - Stop"
	@echo "  make dev-down       - Stop and remove containers"
	@echo "  make dev-logs       - Follow logs"
	@echo "  make dev-restart    - Recreate containers"
	@echo ""
	@echo "Production:"
	@echo "  make prod-up        - Start production"
	@echo "  make prod-down      - Stop production"
	@echo "  make prod-logs      - Follow production logs"
	@echo ""
	@echo "Other:"
	@echo "  make pull           - Pull the pinned images"
	@echo "  make init-db        - One-time schema migration (create_db), dev"
	@echo "  make prod-init-db   - One-time schema migration (create_db), prod"

# ──────────────────────────────────────────────────────────────
# Development
# ──────────────────────────────────────────────────────────────
dev-up-build:
	@echo "Building and starting Redash (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d --build
	@echo "✓ Redash: $(URL)"

dev-up:
	@echo "Starting Redash (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d
	@echo "✓ Redash: $(URL)"

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
prod-up:
	@echo "Starting production Redash..."
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) up -d 
	@echo "✓ Redash started"

prod-down:
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) down

prod-logs:
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) logs -f

# ──────────────────────────────────────────────────────────────
# Images
# ──────────────────────────────────────────────────────────────
pull:
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) pull

# ──────────────────────────────────────────────────────────────
# Extras
# ──────────────────────────────────────────────────────────────
# Redash does not migrate its schema on boot - run once per database
init-db:
	@echo "Running Redash schema migration (create_db)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) run --rm redash-server create_db
	@echo "✓ Redash database initialized"

prod-init-db:
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) run --rm redash-server create_db
