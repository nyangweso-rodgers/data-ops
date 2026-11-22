# web-apps/Makefile
# Docker commands for the Next.js apps in apps/. Each app has its own targets, so
# you can build/run/test one app on its own:
#   make web-portal-dev-up        (from the repo root: same command)
#   make survey-app-dev-logs
# The all-apps targets (dev-up, dev-down, ...) are a convenience on top.

# Docker Compose file combinations
COMPOSE_BASE := docker-compose-web-apps.base.yml
COMPOSE_DEV := -f $(COMPOSE_BASE) -f docker-compose-web-apps.dev.yml
COMPOSE_PROD := -f $(COMPOSE_BASE) -f docker-compose-web-apps.prod.yml

# Docker Compose command with root .env file
# Use relative path to avoid Windows path issues
DOCKER_COMPOSE := docker-compose --env-file ../.env --env-file ../ports.env

# Host port registry (single source of truth) - make reads it for the URLs below
include ../ports.env

# Prod runs registry images (built by CI); pick the tag per command or in ../.env:
#   make web-portal-prod-up WEB_APPS_IMAGE_TAG=sha-1a2b3c4
export WEB_APPS_IMAGE_TAG

# App = compose service = container name = folder in apps/
APPS := web-portal survey-app web-portal-starter data-portal
URL_web-portal := http://localhost:$(WEB_PORTAL_HOST_PORT)
URL_survey-app := http://localhost:$(SURVEY_APP_HOST_PORT)
URL_web-portal-starter := http://localhost:$(WEB_PORTAL_STARTER_HOST_PORT)
URL_data-portal := http://localhost:$(DATA_PORTAL_HOST_PORT)

APP_TARGETS := dev-up-build dev-up dev-stop dev-down dev-logs dev-restart dev-shell \
               prod-up prod-down prod-logs build

.PHONY: help dev-up-build dev-up dev-stop dev-down dev-logs dev-restart \
        prod-up prod-down prod-logs build \
        $(foreach a,$(APPS),$(addprefix $(a)-,$(APP_TARGETS)))

# Default target
help:
	@echo "Web apps (Next.js, apps/*) - Docker commands"
	@echo "Dev runs the production image locally (no hot reload);"
	@echo "hot-reload development runs natively: pnpm dev:portal (see README.md)"
	@echo ""
	@$(foreach a,$(APPS),$(call app_help,$(a)))
	@echo "All apps at once:"
	@echo "  make dev-up | dev-up-build | dev-stop | dev-down | dev-logs | dev-restart"
	@echo "  make prod-up | prod-down | prod-logs | build"

define app_help
echo "$(1) ($(URL_$(1))):"; \
echo "  make $(1)-dev-up         - Build if changed and start"; \
echo "  make $(1)-dev-up-build   - Rebuild image (no cache) and start"; \
echo "  make $(1)-dev-stop       - Stop"; \
echo "  make $(1)-dev-down       - Stop and remove the container"; \
echo "  make $(1)-dev-logs       - Follow logs"; \
echo "  make $(1)-dev-restart    - Recreate the container"; \
echo "  make $(1)-dev-shell      - Shell in the container"; \
echo "  make $(1)-prod-up        - Pull the registry image and start (WEB_APPS_IMAGE_TAG=...)"; \
echo "  make $(1)-prod-down      - Stop and remove production container"; \
echo "  make $(1)-prod-logs      - Follow production logs"; \
echo "  make $(1)-build          - Rebuild image (no cache)"; \
echo "";
endef

# ──────────────────────────────────────────────────────────────
# Per-app targets: <app>-dev-up, <app>-dev-logs, ... (one set per app in APPS)
# ──────────────────────────────────────────────────────────────
define app_targets
$(1)-dev-up:
	@echo "Starting $(1) (dev)..."
	@$$(DOCKER_COMPOSE) $$(COMPOSE_DEV) up -d --build $(1)
	@echo "✓ $(1): $$(URL_$(1))"

$(1)-dev-up-build:
	@echo "Rebuilding and starting $(1) (dev)..."
	@$$(DOCKER_COMPOSE) $$(COMPOSE_DEV) build --no-cache $(1)
	@$$(DOCKER_COMPOSE) $$(COMPOSE_DEV) up -d $(1)
	@echo "✓ $(1): $$(URL_$(1))"

$(1)-dev-stop:
	@$$(DOCKER_COMPOSE) $$(COMPOSE_DEV) stop $(1)

$(1)-dev-down:
	@$$(DOCKER_COMPOSE) $$(COMPOSE_DEV) rm -sf $(1)

$(1)-dev-logs:
	@$$(DOCKER_COMPOSE) $$(COMPOSE_DEV) logs -f $(1)

$(1)-dev-restart: $(1)-dev-down $(1)-dev-up

$(1)-dev-shell:
	@$$(DOCKER_COMPOSE) $$(COMPOSE_DEV) exec $(1) sh

$(1)-prod-up:
	@echo "Pulling and starting production $(1)..."
	@$$(DOCKER_COMPOSE) $$(COMPOSE_PROD) pull $(1)
	@$$(DOCKER_COMPOSE) $$(COMPOSE_PROD) up -d $(1)
	@echo "✓ $(1) started"

$(1)-prod-down:
	@$$(DOCKER_COMPOSE) $$(COMPOSE_PROD) rm -sf $(1)

$(1)-prod-logs:
	@$$(DOCKER_COMPOSE) $$(COMPOSE_PROD) logs -f $(1)

$(1)-build:
	@$$(DOCKER_COMPOSE) $$(COMPOSE_DEV) build --no-cache $(1)
endef

$(foreach a,$(APPS),$(eval $(call app_targets,$(a))))

# ──────────────────────────────────────────────────────────────
# All apps - Development
# ──────────────────────────────────────────────────────────────
dev-up-build:
	@echo "Rebuilding and starting all web apps (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) build --no-cache
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d
	@$(foreach a,$(APPS),echo "✓ $(a): $(URL_$(a))";)

dev-up:
	@echo "Starting all web apps (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d --build
	@$(foreach a,$(APPS),echo "✓ $(a): $(URL_$(a))";)

dev-stop:
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) stop

dev-down:
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) down

dev-logs:
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) logs -f

dev-restart: dev-down dev-up

# ──────────────────────────────────────────────────────────────
# All apps - Production
# ──────────────────────────────────────────────────────────────
prod-up:
	@echo "Pulling and starting all production web apps..."
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) pull
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) up -d
	@echo "✓ Web apps started"

prod-down:
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) down

prod-logs:
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) logs -f

# ──────────────────────────────────────────────────────────────
# All apps - Images
# ──────────────────────────────────────────────────────────────
build:
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) build --no-cache
