from typing import Any, Dict, List, Optional
import logging

from airflow.hooks.base import BaseHook
import clickhouse_connect
from clickhouse_connect.driver.client import Client

# Import constants
from plugins.utils.constants.v1.constants import LOG_LEVELS

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
        connect_timeout: Optional[int] = None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.clickhouse_conn_id = clickhouse_conn_id
        self.connect_timeout = connect_timeout
        self.client = None
        # Set up logging with the specified level
        self.log.setLevel(log_level)
        
    def get_conn(self) -> Client:
        """
        Establishes a connection to ClickHouse.
        
        :return: ClickHouse client instance
        """
        if self.client is not None:
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
        self.log.info(f"Connected to ClickHouse: {conn_config['host']}:{conn_config['port']}")
        return self.client
    
    def test_connection(self) -> tuple[bool, str]:
        """
        Tests the connection to ClickHouse by executing a simple query.
        
        :return: Tuple of (success: bool, message: str)
        """
        try:
            client = self.get_conn()
            client.query("SELECT 1")
            return True, "Connection successful"
        except Exception as e:
            self.log.error(f"Connection test failed: {str(e)}")
            return False, f"Connection failed: {str(e)}"
        
    def database_exists(self, database: str) -> bool:
        """
        Check if a database exists in ClickHouse.
        
        :param database: The name of the database to check
        :return: True if the database exists, False otherwise
        """
        client = self.get_conn()
        result = client.query("SELECT name FROM system.databases WHERE name = %s", (database,))
        return len(result.result_rows) > 0
    
    def table_exists(self, table_name: str, database: Optional[str] = None) -> bool:
        """
        Check if a table exists in the specified database.
        
        :param table_name: The name of the table to check
        :param database: The database name (optional if already specified in connection)
        :return: True if the table exists, False otherwise
        """
        client = self.get_conn()
        
        # If database is not provided, use the current database
        if not database:
            current_db_result = client.query("SELECT currentDatabase()").first_row
            database = current_db_result[0]
            
        query = """
            SELECT name 
            FROM system.tables 
            WHERE database = {database:String} AND name = {table:String}
        """
        
        try:
            result = client.query(query, parameters={
                'database': database,
                'table': table_name
            })
            return len(result.result_rows) > 0
        except Exception as e:
            self.log.error(f"Failed to check if table exists: {str(e)}")
            raise
    
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
        Create a table in ClickHouse if it doesn't exist.
        
        :param table_name: Name of the table to create
        :param schema: List of dictionaries with 'name' and 'type' keys (e.g., [{'name': 'id', 'type': 'UInt32'}])
        :param database: Database name (optional if already specified in connection)
        :param engine: ClickHouse table engine (default: MergeTree())
        :param order_by: ORDER BY clause (required for MergeTree engines)
        :param partition_by: PARTITION BY clause (e.g., 'toYYYYMM(created_at)' for partitioning by created_at)
        :param extra_clauses: Any additional clauses for table creation (e.g., 'SETTINGS ...')
        """
        client = self.get_conn()
        
        if database:
            if not self.database_exists(database):
                client.command(f"CREATE DATABASE IF NOT EXISTS {database}")
        else:
            current_db_result = client.query("SELECT currentDatabase()").first_row
            database = current_db_result[0]

        if self.table_exists(table_name, database):
            self.log.info(f"Table '{database}.{table_name}' already exists")
            return
            
        # Validate schema contains partition_by field if specified
        if partition_by:
            field_names = [col['name'] for col in schema]
            if partition_by not in field_names and not any(part in partition_by for part in field_names):
                raise ValueError(f"partition_by '{partition_by}' must reference a field in the schema: {field_names}")
        
        # Validate engine requirements
        if "MergeTree" in engine and not order_by:
            raise ValueError("MergeTree engine requires an ORDER BY clause")
        
        columns = [f"{col['name']} {col['type']}" for col in schema]
        columns_str = ", ".join(columns)
        
        db_prefix = f"{database}." if database else ""
        query = f"CREATE TABLE {db_prefix}{table_name} ({columns_str}) ENGINE = {engine}"
        
        if "MergeTree" in engine and order_by:
            query += f" ORDER BY ({order_by})"
        
        if partition_by:
            query += f" PARTITION BY {partition_by}"
            
        if extra_clauses:
            query += f" {extra_clauses}"
            
        try:
            client.command(query)
            self.log.info(f"Created table '{database}.{table_name}' with engine {engine}")
        except Exception as e:
            self.log.error(f"Failed to create table '{database}.{table_name}': {str(e)}")
            raise
    
    def insert_rows(
        self,
        table_name: str,
        rows: List[Dict[str, Any]],
        database: Optional[str] = None
    ) -> int:
        """
        Insert multiple rows into a ClickHouse table efficiently.
        
        :param table_name: Name of the table
        :param rows: List of dictionaries with column:value pairs
        :param database: Database name (optional)
        :return: Number of rows inserted
        """
        if not rows:
            return 0

        client = self.get_conn()
        db_prefix = f"{database}." if database else ""
        
        columns = list(rows[0].keys())
        data = [[row[col] for col in columns] for row in rows]
        
        try:
            client.insert(
                table=f"{db_prefix}{table_name}",
                data=data,
                column_names=columns
            )
            self.log.info(f"Inserted {len(rows)} rows into {db_prefix}{table_name}")
            return len(rows)
        except Exception as e:
            self.log.error(f"Failed to insert rows into {db_prefix}{table_name}: {str(e)}")
            raise
        
    def run_query(self, sql: str, parameters: Optional[Dict[str, Any]] = None) -> List[tuple]:
        """
        Execute a query and return the results.
        
        :param sql: SQL query to execute
        :param parameters: Query parameters
        :return: Query results as list of tuples
        """
        client = self.get_conn()
        try:
            result = client.query(sql, parameters=parameters)
            self.log.info(f"Query executed successfully: {sql}")
            return result.result_rows
        except Exception as e:
            self.log.error(f"Failed to execute query: {sql}. Error: {str(e)}")
            raise
    
    def close(self) -> None:
        """
        Close the connection to ClickHouse if it exists.
        """
        if self.client is not None:
            self.client.close()
            self.client = None
            self.log.info("ClickHouse connection closed")