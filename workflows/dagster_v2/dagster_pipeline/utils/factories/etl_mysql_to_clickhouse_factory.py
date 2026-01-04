# dagster_pipeline/utils/factories/mysql_to_clickhouse_factory.py
"""
Factory for MySQL → ClickHouse ETL pipelines with robust state management
"""

from typing import Optional, Dict, Any
from dagster import AssetExecutionContext
from .base_etl_factory import BaseETLFactory
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
        # ClickHouse-specific controls - ALL REQUIRED
        clickhouse_engine: str = None,  # REQUIRED - no default
        clickhouse_order_by: list = None,  # REQUIRED - no default
        clickhouse_partition_by: Optional[str] = None,  # Explicit None means "no partitioning"
        clickhouse_primary_key: Optional[list] = None,
        clickhouse_ttl: Optional[str] = None,
        clickhouse_settings: Optional[Dict[str, Any]] = None,
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
        
        # Validate required ClickHouse parameters
        self._validate_clickhouse_config(
            clickhouse_engine,
            clickhouse_order_by,
            clickhouse_partition_by
        )
        
        # Store ClickHouse table options
        self.clickhouse_engine = clickhouse_engine
        self.clickhouse_order_by = clickhouse_order_by
        self.clickhouse_partition_by = clickhouse_partition_by
        self.clickhouse_primary_key = clickhouse_primary_key
        self.clickhouse_ttl = clickhouse_ttl
        self.clickhouse_settings = clickhouse_settings or {}
    
    def _validate_clickhouse_config(
        self,
        engine: str,
        order_by: list,
        partition_by: Optional[str]
    ):
        """
        Validate required ClickHouse configuration parameters
        
        This ensures data engineers explicitly specify all critical settings.
        """
        errors = []
        
        # Engine is REQUIRED
        if engine is None:
            errors.append(
                "❌ clickhouse_engine is REQUIRED. You must explicitly choose an engine.\n"
                "   Common options:\n"
                "   - 'MergeTree' for append-only data\n"
                "   - 'ReplacingMergeTree' for deduplication\n"
                "   - 'ReplacingMergeTree(version_column)' for versioned deduplication"
            )
        
        # ORDER BY is REQUIRED
        if order_by is None:
            errors.append(
                "❌ clickhouse_order_by is REQUIRED. You must specify how data is sorted.\n"
                "   Example: clickhouse_order_by=['id'] or ['tenant_id', 'created_at', 'id']"
            )
        elif not isinstance(order_by, list) or len(order_by) == 0:
            errors.append(
                "❌ clickhouse_order_by must be a non-empty list of column names.\n"
                f"   Got: {order_by}"
            )
        
        # PARTITION BY must be explicitly set (can be None for no partitioning)
        # We check if it was passed to __init__ by checking if it's the sentinel value
        # This is checked in the factory function instead
        
        if errors:
            error_msg = "\n\n".join(errors)
            error_msg += "\n\n💡 TIP: All ClickHouse table parameters must be explicitly specified."
            raise ValueError(error_msg)

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

    def get_clickhouse_table_options(self) -> Dict[str, Any]:
        """
        Get ClickHouse table creation options
        
        Returns dict with engine, order_by, partition_by, etc.
        Subclass can override this or pass options in __init__
        """
        return {
            "engine": self.clickhouse_engine,
            "order_by": self.clickhouse_order_by,
            "partition_by": self.clickhouse_partition_by,
            "primary_key": self.clickhouse_primary_key,
            "ttl": self.clickhouse_ttl,
            "settings": self.clickhouse_settings,
        }
    
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
    # ClickHouse table options
    clickhouse_engine: Optional[str] = None,
    clickhouse_order_by: Optional[list] = None,
    clickhouse_partition_by: Optional[str] = None,
    clickhouse_primary_key: Optional[list] = None,
    clickhouse_ttl: Optional[str] = None,
    clickhouse_settings: Optional[Dict[str, Any]] = None,
):
    """
    Create a MySQL → ClickHouse ETL asset with full ClickHouse control
    
    Args:
        asset_name: Unique Dagster asset name
        source_database: MySQL database name
        source_table: MySQL table name
        destination_database: ClickHouse database name
        destination_table: ClickHouse table name
        mysql_resource_key: Resource key for MySQL connection
        incremental_key: Column for incremental sync (None = full sync)
        sync_method: "append", "replace", or "upsert"
        batch_size: Rows per batch
        group_name: Dagster asset group
        tags: Additional tags
        
        clickhouse_engine: ClickHouse table engine (default: auto-select based on sync_method)
            Examples:
            - "MergeTree" - Basic sorted storage
            - "ReplacingMergeTree" - Deduplication by ORDER BY
            - "ReplacingMergeTree(updatedAt)" - Dedup by version column
            - "SummingMergeTree" - Auto-sum numeric columns
            - "AggregatingMergeTree" - Pre-aggregated data
            - "CollapsingMergeTree(sign)" - Cancel out rows
        
        clickhouse_order_by: Columns for ORDER BY (default: primary key or first column)
            Examples:
            - ["id"] - Simple ordering
            - ["tenant_id", "created_date", "id"] - Multi-column for partitioning
        
        clickhouse_partition_by: Partition expression (default: None)
            Examples:
            - "toYYYYMM(created_date)" - Monthly partitions
            - "toMonday(created_date)" - Weekly partitions
            - "tenant_id" - By tenant
            - "(tenant_id, toYYYYMM(created_date))" - Composite
        
        clickhouse_primary_key: Primary key columns (default: first ORDER BY column)
            Examples:
            - ["tenant_id", "id"] - Composite primary key
        
        clickhouse_ttl: TTL expression for automatic data expiration
            Examples:
            - "created_date + INTERVAL 90 DAY" - Delete after 90 days
            - "created_date + INTERVAL 1 YEAR TO DISK 'cold'" - Move to cold storage
        
        clickhouse_settings: Table-level settings
            Examples:
            - {"index_granularity": 8192}
            - {"ttl_only_drop_parts": 1}
    
    Returns:
        Dagster asset function
    
    Example - Basic append:
        >>> asset = create_mysql_to_clickhouse_asset(
        ...     asset_name="logs_to_clickhouse",
        ...     source_table="logs",
        ...     destination_table="logs",
        ...     incremental_key="created_at",
        ...     clickhouse_order_by=["created_at", "id"],
        ...     clickhouse_partition_by="toYYYYMM(created_at)"
        ... )
    
    Example - Deduplication:
        >>> asset = create_mysql_to_clickhouse_asset(
        ...     asset_name="users_to_clickhouse",
        ...     source_table="users",
        ...     destination_table="users",
        ...     incremental_key="updated_at",
        ...     clickhouse_engine="ReplacingMergeTree(updated_at)",
        ...     clickhouse_order_by=["id"],
        ...     clickhouse_partition_by="toYYYYMM(created_at)"
        ... )
    
    Example - With TTL:
        >>> asset = create_mysql_to_clickhouse_asset(
        ...     asset_name="events_to_clickhouse",
        ...     source_table="events",
        ...     destination_table="events",
        ...     incremental_key="event_time",
        ...     clickhouse_order_by=["event_time", "id"],
        ...     clickhouse_partition_by="toYYYYMM(event_time)",
        ...     clickhouse_ttl="event_time + INTERVAL 90 DAY"
        ... )
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
        clickhouse_engine=clickhouse_engine,
        clickhouse_order_by=clickhouse_order_by,
        clickhouse_partition_by=clickhouse_partition_by,
        clickhouse_primary_key=clickhouse_primary_key,
        clickhouse_ttl=clickhouse_ttl,
        clickhouse_settings=clickhouse_settings,
    )

    return factory.build()