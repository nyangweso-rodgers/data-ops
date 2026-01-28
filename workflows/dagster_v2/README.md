# Project

## Table Of Contents

- [Project Structure](#project-structure)

# Architecture Overview

- Three types of data operations:
  1. ETL Assets (`assets/etl/`)
     - **Purpose**: Keep destination in sync with source
     - Pattern: Continuous sync with incremental tracking
     - Schedule: Frequent (15-20 mins)
     - Example: MySQL accounts → ClickHouse accounts (live data)

  2. Maintenance Assets (`assets/maintenance/`)
     - **Purpose**: Optimize and clean existing data
     - Pattern: Analyze → Clean → Optimize
     - Schedule: Periodic (daily/weekly)
     - Example: Deduplicate ClickHouse partitions

  3. Snapshot Assets (`assets/snapshots/`)
     - **Purpose**: Capture point-in-time state for history
     - Pattern: Query → Timestamp → Append
     - Schedule: Periodic (daily/monthly)
     - Example: Account status at end of month

  4. Data Quality Assets (`assets/data_quality`)
     - **Purpose**: Data Quality Checks

  5. Reverse ETL Assets (`assets/reverse_etl`)
     - **Purpose**: Extract, Tranform and Load data from data warehouse to a Production DB (MySQL, PostgreSQL, e.t.c.,)

# Project Structure

- dagster_v2/
  - .github/
    - workflows/
      - `validate-pr.yml`
      - `test.yml` # Run tests
      - `deploy.yml` # Build & Deploy

  - dagster_home/
    - `dagster.yaml`
    - `workspace.yaml`

  - dagster_pipeline/
    - `__init__.py`
    - `definitions.py`
    - alerts/
      - `__init__.py`
      - `alert_manager.py`
      - `slack_alerts.py`
      - `email_alerts.py`
      - `alert_types`

    - connectors/
      - sources/ # Source connectors ← DATA EXTRACTION
        - `base_source_connector.py`
        - `mysql_source_connector.py` # MySQL extraction
        - `postgres_source_connector.py` # PostgreSQL extraction
        - `s3_source_connector.py`
        - `api_source_connector.py`
        - `clickhouse_source_connector.py` # For reverse ETL
      - sink/ # Sink connectors - Handles ETL operations (load, schema sync, optimize)
        - `base_sink_connector.py`
        - `clickhouse_sink_connector.py`
        - `bigquery_sink_connector.py`
        - `s3_sink_connector.py`
        - `postgres_sink_connector.py`
        - `mysql_sink_connector.py` # MySQL loading

    - assets/
      - data_migration/
      - data_quality/ # Data Quality
      - etl/ # ETL Assets
        - `mysql_to_clickhouse_asset.py`
        - `postgres_to_clickhouse_asset.py`
      - maintenance/ # Cleanups and Optimizations
        - `clickhouse_optimization.py`
      - snapshots/ # Point-in-time data capture

    - resources/
      - `__init__.py`
      - `clickhouse_resource.py` # Manages connections, pooling, basic health checks
      - `dagster_postgres_resource.py`
      - `mysql_resource.py`
      - `registry.py`

    - schemas/
      - apis/
      - mysql/
        - amtdb/
          - `accounts.yml`
          - `customers.yml`
        - sales_service/
          - `leads.yml`
          - `leadsources.yml`
      - postgres/
        - fma/
          - `premises.yml`
          - `premise_details.yml`
        - sentinel/
          - `devices.yml`
      - templates/
        - `table_schema_template.yml` # ← Template with comments

    - utils/
      - factories/
        - `__init__.py`
        - `etl_base_factory.py` # ← Abstract base class
        - `etl_mysql_to_clickhouse_factory.py` # ← MySQL-specific
        - `etl_postgres_to_clickhouse_factory.py` # ← Postgres-specific
      - `logging_config.py`
      - `schema_loader.py`
      - `state_manager.py`
      - `type_mapper.py`
    - scripts/
      - `__init__.py`
      - `validate_schemas.py`
      - `sync_state_backfill.py`
    - docs/
      - `architecture.md`
      - `adding-new-table.md`
      - `deployment.md`
    - tests/
    - `.dockerignore`
    - `.gitignore`
    - `CHANGELOG.md`
    - `docker-compose-dagster.base.yml`
    - `docker-compose-dagster.local-rds.yml`
    - `docker-compose-dagster.local.yml`
    - `docker-compose-dagster.prod.yml`
    - `Dockerfile`
    - `Makefile`
    - `pyproject.toml`
    - `README.md`

# Resources and Further Reading

1. [docs.dagster.io](https://docs.dagster.io/?_gl=1*1bd3xxt*_ga*Nzc4MzMwNDcxLjE3MTcxNDc3OTM.*_ga_84VRQZG7TV*MTcxNzE0Nzc5My4xLjAuMTcxNzE0Nzc5My42MC4wLjA.*_gcl_au*MTcxOTE5MzIyMS4xNzE3MTQ3Nzk0)
