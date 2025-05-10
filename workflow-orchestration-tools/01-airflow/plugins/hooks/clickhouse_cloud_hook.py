from typing import Any, Dict, List, Optional
import logging

from airflow.hooks.base import BaseHook
import clickhouse_connect
from clickhouse_connect.driver.client import Client

# Import constants
from plugins.utils.constants import LOG_LEVELS

class ClickHouseCloudHook(BaseHook):
    """
    Hook to interact with ClickHouse Cloud.
    :param clickhouse_conn_id: The connection ID to use when connecting to ClickHouse.
    """
    conn_name_attr = 'clickhouse_conn_id'
    default_conn_name = 'clickhouse_default'
    conn_type = 'clickhouse'
    hook_name = 'ClickHouse Cloud Hook'
    
    def __init__(
        self,
        clickhouse_conn_id: str = default_conn_name,
        log_level: int = LOG_LEVELS['INFO'],
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.clickhouse_conn_id = clickhouse_conn_id
        self.client = None
        
        # Set up logging with the specified level
        self.log.setLevel(log_level)
        
    def get_conn(self) -> Client:
        """
        Establishes a connection to ClickHouse.
        
        :return: ClickHouse client instance
        """
        if self.client is None:
            return self.client
        
        conn = self.get_connection(self.clickhouse_conn_id)
        
        conn_config = {
            'host': conn.host,
            'port': conn.port,
            'username': conn.login,
            'password': conn.password
        }
        
        # Extract database from extras if available
        extras = conn.extra_dejson
        if 'database' in extras:
            conn_config['database'] = extras['database']
            
        # Add any other connection parameters from extras
        for key in ['secure', 'verify', 'ca_cert', 'client_cert', 'client_key']:
            if key in extras:
                conn_config[key] = extras[key]
                
        self.client = clickhouse_connect.get_client(**conn_config)
        return self.client
    
    def table_exists(self, table_name: str, database: Optional[str] = None) -> bool:
        """
        Check if a table exists in the specified database.
        
        :param table_name: The name of the table to check
        :param database: The database name (optional if already specified in connection)
        :return: True if the table exists, False otherwise
        """
        client = self.get_conn()
        
        # Construct the query to check if table exists
        query = """
            SELECT name 
            FROM system.tables 
            WHERE database = {database:String} AND name = {table:String}
        """
        
        # If database is not provided, use the current database
        if not database:
            # Get the current database
            current_db_result = client.query("SELECT currentDatabase()").first_row
            database = current_db_result[0]
            
        result = client.query(query, parameters={
            'database': database,
            'table': table_name
        })
        
        return len(result.result_rows) > 0
    
    def create_table(
        self, 
        table_name: str, 
        schema: List[Dict[str, str]], 
        database: Optional[str] = None,
        engine: str = "MergeTree()",
        order_by: Optional[str] = None,
        partition_by: Optional[str] = None,
        extra_clauses: Optional[str] = None
    ) -> None:
        """
        Create a table if it doesn't exist.
        
        :param table_name: Name of the table to create
        :param schema: List of dictionaries with 'name' and 'type' keys
        :param database: Database name (optional if already specified in connection)
        :param engine: ClickHouse table engine (default: MergeTree())
        :param order_by: ORDER BY clause (required for MergeTree engine)
        :param partition_by: PARTITION BY clause (optional)
        :param extra_clauses: Any additional clauses for table creation
        """
        if self.table_exists(table_name, database):
            self.log.info(f"Table '{table_name}' already exists")
            return
            
        client = self.get_conn()
        
        # Prepare the database part
        db_prefix = f"{database}." if database else ""
        
        # Build column definitions
        columns = []
        for col in schema:
            columns.append(f"{col['name']} {col['type']}")
        
        columns_str = ", ".join(columns)
        
        # Build the query
        query = f"CREATE TABLE {db_prefix}{table_name} ({columns_str}) ENGINE = {engine}"
        
        # Add ORDER BY clause (required for MergeTree)
        if "MergeTree" in engine and order_by:
            query += f" ORDER BY ({order_by})"
        
        # Add optional PARTITION BY clause
        if partition_by:
            query += f" PARTITION BY {partition_by}"
            
        # Add any extra clauses
        if extra_clauses:
            query += f" {extra_clauses}"
            
        client.command(query)
        self.log.info(f"Created table '{table_name}'")
        
    def run_query(self, sql: str, parameters: Optional[Dict[str, Any]] = None) -> List[tuple]:
        """
        Execute a query and return the results.
        
        :param sql: SQL query to execute
        :param parameters: Query parameters
        :return: Query results as list of tuples
        """
        client = self.get_conn()
        result = client.query(sql, parameters=parameters)
        return result.result_rows
    
    def close(self) -> None:
        """Close the connection if it exists."""
        if self.client is not None:
            self.client.close()
            self.client = None