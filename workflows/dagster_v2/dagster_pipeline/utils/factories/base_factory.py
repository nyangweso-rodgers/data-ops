# dagster_pipeline/utils/factories/base_factory.py
"""
Abstract base factory for ETL pipelines with enhanced state management
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from dagster import asset, AssetExecutionContext, Output, MetadataValue

from dagster_pipeline.utils.schema_loader import SchemaLoader
from dagster_pipeline.utils.type_mapper import TypeMapper
from dagster_pipeline.utils.state_manager import StateManager

from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class BaseETLFactory(ABC):
    """
    Abstract base class for ETL factories with robust state management
    
    Key improvements:
    - Validates incremental keys before use
    - Retries state saves on failure
    - Better error handling and logging
    - Single Output per asset (no duplicates)
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
        
        self.tags.update({
            "source_type": self.source_type(),
            "destination_type": self.destination_type(),
            "sync_type": "incremental" if incremental_key else "full",
            "sync_method": sync_method
        })
    
    @abstractmethod
    def source_type(self) -> str:
        """Return source type identifier"""
        pass
    
    @abstractmethod
    def destination_type(self) -> str:
        """Return destination type identifier"""
        pass
    
    @abstractmethod
    def get_source_connector(self, context: AssetExecutionContext):
        """Create source connector"""
        pass
    
    @abstractmethod
    def get_destination_connector(self, context: AssetExecutionContext):
        """Create destination connector"""
        pass
    
    @abstractmethod
    def get_required_resource_keys(self) -> set:
        """Return required resource keys"""
        pass
    
    def validate_and_correct_incremental_key(self, context: AssetExecutionContext, schema) -> Optional[str]:
        """
        Validate incremental key - can be overridden by subclasses
        
        Default implementation just returns the key as-is.
        MySQL factory overrides this to do case-insensitive matching.
        """
        return self.incremental_key
    
    def get_clickhouse_table_options(self) -> Dict[str, Any]:
        """
        Get ClickHouse table creation options
        
        Subclasses can override this to provide custom options.
        Returns None values for options that should use defaults.
        """
        return {
            "engine": None,
            "order_by": None,
            "partition_by": None,
            "primary_key": None,
            "ttl": None,
            "settings": {},
        }
    
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
    
    def build(self) -> Callable:
        """Build and return Dagster asset function"""
        
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
                schema_loader = SchemaLoader()
                
                schema = schema_loader.get_schema(
                    self.source_type(),
                    self.source_database,
                    self.source_table
                )
                
                if schema is None:
                    raise ValueError(
                        f"Schema not found: {self.source_type()}/{self.source_database}/{self.source_table}.yml"
                    )
                
                validation_errors = schema_loader.validate_schema(schema)
                if validation_errors:
                    raise ValueError(f"Schema validation failed: {validation_errors}")
                
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
                        raise ValueError(f"Incremental key validation failed: {self.incremental_key}")
                
                # ============================================================
                # STEP 3: MAP TYPES
                # ============================================================
                context.log.info("🔄 STEP 3: Mapping types to destination...")
                
                schema_dict = schema.to_dict()
                converted_columns = TypeMapper.convert_schema(
                    schema_dict,
                    self.destination_type(),
                    optimization="balanced"
                )
                
                context.log.info(f"✅ Types mapped: {len(converted_columns)} columns")
                
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
                    
                    # Log partition and other options
                    if ch_options.get("partition_by"):
                        context.log.info(f"📊 Partitioning by: {ch_options['partition_by']}")
                    
                    if ch_options.get("primary_key"):
                        context.log.info(f"🔑 Primary key: {ch_options['primary_key']}")
                    
                    if ch_options.get("ttl"):
                        context.log.info(f"⏰ TTL: {ch_options['ttl']}")
                    
                    # Create table with options
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
                
                # ============================================================
                # STEP 6: LOAD PREVIOUS STATE
                # ============================================================
                context.log.info("⚙️ STEP 6: Preparing incremental state...")
                
                incremental_config = None
                
                if validated_incremental_key:
                    dagster_postgres = getattr(context.resources, "dagster_postgres_resource", None)
                    
                    if dagster_postgres:
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
                                else:
                                    incremental_config = {
                                        "key": validated_incremental_key,
                                        "last_value": previous_state["last_value"],
                                        "operator": ">"
                                    }
                                    context.log.info(
                                        f"📌 Incremental from: {validated_incremental_key} > {previous_state['last_value']}"
                                    )
                            else:
                                context.log.info("📌 First run - full sync with incremental tracking")
                                
                        except Exception as e:
                            context.log.error(f"❌ Failed to load state: {e}")
                            context.log.info("📌 Continuing with full sync")
                    else:
                        context.log.warning("⚠️ No state manager configured")
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
                    
                    context.log.info(f"📦 Batch {batch_num}: {len(batch_data)} rows")
                    
                    # Track max incremental value
                    if validated_incremental_key:
                        batch_values = [
                            row.get(validated_incremental_key) 
                            for row in batch_data 
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
                        batch_data,
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
                        context.log.error("🚨 State save failed - next run will be full sync!")
                
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
                    "status": MetadataValue.text("success")
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
                    f"({total_rows/duration:.0f} rows/s)"
                )
                context.log.info("=" * 80)
                
                # Return single Output
                return Output(output_value, metadata=metadata)
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                
                context.log.error("=" * 80)
                context.log.error(f"❌ ETL FAILED after {duration:.2f}s")
                context.log.error(f"❌ Error: {str(e)}")
                context.log.error("=" * 80)
                
                # Return Output with error state
                return Output(
                    value={
                        "rows_synced": 0,
                        "status": "failed",
                        "error": str(e),
                        "duration_seconds": duration
                    },
                    metadata={
                        "status": MetadataValue.text("failed"),
                        "error": MetadataValue.text(str(e)),
                        "duration_seconds": MetadataValue.float(duration)
                    }
                )
            
            finally:
                # Cleanup
                if source:
                    source.close()
                if destination:
                    destination.close()
        
        # Get required resource keys
        required_keys = self.get_required_resource_keys()
        
        # Apply @asset decorator
        return asset(
            name=self.asset_name,
            group_name=self.group_name,
            compute_kind=f"{self.source_type().upper()}->{self.destination_type().upper()}",
            description=self._get_asset_description(),
            tags=self.tags,
            required_resource_keys=required_keys,
        )(_etl_asset)