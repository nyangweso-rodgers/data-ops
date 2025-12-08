# dagster_pipeline/pipelines/etl/mysql_to_clickhouse.py
"""
All MySQL → ClickHouse ETL assets
"""

from dagster_pipeline.utils.factories.mysql_to_clickhouse_factory import create_mysql_to_clickhouse_asset
from dagster_pipeline.resources.registry import mysql_amt  
from dagster_pipeline.resources.registry import clickhouse_resource
from dagster_pipeline.utils.schema_loader import SchemaLoader

# ============================================================================
# MYSQL AMT DATABASE → CLICKHOUSE
# ============================================================================

mysql_amt_accounts = create_mysql_to_clickhouse_asset(
    asset_name="mysql_amt_accounts_to_clickhouse",
    source_database="amtdb",
    source_table="accounts",
    destination_database="test",
    destination_table="amt_accounts_test",
    mysql_resource_key="mysql_amt",   
    incremental_key="updatedAt",
)


# Add more tables...

assets = [mysql_amt_accounts]