# workflows/n8n/Makefile
# n8n commands (the root Makefile delegates n8n-* targets here, e.g. make n8n-dev-up)

# Docker Compose file combinations
COMPOSE_BASE := docker-compose-n8n.base.yml
COMPOSE_DEV := -f $(COMPOSE_BASE) -f docker-compose-n8n.dev.yml
COMPOSE_PROD := -f $(COMPOSE_BASE) -f docker-compose-n8n.prod.yml

# Docker Compose command with root .env file
# Use relative path to avoid Windows path issues
DOCKER_COMPOSE := docker-compose --env-file ../../.env --env-file ../../ports.env

# Host port registry (single source of truth) - make reads it for the URLs below
include ../../ports.env

URL := http://localhost:$(N8N_HOST_PORT)

.PHONY: help dev-up-build dev-up dev-stop dev-down dev-logs dev-restart \
        prod-up prod-down prod-logs pull dev-shell init-db

# Default target
help:
	@echo "n8n Commands:"
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
	@echo "  make dev-shell      - Shell in the n8n container"
	@echo "  make init-db        - Create the n8n database in the local postgres container"

# ──────────────────────────────────────────────────────────────
# Development
# ──────────────────────────────────────────────────────────────
dev-up-build:
	@echo "Building and starting n8n (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d --build
	@echo "✓ n8n: $(URL)"

dev-up:
	@echo "Starting n8n (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d
	@echo "✓ n8n: $(URL)"

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
	@echo "Starting production n8n..."
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) up -d 
	@echo "✓ n8n started"

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
dev-shell:
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) exec n8n /bin/sh

init-db:
	@echo "Initializing n8n database..."
	@docker exec -i postgres psql -U postgres < init-n8n-db.sql
	@echo "✓ n8n database initialized"
