from dagster import ConfigurableResource, get_dagster_logger
import clickhouse_connect
import pandas as pd
from contextlib import contextmanager
from typing import Iterator, Dict, Any, Optional, List, Union
import time
from datetime import datetime


class ClickHouseResource(ConfigurableResource):
    """Enhanced ClickHouse resource with connection management and utilities"""
    
    # Connection parameters
    host: str
    port: int = 8123
    database: str = "default"
    username: str = "default"
    password: str = ""
    
    # Connection settings
    secure: bool = False
    compress: bool = True
    connect_timeout: int = 30
    send_receive_timeout: int = 300
    
    # Client settings
    session_timeout: int = 60
    max_execution_time: int = 300
    
    # Insert settings
    insert_block_size: int = 1048576

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._client = None
        self._logger = get_dagster_logger()

    def setup_for_execution(self, context) -> "ClickHouseResource":
        """Initialize ClickHouse client when resource is used"""
        if self._client is None:
            try:
                self._client = clickhouse_connect.get_client(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    username=self.username,
                    password=self.password,
                    secure=self.secure,
                    compress=self.compress,
                    connect_timeout=self.connect_timeout,
                    send_receive_timeout=self.send_receive_timeout,
                    session_timeout=self.session_timeout,
                    settings={
                        'max_execution_time': self.max_execution_time,
                        'max_insert_block_size': self.insert_block_size,
                    }
                )
                self._logger.info(f"Connected to ClickHouse at {self.host}:{self.port}/{self.database}")
            except Exception as e:
                self._logger.error(f"Failed to connect to ClickHouse: {e}")
                raise
        return self

    def teardown_after_execution(self, context) -> None:
        """Clean up ClickHouse client"""
        if self._client:
            self._client.close()
            self._client = None

    @property
    def client(self) -> clickhouse_connect.driver.Client:
        """Get the ClickHouse client"""
        if not self._client:
            raise RuntimeError("Client not initialized. Call setup_for_execution first.")
        return self._client

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Execute a query and return results as DataFrame"""
        try:
            result = self.client.query_df(query, parameters=parameters)
            self._logger.debug(f"Query executed successfully, returned {len(result)} rows")
            return result
        except Exception as e:
            self._logger.error(f"Query execution failed: {e}")
            raise

    def execute_command(self, command: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a command (non-SELECT queries)"""
        try:
            result = self.client.command(command, parameters=parameters)
            self._logger.debug(f"Command executed successfully: {command}")
            return result
        except Exception as e:
            self._logger.error(f"Command execution failed: {e}")
            raise

    def insert_dataframe(self, table: str, df: pd.DataFrame, 
                        if_exists: str = 'append', 
                        column_oriented: bool = True) -> int:
        """Insert DataFrame into ClickHouse table"""
        try:
            if if_exists == 'replace':
                # Truncate table if it exists
                if self.table_exists(table):
                    self.execute_command(f"TRUNCATE TABLE {table}")
            
            # Insert data
            if column_oriented:
                self.client.insert_df(table, df)
            else:
                # Row-oriented insert
                data = df.values.tolist()
                columns = df.columns.tolist()
                self.client.insert(table, data, column_names=columns)
            
            rows_inserted = len(df)
            self._logger.info(f"Inserted {rows_inserted} rows into {table}")
            return rows_inserted
        except Exception as e:
            self._logger.error(f"Insert failed: {e}")
            raise

    def insert_bulk(self, table: str, df: pd.DataFrame, 
                   batch_size: int = 100000) -> int:
        """High-performance bulk insert with batching"""
        total_rows = 0
        
        try:
            # Insert in batches
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                self.client.insert_df(table, batch)
                total_rows += len(batch)
                self._logger.debug(f"Inserted batch {i//batch_size + 1}, rows: {len(batch)}")
            
            self._logger.info(f"Bulk inserted {total_rows} rows into {table}")
            return total_rows
        except Exception as e:
            self._logger.error(f"Bulk insert failed: {e}")
            raise

    def create_table_from_dataframe(self, table: str, df: pd.DataFrame, 
                                  engine: str = "MergeTree()",
                                  order_by: Optional[str] = None,
                                  partition_by: Optional[str] = None,
                                  if_not_exists: bool = True) -> bool:
        """Create table from DataFrame schema"""
        try:
            # Map pandas dtypes to ClickHouse types
            type_mapping = {
                'object': 'String',
                'int64': 'Int64',
                'int32': 'Int32',
                'int16': 'Int16',
                'int8': 'Int8',
                'uint64': 'UInt64',
                'uint32': 'UInt32',
                'uint16': 'UInt16',
                'uint8': 'UInt8',
                'float64': 'Float64',
                'float32': 'Float32',
                'bool': 'UInt8',
                'datetime64[ns]': 'DateTime',
                'datetime64[ns, UTC]': 'DateTime',
                'timedelta64[ns]': 'Int64'
            }
            
            # Build column definitions
            columns = []
            for col, dtype in df.dtypes.items():
                ch_type = type_mapping.get(str(dtype), 'String')
                columns.append(f"`{col}` {ch_type}")
            
            # Build CREATE TABLE statement
            exists_clause = "IF NOT EXISTS " if if_not_exists else ""
            columns_clause = ",\n    ".join(columns)
            
            create_statement = f"""
            CREATE TABLE {exists_clause}{table} (
                {columns_clause}
            ) ENGINE = {engine}
            """
            
            if order_by:
                create_statement += f"\nORDER BY {order_by}"
            
            if partition_by:
                create_statement += f"\nPARTITION BY {partition_by}"
            
            self.execute_command(create_statement)
            self._logger.info(f"Created table {table}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to create table {table}: {e}")
            raise

    def table_exists(self, table: str, database: Optional[str] = None) -> bool:
        """Check if a table exists"""
        target_db = database or self.database
        
        query = """
            SELECT count() FROM system.tables 
            WHERE database = {db:String} AND name = {table:String}
        """
        
        try:
            result = self.execute_query(query, {'db': target_db, 'table': table})
            return result.iloc[0, 0] > 0
        except Exception as e:
            self._logger.error(f"Error checking table existence: {e}")
            return False

    def get_table_row_count(self, table: str) -> int:
        """Get row count for a table"""
        query = f"SELECT count() FROM {table}"
        
        try:
            result = self.execute_query(query)
            return int(result.iloc[0, 0])
        except Exception as e:
            self._logger.error(f"Error getting row count: {e}")
            return 0

    def get_max_value(self, table: str, column: str) -> Any:
        """Get maximum value from a column"""
        query = f"SELECT max({column}) FROM {table}"
        
        try:
            result = self.execute_query(query)
            return result.iloc[0, 0]
        except Exception as e:
            self._logger.error(f"Error getting max value: {e}")
            return None

    def get_table_schema(self, table: str) -> List[Dict[str, str]]:
        """Get table schema information"""
        query = f"DESCRIBE TABLE {table}"
        
        try:
            result = self.execute_query(query)
            return result.to_dict('records')
        except Exception as e:
            self._logger.error(f"Error getting table schema: {e}")
            return []

    def optimize_table(self, table: str, final: bool = False) -> bool:
        """Optimize table (merge parts)"""
        try:
            optimize_clause = "FINAL" if final else ""
            self.execute_command(f"OPTIMIZE TABLE {table} {optimize_clause}")
            self._logger.info(f"Optimized table {table}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to optimize table {table}: {e}")
            return False

    def health_check(self) -> bool:
        """Check if ClickHouse connection is healthy"""
        try:
            result = self.execute_query("SELECT 1")
            return result.iloc[0, 0] == 1
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False

    def get_cluster_info(self) -> pd.DataFrame:
        """Get cluster information"""
        try:
            return self.execute_query("SELECT * FROM system.clusters")
        except Exception as e:
            self._logger.error(f"Error getting cluster info: {e}")
            return pd.DataFrame()

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            metrics = {}
            
            # Get current queries
            current_queries = self.execute_query("SELECT count() FROM system.processes")
            metrics['active_queries'] = int(current_queries.iloc[0, 0])
            
            # Get memory usage
            memory_usage = self.execute_query("SELECT sum(memory_usage) FROM system.processes")
            metrics['memory_usage_bytes'] = int(memory_usage.iloc[0, 0])
            
            # Get parts count
            parts_count = self.execute_query("SELECT sum(active) FROM system.parts")
            metrics['active_parts'] = int(parts_count.iloc[0, 0])
            
            return metrics
        except Exception as e:
            self._logger.error(f"Error getting system metrics: {e}")
            return {}

    def execute_distributed_query(self, query: str, cluster: str = "default") -> pd.DataFrame:
        """Execute query on a distributed cluster"""
        try:
            distributed_query = f"SELECT * FROM clusterAllReplicas('{cluster}', ({query}))"
            return self.execute_query(distributed_query)
        except Exception as e:
            self._logger.error(f"Distributed query failed: {e}")
            raise

    def create_materialized_view(self, view_name: str, target_table: str, 
                                source_table: str, select_query: str) -> bool:
        """Create a materialized view"""
        try:
            mv_query = f"""
            CREATE MATERIALIZED VIEW {view_name}
            TO {target_table}
            AS {select_query}
            FROM {source_table}
            """
            self.execute_command(mv_query)
            self._logger.info(f"Created materialized view {view_name}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to create materialized view: {e}")
            return False