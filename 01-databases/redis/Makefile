# 01-databases/redis/Makefile
# Redis commands (the root Makefile delegates redis-* targets here, e.g. make redis-dev-up)

# Docker Compose file combinations
COMPOSE_BASE := docker-compose-redis.base.yml
COMPOSE_DEV := -f $(COMPOSE_BASE) -f docker-compose-redis.dev.yml
COMPOSE_PROD := -f $(COMPOSE_BASE) -f docker-compose-redis.prod.yml

# Docker Compose command with root .env file
# Use relative path to avoid Windows path issues
DOCKER_COMPOSE := docker-compose --env-file ../../.env --env-file ../../ports.env

# Host port registry (single source of truth) - make reads it for the URLs below
include ../../ports.env

URL := localhost:$(REDIS_HOST_PORT) (RedisInsight: http://localhost:$(REDISINSIGHT_HOST_PORT))

.PHONY: help dev-up-build dev-up dev-stop dev-down dev-logs dev-restart \
        prod-up prod-down prod-logs pull dev-cli

# Default target
help:
	@echo "Redis Commands:"
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
	@echo "  make dev-cli        - redis-cli in the redis container"

# ──────────────────────────────────────────────────────────────
# Development
# ──────────────────────────────────────────────────────────────
dev-up-build:
	@echo "Building and starting Redis (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d --build
	@echo "✓ Redis: $(URL)"

dev-up:
	@echo "Starting Redis (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d
	@echo "✓ Redis: $(URL)"

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
	@echo "Starting production Redis..."
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) up -d 
	@echo "✓ Redis started"

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
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) exec redis sh -c 'redis-cli -a "$$REDIS_PASSWORD"'
