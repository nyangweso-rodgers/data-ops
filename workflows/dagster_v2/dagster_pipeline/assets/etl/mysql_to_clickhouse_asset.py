# dagster_pipeline/pipelines/etl/mysql_to_clickhouse.py
"""
All MySQL → ClickHouse ETL assets
"""

from dagster_pipeline.utils.factories.mysql_to_clickhouse_factory import create_mysql_to_clickhouse_asset

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

mysql_sales_service_leadsources = create_mysql_to_clickhouse_asset(
    asset_name="mysql_sales_service_leadsources_to_clickhouse",
    source_database="sales-service-dev",
    source_table="leadsources",
    destination_database="test",
    destination_table="sales_service_leadsources_test",
    mysql_resource_key="mysql_sales_service_dev",   
    incremental_key="updatedAt",
    group_name="mysql_sales_service_dev_to_clickhouse" # Manually spcecified group name
)
# Add more tables...

assets = [mysql_amt_accounts, mysql_sales_service_leadsources]