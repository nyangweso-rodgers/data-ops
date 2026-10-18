# workflows/prefect/Makefile
# Prefect commands (the root Makefile delegates prefect-* targets here, e.g. make prefect-dev-up)

# Docker Compose file combinations
COMPOSE_BASE := docker-compose-prefect.base.yml
COMPOSE_DEV := -f $(COMPOSE_BASE) -f docker-compose-prefect.dev.yml
COMPOSE_PROD := -f $(COMPOSE_BASE) -f docker-compose-prefect.prod.yml

# Docker Compose command with root .env file
# Use relative path to avoid Windows path issues
DOCKER_COMPOSE := docker-compose --env-file ../../.env --env-file ../../ports.env

# Host port registry (single source of truth) - make reads it for the URLs below
include ../../ports.env

URL := http://localhost:$(PREFECT_HOST_PORT)

.PHONY: help dev-up-build dev-up dev-stop dev-down dev-logs dev-restart \
        prod-up prod-down prod-logs build

# Default target
help:
	@echo "Prefect Commands:"
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
	@echo "  make build          - Rebuild images (no cache)"
	@echo "  make lock           - Re-resolve uv.lock after editing pyproject.toml"
	@echo "  make sync           - Create/update the local .venv from uv.lock (editor, tests)"

# ──────────────────────────────────────────────────────────────
# Development
# ──────────────────────────────────────────────────────────────
dev-up-build:
	@echo "Building and starting Prefect (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d --build
	@echo "✓ Prefect: $(URL)"

dev-up:
	@echo "Starting Prefect (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d
	@echo "✓ Prefect: $(URL)"

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
	@echo "Starting production Prefect..."
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) up -d --build
	@echo "✓ Prefect started"

prod-down:
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) down

prod-logs:
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) logs -f

# ──────────────────────────────────────────────────────────────
# Images
# ──────────────────────────────────────────────────────────────
build:
	@echo "Rebuilding Prefect images..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) build --no-cache
	@echo "✓ Build complete"

# ──────────────────────────────────────────────────────────────
# Python dependencies (uv) - pyproject.toml + uv.lock in this folder
# ──────────────────────────────────────────────────────────────
.PHONY: lock sync

lock:
	@uv lock
	@echo "✓ uv.lock updated - rebuild the image to apply it"

sync:
	@uv sync
