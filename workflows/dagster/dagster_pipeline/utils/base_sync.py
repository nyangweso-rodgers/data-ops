# dagster_pipeline/utils/base_sync.py
from dagster import get_dagster_logger, Config
from typing import Optional, Dict, List
import pandas as pd
from pydantic import Field


class BaseSyncConfig(Config):
    """Base configuration for all table sync operations"""
    table_name: str = Field(description="Table name to sync")
    source_resource: str = Field(description="Source resource name")
    destination_resource: str = Field(description="Destination resource name")
    batch_size: int = Field(default=15000, description="Batch size for fetching")
    sync_mode: str = Field(default="incremental", description="Sync mode: incremental or full")
    incremental_column: Optional[str] = Field(default=None, description="Column for incremental sync")
    incremental_value: Optional[str] = Field(default=None, description="Specific incremental value")
    
    # REQUIRED FIELDS - enforces explicit specification
    selected_fields: List[str] = Field(
        description="REQUIRED: List of specific fields to sync. Must be explicitly specified for data safety."
    )
    field_mapping: Optional[Dict[str, str]] = Field(
        default=None,
        description="Field mapping from source to destination: {'source_field': 'dest_field', ...}"
    )
    table_schema: Optional[Dict[str, str]] = Field(
        default=None,
        description="Schema definition for table creation using DESTINATION field names"
    )
    destination_schema: str = Field(default="public", description="Target database schema")
    create_table_if_not_exists: bool = Field(default=True, description="Create table if it doesn't exist")


