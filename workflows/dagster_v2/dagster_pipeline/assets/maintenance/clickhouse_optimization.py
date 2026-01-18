# dagster_pipeline/assets/maintenance/clickhouse_optimization.py
"""
Simple ClickHouse table optimization to remove duplicates

This runs OPTIMIZE TABLE ... FINAL on specified tables to force
ReplacingMergeTree deduplication immediately instead of waiting for
background merges (which can take hours/days).

Since your ETL appends records when they're updated (based on updatedAt),
this ensures duplicates are cleaned up daily.
"""

from dagster import asset, AssetExecutionContext, Output, MetadataValue
from typing import Dict, List
import time

from dagster_pipeline.utils.logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# CONFIGURATION: List databases and tables to optimize
# ============================================================================

# ============================================================================
# TABLE CONFIGURATION
# ============================================================================
# Map each table to its primary key column for duplicate detection
# If a table has no unique ID column, duplicate stats will just show row counts

TABLE_PRIMARY_KEYS: Dict[str, Dict[str, str]] = {
    "sales-service": {
        "leads_v2": "leadId",
        "leadsources_v1": "id",
        "lead_channels_v1": "id",
        "cds_v1": "id",
        "form_answers_v1": "id",
        "kyc_requests_v1": "id",
        "forms_v1": "id",
    },
    "amt": {
        "accounts_v1": "id",
    },
    "soil_testing_prod": { 
        "policies_v1": "id",
    },
    "fma": {
        "premises_v1": "id",
        "premise_details_v1": "id",
    },
}

# Derived: Simple list of databases → tables for iteration
CLICKHOUSE_TABLES_TO_OPTIMIZE: Dict[str, List[str]] = {
    db: list(tables.keys()) for db, tables in TABLE_PRIMARY_KEYS.items()
}

# ============================================================================
# OPTIMIZATION ASSET
# ============================================================================

@asset(
    name="optimize_clickhouse_tables",
    group_name="clickhouse_maintenance",
    compute_kind="CLICKHOUSE_OPTIMIZE",
    description="Run OPTIMIZE TABLE FINAL on all configured ClickHouse tables to remove duplicates",
    required_resource_keys={"clickhouse_resource"},
)
def optimize_clickhouse_tables(context: AssetExecutionContext) -> Output:
    """
    Optimize all configured ClickHouse tables to remove duplicates
    
    This runs OPTIMIZE TABLE ... FINAL which forces immediate deduplication
    by ReplacingMergeTree engine instead of waiting for background merges.
    """
    
    start_time = time.time()
    
    context.log.info("=" * 80)
    context.log.info("🧹 CLICKHOUSE TABLE OPTIMIZATION")
    context.log.info("=" * 80)
    
    # Get ClickHouse client
    clickhouse_resource = context.resources.clickhouse_resource
    client = clickhouse_resource.get_client()
    
    logger.info("optimization_started", tables_config=CLICKHOUSE_TABLES_TO_OPTIMIZE)
    
    # Track results
    results = {
        "databases_processed": 0,
        "tables_processed": 0,
        "tables_optimized": 0,
        "tables_failed": 0,
        "total_duplicates_removed": 0,
        "details": [],
    }
    
    # Process each database
    for database, tables in CLICKHOUSE_TABLES_TO_OPTIMIZE.items():
        context.log.info(f"\n📊 Processing database: {database}")
        context.log.info(f"   Tables to optimize: {len(tables)}")
        
        results["databases_processed"] += 1
        
        # Process each table
        for table in tables:
            results["tables_processed"] += 1
            
            context.log.info(f"\n   🔨 Optimizing {database}.{table}...")
            
            try:
                # Get stats BEFORE optimization
                stats_before = _get_table_stats(client, database, table, context)
                
                context.log.info(
                    f"      Before: {stats_before['total_rows']:,} rows, "
                    f"{stats_before['duplicate_count']:,} duplicates ({stats_before['duplicate_pct']}%)"
                )
                
                # Run OPTIMIZE TABLE FINAL
                optimize_start = time.time()
                
                optimize_query = f"OPTIMIZE TABLE `{database}`.`{table}` FINAL"
                client.command(optimize_query)
                
                optimize_duration = time.time() - optimize_start
                
                # Get stats AFTER optimization
                stats_after = _get_table_stats(client, database, table, context)
                
                duplicates_removed = stats_before['total_rows'] - stats_after['total_rows']
                
                context.log.info(
                    f"      After: {stats_after['total_rows']:,} rows, "
                    f"{stats_after['duplicate_count']:,} duplicates ({stats_after['duplicate_pct']}%)"
                )
                context.log.info(
                    f"      ✅ Removed {duplicates_removed:,} duplicates in {optimize_duration:.2f}s"
                )
                
                results["tables_optimized"] += 1
                results["total_duplicates_removed"] += duplicates_removed
                
                # Store details
                results["details"].append({
                    "database": database,
                    "table": table,
                    "status": "success",
                    "rows_before": stats_before['total_rows'],
                    "rows_after": stats_after['total_rows'],
                    "duplicates_removed": duplicates_removed,
                    "duration_seconds": round(optimize_duration, 2),
                })
                
                logger.info(
                    "table_optimized",
                    database=database,
                    table=table,
                    duplicates_removed=duplicates_removed,
                    duration=round(optimize_duration, 2),
                )
                
            except Exception as e:
                context.log.error(f"      ❌ Failed to optimize {database}.{table}: {e}")
                
                results["tables_failed"] += 1
                results["details"].append({
                    "database": database,
                    "table": table,
                    "status": "failed",
                    "error": str(e),
                })
                
                logger.error(
                    "table_optimization_failed",
                    database=database,
                    table=table,
                    error=str(e),
                    exc_info=True,
                )
    
    # Calculate total duration
    total_duration = time.time() - start_time
    
    # Log summary
    context.log.info("\n" + "=" * 80)
    context.log.info("🎉 OPTIMIZATION COMPLETE")
    context.log.info("=" * 80)
    context.log.info(f"\n📊 Summary:")
    context.log.info(f"   Databases processed: {results['databases_processed']}")
    context.log.info(f"   Tables processed: {results['tables_processed']}")
    context.log.info(f"   Tables optimized: {results['tables_optimized']}")
    context.log.info(f"   Tables failed: {results['tables_failed']}")
    context.log.info(f"   Total duplicates removed: {results['total_duplicates_removed']:,}")
    context.log.info(f"   Duration: {total_duration:.2f}s")
    context.log.info("=" * 80)
    
    logger.info(
        "optimization_completed",
        databases_processed=results['databases_processed'],
        tables_optimized=results['tables_optimized'],
        tables_failed=results['tables_failed'],
        duplicates_removed=results['total_duplicates_removed'],
        duration=round(total_duration, 2),
    )
    
    # Create metadata for Dagster UI
    metadata = {
        "databases_processed": MetadataValue.int(results['databases_processed']),
        "tables_processed": MetadataValue.int(results['tables_processed']),
        "tables_optimized": MetadataValue.int(results['tables_optimized']),
        "tables_failed": MetadataValue.int(results['tables_failed']),
        "duplicates_removed": MetadataValue.int(results['total_duplicates_removed']),
        "duration_seconds": MetadataValue.float(round(total_duration, 2)),
    }
    
    # Add table details as markdown
    if results['details']:
        details_md = "## Optimization Details\n\n"
        details_md += "| Database | Table | Status | Rows Before | Rows After | Duplicates Removed | Duration |\n"
        details_md += "|----------|-------|--------|-------------|------------|-------------------|----------|\n"
        
        for detail in results['details']:
            if detail['status'] == 'success':
                details_md += (
                    f"| {detail['database']} | {detail['table']} | ✅ | "
                    f"{detail['rows_before']:,} | {detail['rows_after']:,} | "
                    f"{detail['duplicates_removed']:,} | {detail['duration_seconds']}s |\n"
                )
            else:
                details_md += (
                    f"| {detail['database']} | {detail['table']} | ❌ | "
                    f"- | - | - | {detail.get('error', 'Unknown error')} |\n"
                )
        
        metadata["optimization_details"] = MetadataValue.md(details_md)
    
    return Output(results, metadata=metadata)


