# dagster_pipeline/assets/clickhouse/ingest/from_mysql/generator.py
"""
All MySQL → ClickHouse ingestion assets, jobs and schedules

Generated from config/clickhouse/ingest/from_mysql/*.yml (one file per source
database). To add a table, add it to the relevant YAML file - no code changes.
"""

from dagster_pipeline.utils.ingest_config_loader import build_jobs_and_schedules, load_table_specs
from dagster_pipeline.assets.clickhouse.ingest.from_mysql.builder import build_mysql_to_clickhouse_asset

TABLE_SPECS = load_table_specs("from_mysql", source_type="mysql")

assets = [build_mysql_to_clickhouse_asset(spec) for spec in TABLE_SPECS]
jobs, schedules = build_jobs_and_schedules(TABLE_SPECS)
