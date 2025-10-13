# utils/etl_factory.py
"""
Generic ETL factory for syncing from any SQL source to ClickHouse
Eliminates boilerplate for multiple table syncs
"""

import pandas as pd
from dagster import (
    asset,
    AssetExecutionContext,
    Output,
    AssetMaterialization,
    MetadataValue
)
from typing import Dict, Any, Iterator, Callable, Optional, Literal
from .mysql_utils import MySQLUtils 
from .postgres_utils import PostgresUtils
from .clickhouse_utils import ClickHouseUtils
from .etl_utils import ETLUtils
from .state_manager import StateManager


def create_etl_asset(
    asset_name: str,
    source_type: Literal["mysql", "postgres"],
    source_database: str,
    source_table: str,
    incremental_key: Optional[str] = None,
    sync_method: str = "insert",
    batch_size: int = 10000,
    engine: str = "MergeTree",
    group_name: str = "etl",
) -> Callable:
    """
    Generic factory to create any SQL → ClickHouse ETL asset
    
    Args:
        asset_name: Unique asset name
        source_type: "mysql" or "postgres"
        source_database: Source DB name
        source_table: Source table name
        incremental_key: Column for incremental load (optional)
        sync_method: "insert" or "upsert"
        batch_size: Rows per batch
        engine: ClickHouse engine (MergeTree, ReplacingMergeTree, etc.)
        group_name: Dagster asset group
        
    Note: target_database and target_table are read from schema
    """
    
    # Select source utilities and resource key
    if source_type == "mysql":
        source_utils = MySQLUtils
        resource_key = "mysql_resource"
    elif source_type == "postgres":
        source_utils = PostgresUtils
        resource_key = "postgres_resource"
    else:
        raise ValueError(f"Unsupported source_type: {source_type}")
    
    sync_type = "incremental" if incremental_key else "full"
    
    @asset(
        name=asset_name,
        group_name=group_name,
        compute_kind="ETL",
        description=f"Sync {source_table} from {source_type} to ClickHouse ({sync_type})",
        required_resource_keys={resource_key, "clickhouse_resource", "schema_loader", "dagster_postgres_resource"}
    )
    def _etl_asset(context: AssetExecutionContext) -> Iterator[Output[Dict[str, Any]]]:
        """Generated ETL asset"""
        
        source_resource = getattr(context.resources, resource_key)
        clickhouse_resource = context.resources.clickhouse_resource
        schema_loader = context.resources.schema_loader
        dagster_postgres_resource = context.resources.dagster_postgres_resource
        
        # Load schema
        schema = schema_loader.load_table_schema(source_type, source_database, source_table, version="v1")
        
        # Get target from schema
        target_database = schema['target']['database']
        target_table = schema['target']['table']
        
        context.log.info("=" * 80)
        context.log.info(f"ETL: {source_type.upper()} {source_database}.{source_table} → ClickHouse {target_database}.{target_table}")
        context.log.info(f"Type: {sync_type.upper()}, Method: {sync_method.upper()}, Batch: {batch_size}")
        context.log.info("=" * 80)
        
        state_manager = StateManager()
        
        try:
            # Step 1: Validation
            context.log.info("STEP 1: Validating source...")
            source_utils.validate_source_db_table(context, source_resource, source_database, source_table)
            
            source_columns = ETLUtils.get_source_columns(schema)
            source_utils.validate_columns(context, source_resource, source_database, source_table, source_columns)
            
            # Step 2: Validate/Create ClickHouse target
            context.log.info("STEP 2: Validating ClickHouse target...")
            table_exists = ClickHouseUtils.validate_if_ch_table_exists(
                context, clickhouse_resource, target_database, target_table
            )
            
            if not table_exists:
                context.log.info("Creating ClickHouse table...")
                schema['target']['engine'] = engine
                ClickHouseUtils.create_clickhouse_table_from_schema(
                    context, clickhouse_resource, schema, target_database, target_table
                )
            else:
                # Table exists, sync any schema changes (new columns)
                context.log.info("Table exists, checking for schema changes...")
                ClickHouseUtils.sync_schema_columns(
                    context, clickhouse_resource, schema, target_database, target_table
                )
            
            # Step 3: Build incremental config
            context.log.info("STEP 3: Streaming data...")
            incremental_config = None
            max_value_tracker = None
            
            if sync_type == 'incremental' and incremental_key:
                if dagster_postgres_resource is None:
                    context.log.warning("Dagster postgres resource not configured, skipping incremental state management")
                else:
                    previous_state = state_manager.load_incremental_state(
                        context, dagster_postgres_resource, source_type, source_database, source_table
                    )
                    
                    if previous_state:
                        incremental_config = {
                            'key': incremental_key,
                            'last_value': previous_state['last_value'],
                            'operator': '>'
                        }
                    else:
                        incremental_config = {
                            'key': incremental_key,
                            'last_value': None,
                            'operator': '>='
                        }
            
            # Step 4: Process batches
            total_rows = 0
            batch_num = 0
            primary_keys = ETLUtils.get_primary_keys(schema) if sync_method == 'upsert' else []
            
            for batch_num, batch_df in enumerate(
                source_utils.stream_data(
                    context, source_resource, source_database, source_table,
                    source_columns, batch_size, incremental_config
                ), 1
            ):
                context.log.info(f"Batch {batch_num}: {len(batch_df)} rows")
                
                # Transform
                transformed_batch = ETLUtils.transform_data(context, batch_df, schema)
                
                # Track max value for incremental state
                if sync_type == 'incremental' and incremental_key and incremental_key in batch_df.columns:
                    batch_max = batch_df[incremental_key].max()
                    if pd.notna(batch_max):
                        max_value_tracker = batch_max if max_value_tracker is None else max(max_value_tracker, batch_max)
                
                # Load batch
                if sync_method == 'upsert':
                    rows = ClickHouseUtils.upsert_data_to_clickhouse(
                        context, clickhouse_resource, transformed_batch,
                        target_database, target_table, primary_keys
                    )
                else:
                    rows = ClickHouseUtils.insert_data_to_clickhouse(
                        context, clickhouse_resource, transformed_batch,
                        target_database, target_table
                    )
                
                total_rows += rows
                context.log.info(f"✓ Batch {batch_num}: {rows} rows (total: {total_rows})")
            
            # Step 5: Save incremental state
            if sync_type == 'incremental' and incremental_key and max_value_tracker is not None:
                if dagster_postgres_resource is not None:
                    state_manager.save_incremental_state(
                        context, dagster_postgres_resource, source_type, source_database,
                        source_table, incremental_key, max_value_tracker
                    )
                else:
                    context.log.warning("Dagster postgres resource not configured, state not saved")
            
            # Step 6: Verification (only for full syncs)
            final_count = None
            if sync_type == 'full':
                context.log.info("STEP 4: Verification...")
                final_count = ClickHouseUtils.get_row_count(
                    context, clickhouse_resource, target_database, target_table
                )
            
            # Build metadata
            metadata = {
                "rows_synced": MetadataValue.int(total_rows),
                "sync_type": MetadataValue.text(sync_type),
                "sync_method": MetadataValue.text(sync_method),
                "source_type": MetadataValue.text(source_type),
                "status": MetadataValue.text("success"),
                "batches": MetadataValue.int(batch_num if batch_num > 0 else 0)
            }
            
            if final_count is not None:
                metadata["total_rows_in_target"] = MetadataValue.int(final_count)
            
            # Log summary
            if sync_type == 'full':
                summary = f"✓ ETL COMPLETE: {total_rows} rows → {final_count} total"
            else:
                summary = f"✓ ETL COMPLETE: {total_rows} rows synced (incremental)"
            
            context.log.info("=" * 80)
            context.log.info(summary)
            context.log.info("=" * 80)
            
            yield AssetMaterialization(
                asset_key=context.asset_key,
                description=summary,
                metadata=metadata
            )
            
            # Build output
            output = {
                "rows_synced": total_rows,
                "status": "success",
                "source": f"{source_type.upper()} {source_database}.{source_table}",
                "target": f"ClickHouse {target_database}.{target_table}",
                "sync_type": sync_type,
                "sync_method": sync_method,
            }
            
            if final_count is not None:
                output["total_rows"] = final_count
            
            yield Output(output)
            
        except Exception as e:
            context.log.error("=" * 80)
            context.log.error(f"✗ ETL FAILED: {str(e)}")
            context.log.error("=" * 80)
            raise
    
    return _etl_asset