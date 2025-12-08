# dagster_pipeline/utils/factories/mysql_to_clickhouse_factory.py
"""
Factory for MySQL → ClickHouse ETL pipelines with robust state management
"""

from typing import Optional, Dict, Any
from dagster import AssetExecutionContext
from .base_factory import BaseETLFactory
from dagster_pipeline.connectors.sources.mysql_source_connector import MySQLSourceConnector
from dagster_pipeline.connectors.sink.clickhouse_sink_connector import ClickHouseSinkConnector
import structlog

logger = structlog.get_logger(__name__)


class MySQLToClickHouseFactory(BaseETLFactory):
    def __init__(
        self,
        asset_name: str,
        source_database: str,
        source_table: str,
        destination_database: str,
        destination_table: str,
        mysql_resource_key: str = "mysql_amt",
        incremental_key: Optional[str] = None,
        sync_method: str = "append",
        batch_size: int = 10000,
        group_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            asset_name=asset_name,
            source_database=source_database,
            source_table=source_table,
            destination_database=destination_database,
            destination_table=destination_table,
            incremental_key=incremental_key,
            sync_method=sync_method,
            batch_size=batch_size,
            group_name=group_name,
            tags=tags,
        )
        self.mysql_resource_key = mysql_resource_key

    def source_type(self) -> str:
        return "mysql"

    def destination_type(self) -> str:
        return "clickhouse"
    
    def get_required_resource_keys(self) -> set:
        """Return all required resource keys"""
        return {
            self.mysql_resource_key,
            "clickhouse_resource",
            "schema_loader",
            "dagster_postgres_resource",
        }

    def get_source_connector(self, context: AssetExecutionContext):
        """Create MySQL source connector"""
        mysql_res = getattr(context.resources, self.mysql_resource_key, None)
        
        if mysql_res is None:
            available = [attr for attr in dir(context.resources) if not attr.startswith('_')]
            raise ValueError(
                f"MySQL resource '{self.mysql_resource_key}' not found. "
                f"Available resources: {available}"
            )

        config = {
            **mysql_res.get_config(),
            "database": self.source_database,
            "table": self.source_table,
        }
        
        return MySQLSourceConnector(context, config)

    def get_destination_connector(self, context: AssetExecutionContext):
        """Create ClickHouse destination connector"""
        ch_res = getattr(context.resources, "clickhouse_resource", None)
        
        if ch_res is None:
            available = [attr for attr in dir(context.resources) if not attr.startswith('_')]
            raise ValueError(
                f"ClickHouse resource 'clickhouse_resource' not found. "
                f"Available resources: {available}"
            )
        
        config = {**ch_res.get_config()}
        return ClickHouseSinkConnector(context, config)

    def validate_and_correct_incremental_key(self, context: AssetExecutionContext, schema) -> Optional[str]:
        """
        Validate incremental key exists in schema (exact match)
        
        Returns:
            The incremental key as provided (no case correction)
        """
        if not self.incremental_key:
            return None
        
        # Get column names from schema
        column_names = schema.get_column_names(use_source_names=True)
        
        # Check for exact match first
        if self.incremental_key in column_names:
            context.log.info(f"✅ Incremental key validated: {self.incremental_key}")
            return self.incremental_key
        
        # If exact match fails, try case-insensitive search to provide helpful error
        column_names_lower = {col.lower(): col for col in column_names}
        incremental_key_lower = self.incremental_key.lower()
        
        if incremental_key_lower in column_names_lower:
            correct_case = column_names_lower[incremental_key_lower]
            raise ValueError(
                f"Incremental key '{self.incremental_key}' not found (case mismatch). "
                f"Did you mean '{correct_case}'? Update your asset definition to use the exact column name."
            )
        else:
            raise ValueError(
                f"Incremental key '{self.incremental_key}' not found in schema. "
                f"Available columns: {column_names}"
            )


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def create_mysql_to_clickhouse_asset(
    asset_name: str,
    source_database: str,
    source_table: str,
    destination_database: str,
    destination_table: str,
    mysql_resource_key: str = "mysql_amt",
    incremental_key: Optional[str] = None,
    sync_method: str = "append",
    batch_size: int = 10000,
    group_name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
):
    """
    Create a MySQL → ClickHouse ETL asset
    
    Args:
        asset_name: Unique Dagster asset name
        source_database: MySQL database name
        source_table: MySQL table name
        destination_database: ClickHouse database name
        destination_table: ClickHouse table name
        mysql_resource_key: Resource key for MySQL connection (must match definitions.py)
        incremental_key: Column for incremental sync (None = full sync)
        sync_method: "append", "replace", or "upsert"
        batch_size: Rows per batch
        group_name: Dagster asset group
        tags: Additional tags
    
    Returns:
        Dagster asset function
    """
    factory = MySQLToClickHouseFactory(
        asset_name=asset_name,
        source_database=source_database,
        source_table=source_table,
        destination_database=destination_database,
        destination_table=destination_table,
        mysql_resource_key=mysql_resource_key,
        incremental_key=incremental_key,
        sync_method=sync_method,
        batch_size=batch_size,
        group_name=group_name,
        tags=tags,
    )

    return factory.build()