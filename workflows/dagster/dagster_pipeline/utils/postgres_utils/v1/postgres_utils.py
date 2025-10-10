from typing import Dict, Any, Optional, List
import pandas as pd
from dagster import AssetExecutionContext
from dagster_pipeline.resources.databases import PostgreSQLResource


class PostgreSQLUtils:
    """Reusable utilities for PostgreSQL operations"""
    
    @staticmethod
    def validate_postgres_source_db_table(
        context: AssetExecutionContext,
        postgres_resource: PostgreSQLResource,
        database: str,
        schema: str,
        table: str
    ) -> bool:
        """
        Validate if the source database and table exist in PostgreSQL
        
        Args:
            context: Dagster execution context
            postgres_resource: PostgreSQL resource
            database: Database name
            schema: Schema name (usually 'public')
            table: Table name
            
        Returns:
            bool: True if table exists
        """
        context.log.info(f"Validating PostgreSQL source: {database}.{schema}.{table}")
        
        with postgres_resource.get_connection(database) as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_name = %s
            """
            cursor.execute(query, (schema, table))
            result = cursor.fetchone()
            
            if result[0] == 0:
                error_msg = f"Table {database}.{schema}.{table} does not exist in PostgreSQL"
                context.log.error(error_msg)
                cursor.close()
                raise ValueError(error_msg)
            
            context.log.info(f"✓ Table {database}.{schema}.{table} exists in PostgreSQL")
            cursor.close()
            return True
    
    @staticmethod
    def fetch_postgres_source_db_table_data(
        context: AssetExecutionContext,
        postgres_resource: PostgreSQLResource,
        database: str,
        schema: str,
        table: str,
        columns: List[str],
        batch_size: int = 10000,
        incremental_config: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Fetch data from PostgreSQL table in batches
        
        Args:
            context: Dagster execution context
            postgres_resource: PostgreSQL resource
            database: Database name
            schema: Schema name
            table: Table name
            columns: List of columns to fetch
            batch_size: Number of records per batch
            incremental_config: Config for incremental loading
            
        Returns:
            DataFrame with fetched data
        """
        context.log.info(f"Fetching data from {database}.{schema}.{table}")
        
        columns_str = ', '.join(columns)
        query = f'SELECT {columns_str} FROM "{schema}"."{table}"'
        
        if incremental_config:
            key = incremental_config['key']
            last_value = incremental_config['last_value']
            operator = incremental_config.get('operator', '>')
            
            query += f" WHERE {key} {operator} '{last_value}'"
            query += f" ORDER BY {key}"
            context.log.info(f"Incremental load: {key} {operator} {last_value}")
        
        context.log.info(f"Executing query: {query}")
        
        with postgres_resource.get_connection(database) as conn:
            df = pd.read_sql(query, conn, chunksize=batch_size)
            
            all_data = []
            total_rows = 0
            
            for chunk_num, chunk in enumerate(df, 1):
                chunk_rows = len(chunk)
                total_rows += chunk_rows
                all_data.append(chunk)
                context.log.info(f"Fetched batch {chunk_num}: {chunk_rows} rows (total: {total_rows})")
            
            if not all_data:
                context.log.warning(f"No data fetched from {database}.{schema}.{table}")
                return pd.DataFrame()
            
            result_df = pd.concat(all_data, ignore_index=True)
            context.log.info(f"✓ Total rows fetched: {len(result_df)}")
            
            return result_df