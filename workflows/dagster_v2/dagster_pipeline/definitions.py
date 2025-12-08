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
    
)

# Import assets 
from dagster_pipeline.assets.etl.mysql_to_clickhouse_asset import assets

# Import SchemaLoader class
from dagster_pipeline.utils.schema_loader import SchemaLoader


# ═════════════════════════════════════════════════════════════════════════════
# DAGSTER DEFINITIONS
# ═════════════════════════════════════════════════════════════════════════════

defs = Definitions(
    assets=assets,
    resources={
        # MySQL
        "mysql_amt": mysql_amt,
        "mysql_sales_service_dev": mysql_sales_service_dev,
        
        # Po
        
        # ClickHouse
        "clickhouse_resource": clickhouse_resource,
        
        # Infrastructure
        "dagster_postgres_resource": dagster_postgres_resource,
        
        # Utilities
        "schema_loader": SchemaLoader(),
    },
)