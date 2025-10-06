import pandas as pd
import numpy as np
from dagster import asset, AssetExecutionContext, Output, AssetMaterialization, DagsterEventType, EventRecordsFilter
from dagster_pipeline.utils import MySQLUtils, ClickHouseUtils, ETLUtils
from typing import Dict, Any, Iterator

@asset(
    name="mysql_amtdb_accounts_to_clickhouse",
    group_name="mysql_to_clickhouse",
    compute_kind="ETL",
    description="Sync accounts table from MySQL amtdb to ClickHouse",
    required_resource_keys={"mysql_resource", "clickhouse_resource", "schema_loader"}
)
def sync_accounts(context: AssetExecutionContext) -> Iterator[Output[Dict[str, Any]]]:
    """Sync accounts table from MySQL to ClickHouse"""
    
    # Inject resources
    mysql_resource = context.resources.mysql_resource
    clickhouse_resource = context.resources.clickhouse_resource
    schema_loader = context.resources.schema_loader
    
    # Load schema configuration
    schema = schema_loader.load_table_schema("mysql", "amtdb", "accounts")
    
    source_db = schema['source']['database']
    source_table = schema['source']['table']
    target_db = schema['target']['database']
    target_table = schema['target']['table']
    etl_config = schema['etl_config']
    
    context.log.info(f"=" * 80)
    context.log.info(f"Starting ETL: {source_db}.{source_table} -> {target_db}.{target_table}")
    context.log.info(f"=" * 80)
    
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
        
        # Step 3: Extract data from MySQL (with incremental)
        context.log.info("STEP 3: Extracting data from MySQL...")
        
        incremental_config = None  # Always defined
        df_source = None
        last_sync_value = None
        if etl_config.get('sync_type') == 'incremental':
            incremental_key = etl_config.get('incremental_key')
            if incremental_key:
                # Query event log for previous max
                events = context.instance.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_MATERIALIZATION,
                        asset_key=context.asset_key,
                    ),
                    limit=1,
                )
                if events:
                    sorted_events = sorted(events, key=lambda e: e.timestamp, reverse=True)
                    latest_mat = sorted_events[0]
                    try:
                        event_entry = latest_mat.event_log_entry
                        if event_entry and 'materialization' in event_entry:
                            metadata = event_entry['materialization'].get('metadata', {})
                            last_sync_value = metadata.get("last_sync_value_for_accounts")
                            context.log.debug(f"Retrieved last_sync_value: {last_sync_value}")
                    except Exception as parse_err:
                        context.log.warning(f"Parse error: {parse_err}")
                
                if last_sync_value is None:
                    # Initial: Fetch ALL (no filter), then compute new max
                    context.log.info(f"Initial full sync for {incremental_key}")
                    df_source = MySQLUtils.fetch_mysql_source_db_table_data(
                        context=context,
                        mysql_resource=mysql_resource,
                        database=source_db,
                        table=source_table,
                        columns=source_columns,
                        batch_size=etl_config.get('batch_size', 10000),
                        incremental_config=None  # Full
                    )
                    if not df_source.empty:
                        new_max = df_source[incremental_key].max()
                        last_sync_value = str(new_max) if pd.notna(new_max) else "1970-01-01 00:00:00"
                        context.log.info(f"Full sync complete; new max {incremental_key} = {last_sync_value}")
                    else:
                        last_sync_value = "1970-01-01 00:00:00"
                        context.log.warning("Full sync: No data found")
                else:
                    # Subsequent: Filter > previous
                    context.log.info(f"Incremental sync: {incremental_key} > {last_sync_value}")
                    incremental_config = {
                        'key': incremental_key,
                        'last_value': last_sync_value,
                        'operator': '>'
                    }
                    df_source = MySQLUtils.fetch_mysql_source_db_table_data(
                        context=context,
                        mysql_resource=mysql_resource,
                        database=source_db,
                        table=source_table,
                        columns=source_columns,
                        batch_size=etl_config.get('batch_size', 10000),
                        incremental_config=incremental_config
                    )
                    if not df_source.empty:
                        new_max = df_source[incremental_key].max()
                        last_sync_value = str(new_max) if pd.notna(new_max) else last_sync_value
                        context.log.info(f"Incremental sync; updated max {incremental_key} = {last_sync_value}")
                    else:
                        context.log.info("No new data; keeping previous max")
        
        # If no df_source (non-incremental), fetch all
        if df_source is None:
            df_source = MySQLUtils.fetch_mysql_source_db_table_data(
                context=context,
                mysql_resource=mysql_resource,
                database=source_db,
                table=source_table,
                columns=source_columns,
                batch_size=etl_config.get('batch_size', 10000),
                incremental_config=None
            )
                
        df_source = MySQLUtils.fetch_mysql_source_db_table_data(
            context=context,
            mysql_resource=mysql_resource,
            database=source_db,
            table=source_table,
            columns=source_columns,
            batch_size=etl_config.get('batch_size', 10000),
            incremental_config=incremental_config
        )
        
        if df_source.empty:
            context.log.warning("No data to sync")
            current_sync_value = pd.Timestamp.now()
            yield AssetMaterialization(
                asset_key="mysql_amtdb_accounts_to_clickhouse",
                description="No new data synced",
                metadata={"last_sync_value_for_accounts": str(current_sync_value)}
            )
            yield Output(
                {
                    "rows_synced": 0,
                    "status": "no_data",
                    "source": f"{source_db}.{source_table}",
                    "target": f"{target_db}.{target_table}"
                }
            )
            return  # End generator after yield Output
        
        # Step 4: Transform data
        context.log.info("STEP 4: Transforming data...")
        df_transformed = ETLUtils.transform_data(
            context=context,
            df=df_source,
            schema=schema
        )
        
        # Step 5: Load to ClickHouse
        context.log.info("STEP 5: Loading data to ClickHouse...")
            
        rows_synced = ClickHouseUtils.insert_data_to_clickhouse(
            context=context,
            clickhouse_resource=clickhouse_resource,
            df=df_transformed,
            database=target_db,
            table=target_table
        )
        
        # Step 6: Verification
        context.log.info("STEP 6: Verification...")
        final_count = ClickHouseUtils.get_row_count(
            context=context,
            clickhouse_resource=clickhouse_resource,
            database=target_db,
            table=target_table
        )
        
        # Yield materialization with metadata
        current_sync_value = pd.Timestamp.now()
        yield AssetMaterialization(
            asset_key="mysql_amtdb_accounts_to_clickhouse",
            description=f"Synced {rows_synced} rows from {source_db}.{source_table}",
            metadata={
                "rows_synced": rows_synced,
                "total_rows": final_count,
                "last_sync_value_for_accounts": str(current_sync_value)
            }
        )
        
        context.log.info(f"=" * 80)
        context.log.info(f"✓ ETL COMPLETED SUCCESSFULLY")
        context.log.info(f"  Rows Synced: {rows_synced}")
        context.log.info(f"  Total Rows in Target: {final_count}")
        context.log.info(f"=" * 80)
        
        # Yield the output (makes function a generator consistently)
        yield Output({
            "rows_synced": rows_synced,
            "total_rows_in_target": final_count,
            "status": "success",
            "source": f"{source_db}.{source_table}",
            "target": f"{target_db}.{target_table}",
            "sync_type": etl_config.get('sync_type', 'full')
        })
        
    except Exception as e:
        context.log.error(f"=" * 80)
        context.log.error(f"✗ ETL FAILED: {str(e)}")
        context.log.error(f"=" * 80)
        raise