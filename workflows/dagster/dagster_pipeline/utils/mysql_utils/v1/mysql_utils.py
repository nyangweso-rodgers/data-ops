from typing import Dict, Any, Optional, List
import pandas as pd
from dagster import AssetExecutionContext
from dagster_pipeline.resources.databases import MySQLResource
from typing import Iterator
import json
from pathlib import Path
from datetime import datetime


class MySQLUtils:
    """Reusable utilities for MySQL operations"""
    
    # State management
    STATE_DIR = Path("dagster_pipeline/.incremental_state")
    
    @staticmethod
    def _ensure_state_dir():
        """Create state directory if it doesn't exist"""
        MySQLUtils.STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _get_state_file(database: str, table: str) -> Path:
        """Get the state file path for a table"""
        MySQLUtils._ensure_state_dir()
        state_file = f"mysql_{database}_{table}.json"
        return MySQLUtils.STATE_DIR / state_file
    
    @staticmethod
    def load_incremental_state(
        context: AssetExecutionContext,
        database: str,
        table: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load the incremental state for a table
        
        Returns:
            Dict with 'last_value' and 'key', or None if no state exists
        """
        state_file = MySQLUtils._get_state_file(database, table)
        
        if not state_file.exists():
            context.log.info(f"No previous state found for {database}.{table}")
            return None
        
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            context.log.info(f"Loaded state: {state}")
            return state
        except Exception as e:
            context.log.warning(f"Failed to load state from {state_file}: {e}")
            return None
    
    @staticmethod
    def save_incremental_state(
        context: AssetExecutionContext,
        database: str,
        table: str,
        last_value: Any,
        incremental_key: str
    ) -> None:
        """
        Save the incremental state for a table
        
        Args:
            context: Dagster execution context
            database: Database name
            table: Table name
            last_value: The maximum value of the incremental key
            incremental_key: Name of the column used for incrementing
        """
        MySQLUtils._ensure_state_dir()
        state_file = MySQLUtils._get_state_file(database, table)
        
        state = {
            'last_value': str(last_value),
            'key': incremental_key,
            'last_synced_at': datetime.now().isoformat(),
        }
        
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            context.log.info(f"✓ State saved: {state}")
        except Exception as e:
            context.log.warning(f"Failed to save state: {e}")
    
    @staticmethod
    def clear_incremental_state(
        context: AssetExecutionContext,
        database: str,
        table: str
    ) -> None:
        """Clear the state for a table (useful for full resyncs)"""
        state_file = MySQLUtils._get_state_file(database, table)
        
        if state_file.exists():
            state_file.unlink()
            context.log.info(f"✓ Cleared state for {database}.{table}")
    
    @staticmethod
    def build_incremental_config(
        context: AssetExecutionContext,
        database: str,
        table: str,
        incremental_key: str
    ) -> Dict[str, Any]:
        """
        Build incremental configuration based on previous state
        
        - First run: Returns config for fetching all records
        - Subsequent runs: Returns config for fetching only new/updated records
        """
        context.log.info(f"Building incremental config for {database}.{table}")
        
        # Load previous state
        previous_state = MySQLUtils.load_incremental_state(context, database, table)
        
        if previous_state:
            # Incremental load - only fetch records newer than last sync
            context.log.info(f"Incremental load: {incremental_key} > {previous_state['last_value']}")
            
            return {
                'key': incremental_key,
                'last_value': previous_state['last_value'],
                'operator': '>'
            }
        else:
            # Full load - first time syncing this table
            context.log.info(f"Full load: No previous state found")
            
            return {
                'key': incremental_key,
                'last_value': None,
                'operator': '>='
            }
    
    @staticmethod
    def validate_mysql_source_db_table(
        context: AssetExecutionContext,
        mysql_resource: MySQLResource,
        database: str,
        table: str
    ) -> bool:
        """
        Validate if the source database and table exist in MySQL
        """
        context.log.info(f"Validating MySQL source: {database}.{table}")
        
        with mysql_resource.get_connection(database) as conn:
            cursor = conn.cursor()
            
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
        """
        context.log.info(f"Validating columns in {database}.{table}")
        
        with mysql_resource.get_connection(database) as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT COLUMN_NAME 
                FROM information_schema.columns 
                WHERE table_schema = %s 
                AND table_name = %s
            """
            cursor.execute(query, (database, table))
            actual_columns = {row[0] for row in cursor.fetchall()}
            
            missing_columns = set(required_columns) - actual_columns
            
            if missing_columns:
                error_msg = f"Missing columns in {database}.{table}: {missing_columns}"
                context.log.error(error_msg)
                cursor.close()
                raise ValueError(error_msg)
            
            context.log.info(f"✓ All required columns exist in {database}.{table}")
            cursor.close()
            return True

    @staticmethod 
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
        Stream data from MySQL as batches (generator)
        """
        context.log.info(f"Streaming data from {database}.{table}")
        
        columns_str = ', '.join(columns)
        query = f"SELECT {columns_str} FROM {table}"
        
        if incremental_config and incremental_config['last_value'] is not None:
            key = incremental_config['key']
            last_value = incremental_config['last_value']
            operator = incremental_config.get('operator', '>')
            query += f" WHERE {key} {operator} '{last_value}'"
        
        if incremental_config and incremental_config.get('key'):
            query += f" ORDER BY {incremental_config['key']}"
        
        context.log.info(f"Executing query: {query}")
        
        with mysql_resource.get_connection(database) as conn:
            cursor = conn.cursor()
            
            try:
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
            
            max_value = result[0] if result and result[0] is not None else None
            context.log.info(f"Max value for {column}: {max_value}")
            
            return max_value