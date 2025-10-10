from typing import Dict, Any, List, Optional
import pandas as pd
from dagster import AssetExecutionContext
from dagster_pipeline.resources.database import ClickHouseResource
import time  # For mutation wait

class ClickHouseUtils:
    """Reusable utilities for ClickHouse operations"""
    
    @staticmethod
    def validate_if_ch_table_exists(
        context: AssetExecutionContext,
        clickhouse_resource: ClickHouseResource,
        database: str,
        table: str
    ) -> bool:
        """
        Check if ClickHouse table exists
        """
        context.log.info(f"Checking if ClickHouse table exists: {database}.{table}")
        
        with clickhouse_resource.get_client(database) as client:
            query = f"""
                SELECT count() 
                FROM system.tables 
                WHERE database = '{database}' 
                AND name = '{table}'
            """
            result = client.query(query).result_rows[0][0]
            
            exists = result > 0
            
            if exists:
                context.log.info(f"✓ Table {database}.{table} exists in ClickHouse")
            else:
                context.log.info(f"Table {database}.{table} does not exist in ClickHouse")
            
            return exists
    
    @staticmethod
    def create_clickhouse_table_from_schema(
        context: AssetExecutionContext,
        clickhouse_resource: ClickHouseResource,
        schema: Dict[str, Any],
        database: str,
        table: str
    ):
        """
        Create ClickHouse table based on schema configuration
        """
        context.log.info(f"Creating ClickHouse table: {database}.{table}")
        
        columns = []
        primary_keys = []
        
        # Build column definitions
        for col in schema['columns']:
            col_def = f"`{col['target_name']}` {col['target_type']}"
            
            if not col.get('nullable', True):
                col_def += " NOT NULL"
            
            columns.append(col_def)
            
            if col.get('primary_key', False):
                primary_keys.append(col['target_name'])
        
        # Add sync metadata columns
        sync_metadata = schema['target'].get('sync_metadata', {})
        if sync_metadata.get('enabled', False):
            for col_name, col_config in sync_metadata.get('columns', {}).items():
                if col_config.get('enabled', False):
                    col_def = f"`{col_name}` {col_config['type']}"
                    columns.append(col_def)
                    
                    context.log.info(f"Adding sync metadata column: {col_name}")
        
        # Determine engine and order
        engine = schema['target'].get('engine', 'MergeTree')
        order_by = ', '.join(f"`{key}`" for key in primary_keys) if primary_keys else 'tuple()'
        
        # Build joined columns string outside f-string
        columns_str = ',\n            '.join(columns)
        
        # Build CREATE TABLE statement
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS `{database}`.`{table}` (
            {columns_str}
        ) 
        ENGINE = {engine}
        ORDER BY ({order_by})
        """
        
        context.log.info(f"Executing CREATE TABLE:\n{create_sql}")
        
        with clickhouse_resource.get_client(database) as client:
            client.command(create_sql)
            context.log.info(f"✓ Table {database}.{table} created successfully")
    
    @staticmethod
    def insert_data_to_clickhouse(
        context: AssetExecutionContext,
        clickhouse_resource: ClickHouseResource,
        df: pd.DataFrame,
        database: str,
        table: str
    ) -> int:
        """
        Append data to ClickHouse table (no upsert/dedup)
        - OPTIMIZED FOR STREAMING
        """
        if df.empty:
            context.log.warning("DataFrame is empty, nothing to insert")
            return 0
        
        context.log.info(f"Appending {len(df)} rows to {database}.{table}")
        
        with clickhouse_resource.get_client(database) as client:
            # Use optimized settings for streaming
            settings = {
                'max_insert_block_size': 50000,
                'async_insert': 1,
                'wait_for_async_insert': 0,
            }
            
            # Use insert_df with optimized settings
            client.insert_df(table, df, settings=settings)
            context.log.info(f"✓ Successfully appended {len(df)} rows to ClickHouse")
            
            return len(df)
    
    @staticmethod
    def upsert_data_to_clickhouse(
        context: AssetExecutionContext,
        clickhouse_resource: ClickHouseResource,
        df: pd.DataFrame,
        database: str,
        table: str,
        primary_keys: List[str]
    ) -> int:
        """
        Upsert data to ClickHouse (delete existing + insert new)
        - OPTIMIZED FOR STREAMING
        """
        if df.empty:
            context.log.warning("DataFrame is empty, nothing to upsert")
            return 0
        
        context.log.info(f"Upserting {len(df)} rows to {database}.{table}")
        
        with clickhouse_resource.get_client(database) as client:
            # Extract unique keys from this batch only
            unique_keys = df[primary_keys].drop_duplicates()
            
            if len(primary_keys) == 1:
                key = primary_keys[0]
                values = unique_keys[key].tolist()
                values_str = ', '.join([f"'{v}'" if isinstance(v, str) else str(v) for v in values])
                delete_query = f"ALTER TABLE `{database}`.`{table}` DELETE WHERE `{key}` IN ({values_str})"
            else:
                conditions = []
                for _, row in unique_keys.iterrows():
                    condition_parts = [
                        f"`{key}` = '{row[key]}'" if isinstance(row[key], str) else f"`{key}` = {row[key]}"
                        for key in primary_keys
                    ]
                    conditions.append(f"({' AND '.join(condition_parts)})")
                
                delete_query = f"ALTER TABLE `{database}`.`{table}` DELETE WHERE {' OR '.join(conditions)}"
            
            context.log.info(f"Deleting existing records: {len(unique_keys)} unique key combinations")
            client.command(delete_query)
            
            # Wait for mutation to complete
            time.sleep(2)
            
            # Use optimized insert with streaming settings
            settings = {
                'max_insert_block_size': 50000,
                'async_insert': 1,
                'wait_for_async_insert': 0,
            }
            
            client.insert_df(table, df, settings=settings)
            context.log.info(f"✓ Successfully upserted {len(df)} rows to ClickHouse")
            
            return len(df)
    
    @staticmethod
    def get_row_count(
        context: AssetExecutionContext,
        clickhouse_resource: ClickHouseResource,
        database: str,
        table: str
    ) -> int:
        """Get total row count from ClickHouse table"""
        with clickhouse_resource.get_client(database) as client:
            query = f"SELECT count() FROM `{database}`.`{table}`"
            result = client.query(query).result_rows[0][0]
            context.log.info(f"Row count in {database}.{table}: {result}")
            return result

    # NEW: Ultra-optimized method for pure streaming
    @staticmethod
    def stream_insert_optimized(
        context: AssetExecutionContext,
        clickhouse_resource: ClickHouseResource,
        df: pd.DataFrame,
        database: str,
        table: str,
        settings: dict = None
    ) -> int:
        """
        Ultra-optimized streaming insert for maximum performance
        Use this for the fastest possible batch insertion
        """
        if df.empty:
            return 0
        
        if settings is None:
            settings = {
                'max_insert_block_size': 100000,
                'async_insert': 1,
                'wait_for_async_insert': 0,
                'max_memory_usage': 10000000000,  # 10GB
            }
        
        with clickhouse_resource.get_client(database) as client:
            try:
                # Most efficient: use native insert with column-oriented data
                data = [df[col].values.tolist() for col in df.columns]
                
                client.insert(
                    table, 
                    data, 
                    column_names=df.columns.tolist(),
                    settings=settings
                )
                
                context.log.debug(f"✓ Stream inserted {len(df)} rows")
                return len(df)
                
            except Exception as e:
                context.log.warning(f"Native insert failed, falling back to insert_df: {e}")
                # Fallback to standard method
                client.insert_df(table, df, settings=settings)
                return len(df)