# __init__.py
# dagster-pipeline/resources/__init__.py
import os
from .v1.databases import MySQLResource, ClickHouseResource, PostgreSQLResource
from ..schema_loader import SchemaLoader

resources = {
    "mysql_resource": MySQLResource(
        host=os.getenv("SC_AMT_REPLICA_MYSQL_DB_HOST"),
        port=int(os.getenv("MYSQL_DB_PORT", 3306)),
        user=os.getenv("MYSQL_AMT_DB_USER"),
        password=os.getenv("MYSQL_AMT_DB_PASSWORD", "")
    ),
    "clickhouse_resource": ClickHouseResource(
        host=os.getenv("SC_CH_DB_HOST"),
        port=int(os.getenv("SC_CH_DB_PORT", 8443)),
        user=os.getenv("SC_CH_DB_USER"),
        password=os.getenv("SC_CH_DB_PASSWORD", ""),
        secure=os.getenv("CLICKHOUSE_SECURE", "True").lower() == "true"
    ),
    "schema_loader": SchemaLoader(config_base_path="/app/dagster_pipeline/config")
}