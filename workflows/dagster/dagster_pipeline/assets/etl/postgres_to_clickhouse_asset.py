# dagster_pipeline/pipelines/etl/mysql_to_clickhouse.py
"""
All PostgeSQL → ClickHouse ETL assets

⚠️  IMPORTANT: All ClickHouse parameters must be explicitly specified:
   • clickhouse_engine - REQUIRED
   • clickhouse_order_by - REQUIRED  
   • clickhouse_partition_by - REQUIRED (use None for no partitioning)
"""

from dagster_pipeline.utils.factories.etl_postgres_to_clickhouse_factory import create_postgres_to_clickhouse_asset

# ============================================================================
# POSTGRES FMA DATABASE → CLICKHOUSE
# ============================================================================
postgres_fma_premises = create_postgres_to_clickhouse_asset(
     # Asset Identity
    asset_name="postgres_fma_premises_to_clickhouse",
    group_name="postgres_fma_to_clickhouse",

    # Source Config
    source_database="sunculture_ep",
    source_table="premises",
    incremental_key="updated_at",
    
    # Destination Config (ClickHouse)
    destination_database="fma",
    destination_table="premises_v1",
    postgres_resource_key="postgres_fma",
    
    clickhouse_engine="ReplacingMergeTree(updated_at)",
    clickhouse_order_by=["id"],                          
    clickhouse_partition_by=None,                   
)

postgres_fma_premise_details = create_postgres_to_clickhouse_asset(
     # Asset Identity
    asset_name="postgres_fma_premise_details_to_clickhouse",
    group_name="postgres_fma_to_clickhouse",
    
    # Source Config
    source_database="sunculture_ep",
    source_table="premise_details",
    incremental_key="updated_at",
    
    # Destination Config (ClickHouse)
    destination_database="fma",
    destination_table="premise_details_v1",
    postgres_resource_key="postgres_fma",
    clickhouse_engine="ReplacingMergeTree(updated_at)",
    clickhouse_order_by=["id"],
    clickhouse_partition_by=None,
)

# Add more tables...

# ============================================================================
# ASSET COLLECTION
# ============================================================================
assets = [
    postgres_fma_premises,
    postgres_fma_premise_details
]