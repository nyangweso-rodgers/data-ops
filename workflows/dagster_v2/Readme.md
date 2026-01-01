# Project

## Table Of Contents

- [Project Structure](#project-structure)

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
      - sink/ # Sink connectors ← DATA LOADING
        - `base_sink_connector.py`
        - `clickhouse_sink_connector.py`
        - `bigquery_sink_connector.py`
        - `s3_sink_connector.py`
        - `postgres_sink_connector.py`
        - `mysql_sink_connector.py` # MySQL loading

    - assets/

      - etl/
        - `mysql_to_clickhouse_asset.py`

    - resources/

      - `__init__.py`
      - `clickhouse_resource.py`
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
      - postgres/
        - fma/
          - `premises.yml`
        - sentinel/
          - `devices.yml`
      - templates/
        - `table_schema_template.yml` # ← Template with comments

    - utils/
      - factories/
        - `__init__.py`
        - `base_factory.py` # ← Abstract base class
        - `mysql_to_clickhouse_factory.py` # ← MySQL-specific
        - `postgres_to_clickhouse_factory.py` # ← Postgres-specific
        - `s3_to_clickhouse_factory.py` ← S3/Parquet files
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
      - `test_type_mapper.py`
      - `test_schema_loader.py`
      - `test_mysql_to_clickhouse_factory.py`
    - `.dockerignore`
    - `.env.dagster`
    - `.gitignore`
    - `CHANGELOG.md`
    - `docker-compose-dagster.base.yml`
    - `docker-compose-dagster.local.yml`
    - `docker-compose-dagster.prod.yml`
    - `Dockerfile`
    - `Makefile`
    - `pyproject.toml`
    - `README.md`
    - `requirements.txt`

# Resources and Further Reading

1. [docs.dagster.io](https://docs.dagster.io/?_gl=1*1bd3xxt*_ga*Nzc4MzMwNDcxLjE3MTcxNDc3OTM.*_ga_84VRQZG7TV*MTcxNzE0Nzc5My4xLjAuMTcxNzE0Nzc5My42MC4wLjA.*_gcl_au*MTcxOTE5MzIyMS4xNzE3MTQ3Nzk0)
