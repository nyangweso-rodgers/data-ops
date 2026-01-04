# dagster_pipeline/utils/factories/postgres_to_clickhouse_factory.py
"""
Factory for PostgreSQL → ClickHouse ETL pipelines

Shares the same base factory as MySQL, only differs in connector creation.
"""

from typing import Optional, Dict, Any
from dagster import AssetExecutionContext
from .base_etl_factory import BaseETLFactory
from dagster_pipeline.connectors.sources.postgres_source_connector import PostgresSourceConnector
from dagster_pipeline.connectors.sink.clickhouse_sink_connector import ClickHouseSinkConnector
import structlog

logger = structlog.get_logger(__name__)


class PostgresToClickHouseFactory(BaseETLFactory):
    """
    Postgres → ClickHouse ETL factory
    
    Inherits all ETL logic from BaseETLFactory.
    Only implements Postgres-specific connector creation.
    """
    
    def __init__(
        self,
        asset_name: str,
        source_database: str,
        source_table: str,
        destination_database: str,
        destination_table: str,
        postgres_resource_key: str = "postgres_default",
        incremental_key: Optional[str] = None,
        sync_method: str = "append",
        batch_size: int = 10000,
        group_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        # ClickHouse-specific controls - ALL REQUIRED
        clickhouse_engine: str = None,
        clickhouse_order_by: list = None,
        clickhouse_partition_by: Optional[str] = None,
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
        self.postgres_resource_key = postgres_resource_key
        
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
        """Validate required ClickHouse configuration parameters"""
        errors = []
        
        if engine is None:
            errors.append(
                "❌ clickhouse_engine is REQUIRED. You must explicitly choose an engine.\n"
                "   Common options:\n"
                "   - 'MergeTree' for append-only data\n"
                "   - 'ReplacingMergeTree' for deduplication\n"
                "   - 'ReplacingMergeTree(version_column)' for versioned deduplication"
            )
        
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
        
        if errors:
            error_msg = "\n\n".join(errors)
            error_msg += "\n\n💡 TIP: All ClickHouse table parameters must be explicitly specified."
            raise ValueError(error_msg)

    def source_type(self) -> str:
        return "postgres"

    def destination_type(self) -> str:
        return "clickhouse"
    
    def get_required_resource_keys(self) -> set:
        """Return all required resource keys"""
        return {
            self.postgres_resource_key,
            "clickhouse_resource",
            "schema_loader",
            "dagster_postgres_resource",
        }

    def get_source_connector(self, context: AssetExecutionContext):
        """Create PostgreSQL source connector"""
        postgres_res = getattr(context.resources, self.postgres_resource_key, None)
        
        if postgres_res is None:
            available = [attr for attr in dir(context.resources) if not attr.startswith('_')]
            raise ValueError(
                f"Postgres resource '{self.postgres_resource_key}' not found. "
                f"Available resources: {available}"
            )

        config = {
            **postgres_res.get_config(),
            "database": self.source_database,
            "table": self.source_table,
        }
        
        return PostgresSourceConnector(context, config)

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
        """Get ClickHouse table creation options"""
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
        
        Postgres is case-sensitive by default, so we do exact matching.
        """
        if not self.incremental_key:
            return None
        
        # Get column names from schema
        column_names = schema.get_column_names(use_source_names=True)
        
        # Check for exact match
        if self.incremental_key in column_names:
            context.log.info(f"✅ Incremental key validated: {self.incremental_key}")
            return self.incremental_key
        
        # Postgres columns are often lowercase by default
        # Try lowercase version if exact match fails
        incremental_key_lower = self.incremental_key.lower()
        if incremental_key_lower in column_names:
            context.log.warning(
                f"⚠️ Incremental key found with different case: '{self.incremental_key}' → '{incremental_key_lower}'"
            )
            return incremental_key_lower
        
        # If still not found, provide helpful error
        column_names_lower = {col.lower(): col for col in column_names}
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

def create_postgres_to_clickhouse_asset(
    asset_name: str,
    source_database: str,
    source_table: str,
    destination_database: str,
    destination_table: str,
    postgres_resource_key: str = "postgres_default",
    incremental_key: Optional[str] = None,
    sync_method: str = "append",
    batch_size: int = 10000,
    group_name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    # ClickHouse table options - REQUIRED FIELDS
    clickhouse_engine: str = None,
    clickhouse_order_by: list = None,
    clickhouse_partition_by: Optional[str] = None,
    clickhouse_primary_key: Optional[list] = None,
    clickhouse_ttl: Optional[str] = None,
    clickhouse_settings: Optional[Dict[str, Any]] = None,
):
    """
    Create a PostgreSQL → ClickHouse ETL asset with REQUIRED ClickHouse configuration
    
    ⚠️  REQUIRED FIELDS - MUST BE EXPLICITLY SET:
    - clickhouse_engine: Table engine (e.g., "MergeTree", "ReplacingMergeTree")
    - clickhouse_order_by: Sort columns (e.g., ["id"] or ["tenant_id", "created_at"])
    - clickhouse_partition_by: Partition expression or None (e.g., "toYYYYMM(created_at)" or None)
    
    Args:
        asset_name: Unique Dagster asset name
        source_database: PostgreSQL database name
        source_table: PostgreSQL table name
        destination_database: ClickHouse database name
        destination_table: ClickHouse table name
        postgres_resource_key: Resource key for Postgres connection
        incremental_key: Column for incremental sync (None = full sync)
        sync_method: "append", "replace", or "upsert"
        batch_size: Rows per batch
        group_name: Dagster asset group
        tags: Additional tags
        
        clickhouse_engine: REQUIRED - ClickHouse table engine
        clickhouse_order_by: REQUIRED - Columns for ORDER BY
        clickhouse_partition_by: REQUIRED (can be None) - Partition expression
        clickhouse_primary_key: Optional - Primary key columns
        clickhouse_ttl: Optional - TTL expression for data expiration
        clickhouse_settings: Optional - Table-level settings
    
    Returns:
        Dagster asset function
    
    Example - Small dimension table:
        >>> asset = create_postgres_to_clickhouse_asset(
        ...     asset_name="postgres_users_to_clickhouse",
        ...     source_database="app_db",
        ...     source_table="users",
        ...     destination_database="analytics",
        ...     destination_table="users",
        ...     postgres_resource_key="postgres_app",
        ...     incremental_key="updated_at",
        ...     clickhouse_engine="ReplacingMergeTree(updated_at)",
        ...     clickhouse_order_by=["id"],
        ...     clickhouse_partition_by=None,
        ... )
    
    Example - Large event table:
        >>> asset = create_postgres_to_clickhouse_asset(
        ...     asset_name="postgres_events_to_clickhouse",
        ...     source_database="app_db",
        ...     source_table="events",
        ...     destination_database="analytics",
        ...     destination_table="events",
        ...     postgres_resource_key="postgres_app",
        ...     incremental_key="created_at",
        ...     clickhouse_engine="MergeTree",
        ...     clickhouse_order_by=["user_id", "created_at"],
        ...     clickhouse_partition_by="toYYYYMM(created_at)",
        ...     clickhouse_ttl="created_at + INTERVAL 90 DAY",
        ... )
    """
    
    factory = PostgresToClickHouseFactory(
        asset_name=asset_name,
        source_database=source_database,
        source_table=source_table,
        destination_database=destination_database,
        destination_table=destination_table,
        postgres_resource_key=postgres_resource_key,
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