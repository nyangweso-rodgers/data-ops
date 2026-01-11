"""
Abstract base factory for ETL pipelines with enhanced state management

Architecture:
- Uses SchemaLoader as resource (not creating new instance)
- Better error handling (raises exceptions instead of returning error Output)
- Validates incremental key earlier in process
- Cleaner separation of concerns
- More robust state management
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List
from dagster import asset, AssetExecutionContext, Output, MetadataValue

from dagster_pipeline.connectors.sources.base_source_connector import IncrementalConfig

from dagster_pipeline.utils.schema_loader import (
    SchemaLoader,
    SchemaNotFoundError,
    SchemaValidationError,
    TableSchema
)
from dagster_pipeline.utils.type_mapper import TypeMapper
from dagster_pipeline.utils.state_manager import StateManager

from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class BaseETLFactory(ABC):
    """
    Abstract base class for ETL factories with robust state management
    
    Key Features:
    - Schema validation before execution
    - Incremental key validation with case-insensitive matching
    - Robust state management with retries
    - Proper error handling (raises exceptions)
    - Single Output per asset
    - Uses resources efficiently
    
    Usage:
        class MySQLToClickHouseFactory(BaseETLFactory):
            def source_type(self) -> str:
                return "mysql"
            
            def destination_type(self) -> str:
                return "clickhouse"
            
            # ... implement other methods
        
        factory = MySQLToClickHouseFactory(
            asset_name="mysql_accounts_to_clickhouse",
            source_database="amtdb",
            source_table="accounts",
            destination_database="amt",
            destination_table="accounts_test",
            incremental_key="updatedAt"
        )
        
        asset = factory.build()
    """
    
    def __init__(
        self,
        asset_name: str,
        source_database: str,
        source_table: str,
        destination_database: str,
        destination_table: str,
        incremental_key: Optional[str] = None,
        sync_method: str = "append",
        batch_size: int = 10000,
        group_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        self.asset_name = asset_name
        self.source_database = source_database
        self.source_table = source_table
        self.destination_database = destination_database
        self.destination_table = destination_table
        self.incremental_key = incremental_key
        self.sync_method = sync_method
        self.batch_size = batch_size
        self.group_name = group_name or self._default_group_name()
        self.tags = tags or {}
        
        # Update tags with metadata
        self.tags.update({
            "source_type": self.source_type(),
            "destination_type": self.destination_type(),
            "sync_type": "incremental" if incremental_key else "full",
            "sync_method": sync_method
        })
    
    # ========================================================================
    # ABSTRACT METHODS - Must be implemented by subclasses
    # ========================================================================
    
    @abstractmethod
    def source_type(self) -> str:
        """Return source type identifier (e.g., 'mysql', 'postgres')"""
        pass
    
    @abstractmethod
    def destination_type(self) -> str:
        """Return destination type identifier (e.g., 'clickhouse')"""
        pass
    
    @abstractmethod
    def get_source_connector(self, context: AssetExecutionContext):
        """Create and return source connector instance"""
        pass
    
    @abstractmethod
    def get_destination_connector(self, context: AssetExecutionContext):
        """Create and return destination connector instance"""
        pass
    
    @abstractmethod
    def get_required_resource_keys(self) -> set:
        """
        Return set of required resource keys
        
        IMPORTANT: Must include 'schema_loader'!
        
        Example:
            return {"schema_loader", "mysql_source", "clickhouse_resource"}
        """
        pass
    
    # ========================================================================
    # OPTIONAL METHODS - Can be overridden by subclasses
    # ========================================================================
    
    def validate_and_correct_incremental_key(
        self,
        context: AssetExecutionContext,
        schema: TableSchema
    ) -> Optional[str]:
        """
        Validate and potentially correct incremental key
        
        Default: Returns key as-is if it exists in schema, None otherwise
        
        Override in subclasses for custom behavior (e.g., case-insensitive matching)
        
        Args:
            context: Dagster execution context
            schema: Loaded TableSchema
        
        Returns:
            Validated incremental key or None if invalid
        """
        if not self.incremental_key:
            return None
        
        # Check if key exists in schema
        if schema.has_column(self.incremental_key):
            return self.incremental_key
        
        context.log.error(
            f"Incremental key '{self.incremental_key}' not found in schema. "
            f"Available columns: {schema.get_column_names()}"
        )
        return None
    
    def get_clickhouse_table_options(self) -> Dict[str, Any]:
        """
        Get ClickHouse table creation options
        
        Override to customize table creation.
        
        Returns:
            Dictionary with table options:
            - engine: Table engine (None = auto-select)
            - order_by: ORDER BY columns (None = use primary keys)
            - partition_by: PARTITION BY expression (None = no partitioning)
            - primary_key: PRIMARY KEY columns (None = same as ORDER BY)
            - ttl: TTL expression (None = no TTL)
            - settings: Additional table settings dict
        """
        return {
            "engine": None,
            "order_by": None,
            "partition_by": None,
            "primary_key": None,
            "ttl": None,
            "settings": {},
        }
    
    def transform_batch(
        self,
        batch: List[Dict[str, Any]],
        schema: TableSchema
    ) -> List[Dict[str, Any]]:
        """
        Transform batch data before loading
        
        Override to add custom transformations:
        - Rename columns
        - Add computed columns
        - Filter rows
        - Data type conversions
        
        Args:
            batch: List of row dictionaries
            schema: TableSchema for reference
        
        Returns:
            Transformed batch
        """
        return batch  # Default: no transformation
    
    # ========================================================================
    # INTERNAL HELPER METHODS
    # ========================================================================
    
    def _default_group_name(self) -> str:
        """Generate default group name"""
        source_db_safe = self.source_database.replace("-", "_")
        return f"{self.source_type()}_{source_db_safe}_to_{self.destination_type()}"
    
    def _get_asset_description(self) -> str:
        """Generate asset description"""
        sync_type = "incremental" if self.incremental_key else "full"
        return (
            f"ETL: {self.source_type().upper()} {self.source_database}.{self.source_table} → "
            f"{self.destination_type().upper()} {self.destination_database}.{self.destination_table} "
            f"({sync_type}, {self.sync_method})"
        )
    
    def _load_and_validate_schema(
        self,
        context: AssetExecutionContext
    ) -> TableSchema:
        """
        Load and validate schema using SchemaLoader resource
        
        Raises:
            ValueError: If schema not found or invalid
        """
        # Get SchemaLoader from resources
        schema_loader = context.resources.schema_loader
        
        try:
            schema = schema_loader.get_schema(
                self.source_type(),
                self.source_database,
                self.source_table
            )
        except SchemaNotFoundError as e:
            raise ValueError(
                f"Schema not found: {self.source_type()}/{self.source_database}/{self.source_table}.yml. "
                f"Create schema file or check path. Error: {e}"
            ) from e
        except SchemaValidationError as e:
            raise ValueError(f"Schema validation failed: {e}") from e
        
        if schema is None:
            raise ValueError(
                f"Schema not found: {self.source_type()}/{self.source_database}/{self.source_table}.yml"
            )
        
        # Additional validation
        validation_errors = schema_loader.validate_schema(schema)
        if validation_errors:
            raise ValueError(
                f"Schema validation failed:\n" + "\n".join(f"  - {err}" for err in validation_errors)
            )
        
        return schema
    
    def _save_state_with_retry(
        self,
        context: AssetExecutionContext,
        validated_incremental_key: str,
        max_value: Any,
        total_rows: int,
        max_retries: int = 3
    ) -> bool:
        """
        Save incremental state with retry logic
        
        Args:
            context: Dagster execution context
            validated_incremental_key: Validated incremental key
            max_value: Maximum value to save as watermark
            total_rows: Total rows synced
            max_retries: Maximum retry attempts
        
        Returns:
            True if saved successfully, False otherwise
        """
        dagster_postgres = getattr(context.resources, "dagster_postgres_resource", None)
        
        if not dagster_postgres:
            context.log.warning("⚠️ No dagster_postgres_resource - state will not be saved")
            return False
        
        context.log.info(f"💾 Saving state: {validated_incremental_key} = {max_value}")
        
        for attempt in range(1, max_retries + 1):
            try:
                success = StateManager.save_incremental_state(
                    context,
                    dagster_postgres,
                    source_type=self.source_type(),
                    source_database=self.source_database,
                    source_table=self.source_table,
                    incremental_key=validated_incremental_key,
                    last_value=max_value,
                    additional_metadata={
                        "rows_synced": total_rows,
                        "asset_name": self.asset_name,
                    }
                )
                
                if success:
                    context.log.info(f"✅ State saved successfully (attempt {attempt})")
                    return True
                else:
                    context.log.warning(f"⚠️ State save returned False (attempt {attempt})")
                    
            except Exception as e:
                context.log.error(f"❌ State save failed (attempt {attempt}): {e}")
            
            # Wait before retry
            if attempt < max_retries:
                import time
                time.sleep(1)
        
        context.log.error(
            "🚨 CRITICAL: Failed to save state after all retries. "
            "Next run will be a FULL SYNC!"
        )
        return False
    
    def _setup_destination_table(
        self,
        context: AssetExecutionContext,
        destination,
        schema: TableSchema,
        converted_columns: List[Dict[str, Any]]
    ):
        """Setup destination table (create or sync schema)"""
        
        if not destination.table_exists(self.destination_database, self.destination_table):
            context.log.info(f"📝 Creating table {self.destination_database}.{self.destination_table}")
            
            # Get ClickHouse options from subclass
            ch_options = self.get_clickhouse_table_options()
            
            # Determine engine
            if ch_options.get("engine"):
                engine = ch_options["engine"]
                context.log.info(f"🔧 Using custom engine: {engine}")
            else:
                # Auto-select based on sync_method
                if self.sync_method == "upsert":
                    engine = "ReplacingMergeTree"
                else:
                    engine = "MergeTree"
                context.log.info(f"🔧 Using default engine: {engine}")
            
            # Determine ORDER BY
            if ch_options.get("order_by"):
                order_by = ch_options["order_by"]
                context.log.info(f"🔧 Using custom ORDER BY: {order_by}")
            else:
                # Default: use primary keys or first column
                primary_keys = schema.get_primary_keys()
                order_by = [primary_keys[0].name] if primary_keys else [converted_columns[0]["name"]]
                context.log.info(f"🔧 Using default ORDER BY: {order_by}")
            
            # Log additional options
            if ch_options.get("partition_by"):
                context.log.info(f"📊 Partitioning by: {ch_options['partition_by']}")
            
            if ch_options.get("primary_key"):
                context.log.info(f"🔑 Primary key: {ch_options['primary_key']}")
            
            if ch_options.get("ttl"):
                context.log.info(f"⏰ TTL: {ch_options['ttl']}")
            
            # Create table
            destination.create_table(
                self.destination_database,
                self.destination_table,
                converted_columns,
                engine=engine,
                order_by=order_by,
                partition_by=ch_options.get("partition_by"),
                primary_key=ch_options.get("primary_key"),
                ttl=ch_options.get("ttl"),
                settings=ch_options.get("settings", {})
            )
            context.log.info("✅ Table created")
        else:
            context.log.info("🔄 Table exists, syncing schema...")
            destination.sync_schema(
                self.destination_database,
                self.destination_table,
                converted_columns
            )
            context.log.info("✅ Schema synced")
    
    def _load_incremental_state(
        self,
        context: AssetExecutionContext,
        validated_incremental_key: str
    ) -> Optional[IncrementalConfig]:  # ✅ Changed from Dict to IncrementalConfig
        """Load previous incremental state as IncrementalConfig object"""
        
        from dagster_pipeline.connectors.sources.base_source_connector import IncrementalConfig
        
        dagster_postgres = getattr(context.resources, "dagster_postgres_resource", None)
        
        if not dagster_postgres:
            context.log.warning("⚠️ No state manager configured")
            return None
        
        try:
            previous_state = StateManager.load_incremental_state(
                context,
                dagster_postgres,
                self.source_type(),
                self.source_database,
                self.source_table
            )
            
            if previous_state:
                # Verify state key matches
                state_key = previous_state.get('key')
                if state_key != validated_incremental_key:
                    context.log.warning(
                        f"⚠️ State key mismatch! State: '{state_key}', "
                        f"Config: '{validated_incremental_key}'. Ignoring state."
                    )
                    return None
                
                # ✅ Return IncrementalConfig object, NOT dict
                return IncrementalConfig(
                    key=validated_incremental_key,
                    last_value=previous_state["last_value"],
                    operator=previous_state.get("operator", ">"),
                    order_by=previous_state.get("order_by")
                )
            
            return None
            
        except Exception as e:
            context.log.error(f"❌ Failed to load state: {e}")
            return None
    
    # ========================================================================
    # MAIN BUILD METHOD
    # ========================================================================
    
    def build(self) -> Callable:
        """
        Build and return Dagster asset function
        
        Returns:
            Decorated Dagster asset function
        """
        
        def _etl_asset(context: AssetExecutionContext) -> Output:
            """Generated ETL asset with enhanced state management"""
            
            start_time = datetime.now()
            
            context.log.info("=" * 80)
            context.log.info(f"🚀 ETL START: {self.asset_name}")
            context.log.info(f"📊 Source: {self.source_type().upper()} {self.source_database}.{self.source_table}")
            context.log.info(f"🎯 Destination: {self.destination_type().upper()} {self.destination_database}.{self.destination_table}")
            context.log.info(f"⚙️ Mode: {self.sync_method}, Incremental: {self.incremental_key or 'None'}")
            context.log.info("=" * 80)
            
            source = None
            destination = None
            
            try:
                # ============================================================
                # STEP 1: LOAD SCHEMA
                # ============================================================
                context.log.info("📋 STEP 1: Loading schema...")
                
                schema = self._load_and_validate_schema(context)
                
                source_columns = schema.get_column_names(use_source_names=True)
                context.log.info(f"✅ Schema loaded: {len(source_columns)} columns")
                
                # ============================================================
                # STEP 2: VALIDATE INCREMENTAL KEY
                # ============================================================
                validated_incremental_key = None
                
                if self.incremental_key:
                    context.log.info("🔍 STEP 2: Validating incremental key...")
                    validated_incremental_key = self.validate_and_correct_incremental_key(
                        context, schema
                    )
                    
                    if not validated_incremental_key:
                        raise ValueError(
                            f"Incremental key '{self.incremental_key}' not found in schema. "
                            f"Available columns: {schema.get_column_names()}"
                        )
                    
                    context.log.info(f"✅ Incremental key validated: {validated_incremental_key}")
                else:
                    context.log.info("ℹ️ No incremental key configured - full sync mode")
                
                # ============================================================
                # STEP 3: MAP TYPES
                # ============================================================
                context.log.info("🔄 STEP 3: Mapping types to destination...")
                
                # Create schema dictionary from TableSchema
                schema_dict = schema.to_dict()
                
                # DEBUG: Log schema details
                context.log.info(f"🔍 Schema loaded from: {schema.full_name}")
                context.log.info(f"   Total columns: {len(schema.columns)}")
                context.log.info(f"   Source type: {schema.source_type.value}")
                context.log.info(f"   Database: {schema.database}")
                context.log.info(f"   Table: {schema.table}")
                
                columns = schema_dict.get('source', {}).get('columns', [])
                context.log.info(f"Number of columns in schema_dict: {len(columns)}")
                
                # List all columns
                for i, col in enumerate(columns):
                    context.log.info(f"Column {i}: {col.get('name')} -> {col.get('type')}")

                converted_columns = TypeMapper.convert_schema(
                    schema_dict,
                    self.destination_type(),
                    optimization="balanced"
                )
                
                schema_dict = schema.to_dict()
                # DEBUG: Log the result
                context.log.info(f"✅ Types mapped: {len(converted_columns)} columns")
                
                if len(converted_columns) == 0:
                    context.log.error("❌ CRITICAL: TypeMapper returned empty converted_columns list!")
                    context.log.error(f"Schema that was passed to TypeMapper:")
                    context.log.error(f"Source: {schema_dict.get('source', {}).get('type')}.{schema_dict.get('source', {}).get('database')}.{schema_dict.get('source', {}).get('table')}")
                    context.log.error(f"Columns in schema: {len(columns)}")
                    for col in columns:
                        context.log.error(f"  - {col.get('name')}: {col.get('type')} (nullable: {col.get('nullable', True)})")
                    
                    raise ValueError("Type conversion failed - all columns may have unsupported types")
                
                # ============================================================
                # STEP 4: INITIALIZE CONNECTORS
                # ============================================================
                context.log.info("🔌 STEP 4: Initializing connectors...")
                
                source = self.get_source_connector(context)
                destination = self.get_destination_connector(context)
                
                source.validate()
                destination.validate()
                
                context.log.info("✅ Connectors validated")
                
                # ============================================================
                # STEP 5: SETUP DESTINATION TABLE
                # ============================================================
                context.log.info("🎯 STEP 5: Setting up destination table...")
                
                self._setup_destination_table(
                    context,
                    destination,
                    schema,
                    converted_columns
                )
                
                # ============================================================
                # STEP 6: LOAD PREVIOUS STATE
                # ============================================================
                context.log.info("⚙️ STEP 6: Loading incremental state...")
                
                incremental_config = None
                
                if validated_incremental_key:
                    incremental_config = self._load_incremental_state(
                        context,
                        validated_incremental_key
                    )
                    
                    if incremental_config:
                        context.log.info(
                            f"📌 Incremental from: {validated_incremental_key} > {incremental_config.last_value}"
                        )
                    else:
                        context.log.info("📌 First run - full sync with incremental tracking")
                else:
                    context.log.info("📌 Full sync mode")
                
                # ============================================================
                # STEP 7: EXTRACT AND LOAD DATA
                # ============================================================
                context.log.info("🌊 STEP 7: Extracting and loading data...")
                
                total_rows = 0
                batch_num = 0
                max_value_tracker = None
                
                for batch_num, batch_data in enumerate(
                    source.extract_data(
                        columns=source_columns,
                        batch_size=self.batch_size,
                        incremental_config=incremental_config
                    ), 1
                ):
                    batch_start = datetime.now()
                    
                    if not batch_data:
                        continue
                    
                    # Apply transformations
                    transformed_batch = self.transform_batch(batch_data, schema)
                    
                    context.log.info(f"📦 Batch {batch_num}: {len(transformed_batch)} rows")
                    
                    # Track max incremental value
                    if validated_incremental_key:
                        batch_values = [
                            row.get(validated_incremental_key) 
                            for row in transformed_batch 
                            if row.get(validated_incremental_key) is not None
                        ]
                        
                        if batch_values:
                            batch_max = max(batch_values)
                            
                            if max_value_tracker is None or batch_max > max_value_tracker:
                                max_value_tracker = batch_max
                    
                    # Load to destination
                    rows_loaded = destination.load_data(
                        self.destination_database,
                        self.destination_table,
                        transformed_batch,
                        mode=self.sync_method
                    )
                    
                    total_rows += rows_loaded
                    
                    batch_duration = (datetime.now() - batch_start).total_seconds()
                    rows_per_sec = rows_loaded / batch_duration if batch_duration > 0 else 0
                    
                    context.log.info(
                        f"✅ Batch {batch_num}: {rows_loaded} rows in {batch_duration:.2f}s "
                        f"({rows_per_sec:.0f} rows/s) | Total: {total_rows:,}"
                    )
                
                # ============================================================
                # STEP 8: SAVE STATE (WITH RETRY)
                # ============================================================
                if validated_incremental_key and max_value_tracker is not None:
                    context.log.info("💾 STEP 8: Saving incremental state...")
                    
                    state_saved = self._save_state_with_retry(
                        context,
                        validated_incremental_key,
                        max_value_tracker,
                        total_rows
                    )
                    
                    if not state_saved:
                        context.log.warning(
                            "⚠️ State save failed - next run will perform full sync!"
                        )
                
                # ============================================================
                # FINALIZE
                # ============================================================
                duration = (datetime.now() - start_time).total_seconds()
                
                metadata = {
                    "rows_synced": MetadataValue.int(total_rows),
                    "batches": MetadataValue.int(batch_num),
                    "duration_seconds": MetadataValue.float(duration),
                    "rows_per_second": MetadataValue.float(total_rows / duration if duration > 0 else 0),
                    "sync_type": MetadataValue.text("incremental" if validated_incremental_key else "full"),
                    "sync_method": MetadataValue.text(self.sync_method),
                    "source": MetadataValue.text(f"{self.source_type()} {self.source_database}.{self.source_table}"),
                    "destination": MetadataValue.text(f"{self.destination_type()} {self.destination_database}.{self.destination_table}"),
                }
                
                if max_value_tracker is not None:
                    metadata["last_incremental_value"] = MetadataValue.text(str(max_value_tracker))
                
                output_value = {
                    "rows_synced": total_rows,
                    "batches": batch_num,
                    "duration_seconds": duration,
                    "status": "success",
                    "last_incremental_value": str(max_value_tracker) if max_value_tracker else None
                }
                
                context.log.info("=" * 80)
                context.log.info(
                    f"🎉 ETL COMPLETE: {total_rows:,} rows in {duration:.2f}s "
                    f"({total_rows/duration:.0f} rows/s)" if duration > 0 else f"🎉 ETL COMPLETE: {total_rows:,} rows"
                )
                context.log.info("=" * 80)
                
                return Output(output_value, metadata=metadata)
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                
                context.log.error("=" * 80)
                context.log.error(f"❌ ETL FAILED after {duration:.2f}s")
                context.log.error(f"❌ Error: {str(e)}")
                context.log.error("=" * 80)
                
                # Re-raise exception so Dagster marks asset as failed
                raise
            
            finally:
                # Cleanup
                if source:
                    try:
                        source.close()
                    except Exception as e:
                        context.log.warning(f"Error closing source: {e}")
                
                if destination:
                    try:
                        destination.close()
                    except Exception as e:
                        context.log.warning(f"Error closing destination: {e}")
        
        # Get required resource keys
        required_keys = self.get_required_resource_keys()
        
        # Ensure schema_loader is in required keys
        if "schema_loader" not in required_keys:
            raise ValueError(
                f"Factory {self.__class__.__name__} must include 'schema_loader' "
                f"in get_required_resource_keys()"
            )
        
        # Apply @asset decorator
        return asset(
            name=self.asset_name,
            group_name=self.group_name,
            compute_kind=f"{self.source_type().upper()}->{self.destination_type().upper()}",
            description=self._get_asset_description(),
            tags=self.tags,
            required_resource_keys=required_keys,
        )(_etl_asset)