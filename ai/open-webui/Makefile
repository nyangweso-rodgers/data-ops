# ai/open-webui/Makefile
# Open WebUI commands (the root Makefile delegates open-webui-* targets here, e.g. make open-webui-dev-up)

# Docker Compose file combinations
COMPOSE_BASE := docker-compose-open-webui.base.yml
COMPOSE_DEV := -f $(COMPOSE_BASE) -f docker-compose-open-webui.dev.yml
COMPOSE_PROD := -f $(COMPOSE_BASE) -f docker-compose-open-webui.prod.yml

# Docker Compose command with root .env file
# Use relative path to avoid Windows path issues
DOCKER_COMPOSE := docker-compose --env-file ../../.env --env-file ../../ports.env

# Host port registry (single source of truth) - make reads it for the URLs below
include ../../ports.env

URL := http://localhost:$(OPEN_WEBUI_HOST_PORT)

.PHONY: help dev-up-build dev-up dev-stop dev-down dev-logs dev-restart \
        prod-up prod-down prod-logs pull dev-pull-model dev-models

# Default target
help:
	@echo "Open WebUI Commands:"
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
	@echo "  make dev-pull-model MODEL=<name> - Pull an Ollama model (e.g. MODEL=llama3.2)"
	@echo "  make dev-models     - List pulled Ollama models"

# ──────────────────────────────────────────────────────────────
# Development
# ──────────────────────────────────────────────────────────────
dev-up-build:
	@echo "Building and starting Open WebUI (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d --build
	@echo "✓ Open WebUI: $(URL)"

dev-up:
	@echo "Starting Open WebUI (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d
	@echo "✓ Open WebUI: $(URL)"

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
	@echo "Starting production Open WebUI..."
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) up -d 
	@echo "✓ Open WebUI started"

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
dev-pull-model:
	@test -n "$(MODEL)" || (echo "Usage: make dev-pull-model MODEL=<name>"; exit 1)
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) exec ollama ollama pull $(MODEL)

dev-models:
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) exec ollama ollama list
