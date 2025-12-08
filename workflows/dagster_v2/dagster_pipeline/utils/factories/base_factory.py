# dagster_pipeline/factories/base_factory.py
"""
Abstract base factory for ETL pipelines

All ETL factories (MySQL→ClickHouse, Postgres→BigQuery, etc.) 
inherit from this base class to ensure consistent behavior.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Generator
from dagster import asset, AssetExecutionContext, Output, AssetMaterialization, MetadataValue
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class BaseETLFactory(ABC):
    """
    Abstract base class for ETL factories
    
    ETL factories create Dagster assets that:
    1. Extract data from a source (via source connector)
    2. Transform data (type mapping, column mapping)
    3. Load data to a destination (via destination connector)
    4. Manage incremental state
    
    Subclasses must implement:
    - source_type() - Return source type ("mysql", "postgres", etc.)
    - destination_type() - Return destination type ("clickhouse", "bigquery", etc.)
    - get_source_connector() - Create source connector instance
    - get_destination_connector() - Create destination connector instance
    - get_required_resource_keys() - Return set of required resource keys
    
    Example:
        >>> factory = MySQLToClickHouseFactory(
        ...     asset_name="mysql_amt_accounts_to_clickhouse",
        ...     source_database="amt",
        ...     source_table="accounts",
        ...     destination_database="analytics",
        ...     destination_table="amt_accounts",
        ...     incremental_key="updated_at"
        ... )
        >>> asset_func = factory.build()
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
        """
        Initialize ETL factory
        
        Args:
            asset_name: Unique Dagster asset name
            source_database: Source database name
            source_table: Source table name
            destination_database: Destination database name
            destination_table: Destination table name
            incremental_key: Column for incremental sync (None = full sync)
            sync_method: "append", "replace", or "upsert"
            batch_size: Rows per batch
            group_name: Dagster asset group (auto-generated if None)
            tags: Additional asset tags
        """
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
        
        # Add standard tags
        self.tags.update({
            "source_type": self.source_type(),
            "destination_type": self.destination_type(),
            "sync_type": "incremental" if incremental_key else "full",
            "sync_method": sync_method
        })
        
        logger.debug(
            "etl_factory_initialized",
            asset_name=asset_name,
            source=f"{self.source_type()}:{source_database}.{source_table}",
            destination=f"{self.destination_type()}:{destination_database}.{destination_table}"
        )
    
    @abstractmethod
    def source_type(self) -> str:
        """Return source type identifier (e.g., 'mysql', 'postgres')"""
        pass
    
    @abstractmethod
    def destination_type(self) -> str:
        """Return destination type identifier (e.g., 'clickhouse', 'bigquery')"""
        pass
    
    @abstractmethod
    def get_source_connector(self, context: AssetExecutionContext):
        """
        Create and return source connector instance
        
        Args:
            context: Dagster execution context (contains resources)
        
        Returns:
            Source connector instance (e.g., MySQLSourceConnector)
        """
        pass
    
    @abstractmethod
    def get_destination_connector(self, context: AssetExecutionContext):
        """
        Create and return destination connector instance
        
        Args:
            context: Dagster execution context (contains resources)
        
        Returns:
            Destination connector instance (e.g., ClickHouseDestinationConnector)
        """
        pass
    
    @abstractmethod
    def get_required_resource_keys(self) -> set:
        """
        Return set of required resource keys for this ETL pipeline
        
        Returns:
            Set of resource key strings (e.g., {"mysql_amt", "clickhouse_resource", "schema_loader"})
        """
        pass
    
    def _default_group_name(self) -> str:
        """Generate default group name"""
        return f"{self.source_type()}_{self.source_database}_to_{self.destination_type()}"
    
    def _get_asset_description(self) -> str:
        """Generate asset description"""
        sync_type = "incremental" if self.incremental_key else "full"
        return (
            f"ETL: {self.source_type().upper()} {self.source_database}.{self.source_table} → "
            f"{self.destination_type().upper()} {self.destination_database}.{self.destination_table} "
            f"({sync_type}, {self.sync_method})"
        )
    
    def build(self) -> Callable:
        """
        Build and return Dagster asset function
        
        Returns:
            Dagster asset function that executes the ETL pipeline
        """
        
        def _etl_asset(context: AssetExecutionContext) -> Generator:
            """
            Generated ETL asset
            
            Executes the complete ETL pipeline:
            1. Load schema
            2. Validate source and destination
            3. Extract data in batches
            4. Transform data
            5. Load to destination
            6. Save incremental state
            """
            from dagster_pipeline.utils.schema_loader import SchemaLoader
            from dagster_pipeline.utils.type_mapper import TypeMapper
            from dagster_pipeline.utils.state_manager import StateManager
            
            start_time = datetime.now()
            
            context.log.info("=" * 80)
            context.log.info(f"🚀 ETL START: {self.asset_name}")
            context.log.info(f"📊 Source: {self.source_type().upper()} {self.source_database}.{self.source_table}")
            context.log.info(f"🎯 Destination: {self.destination_type().upper()} {self.destination_database}.{self.destination_table}")
            context.log.info(f"⚙️ Mode: {self.sync_method}, Incremental: {self.incremental_key or 'None'}")
            context.log.info("=" * 80)
            
            try:
                # ================================================================
                # STEP 1: LOAD AND VALIDATE SCHEMA
                # ================================================================
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
                
                # Validate schema
                validation_errors = schema_loader.validate_schema(schema)
                if validation_errors:
                    raise ValueError(f"Schema validation failed: {validation_errors}")
                
                # Get columns
                source_columns = schema.get_column_names(use_source_names=True)
                
                context.log.info(f"✅ Schema loaded: {len(source_columns)} columns")
                
                # ================================================================
                # STEP 2: MAP TYPES FOR DESTINATION
                # ================================================================
                context.log.info("🔄 STEP 2: Mapping types to destination...")
                
                schema_dict = schema.to_dict()
                converted_columns = TypeMapper.convert_schema(
                    schema_dict,
                    self.destination_type(),
                    optimization="balanced"
                )
                
                context.log.info(f"✅ Types mapped: {len(converted_columns)} columns")
                
                # ================================================================
                # STEP 3: INITIALIZE CONNECTORS
                # ================================================================
                context.log.info("🔌 STEP 3: Initializing connectors...")
                
                # Pass context directly - connectors will access resources from context
                source = self.get_source_connector(context)
                destination = self.get_destination_connector(context)
                
                # Validate connectors
                source.validate()
                destination.validate()
                
                context.log.info("✅ Connectors validated")
                
                # ================================================================
                # STEP 4: SETUP DESTINATION TABLE
                # ================================================================
                context.log.info("🎯 STEP 4: Setting up destination table...")
                
                if not destination.table_exists(self.destination_database, self.destination_table):
                    context.log.info(f"📝 Creating table {self.destination_database}.{self.destination_table}")
                    
                    destination.create_table(
                        self.destination_database,
                        self.destination_table,
                        converted_columns,
                        engine="ReplacingMergeTree" if self.sync_method == "upsert" else "MergeTree",
                        order_by=[schema.get_primary_keys()[0].name] if schema.get_primary_keys() else [converted_columns[0]["name"]]
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
                
                # ================================================================
                # STEP 5: PREPARE INCREMENTAL STATE
                # ================================================================
                context.log.info("⚙️ STEP 5: Preparing incremental state...")
                
                incremental_config = None
                max_value_tracker = None
                
                if self.incremental_key:
                    state_manager = StateManager()
                    dagster_postgres = getattr(context.resources, "dagster_postgres_resource", None)
                    
                    if dagster_postgres:
                        previous_state = state_manager.load_incremental_state(
                            context,
                            dagster_postgres,
                            self.source_type(),
                            self.source_database,
                            self.source_table
                        )
                        
                        if previous_state:
                            incremental_config = {
                                "key": self.incremental_key,
                                "last_value": previous_state["last_value"],
                                "operator": ">"
                            }
                            context.log.info(f"📌 Incremental from: {self.incremental_key} > {previous_state['last_value']}")
                        else:
                            incremental_config = {
                                "key": self.incremental_key,
                                "last_value": None,
                                "operator": ">="
                            }
                            context.log.info("📌 First run - full sync with incremental tracking")
                    else:
                        context.log.warning("⚠️ No state manager configured - running full sync")
                else:
                    context.log.info("📌 Full sync mode")
                
                # ================================================================
                # STEP 6: EXTRACT, TRANSFORM, LOAD (ETL)
                # ================================================================
                context.log.info("🌊 STEP 6: Extracting and loading data...")
                
                total_rows = 0
                batch_num = 0
                
                for batch_num, batch_data in enumerate(
                    source.extract_data(
                        columns=source_columns,
                        batch_size=self.batch_size,
                        incremental_config=incremental_config
                    ), 1
                ):
                    batch_start = datetime.now()
                    
                    context.log.info(f"📦 Batch {batch_num}: {len(batch_data)} rows")
                    
                    # Track max incremental value
                    if self.incremental_key and batch_data:
                        # batch_data is now list of dicts, not DataFrame
                        batch_values = [row.get(self.incremental_key) for row in batch_data]
                        batch_max = max((v for v in batch_values if v is not None), default=None)
                        
                        if batch_max is not None:
                            max_value_tracker = (
                                batch_max if max_value_tracker is None
                                else max(max_value_tracker, batch_max)
                            )
                    
                    # Load to destination
                    rows_loaded = destination.load_data(
                        self.destination_database,
                        self.destination_table,
                        batch_data,  # Now passes list of dicts
                        mode=self.sync_method
                    )
                    
                    total_rows += rows_loaded
                    
                    batch_duration = (datetime.now() - batch_start).total_seconds()
                    rows_per_sec = rows_loaded / batch_duration if batch_duration > 0 else 0
                    
                    context.log.info(
                        f"✅ Batch {batch_num}: {rows_loaded} rows in {batch_duration:.2f}s "
                        f"({rows_per_sec:.0f} rows/s) | Total: {total_rows:,}"
                    )
                
                # ================================================================
                # STEP 7: SAVE INCREMENTAL STATE
                # ================================================================
                if self.incremental_key and max_value_tracker is not None:
                    context.log.info("💾 STEP 7: Saving incremental state...")
                    
                    state_manager = StateManager()
                    dagster_postgres = getattr(context.resources, "dagster_postgres_resource", None)
                    
                    if dagster_postgres:
                        state_manager.save_incremental_state(
                            context,
                            dagster_postgres,
                            self.source_type(),
                            self.source_database,
                            self.source_table,
                            self.incremental_key,
                            max_value_tracker,
                            additional_metadata={"rows_synced": total_rows}
                        )
                        context.log.info(f"✅ State saved: {self.incremental_key} = {max_value_tracker}")
                
                # ================================================================
                # STEP 8: VERIFICATION (optional for full syncs)
                # ================================================================
                final_count = None
                if not self.incremental_key:
                    context.log.info("🔍 STEP 8: Verifying final count...")
                    final_count = destination.get_row_count(
                        self.destination_database,
                        self.destination_table
                    )
                    context.log.info(f"✅ Total rows in destination: {final_count:,}")
                
                # ================================================================
                # FINALIZE
                # ================================================================
                duration = (datetime.now() - start_time).total_seconds()
                
                # Build metadata
                metadata = {
                    "rows_synced": MetadataValue.int(total_rows),
                    "batches": MetadataValue.int(batch_num if batch_num > 0 else 0),
                    "duration_seconds": MetadataValue.float(duration),
                    "rows_per_second": MetadataValue.float(total_rows / duration if duration > 0 else 0),
                    "sync_type": MetadataValue.text("incremental" if self.incremental_key else "full"),
                    "sync_method": MetadataValue.text(self.sync_method),
                    "source": MetadataValue.text(f"{self.source_type()} {self.source_database}.{self.source_table}"),
                    "destination": MetadataValue.text(f"{self.destination_type()} {self.destination_database}.{self.destination_table}"),
                    "status": MetadataValue.text("success")
                }
                
                if final_count is not None:
                    metadata["total_rows_in_destination"] = MetadataValue.int(final_count)
                
                if max_value_tracker is not None:
                    metadata["last_incremental_value"] = MetadataValue.text(str(max_value_tracker))
                
                # Log summary
                context.log.info("=" * 80)
                context.log.info(f"🎉 ETL COMPLETE: {total_rows:,} rows in {duration:.2f}s ({total_rows/duration:.0f} rows/s)")
                if final_count:
                    context.log.info(f"📊 Total in destination: {final_count:,} rows")
                context.log.info("=" * 80)
                
                # Materialize
                yield AssetMaterialization(
                    asset_key=context.asset_key,
                    description=f"Synced {total_rows:,} rows in {duration:.2f}s",
                    metadata=metadata
                )
                
                # Return output
                output_value = {
                    "rows_synced": total_rows,
                    "batches": batch_num,
                    "duration_seconds": duration,
                    "status": "success"
                }
                
                if final_count is not None:
                    output_value["total_rows_in_destination"] = final_count
                
                yield Output(output_value, metadata=metadata)
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                
                context.log.error("=" * 80)
                context.log.error(f"❌ ETL FAILED after {duration:.2f}s")
                context.log.error(f"❌ Error: {str(e)}")
                context.log.error("=" * 80)
                
                # Log failure
                yield AssetMaterialization(
                    asset_key=context.asset_key,
                    description=f"Failed: {str(e)}",
                    metadata={
                        "status": MetadataValue.text("failed"),
                        "error": MetadataValue.text(str(e)),
                        "duration_seconds": MetadataValue.float(duration)
                    }
                )
                
                raise
            
            finally:
                # Cleanup connectors
                if 'source' in locals():
                    source.close()
                if 'destination' in locals():
                    destination.close()
        
        # Get required resource keys from subclass
        required_keys = self.get_required_resource_keys()
        
        # Apply the @asset decorator with proper configuration
        return asset(
            name=self.asset_name,
            group_name=self.group_name,
            compute_kind=f"{self.source_type().upper()}->{self.destination_type().upper()}",
            description=self._get_asset_description(),
            tags=self.tags,
            required_resource_keys=required_keys,   # THIS IS THE FIX
        )(_etl_asset)