# 03_messaging_services/kafka/Makefile
# Kafka commands (the root Makefile delegates kafka-* targets here, e.g. make kafka-dev-up)

# Docker Compose file combinations
COMPOSE_BASE := docker-compose-kafka.base.yml
COMPOSE_DEV := -f $(COMPOSE_BASE) -f docker-compose-kafka.dev.yml
COMPOSE_PROD := -f $(COMPOSE_BASE) -f docker-compose-kafka.prod.yml

# Docker Compose command with root .env file
# Use relative path to avoid Windows path issues
DOCKER_COMPOSE := docker-compose --env-file ../../.env --env-file ../../ports.env

# Host port registry (single source of truth) - make reads it for the URLs below
include ../../ports.env

URL := localhost:$(KAFKA_HOST_PORT) (UI: http://localhost:$(KAFKA_UI_HOST_PORT))

.PHONY: help dev-up-build dev-up dev-stop dev-down dev-logs dev-restart \
        prod-up prod-down prod-logs build dev-topics

# Default target
help:
	@echo "Kafka Commands:"
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
	@echo "  make dev-topics     - List topics"

# ──────────────────────────────────────────────────────────────
# Development
# ──────────────────────────────────────────────────────────────
dev-up-build:
	@echo "Building and starting Kafka (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d --build
	@echo "✓ Kafka: $(URL)"

dev-up:
	@echo "Starting Kafka (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d
	@echo "✓ Kafka: $(URL)"

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
	@echo "Starting production Kafka..."
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) up -d --build
	@echo "✓ Kafka started"

prod-down:
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) down

prod-logs:
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) logs -f

# ──────────────────────────────────────────────────────────────
# Images
# ──────────────────────────────────────────────────────────────
build:
	@echo "Rebuilding Kafka images..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) build --no-cache
	@echo "✓ Build complete"

# ──────────────────────────────────────────────────────────────
# Extras
# ──────────────────────────────────────────────────────────────
dev-topics:
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) exec kafka kafka-topics --bootstrap-server kafka:29092 --list
