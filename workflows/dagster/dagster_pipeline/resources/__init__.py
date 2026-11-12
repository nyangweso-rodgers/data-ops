import os

from dagster import EnvVar

# ════════════════════════════════════════════════════════════════════════════
# IMPORT RESOURCE CLASSES
# ════════════════════════════════════════════════════════════════════════════

from .databases import (
    MySQLResource,
    PostgresResource,
    MongoDBResource,
    ClickHouseResource,
    DagsterPostgresResource,
    ADXResource,
    NetSuiteResource,
)

from .apis import (
    CallCenterStudioAPIResource,
    CCSTenant,
    PowerBIResource,
    GoogleSheetsResource,
)

from .storage import (
    S3Resource,
)

# Import alert resources
from dagster_pipeline.alerts.slack_alerts import SlackAlertSender
from dagster_pipeline.alerts.alert_manager import AlertManager

# ════════════════════════════════════════════════════════════════════════════
# MYSQL - LOCAL DEVELOPMENT
# ════════════════════════════════════════════════════════════════════════════
local_mysql = MySQLResource(
    host=EnvVar("LOCAL_MYSQL_DB_HOST"),
    port=3306,
    user=EnvVar("LOCAL_MYSQL_DB_USER"),
    password=EnvVar("LOCAL_MYSQL_DB_PASSWORD"),
    database=EnvVar("LOCAL_MYSQL_DB_NAME"),
    read_timeout=300,  # 5 min standard
)

# ════════════════════════════════════════════════════════════════════════════
# POSTGRES - LOCAL DEVELOPMENT
# ════════════════════════════════════════════════════════════════════════════
local_postgres = PostgresResource(
    host=EnvVar("LOCAL_POSTGRES_DB_HOST"),
    port=5432,
    user=EnvVar("LOCAL_POSTGRES_DB_USER"),
    password=EnvVar("LOCAL_POSTGRES_DB_PASSWORD"),
    database=EnvVar("LOCAL_POSTGRES_DB_NAME"),
    db_schema="public",
    statement_timeout=300000,  # 5 min standard
)