# ============================================================================
# HELPER FUNCTION
# ============================================================================

def _get_table_stats(client, database: str, table: str, context: AssetExecutionContext) -> Dict:
    """Get duplicate statistics for a table"""
    
    # Get the primary key column for this table
    primary_key = TABLE_PRIMARY_KEYS.get(database, {}).get(table)
    
    if not primary_key:
        # No primary key configured, just count rows
        context.log.debug(f"No primary key configured for {database}.{table}, counting rows only")
        try:
            count_result = client.query(f"SELECT count() FROM `{database}`.`{table}`")
            total_rows = count_result.result_rows[0][0] if count_result.result_rows else 0
            
            return {
                "total_rows": total_rows,
                "unique_ids": total_rows,
                "duplicate_count": 0,
                "duplicate_pct": 0.0,
            }
        except Exception as e:
            context.log.warning(f"Could not count rows for {database}.{table}: {e}")
            return {
                "total_rows": 0,
                "unique_ids": 0,
                "duplicate_count": 0,
                "duplicate_pct": 0.0,
            }
    
    # Use the configured primary key to detect duplicates
    query = f"""
        SELECT
            count() as total_rows,
            uniqExact({primary_key}) as unique_ids,
            count() - uniqExact({primary_key}) as duplicate_count,
            round((count() - uniqExact({primary_key}) * 100.0 / count(), 2) as duplicate_pct
        FROM `{database}`.`{table}`
    """
    
    try:
        result = client.query(query)
        
        if result.result_rows:
            row = result.result_rows[0]
            return {
                "total_rows": row[0],
                "unique_ids": row[1],
                "duplicate_count": row[2],
                "duplicate_pct": round(row[3], 2),
            }
        
        return {
            "total_rows": 0,
            "unique_ids": 0,
            "duplicate_count": 0,
            "duplicate_pct": 0.0,
        }
        
    except Exception as e:
        # If query fails (e.g., primary key column doesn't exist), just count rows
        context.log.warning(f"Could not get duplicate stats for {database}.{table}: {e}")
        
        try:
            count_result = client.query(f"SELECT count() FROM `{database}`.`{table}`")
            total_rows = count_result.result_rows[0][0] if count_result.result_rows else 0
            
            return {
                "total_rows": total_rows,
                "unique_ids": total_rows,
                "duplicate_count": 0,
                "duplicate_pct": 0.0,
            }
        except:
            return {
                "total_rows": 0,
                "unique_ids": 0,
                "duplicate_count": 0,
                "duplicate_pct": 0.0,
            }


# ============================================================================
# EXPORT
# ============================================================================

assets = [optimize_clickhouse_tables]