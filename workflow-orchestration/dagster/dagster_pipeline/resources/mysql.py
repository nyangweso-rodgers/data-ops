from dagster import ConfigurableResource, get_dagster_logger
import mysql.connector
from mysql.connector import pooling
import pandas as pd
from contextlib import contextmanager
from typing import Iterator, Dict, Any, Optional, List
import time


class MySQLResource(ConfigurableResource):
    """Enhanced MySQL resource with connection pooling and utilities"""
    
    # Connection parameters
    host: str
    port: int = 3306
    database: str
    username: str
    password: str
    
    # Pool configuration
    pool_name: str = "mysql_pool"
    pool_size: int = 5
    pool_reset_session: bool = True
    
    # Connection configuration
    connect_timeout: int = 30
    autocommit: bool = False
    charset: str = "utf8mb4"
    
    # Query configuration
    buffered: bool = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pool = None
        self._logger = get_dagster_logger()

    def setup_for_execution(self, context) -> "MySQLResource":
        """Initialize connection pool when resource is used"""
        if self._pool is None:
            try:
                pool_config = {
                    'pool_name': self.pool_name,
                    'pool_size': self.pool_size,
                    'pool_reset_session': self.pool_reset_session,
                    'host': self.host,
                    'port': self.port,
                    'database': self.database,
                    'user': self.username,
                    'password': self.password,
                    'connect_timeout': self.connect_timeout,
                    'autocommit': self.autocommit,
                    'charset': self.charset,
                    'buffered': self.buffered
                }
                
                self._pool = mysql.connector.pooling.MySQLConnectionPool(**pool_config)
                self._logger.info(f"Created MySQL connection pool for {self.host}:{self.port}/{self.database}")
            except Exception as e:
                self._logger.error(f"Failed to create connection pool: {e}")
                raise
        return self

    def teardown_after_execution(self, context) -> None:
        """Clean up connection pool"""
        if self._pool:
            # MySQL connector doesn't have a direct closeall method
            # The pool will be garbage collected
            self._pool = None

    @contextmanager
    def get_connection(self) -> Iterator[mysql.connector.MySQLConnection]:
        """Get a connection from the pool"""
        if not self._pool:
            raise RuntimeError("Connection pool not initialized. Call setup_for_execution first.")
        
        conn = self._pool.get_connection()
        try:
            yield conn
        finally:
            conn.close()  # Returns connection to pool

    def execute_query(self, query: str, params: Optional[tuple] = None, 
                     fetch_size: int = 10000) -> pd.DataFrame:
        """Execute a query and return results as DataFrame"""
        with self.get_connection() as conn:
            cursor = conn.cursor(buffered=True)
            
            try:
                cursor.execute(query, params)
                
                # Get column names
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                if fetch_size and fetch_size > 0:
                    # Fetch in chunks for large results
                    chunks = []
                    while True:
                        rows = cursor.fetchmany(fetch_size)
                        if not rows:
                            break
                        chunk_df = pd.DataFrame(rows, columns=columns)
                        chunks.append(chunk_df)
                    
                    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
                else:
                    # Fetch all results
                    rows = cursor.fetchall()
                    return pd.DataFrame(rows, columns=columns)
            finally:
                cursor.close()

    def _infer_mysql_column_types(self, df: pd.DataFrame) -> Dict[str, str]:
        """Infer MySQL column types from pandas DataFrame"""
        type_mapping = {
            'object': 'TEXT',
            'int64': 'BIGINT',
            'int32': 'INT',
            'int16': 'SMALLINT',
            'float64': 'DOUBLE',
            'float32': 'FLOAT',
            'bool': 'BOOLEAN',
            'datetime64[ns]': 'DATETIME',
            'datetime64[ns, UTC]': 'DATETIME',
            'timedelta64[ns]': 'TIME'
        }
        
        schema = {}
        for column, dtype in df.dtypes.items():
            mysql_type = type_mapping.get(str(dtype), 'TEXT')
            # Handle string columns that might need VARCHAR with length
            if mysql_type == 'TEXT' and df[column].dtype == 'object':
                max_length = df[column].astype(str).str.len().max()
                if pd.notna(max_length) and max_length < 255:
                    mysql_type = f'VARCHAR({min(255, int(max_length * 1.2))})'  # 20% buffer
                elif pd.notna(max_length) and max_length < 65535:
                    mysql_type = 'TEXT'
                else:
                    mysql_type = 'LONGTEXT'
            schema[column] = mysql_type
        
        return schema

    def create_table(self, table_name: str, schema_definition: Dict[str, str], 
                    database: Optional[str] = None) -> None:
        """Create a table with the provided schema definition"""
        target_db = database or self.database
        full_table_name = f"`{target_db}`.`{table_name}`" if target_db else f"`{table_name}`"
        
        # Build CREATE TABLE query with backtick identifiers for MySQL
        columns = [f"`{col}` {data_type}" for col, data_type in schema_definition.items()]
        columns_str = ", ".join(columns)
        query = f"CREATE TABLE {full_table_name} ({columns_str})"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query)
                conn.commit()
                self._logger.info(f"Created table {full_table_name}")
            except Exception as e:
                conn.rollback()
                self._logger.error(f"Failed to create table {full_table_name}: {e}")
                raise
            finally:
                cursor.close()

    def execute_insert(self, table: str, df: pd.DataFrame, 
                      if_exists: str = 'append', batch_size: int = 1000,
                      create_table_if_not_exists: bool = True) -> int:
        """Insert DataFrame into MySQL table with optional table creation"""
        
        # Check if table exists and create if needed
        if create_table_if_not_exists and not self.table_exists(table):
            self._logger.info(f"Table {table} does not exist. Creating it...")
            column_types = self._infer_mysql_column_types(df)
            self.create_table(table, column_types)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                if if_exists == 'replace' and self.table_exists(table):
                    cursor.execute(f"DROP TABLE `{table}`")
                
                # Convert DataFrame to list of tuples for insertion
                columns = df.columns.tolist()
                placeholders = ', '.join(['%s'] * len(columns))
                column_names = ', '.join([f"`{col}`" for col in columns])  # Use backticks for MySQL
                insert_query = f"INSERT INTO `{table}` ({column_names}) VALUES ({placeholders})"
                
                # Insert in batches
                rows_inserted = 0
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size]
                    # Handle None/NaN values properly
                    values = [tuple(None if pd.isna(val) else val for val in row) for row in batch.values]
                    cursor.executemany(insert_query, values)
                    rows_inserted += len(values)
                
                conn.commit()
                self._logger.info(f"Inserted {rows_inserted} rows into {table}")
                return rows_inserted
            except Exception as e:
                conn.rollback()
                self._logger.error(f"Insert failed: {e}")
                raise
            finally:
                cursor.close()

    def execute_bulk_insert(self, table: str, df: pd.DataFrame, 
                           on_duplicate: str = 'IGNORE',
                           create_table_if_not_exists: bool = True) -> int:
        """High-performance bulk insert with optional table creation"""
        
        # Check if table exists and create if needed
        if create_table_if_not_exists and not self.table_exists(table):
            self._logger.info(f"Table {table} does not exist. Creating it...")
            column_types = self._infer_mysql_column_types(df)
            self.create_table(table, column_types)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                columns = df.columns.tolist()
                placeholders = ', '.join(['%s'] * len(columns))
                column_names = ', '.join([f"`{col}`" for col in columns])  # Use backticks for MySQL
                
                if on_duplicate.upper() == 'IGNORE':
                    insert_query = f"INSERT IGNORE INTO `{table}` ({column_names}) VALUES ({placeholders})"
                elif on_duplicate.upper() == 'REPLACE':
                    insert_query = f"REPLACE INTO `{table}` ({column_names}) VALUES ({placeholders})"
                else:
                    insert_query = f"INSERT INTO `{table}` ({column_names}) VALUES ({placeholders})"
                
                # Convert DataFrame to list of tuples, handling None/NaN values
                values = [tuple(None if pd.isna(val) else val for val in row) for row in df.values]
                
                cursor.executemany(insert_query, values)
                conn.commit()
                
                self._logger.info(f"Bulk inserted {len(df)} rows into {table}")
                return len(df)
            except Exception as e:
                conn.rollback()
                self._logger.error(f"Bulk insert failed: {e}")
                raise
            finally:
                cursor.close()

    def table_exists(self, table: str, database: Optional[str] = None) -> bool:
        """Check if a table exists"""
        target_db = database or self.database
        
        query = """
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, (target_db, table))
                return cursor.fetchone()[0] > 0
            finally:
                cursor.close()

    def get_table_row_count(self, table: str) -> int:
        """Get row count for a table"""
        query = f"SELECT COUNT(*) FROM `{table}`"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query)
                return cursor.fetchone()[0]
            finally:
                cursor.close()

    def get_max_value(self, table: str, column: str) -> Any:
        """Get maximum value from a column (useful for incremental syncs)"""
        query = f"SELECT MAX(`{column}`) FROM `{table}`"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                return result[0] if result else None
            finally:
                cursor.close()

    def get_table_schema(self, table: str) -> List[Dict[str, Any]]:
        """Get table schema information"""
        query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, (self.database, table))
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            finally:
                cursor.close()

    def create_database_if_not_exists(self, database: str):
        """Create database if it doesn't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}`")
                conn.commit()
                self._logger.info(f"Created database {database} if not exists")
            finally:
                cursor.close()

    def health_check(self) -> bool:
        """Check if database connection is healthy"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT 1")
                    return cursor.fetchone()[0] == 1
                finally:
                    cursor.close()
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False

    def get_incremental_data(self, table: str, timestamp_column: str, 
                           last_sync_time: Optional[Any] = None, 
                           batch_size: int = 10000) -> pd.DataFrame:
        """Get incremental data based on timestamp column"""
        if last_sync_time:
            query = f"""
                SELECT * FROM `{table}` 
                WHERE `{timestamp_column}` > %s 
                ORDER BY `{timestamp_column}`
            """
            params = (last_sync_time,)
        else:
            query = f"SELECT * FROM `{table}` ORDER BY `{timestamp_column}`"
            params = None
        
        return self.execute_query(query, params, fetch_size=batch_size)