# definitions.py
"""
Main Dagster definitions file.
"""

from dagster import Definitions

# Import ALL resources from the central registry
from dagster_pipeline.resources.registry import (
    mysql_amt,
    mysql_sales_service_dev,
    clickhouse_resource,
    dagster_postgres_resource,
    postgres_fma,
    
)

# Import assets 
from dagster_pipeline.assets.etl.mysql_to_clickhouse_asset import assets as mysql_assets
from dagster_pipeline.assets.etl.postgres_to_clickhouse_asset import assets as postgres_assets

# Import SchemaLoader class
from dagster_pipeline.utils.schema_loader import SchemaLoader


# ═════════════════════════════════════════════════════════════════════════════
# DAGSTER DEFINITIONS
# ═════════════════════════════════════════════════════════════════════════════

defs = Definitions(
    assets=[
        *mysql_assets,
        *postgres_assets,
    ],
    resources={
        # MySQL
        "mysql_amt": mysql_amt,
        "mysql_sales_service_dev": mysql_sales_service_dev,
        
        # PostgreSQL
        "postgres_fma": postgres_fma,
        
        # ClickHouse
        "clickhouse_resource": clickhouse_resource,
        
        # Infrastructure
        "dagster_postgres_resource": dagster_postgres_resource,
        
        # Utilities
        "schema_loader": SchemaLoader(),
    },
)