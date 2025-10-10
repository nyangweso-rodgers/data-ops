import pandas as pd
import numpy as np
from dagster import (
    asset, 
    AssetExecutionContext, 
    Output, 
    AssetMaterialization,
    MetadataValue
)
from dagster_pipeline.utils import MySQLUtils, ClickHouseUtils, ETLUtils
from typing import Dict, Any, Iterator, Optional

@asset(
    name="mysql_amtdb_accounts_to_clickhouse",
    group_name="mysql_to_clickhouse",
    compute_kind="ETL",
    description="Sync accounts table from MySQL amtdb to ClickHouse with incremental support",
    required_resource_keys={"mysql_resource", "clickhouse_resource", "schema_loader"}
)
def sync_accounts_to_clickhouse(context: AssetExecutionContext) -> Iterator[Output[Dict[str, Any]]]:
    """Sync accounts table from MySQL to ClickHouse with incremental loading using streaming"""
    
    # Inject resources
    mysql_resource = context.resources.mysql_resource
    clickhouse_resource = context.resources.clickhouse_resource
    schema_loader = context.resources.schema_loader
    
    # Load schema configuration
    schema_version = "v1"
    schema = schema_loader.load_table_schema("mysql", "amtdb", "accounts", version=schema_version)
    
    source_db = schema['source']['database']
    source_table = schema['source']['table']
    target_db = schema['target']['database']
    target_table = schema['target']['table']
    etl_config = schema['etl_config']
    
    context.log.info("=" * 80)
    context.log.info(f"Starting STREAMING ETL: {source_db}.{source_table} -> {target_db}.{target_table}")
    context.log.info("=" * 80)
    
    try:
        # Step 1: Validate MySQL source
        context.log.info("STEP 1: Validating MySQL source...")
        MySQLUtils.validate_mysql_source_db_table(
            context=context,
            mysql_resource=mysql_resource,
            database=source_db,
            table=source_table
        )
        
        # Validate columns exist
        source_columns = ETLUtils.get_source_columns(schema)
        MySQLUtils.validate_mysql_columns(
            context=context,
            mysql_resource=mysql_resource,
            database=source_db,
            table=source_table,
            required_columns=source_columns
        )
        
        # Step 2: Validate/Create ClickHouse target
        context.log.info("STEP 2: Validating ClickHouse target...")
        table_exists = ClickHouseUtils.validate_if_ch_table_exists(
            context=context,
            clickhouse_resource=clickhouse_resource,
            database=target_db,
            table=target_table
        )
        
        if not table_exists and etl_config.get('create_target', True):
            context.log.info("Creating ClickHouse target table...")
            ClickHouseUtils.create_clickhouse_table_from_schema(
                context=context,
                clickhouse_resource=clickhouse_resource,
                schema=schema,
                database=target_db,
                table=target_table
            )
        elif not table_exists:
            raise ValueError(
                f"Target table {target_db}.{target_table} does not exist and "
                f"create_target is set to False"
            )
        
        # Step 3: Stream data from MySQL (with incremental support)
        context.log.info("STEP 3: Streaming data from MySQL...")
        
        # Determine if this is incremental sync
        sync_type = etl_config.get('sync_type', 'full')
        incremental_key = etl_config.get('incremental_key')
        incremental_config = None
        new_max_value = None
        
        if sync_type == 'incremental' and incremental_key:
            # Build incremental config using MySQLUtils state management
            incremental_config = MySQLUtils.build_incremental_config(
                context=context,
                database=source_db,
                table=source_table,
                incremental_key=incremental_key
            )
        
        # Streaming approach - process batches as they come
        total_rows_synced = 0
        batch_num = 0
        max_value_tracker = None
        
        # Get sync method configuration
        sync_method = etl_config.get('sync_method', 'insert')
        primary_keys = ETLUtils.get_primary_keys(schema) if sync_method == 'upsert' else []
        
        context.log.info(f"Starting streaming ETL with method: {sync_method}")
        
        for batch_num, batch_df in enumerate(MySQLUtils.stream_mysql_data(
            context=context,
            mysql_resource=mysql_resource,
            database=source_db,
            table=source_table,
            columns=source_columns,
            batch_size=etl_config.get('batch_size', 10000),
            incremental_config=incremental_config
        ), 1):
            
            context.log.info(f"Processing batch {batch_num} with {len(batch_df)} rows")
            
            # Step 4: Transform this batch
            transformed_batch = ETLUtils.transform_data(
                context=context,
                df=batch_df,
                schema=schema
            )
            
            # Track max value for incremental sync
            if sync_type == 'incremental' and incremental_key and incremental_key in batch_df.columns:
                batch_max = batch_df[incremental_key].max()
                if pd.notna(batch_max):
                    if max_value_tracker is None:
                        max_value_tracker = batch_max
                    else:
                        max_value_tracker = max(max_value_tracker, batch_max)
            
            # Step 5: Load this batch to ClickHouse immediately
            if sync_method == 'upsert':
                batch_rows = ClickHouseUtils.upsert_data_to_clickhouse(
                    context=context,
                    clickhouse_resource=clickhouse_resource,
                    df=transformed_batch,
                    database=target_db,
                    table=target_table,
                    primary_keys=primary_keys
                )
            else:  # insert/append
                batch_rows = ClickHouseUtils.insert_data_to_clickhouse(
                    context=context,
                    clickhouse_resource=clickhouse_resource,
                    df=transformed_batch,
                    database=target_db,
                    table=target_table
                )
            
            total_rows_synced += batch_rows
            context.log.info(f"✓ Batch {batch_num} completed: {batch_rows} rows synced (total: {total_rows_synced})")
        
        # Save incremental state for next run
        if sync_type == 'incremental' and incremental_key and max_value_tracker is not None:
            MySQLUtils.save_incremental_state(
                context=context,
                database=source_db,
                table=source_table,
                last_value=max_value_tracker,
                incremental_key=incremental_key
            )
            new_max_value = str(max_value_tracker)
        
        # Step 6: Verification
        context.log.info("STEP 6: Verification...")
        final_count = ClickHouseUtils.get_row_count(
            context=context,
            clickhouse_resource=clickhouse_resource,
            database=target_db,
            table=target_table
        )
        
        # Build metadata
        metadata = {
            "rows_synced": MetadataValue.int(total_rows_synced),
            "total_rows_in_target": MetadataValue.int(final_count),
            "sync_type": MetadataValue.text(sync_type),
            "sync_method": MetadataValue.text(sync_method),
            "status": MetadataValue.text("success"),
            "batches_processed": MetadataValue.int(batch_num if batch_num > 0 else 0)
        }
        
        # Store new max value in metadata (for reference/debugging)
        if new_max_value is not None:
            metadata[f"last_{incremental_key}"] = MetadataValue.text(new_max_value)
        
        # Yield materialization on success
        yield AssetMaterialization(
            asset_key=context.asset_key,
            description=f"Streamed {total_rows_synced} rows from {source_db}.{source_table}",
            metadata=metadata
        )
        
        context.log.info("=" * 80)
        context.log.info(f"✓ STREAMING ETL COMPLETED SUCCESSFULLY")
        context.log.info(f"  Total Rows Synced: {total_rows_synced}")
        context.log.info(f"  Total Rows in Target: {final_count}")
        context.log.info(f"  Sync Type: {sync_type}")
        context.log.info(f"  Sync Method: {sync_method}")
        if new_max_value:
            context.log.info(f"  New Max {incremental_key}: {new_max_value}")
        context.log.info("=" * 80)
        
        yield Output({
            "rows_synced": total_rows_synced,
            "total_rows_in_target": final_count,
            "status": "success",
            "source": f"{source_db}.{source_table}",
            "target": f"{target_db}.{target_table}",
            "sync_type": sync_type,
            "sync_method": sync_method,
            "last_sync_value": new_max_value
        })
        
    except Exception as e:
        context.log.error("=" * 80)
        context.log.error(f"✗ STREAMING ETL FAILED: {str(e)}")
        context.log.error("=" * 80)
        raise