def execute_table_sync(context, config: BaseSyncConfig):
    """
    Shared sync execution logic that can be used by any table sync asset
    """
    logger = get_dagster_logger()
    
    # Get resources dynamically based on config
    source_db = getattr(context.resources, config.source_resource)
    target_db = getattr(context.resources, config.destination_resource)
    
    # Ensure resources are set up
    source_db = source_db.setup_for_execution(context)
    target_db = target_db.setup_for_execution(context)
    
    try:
        # SAFETY CHECK: Ensure fields are explicitly specified
        if not config.selected_fields or len(config.selected_fields) == 0:
            error_msg = (
                f"CONFIGURATION ERROR for {config.table_name}: selected_fields must be explicitly specified. "
                "Syncing entire tables without field specification is not allowed for data safety."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"✓ {config.table_name}: Field selection validated - {len(config.selected_fields)} fields specified")
        
        # Ensure target schema exists
        if hasattr(target_db, 'create_schema_if_not_exists'):
            target_db.create_schema_if_not_exists(config.destination_schema)
        
        # Build field selection with mapping
        source_fields = config.selected_fields.copy()
        destination_fields = []
        
        # Apply field mapping if provided
        if config.field_mapping:
            destination_fields = [
                config.field_mapping.get(field, field) for field in source_fields
            ]
            logger.info(f"{config.table_name}: Field mapping applied - {dict(zip(source_fields, destination_fields))}")
        else:
            destination_fields = source_fields.copy()
            logger.info(f"{config.table_name}: No field mapping - using source field names")
            
        # Build SELECT with aliases for mapped fields
        select_parts = []
        for source_field, dest_field in zip(source_fields, destination_fields):
            if source_field != dest_field:
                select_parts.append(f"{source_field} AS {dest_field}")
            else:
                select_parts.append(source_field)
        
        fields_str = ", ".join(select_parts)
        logger.info(f"{config.table_name}: Syncing fields - {fields_str}")
        
        # Handle incremental column mapping
        incremental_source_column = config.incremental_column
        incremental_dest_column = config.incremental_column
        
        if config.sync_mode == "incremental" and config.incremental_column:
            # Validate incremental column is in selected fields
            if config.incremental_column not in source_fields:
                error_msg = (
                    f"CONFIGURATION ERROR for {config.table_name}: "
                    f"Incremental column '{config.incremental_column}' must be included in selected_fields. "
                    f"Current selected_fields: {source_fields}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Check if incremental column needs mapping
            if config.field_mapping and config.incremental_column in config.field_mapping:
                incremental_dest_column = config.field_mapping[config.incremental_column]
                logger.info(f"{config.table_name}: Incremental column mapped - {incremental_source_column} -> {incremental_dest_column}")
        
        # Build query
        query = f"SELECT {fields_str} FROM {config.table_name}"
        params = None
        
        if config.sync_mode == "incremental" and config.incremental_column:
            # Get incremental value
            incremental_value = None
            
            if hasattr(context, 'partition_key') and context.partition_key:
                incremental_value = context.partition_key
            elif config.incremental_value:
                incremental_value = config.incremental_value
            else:
                # Get the max value from the target table (only if table exists)
                try:
                    if target_db.table_exists(config.table_name, schema=config.destination_schema):
                        incremental_value = target_db.get_max_value(
                            config.table_name, 
                            incremental_dest_column,
                            schema=config.destination_schema
                        )
                        logger.info(f"{config.table_name}: Found max incremental value: {incremental_value}")
                    else:
                        logger.info(f"{config.table_name}: Target table doesn't exist yet, starting from beginning")
                        incremental_value = None
                except Exception as e:
                    logger.warning(f"{config.table_name}: Could not get max value, starting from beginning: {e}")
                    incremental_value = None
            
            if incremental_value:
                query += f" WHERE {incremental_source_column} > %s"
                params = (incremental_value,)
                logger.info(f"{config.table_name}: Incremental sync from {incremental_source_column} > {incremental_value}")
            else:
                logger.info(f"{config.table_name}: No incremental value found, doing full sync")
        
        logger.info(f"{config.table_name}: Executing query - {query}")
        
        # Fetch data
        df = source_db.execute_query(query, params=params, fetch_size=config.batch_size)
        
        if df.empty:
            logger.info(f"{config.table_name}: No new data to sync")
            return {
                "table_name": config.table_name,
                "rows_synced": 0,
                "status": "no_new_data"
            }
        
        logger.info(f"{config.table_name}: Fetched {len(df)} rows from source")
        
        # Validate that DataFrame columns match expected destination fields
        expected_columns = set(destination_fields)
        actual_columns = set(df.columns.tolist())
        
        if expected_columns != actual_columns:
            error_msg = (
                f"Column mismatch for {config.table_name}: "
                f"Expected: {sorted(expected_columns)}, "
                f"Got: {sorted(actual_columns)}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Insert data using bulk insert for performance
        if hasattr(target_db, 'execute_bulk_insert'):
            rows_inserted = target_db.execute_bulk_insert(
                config.table_name, 
                df, 
                schema=config.destination_schema,
                create_table_if_not_exists=config.create_table_if_not_exists,
                table_schema=config.table_schema
            )
        else:
            # Fallback to regular insert (create table first if needed)
            if config.create_table_if_not_exists and config.table_schema:
                if not target_db.table_exists(config.table_name, schema=config.destination_schema):
                    target_db.create_table(
                        table_name=config.table_name,
                        schema_definition=config.table_schema,
                        schema=config.destination_schema
                    )
            
            rows_inserted = target_db.execute_insert(
                config.table_name, df, if_exists='append', schema=config.destination_schema
            )
        
        logger.info(f"{config.table_name}: Successfully synced {rows_inserted} rows")
        
        return {
            "table_name": config.table_name,
            "rows_synced": rows_inserted,
            "source_fields": source_fields,
            "destination_fields": destination_fields,
            "field_mapping_applied": bool(config.field_mapping),
            "sync_mode": config.sync_mode,
            "destination_schema": config.destination_schema,
            "status": "success"
        }
    
    finally:
        # Clean up resources
        if hasattr(source_db, 'teardown_after_execution'):
            source_db.teardown_after_execution(context)
        if hasattr(target_db, 'teardown_after_execution'):
            target_db.teardown_after_execution(context)