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
    destination_database="amt",
    destination_table="accounts_test",
    mysql_resource_key="mysql_amt",   
    incremental_key="updatedAt",
    
    # ClickHouse table settings
    # Accounts are dimension data - deduplicate by id, keep latest version
    clickhouse_engine="ReplacingMergeTree(updatedAt)", 
    clickhouse_order_by=["id"],                         
    clickhouse_partition_by=None, 
    
    group_name="mysql_amt_to_clickhouse"
)

# ============================================================================
# MYSQL SALES SERVICE DATABASE → CLICKHOUSE
# ============================================================================
mysql_sales_service_leadsources = create_mysql_to_clickhouse_asset(
    asset_name="mysql_sales_service_leadsources_to_clickhouse",
    source_database="sales-service-dev",
    source_table="leadsources",
    destination_database="sales-service",
    destination_table="leadsources_test",
    mysql_resource_key="mysql_sales_service_dev",
    incremental_key="updatedAt",
    
    # ClickHouse table settings
    # Lead sources - small dimension table with updates
    clickhouse_engine="ReplacingMergeTree(updatedAt)", # Use ReplacingMergeTree to keep only latest version
    clickhouse_order_by=["id"],
    clickhouse_partition_by=None, # Small table, no partitioning
    
    group_name="mysql_sales_service_to_clickhouse"
)
# Add more tables...

# ============================================================================
# ASSET COLLECTION
# ============================================================================
assets = [mysql_amt_accounts, mysql_sales_service_leadsources]