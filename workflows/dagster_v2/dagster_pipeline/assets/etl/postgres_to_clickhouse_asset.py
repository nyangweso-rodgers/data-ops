# dagster_pipeline/pipelines/etl/mysql_to_clickhouse.py
"""
All PostgeSQL → ClickHouse ETL assets

⚠️  IMPORTANT: All ClickHouse parameters must be explicitly specified:
   • clickhouse_engine - REQUIRED
   • clickhouse_order_by - REQUIRED  
   • clickhouse_partition_by - REQUIRED (use None for no partitioning)
"""

from dagster_pipeline.utils.factories.postgres_to_clickhouse_factory import create_postgres_to_clickhouse_asset

# ============================================================================
# POSTGRES FMA DATABASE → CLICKHOUSE
# ============================================================================
postgres_fma_premises = create_postgres_to_clickhouse_asset(
    asset_name="postgres_fma_premises_to_clickhouse",
    source_database="sunculture_ep",
    source_table="premises",
    destination_database="fma",
    destination_table="premises_test",
    postgres_resource_key="postgres_fma",
    incremental_key="updated_at",
    
    # ✅ REQUIRED FIELDS - All must be explicit
    # Premises - property dimension data with updates (~100K rows)
    clickhouse_engine="ReplacingMergeTree(updated_at)",  # ✅ REQUIRED - Dedup by timestamp
    clickhouse_order_by=["id"],                          # ✅ REQUIRED - Query by premise ID
    clickhouse_partition_by=None,                   # ✅ REQUIRED - 10 partitions for distribution
    
    group_name="postgres_fma_to_clickhouse"
)

postgres_fma_premise_details = create_postgres_to_clickhouse_asset(
    asset_name="postgres_fma_premise_details_to_clickhouse",
    source_database="sunculture_ep",
    source_table="premise_details",
    destination_database="fma",
    destination_table="premise_details_test",
    postgres_resource_key="postgres_fma",
    incremental_key="updated_at",
    clickhouse_engine="ReplacingMergeTree(updated_at)",
    clickhouse_order_by=["id"],
    clickhouse_partition_by=None,
    group_name="postgres_fma_to_clickhouse"
)
# Add more tables...

# ============================================================================
# ASSET COLLECTION
# ============================================================================
assets = [
    postgres_fma_premises,
    postgres_fma_premise_details,
]