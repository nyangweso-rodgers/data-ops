# workflows/airflow/Makefile
# Airflow-specific commands (the root Makefile delegates its airflow-* targets here)

# Docker Compose file combinations
COMPOSE_BASE := docker-compose-airflow.base.yml
COMPOSE_DEV := -f $(COMPOSE_BASE) -f docker-compose-airflow.dev.yml
COMPOSE_PROD := -f $(COMPOSE_BASE) -f docker-compose-airflow.prod.yml

# Docker Compose command with root .env file
# Use relative path to avoid Windows path issues
DOCKER_COMPOSE := docker-compose --env-file ../../.env --env-file ../../ports.env

# Host port registry (single source of truth) - make reads it for the URLs below
include ../../ports.env

# Stop Git Bash on Windows from rewriting container paths (e.g. /opt/airflow)
export MSYS_NO_PATHCONV := 1

AIRFLOW_URL := http://localhost:$(AIRFLOW_HOST_PORT)

.PHONY: help env-info \
        dev-up-build dev-up dev-stop dev-down dev-logs dev-restart dev-shell \
        dags import-errors test test-dags \
        prod-up prod-down prod-logs build clean

# Default target
help:
	@echo "Airflow Commands:"
	@echo ""
	@echo "Development (local postgres):"
	@echo "  make dev-up-build   - Build and start Airflow (webserver + scheduler)"
	@echo "  make dev-up         - Start Airflow"
	@echo "  make dev-stop       - Stop Airflow"
	@echo "  make dev-down       - Stop and remove Airflow containers"
	@echo "  make dev-logs       - Follow webserver + scheduler logs"
	@echo "  make dev-restart    - Recreate Airflow containers"
	@echo "  make dev-shell      - Bash shell in the scheduler container"
	@echo ""
	@echo "DAGs and tests:"
	@echo "  make dags           - List DAGs (running scheduler)"
	@echo "  make import-errors  - Show DAG import errors (running scheduler)"
	@echo "  make test           - Run unit tests locally (pytest)"
	@echo "  make test-dags      - Run all tests incl. DAG integrity inside the running scheduler"
	@echo ""
	@echo "Production:"
	@echo "  make prod-up        - Start production Airflow (RDS metadata DB)"
	@echo "  make prod-down      - Stop production Airflow"
	@echo "  make prod-logs      - Follow production logs"
	@echo ""
	@echo "Other:"
	@echo "  make build          - Rebuild the Airflow image (no cache)"
	@echo "  make lock           - Re-resolve uv.lock after editing pyproject.toml"
	@echo "  make sync           - Create/update the local .venv from uv.lock (editor, tests)"
	@echo "  make clean          - Remove dev containers and volumes"
	@echo "  make env-info       - Show environment file location"

# Show which .env file is being used
env-info:
	@echo "Using .env file from: ../../.env"
	@if [ -f ../../.env ]; then \
		echo "✓ File exists"; \
		echo ""; \
		echo "Airflow-related variables (values hidden):"; \
		grep -E "^(APACHE_AIRFLOW_|AIRFLOW_|LOCAL_PG_DB_HOST|RDS_)" ../../.env | sed -E 's/=.*/=…/' || echo "No Airflow variables found"; \
	else \
		echo "❌ File not found!"; \
	fi

# ──────────────────────────────────────────────────────────────
# Development (with local postgres)
# ──────────────────────────────────────────────────────────────
dev-up-build:
	@echo "Building and starting Airflow (dev)..."
	@echo "Using .env from: ../../.env"
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d --build
	@echo "✓ Airflow UI: $(AIRFLOW_URL) (first start initializes the metadata DB - give it a minute)"

dev-up:
	@echo "Starting Airflow (dev)..."
	@echo "Using .env from: ../../.env"
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d
	@echo "✓ Airflow UI: $(AIRFLOW_URL)"

dev-stop:
	@echo "Stopping Airflow (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) stop

dev-down:
	@echo "Stopping and removing Airflow (dev)..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) down

dev-logs:
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) logs -f

dev-restart: dev-down dev-up

dev-shell:
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) exec airflow-scheduler bash

# ──────────────────────────────────────────────────────────────
# DAGs and tests
# ──────────────────────────────────────────────────────────────
dags:
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) exec airflow-scheduler airflow dags list

import-errors:
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) exec airflow-scheduler airflow dags list-import-errors

test:
	@uv run pytest

# The image has no tests/ or pytest - copy tests in, install pytest into the (disposable) container, run, clean up
test-dags:
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) exec airflow-scheduler mkdir -p /tmp/airflow-tests
	@docker cp tests airflow-scheduler:/tmp/airflow-tests/tests
	@docker cp pyproject.toml airflow-scheduler:/tmp/airflow-tests/pyproject.toml
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) exec -u root airflow-scheduler chown -R airflow /tmp/airflow-tests
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) exec airflow-scheduler bash -c "\
		python -c 'import pytest' 2>/dev/null || uv pip install -q pytest==8.0.0; \
		cd /tmp/airflow-tests && for d in dataflow dags configs schemas sql; do ln -sfn /opt/airflow/\$$d \$$d; done; \
		python -m pytest -q -p no:cacheprovider tests"; \
	status=$$?; \
	$(DOCKER_COMPOSE) $(COMPOSE_DEV) exec -u root airflow-scheduler rm -rf /tmp/airflow-tests; \
	exit $$status

# ──────────────────────────────────────────────────────────────
# Production
# ──────────────────────────────────────────────────────────────
prod-up:
	@echo "Starting production Airflow (RDS)..."
	@echo "Using .env from: ../../.env"
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) up -d
	@echo "✓ Airflow started"

prod-down:
	@echo "Stopping production Airflow..."
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) down

prod-logs:
	@$(DOCKER_COMPOSE) $(COMPOSE_PROD) logs -f

# ──────────────────────────────────────────────────────────────
# Build and Clean
# ──────────────────────────────────────────────────────────────
build:
	@echo "Rebuilding Airflow image..."
	@$(DOCKER_COMPOSE) -f $(COMPOSE_BASE) build --no-cache
	@echo "✓ Build complete"

clean:
	@echo "Cleaning up dev environment..."
	@$(DOCKER_COMPOSE) $(COMPOSE_DEV) down -v
	@echo "✓ Cleaned up dev environment"

# ──────────────────────────────────────────────────────────────
# Python dependencies (uv) - pyproject.toml + uv.lock in this folder
# ──────────────────────────────────────────────────────────────
.PHONY: lock sync

lock:
	@uv lock
	@echo "✓ uv.lock updated - rebuild the image to apply it"

sync:
	@uv sync
