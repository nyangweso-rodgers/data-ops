# definitions.py
"""
Main Dagster definitions file.
"""

from dagster import Definitions

# Import ALL resources from the central registry
from dagster_pipeline.resources.registry import (
    mysql_amt,
    clickhouse_resource,
    dagster_postgres_resource,
)

# Import assets 
from dagster_pipeline.pipelines.etl.mysql_to_clickhouse import assets

# Import SchemaLoader class
from dagster_pipeline.utils.schema_loader import SchemaLoader


# ═════════════════════════════════════════════════════════════════════════════
# DAGSTER DEFINITIONS
# ═════════════════════════════════════════════════════════════════════════════

defs = Definitions(
    assets=assets,
    resources={
        # Source databases
        "mysql_amt": mysql_amt,
        
        # Destination databases
        "clickhouse_resource": clickhouse_resource,
        
        # Infrastructure
        "dagster_postgres_resource": dagster_postgres_resource,
        
        # Utilities
        "schema_loader": SchemaLoader(),
    },
)