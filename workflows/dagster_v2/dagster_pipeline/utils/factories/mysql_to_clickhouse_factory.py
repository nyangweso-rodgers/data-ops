# dagster_pipeline/utils/factories/mysql_to_clickhouse_factory.py
"""
Factory for MySQL → ClickHouse ETL pipelines
"""

from typing import Optional, Dict, Any
from dagster import AssetExecutionContext
from .base_factory import BaseETLFactory
from dagster_pipeline.connectors.sources.mysql_source import MySQLSourceConnector
from dagster_pipeline.connectors.destinations.clickhouse_destination import ClickHouseDestinationConnector


class MySQLToClickHouseFactory(BaseETLFactory):
    def __init__(
        self,
        asset_name: str,
        source_database: str,
        source_table: str,
        destination_database: str,
        destination_table: str,
        mysql_resource_key: str = "mysql_amt",  # ← explicit key
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
        """
        Return all required resource keys for MySQL → ClickHouse ETL
        
        CRITICAL: This must match EXACTLY what's in definitions.py
        """
        return {
            self.mysql_resource_key,           # e.g., "mysql_amt"
            "clickhouse_resource",             # Destination
            "schema_loader",                   # Schema loading
            "dagster_postgres_resource",       # State management for incremental tracking
        }

    def get_source_connector(self, context: AssetExecutionContext):
        """
        Create MySQL source connector
        
        Args:
            context: Dagster execution context with resources
        
        Returns:
            MySQLSourceConnector instance
        """
        # Access MySQL resource from context.resources
        mysql_res = getattr(context.resources, self.mysql_resource_key, None)
        
        if mysql_res is None:
            # Get available resource names for debugging
            available = [attr for attr in dir(context.resources) if not attr.startswith('_')]
            raise ValueError(
                f"MySQL resource '{self.mysql_resource_key}' not found. "
                f"Available resources: {available}\n"
                f"Make sure '{self.mysql_resource_key}' is defined in definitions.py"
            )

        # Build config for MySQL connector
        config = {
            **mysql_res.get_config(),
            "database": self.source_database,
            "table": self.source_table,  # Add table name to config
        }
        
        return MySQLSourceConnector(context, config)

    def get_destination_connector(self, context: AssetExecutionContext):
        """
        Create ClickHouse destination connector
        
        Args:
            context: Dagster execution context with resources
        
        Returns:
            ClickHouseDestinationConnector instance
        """
        # Access ClickHouse resource from context.resources
        ch_res = getattr(context.resources, "clickhouse_resource", None)
        
        if ch_res is None:
            # Get available resource names for debugging
            available = [attr for attr in dir(context.resources) if not attr.startswith('_')]
            raise ValueError(
                f"ClickHouse resource 'clickhouse_resource' not found. "
                f"Available resources: {available}"
            )
        
        config = {**ch_res.get_config()}
        return ClickHouseDestinationConnector(context, config)


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