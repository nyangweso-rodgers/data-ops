# 01-databases/mysql/Makefile
# MySQL commands (the root Makefile delegates mysql-* targets here, e.g. make mysql-dev-up)

# Docker Compose file combinations
COMPOSE_BASE := docker-compose-mysql.base.yml
COMPOSE_DEV := -f $(COMPOSE_BASE) -f docker-compose-mysql.dev.yml
COMPOSE_PROD := -f $(COMPOSE_BASE) -f docker-compose-mysql.prod.yml

# Docker Compose command with root .env file
# Use relative path to avoid Windows path issues
# -p data-ops: same project as the root docker-compose.yml, so these targets manage the
# containers the rest of the stack already uses (no "container name already in use")
DOCKER_COMPOSE := docker-compose -p data-ops --env-file ../../.env --env-file ../../ports.env

# Host port registry (single source of truth) - make reads it for the URLs below
include ../../ports.env

URL := localhost:$(MYSQL_HOST_PORT)

.PHONY: help dev-up-build dev-up dev-stop dev-down dev-logs dev-restart \
        prod-up prod-down prod-logs pull dev-cli

# Default target
help:
	@echo "MySQL Commands:"
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
	@echo "  make dev-cli        - mysql client in the mysql container"

# ──────────────────────────────────────────────────────────────
# Development
# ──────────────────────────────────────────────────────────────
dev-up-build:
	@echo "Building and starting MySQL (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d --build
	@echo "✓ MySQL: $(URL)"

dev-up:
	@echo "Starting MySQL (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d
	@echo "✓ MySQL: $(URL)"

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
	@echo "Starting production MySQL..."
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) up -d 
	@echo "✓ MySQL started"

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
dev-cli:
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) exec mysql sh -c 'mysql -uroot -p"$$MYSQL_ROOT_PASSWORD"'
