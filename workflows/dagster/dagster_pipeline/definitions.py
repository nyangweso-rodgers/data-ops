# dagster_pipeline/definitions.py
import os
from dagster import Definitions, ScheduleDefinition, RunRequest, AssetMaterialization
from dagster_pipeline.resources.databases.v1.databases import MySQLResource, ClickHouseResource
from dagster_pipeline.resources.schema_loader.v1.schema_loader import SchemaLoader
from dagster_pipeline.assets.etl.mysql_to_clickhouse.amtdb.accounts.v1.accounts_asset import sync_accounts_to_clickhouse
from .jobs.mysql_amtdb_accounts_job import mysql_amtdb_accounts_job  # Import job only

# Global resources (env-safe; None if vars missing—override in Dagit)
all_resources = {
    "mysql_resource": MySQLResource(
        host=os.getenv("SC_AMT_REPLICA_MYSQL_DB_HOST"),
        port=int(os.getenv("MYSQL_DB_PORT", 3306)),
        user=os.getenv("MYSQL_AMT_DB_USER"),
        password=os.getenv("MYSQL_AMT_DB_PASSWORD", "")
    ) if all(os.getenv(k) for k in ["SC_AMT_REPLICA_MYSQL_DB_HOST", "MYSQL_AMT_DB_USER"]) else None,
    "clickhouse_resource": ClickHouseResource(
        host=os.getenv("SC_CH_DB_HOST"),
        port=int(os.getenv("SC_CH_DB_PORT", 8443)),
        user=os.getenv("SC_CH_DB_USER"),
        password=os.getenv("SC_CH_DB_PASSWORD", ""),
        secure=os.getenv("CLICKHOUSE_SECURE", "True").lower() == "true"
    ) if all(os.getenv(k) for k in ["SC_CH_DB_HOST", "SC_CH_DB_USER"]) else None,
    "schema_loader": SchemaLoader(config_base_path="/app/dagster_pipeline/config")
}

# Schedule (attach to job)
accounts_schedule = ScheduleDefinition(
    job=mysql_amtdb_accounts_job,
    cron_schedule="*/15 6-21 * * *",
    execution_timezone="UTC"
)

# Central defs
defs = Definitions(
    assets=[sync_accounts_to_clickhouse],
    jobs=[mysql_amtdb_accounts_job],
    schedules=[accounts_schedule],
    resources=all_resources
)