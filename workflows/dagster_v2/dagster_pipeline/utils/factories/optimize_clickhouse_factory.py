# dagster_pipeline/utils/factories/clickhouse_optimize_factory.py
"""
Factory for ClickHouse OPTIMIZE TABLE operations (for ReplacingMergeTree deduplication)

This is the CORRECT way to deduplicate across partitions if using ReplacingMergeTree.
"""

from typing import Optional, Dict, Any, List
from dagster import AssetExecutionContext
import time

from dagster_pipeline.utils.factories.base_maintenance_factory import BaseMaintenanceFactory
from dagster_pipeline.utils.logging_config import get_logger, log_execution_time

# Initialize logger
logger = get_logger(__name__)


class OptimizeClickHouseFactory(BaseMaintenanceFactory):
    """
    Factory for running OPTIMIZE TABLE FINAL on ClickHouse ReplacingMergeTree tables
    
    This leverages ClickHouse's native deduplication for ReplacingMergeTree tables.
    Much simpler and safer than manual partition manipulation.
    
    Usage:
        factory = OptimizeClickHouseFactory(
            asset_name="optimize_leads_table",
            database="sales-service",
            table="leads_v2",
        )
        
        asset = factory.build()
    """
    
    def __init__(
        self,
        asset_name: str,
        database: str,
        table: str,
        group_name: str = "clickhouse_maintenance",
        partition_column: Optional[str] = None,
        partition_format: Optional[str] = None,
        specific_partitions: Optional[List[str]] = None,
    ):
        super().__init__(
            asset_name=asset_name,
            group_name=group_name,
            description=f"Run OPTIMIZE TABLE FINAL on {database}.{table}",
        )
        
        self.database = database
        self.table = table
        self.partition_column = partition_column
        self.partition_format = partition_format
        self.specific_partitions = specific_partitions
        
        self.tags.update({
            "database": database,
            "table": table,
        })
        
        # Update logger context with database and table info
        self.logger = get_logger(
            self.__class__.__name__,
            context={
                "asset_name": asset_name,
                "maintenance_type": "clickhouse_optimize",
                "database": database,
                "table": table,
            }
        )
        
        self.logger.info(
            "optimize_factory_initialized",
            partition_column=partition_column,
            specific_partitions=specific_partitions,
        )
    
    def maintenance_type(self) -> str:
        return "clickhouse_optimize"
    
    def get_required_resource_keys(self) -> set:
        return {"clickhouse_resource"}
    
    def perform_maintenance(
        self,
        context: AssetExecutionContext,
        **resources
    ) -> Dict[str, Any]:
        """Run OPTIMIZE TABLE FINAL"""
        
        clickhouse_resource = resources["clickhouse_resource"]
        client = clickhouse_resource.get_client()
        
        self.logger.info("clickhouse_connected", client_type=type(client).__name__)
        context.log.info(f"📌 Connected to ClickHouse: {type(client).__name__}")
        
        # Get stats before optimization
        context.log.info("📊 Getting stats before optimization...")
        with log_execution_time(self.logger, "stats_collection_before"):
            stats_before = self._get_table_stats(client, context)
        
        self.logger.info(
            "stats_before_optimization",
            total_rows=stats_before['total_rows'],
            unique_ids=stats_before['unique_ids'],
            duplicate_count=stats_before['duplicate_count'],
            duplicate_pct=stats_before['duplicate_pct'],
        )
        
        context.log.info(
            f"   Before: {stats_before['total_rows']:,} total rows, "
            f"{stats_before['unique_ids']:,} unique leadIds, "
            f"{stats_before['duplicate_count']:,} duplicates ({stats_before['duplicate_pct']}%)"
        )
        
        # Run OPTIMIZE
        start_time = time.time()
        
        if self.specific_partitions:
            # Optimize specific partitions
            self.logger.info("optimizing_specific_partitions", partitions=self.specific_partitions)
            context.log.info(f"🔨 Optimizing {len(self.specific_partitions)} specific partition(s)...")
            
            for partition in self.specific_partitions:
                context.log.info(f"   → Optimizing partition {partition}...")
                optimize_query = f"OPTIMIZE TABLE `{self.database}`.`{self.table}` PARTITION %(partition)s FINAL SETTINGS alter_sync=2"
                
                with log_execution_time(self.logger, "partition_optimization", partition=partition):
                    client.command(optimize_query, parameters={"partition": partition})
        else:
            # Optimize entire table
            self.logger.info("optimizing_entire_table")
            context.log.info("🔨 Optimizing entire table (this may take a while)...")
            optimize_query = f"OPTIMIZE TABLE `{self.database}`.`{self.table}` FINAL SETTINGS alter_sync=2"
            
            with log_execution_time(self.logger, "table_optimization"):
                client.command(optimize_query)
        
        duration = time.time() - start_time
        self.logger.info("optimization_completed", duration=round(duration, 2))
        context.log.info(f"   ✅ OPTIMIZE completed in {duration:.2f}s")
        
        # Get stats after optimization
        context.log.info("📊 Getting stats after optimization...")
        with log_execution_time(self.logger, "stats_collection_after"):
            stats_after = self._get_table_stats(client, context)
        
        duplicates_removed = stats_before['total_rows'] - stats_after['total_rows']
        
        self.logger.info(
            "stats_after_optimization",
            total_rows=stats_after['total_rows'],
            unique_ids=stats_after['unique_ids'],
            duplicate_count=stats_after['duplicate_count'],
            duplicate_pct=stats_after['duplicate_pct'],
            duplicates_removed=duplicates_removed,
        )
        
        context.log.info(
            f"   After: {stats_after['total_rows']:,} total rows, "
            f"{stats_after['unique_ids']:,} unique leadIds, "
            f"{stats_after['duplicate_count']:,} duplicates ({stats_after['duplicate_pct']}%)"
        )
        context.log.info(f"   🎯 Removed {duplicates_removed:,} duplicate rows")
        
        return {
            "status": "success" if duplicates_removed > 0 else "no_cleanup_needed",
            "items_processed": 1,
            "items_modified": 1 if duplicates_removed > 0 else 0,
            "operation_details": {
                "database": self.database,
                "table": self.table,
                "rows_before": stats_before['total_rows'],
                "rows_after": stats_after['total_rows'],
                "duplicates_removed": duplicates_removed,
                "optimize_duration_seconds": round(duration, 2),
            },
            "warnings": [],
        }
    
    def _get_table_stats(self, client, context: AssetExecutionContext) -> Dict[str, Any]:
        """Get table statistics"""
        
        query = f"""
            SELECT
                count() as total_rows,
                uniqExact(leadId) as unique_ids,
                count() - uniqExact(leadId) as duplicate_count,
                round((count() - uniqExact(leadId)) * 100.0 / count(), 2) as duplicate_pct
            FROM `{self.database}`.`{self.table}`
        """
        
        try:
            result = client.query(query)
            
            if result.result_rows:
                row = result.result_rows[0]
                stats = {
                    "total_rows": row[0],
                    "unique_ids": row[1],
                    "duplicate_count": row[2],
                    "duplicate_pct": round(row[3], 2),
                }
                
                self.logger.debug("table_stats_retrieved", **stats)
                return stats
            
            self.logger.warning("no_stats_data_returned")
            return {
                "total_rows": 0,
                "unique_ids": 0,
                "duplicate_count": 0,
                "duplicate_pct": 0.0,
            }
            
        except Exception as e:
            self.logger.error("stats_collection_failed", error=str(e), exc_info=True)
            raise


def create_clickhouse_optimize_asset(
    asset_name: str,
    database: str,
    table: str,
    group_name: str = "clickhouse_maintenance",
    partition_column: Optional[str] = None,
    partition_format: Optional[str] = None,
    specific_partitions: Optional[List[str]] = None,
):
    """
    Create ClickHouse OPTIMIZE TABLE asset
    
    This is the recommended approach for ReplacingMergeTree tables.
    """
    factory = OptimizeClickHouseFactory(
        asset_name=asset_name,
        database=database,
        table=table,
        group_name=group_name,
        partition_column=partition_column,
        partition_format=partition_format,
        specific_partitions=specific_partitions,
    )
    
    return factory.build()