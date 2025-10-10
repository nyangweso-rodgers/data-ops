from typing import Dict, Any, Optional, List
import pandas as pd
from dagster import AssetExecutionContext
from dagster_pipeline.resources.databases import MySQLResource
from typing import Iterator


class MySQLUtils:
    """Reusable utilities for MySQL operations"""
    
    @staticmethod
    def validate_mysql_source_db_table(
        context: AssetExecutionContext,
        mysql_resource: MySQLResource,
        database: str,
        table: str
    ) -> bool:
        """
        Validate if the source database and table exist in MySQL
        
        Args:
            context: Dagster execution context for logging
            mysql_resource: MySQL resource
            database: Database name
            table: Table name
            
        Returns:
            bool: True if table exists, raises exception otherwise
        """
        context.log.info(f"Validating MySQL source: {database}.{table}")
        
        with mysql_resource.get_connection(database) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            query = """
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_name = %s
            """
            cursor.execute(query, (database, table))
            result = cursor.fetchone()
            
            if result[0] == 0:
                error_msg = f"Table {database}.{table} does not exist in MySQL"
                context.log.error(error_msg)
                raise ValueError(error_msg)
            
            context.log.info(f"✓ Table {database}.{table} exists in MySQL")
            cursor.close()
            return True
    
    @staticmethod
    def validate_mysql_columns(
        context: AssetExecutionContext,
        mysql_resource: MySQLResource,
        database: str,
        table: str,
        required_columns: List[str]
    ) -> bool:
        """
        Validate if required columns exist in the MySQL table
        
        Args:
            context: Dagster execution context
            mysql_resource: MySQL resource
            database: Database name
            table: Table name
            required_columns: List of column names to validate
            
        Returns:
            bool: True if all columns exist
        """
        context.log.info(f"Validating columns in {database}.{table}")
        
        with mysql_resource.get_connection(database) as conn:
            cursor = conn.cursor()
            
            # Get actual columns
            query = """
                SELECT COLUMN_NAME 
                FROM information_schema.columns 
                WHERE table_schema = %s 
                AND table_name = %s
            """
            cursor.execute(query, (database, table))
            actual_columns = {row[0] for row in cursor.fetchall()}
            
            # Check for missing columns
            missing_columns = set(required_columns) - actual_columns
            
            if missing_columns:
                error_msg = f"Missing columns in {database}.{table}: {missing_columns}"
                context.log.error(error_msg)
                cursor.close()
                raise ValueError(error_msg)
            
            context.log.info(f"✓ All required columns exist in {database}.{table}")
            cursor.close()
            return True

    @staticmethod  # ← FIXED INDENTATION
    def stream_mysql_data(
        context: AssetExecutionContext,
        mysql_resource: MySQLResource,
        database: str,
        table: str,
        columns: List[str],
        batch_size: int = 10000,
        incremental_config: Optional[Dict[str, Any]] = None
    ) -> Iterator[pd.DataFrame]:
        """
        Stream data from MySQL as batches (generator) - MOST EFFICIENT
        """
        context.log.info(f"Streaming data from {database}.{table}")
        
        # Build query (same as before)
        columns_str = ', '.join(columns)
        query = f"SELECT {columns_str} FROM {table}"
        
        if incremental_config:
            key = incremental_config['key']
            last_value = incremental_config['last_value']
            operator = incremental_config.get('operator', '>')
            query += f" WHERE {key} {operator} '{last_value}'"
        
        if incremental_config:
            query += f" ORDER BY {incremental_config['key']}"
        
        context.log.info(f"Executing query: {query}")
        
        with mysql_resource.get_connection(database) as conn:
            cursor = conn.cursor()
            
            try:
                # Set timeouts
                cursor.execute("SET SESSION net_read_timeout = 3600")
                cursor.execute("SET SESSION net_write_timeout = 3600")
                
                cursor.execute(query)
                column_names = [desc[0] for desc in cursor.description]
                
                total_rows = 0
                batch_num = 0
                
                while True:
                    rows = cursor.fetchmany(batch_size)
                    if not rows:
                        break
                    
                    batch_num += 1
                    batch_rows = len(rows)
                    total_rows += batch_rows
                    
                    batch_df = pd.DataFrame(rows, columns=column_names)
                    
                    context.log.info(f"Yielding batch {batch_num}: {batch_rows} rows (total: {total_rows})")
                    yield batch_df
                    
            finally:
                cursor.close()
        
        context.log.info(f"✓ Finished streaming {total_rows} total rows")
    
    @staticmethod
    def get_max_incremental_value(
        context: AssetExecutionContext,
        mysql_resource: MySQLResource,
        database: str,
        table: str,
        column: str
    ) -> Optional[Any]:
        """
        Get the maximum value of an incremental column
        """
        query = f"SELECT MAX({column}) as max_value FROM {table}"
        
        with mysql_resource.get_connection(database) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            
            max_value = result[0] if result and result[0] is not None else None  # Fix: Handle None explicitly
            context.log.info(f"Max value for {column}: {max_value}")
            
            return max_value