# dagster_pipeline/assets/maintenance/optimize_clickhouse_asset.py
"""
ClickHouse cleanup/optimization assets
"""

from dagster_pipeline.utils.factories.optimize_clickhouse_factory import (
    create_clickhouse_optimize_asset
)

# ============================================================================
# Sales Service Leads Optimization (CORRECT for ReplacingMergeTree)
# ============================================================================
cleanup_sales_service_leads = create_clickhouse_optimize_asset(
    asset_name="cleanup_sales_service_leads",  # ← Changed from "optimize_..."
    group_name="clickhouse_maintenance",
    database="sales-service",
    table="leads_v2",
)

# ============================================================================
# ASSET COLLECTION
# ============================================================================
assets = [
    cleanup_sales_service_leads
]