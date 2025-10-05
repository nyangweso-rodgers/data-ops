from dagster import ConfigurableResource, get_dagster_logger
import psycopg2
from psycopg2 import pool
import pandas as pd
from contextlib import contextmanager
from typing import Iterator, Dict, Any, Optional, List
import time


class PostgresResource(ConfigurableResource):
    """Enhanced PostgreSQL resource with connection pooling and utilities"""
    
    # Connection parameters
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    
    # Pool configuration
    min_connections: int = 1
    max_connections: int = 20
    
    # Query configuration
    query_timeout: int = 300
    connect_timeout: int = 30
    
    # Schema/search path
    db_schema: Optional[str] = None
    search_path: Optional[List[str]] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pool = None
        self._logger = get_dagster_logger()

    def setup_for_execution(self, context) -> "PostgresResource":
        """Initialize connection pool when resource is used"""
        if self._pool is None:
            try:
                self._pool = psycopg2.pool.ThreadedConnectionPool(
                    self.min_connections,
                    self.max_connections,
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.username,
                    password=self.password,
                    connect_timeout=self.connect_timeout
                )
                self._logger.info(f"Created PostgreSQL connection pool for {self.host}:{self.port}/{self.database}")
            except Exception as e:
                self._logger.error(f"Failed to create connection pool: {e}")
                raise
        return self

    def teardown_after_execution(self, context) -> None:
        """Clean up connection pool"""
        if self._pool:
            self._pool.closeall()
            self._pool = None

    @contextmanager
    def get_connection(self) -> Iterator[psycopg2.extensions.connection]:
        """Get a connection from the pool"""
        if not self._pool:
            raise RuntimeError("Connection pool not initialized. Call setup_for_execution first.")
        
        conn = self._pool.getconn()
        try:
            if self.search_path:
                with conn.cursor() as cursor:
                    cursor.execute(f"SET search_path = {','.join(self.search_path)}")
            yield conn
        finally:
            self._pool.putconn(conn)

    def execute_query(self, query: str, params: Optional[tuple] = None, fetch_size: int = 10000) -> pd.DataFrame:
        """Execute a query and return results as DataFrame with chunking for large results"""
        with self.get_connection() as conn:
            if fetch_size and fetch_size > 0:
                # Use server-side cursor for large results
                cursor_name = f"cursor_{int(time.time())}"
                cursor = conn.cursor(cursor_name)
                cursor.itersize = fetch_size
                
                try:
                    cursor.execute(query, params)
                    
                    # Fetch all results in chunks
                    chunks = []
                    while True:
                        rows = cursor.fetchmany(fetch_size)
                        if not rows:
                            break
                        
                        # Get column names from cursor description
                        columns = [desc[0] for desc in cursor.description]
                        chunk_df = pd.DataFrame(rows, columns=columns)
                        chunks.append(chunk_df)
                    
                    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
                finally:
                    cursor.close()
            else:
                # Regular query execution
                return pd.read_sql(query, conn, params=params)

    def execute_insert(self, table: str, df: pd.DataFrame, if_exists: str = 'append', 
                      schema: Optional[str] = None, method: str = 'multi') -> int:
        """Insert DataFrame into PostgreSQL table with better performance"""
        target_schema = schema or self.db_schema
        table_name = f"{target_schema}.{table}" if target_schema else table
        
        with self.get_connection() as conn:
            rows_inserted = df.to_sql(
                table, 
                conn, 
                if_exists=if_exists, 
                index=False, 
                method=method,
                schema=target_schema
            )
            conn.commit()
            self._logger.info(f"Inserted {len(df)} rows into {table_name}")
            return len(df)

    def _infer_column_types(self, df: pd.DataFrame) -> Dict[str, str]:
        """Infer PostgreSQL column types from pandas DataFrame"""
        type_mapping = {
            'object': 'TEXT',
            'int64': 'BIGINT',
            'int32': 'INTEGER',
            'int16': 'SMALLINT',
            'float64': 'DOUBLE PRECISION',
            'float32': 'REAL',
            'bool': 'BOOLEAN',
            'datetime64[ns]': 'TIMESTAMP',
            'datetime64[ns, UTC]': 'TIMESTAMP WITH TIME ZONE',
            'timedelta64[ns]': 'INTERVAL'
        }
        
        schema = {}
        for column, dtype in df.dtypes.items():
            pg_type = type_mapping.get(str(dtype), 'TEXT')
            # Handle string columns that might need VARCHAR with length
            if pg_type == 'TEXT' and df[column].dtype == 'object':
                max_length = df[column].astype(str).str.len().max()
                if pd.notna(max_length) and max_length < 255:
                    pg_type = f'VARCHAR({min(255, int(max_length * 1.2))})'  # 20% buffer
            schema[column] = pg_type
        
        return schema
    
    def execute_bulk_insert(self, table: str, df: pd.DataFrame, schema: Optional[str] = None, 
                   create_table_if_not_exists: bool = True, table_schema: Optional[Dict[str, str]] = None) -> int:
        """High-performance bulk insert using COPY with strict table schema validation"""
        import io
        
        target_schema = schema or self.db_schema or 'public'
        table_name = f"{target_schema}.{table}"  # For logging
        
        # Check if table exists and create if needed
        if create_table_if_not_exists and not self.table_exists(table, target_schema):
            self._logger.info(f"Table {table_name} does not exist. Creating it...")
            
            # Create schema if it doesn't exist
            if target_schema != 'public':
                self.create_schema_if_not_exists(target_schema)
            
            # STRICT VALIDATION: Table schema must be provided
            if not table_schema:
                error_msg = f"Table creation failed for {table_name}: table_schema must be provided for table creation"
                self._logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Validate DataFrame columns against schema
            df_columns = set(df.columns.tolist())
            schema_columns = set(table_schema.keys())
            
            missing_in_schema = df_columns - schema_columns
            if missing_in_schema:
                error_msg = (
                    f"Schema validation failed for {table_name}: "
                    f"DataFrame columns {sorted(missing_in_schema)} are not defined in the provided table_schema. "
                    f"Provided schema columns: {sorted(schema_columns)}"
                )
                self._logger.error(error_msg)
                raise ValueError(error_msg)
            
            extra_in_schema = schema_columns - df_columns
            if extra_in_schema:
                self._logger.warning(
                    f"Table schema for {table_name} contains extra columns {sorted(extra_in_schema)} "
                    f"that are not in the DataFrame. These will be created as NULLable columns."
                )
            
            self._logger.info(f"Using provided schema definition for {table_name}")
            self.create_table(table, table_schema, target_schema)
            
            # Verify table was created successfully
            if not self.table_exists(table, target_schema):
                error_msg = f"Table creation failed for {table_name}: Table still does not exist after creation attempt"
                self._logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            self._logger.info(f"Successfully created and verified table {table_name}")
        
        # Convert DataFrame to CSV string
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, header=False, sep='\t', na_rep='\\N')
        csv_buffer.seek(0)
        
        # Use properly quoted table name for COPY command
        quoted_table_name = f'"{target_schema}"."{table}"' if target_schema != 'public' else f'"{table}"'
        
        self._logger.info(f"Executing COPY to {quoted_table_name} with columns {df.columns.tolist()}")
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    # Set search path for the session
                    cursor.execute(f"SET search_path TO {target_schema}")
                    
                    # Use the properly quoted table name for COPY
                    cursor.copy_from(
                        csv_buffer, 
                        table, 
                        columns=df.columns.tolist(), 
                        sep='\t',
                        null='\\N'
                    )
                    conn.commit()
                    self._logger.info(f"Bulk inserted {len(df)} rows into {table_name}")
                    return len(df)
                except Exception as e:
                    conn.rollback()
                    self._logger.error(f"Failed to bulk insert into {table_name}: {e}")
                    
                    # Additional debugging info
                    self._logger.error(f"Attempted table name: {quoted_table_name}")
                    self._logger.error(f"DataFrame columns: {df.columns.tolist()}")
                    self._logger.error(f"DataFrame shape: {df.shape}")
                    
                    # Check if table still exists
                    table_still_exists = self.table_exists(table, target_schema)
                    self._logger.error(f"Table exists after error: {table_still_exists}")
                    
                    raise
            

    def table_exists(self, table: str, schema: Optional[str] = None) -> bool:
        """Check if a table exists"""
        target_schema = schema or self.db_schema or 'public'
        
        query = """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            )
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (target_schema, table))
                result = cursor.fetchone()[0]
                self._logger.info(f"Table exists check: {target_schema}.{table} -> {result}")
                return result
            
    def create_table(self, table_name: str, schema_definition: Dict[str, str], schema: Optional[str] = None) -> None:
        """Create a table with the provided schema definition"""
        target_schema = schema or self.db_schema or 'public'
        full_table_name = f'"{target_schema}"."{table_name}"' if target_schema else f'"{table_name}"'
        
        # Build CREATE TABLE query with quoted identifiers
        columns = []
        for col, data_type in schema_definition.items():
            # Handle primary key constraint
            if "PRIMARY KEY" in data_type.upper():
                # Extract the base type and add PRIMARY KEY constraint separately
                base_type = data_type.replace("PRIMARY KEY", "").replace("primary key", "").strip()
                columns.append(f'"{col}" {base_type} PRIMARY KEY')
            else:
                columns.append(f'"{col}" {data_type}')
        
        columns_str = ", ".join(columns)
        query = f"CREATE TABLE {full_table_name} ({columns_str})"
        
        self._logger.info(f"Creating table with query: {query}")
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(query)
                    conn.commit()
                    self._logger.info(f"Successfully created table {full_table_name}")
                    
                    # Verify the table was actually created
                    verify_query = """
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_schema = %s AND table_name = %s
                        )
                    """
                    cursor.execute(verify_query, (target_schema, table_name))
                    verified = cursor.fetchone()[0]
                    self._logger.info(f"Table creation verified: {verified}")
                    
                except Exception as e:
                    conn.rollback()
                    self._logger.error(f"Failed to create table {full_table_name}: {e}")
                    raise

    def get_table_row_count(self, table: str, schema: Optional[str] = None) -> int:
        """Get row count for a table"""
        target_schema = schema or self.db_schema or 'public'
        table_name = f"{target_schema}.{table}"
        
        query = f"SELECT COUNT(*) FROM {table_name}"
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchone()[0]

    def get_max_value(self, table: str, column: str, schema: Optional[str] = None) -> Any:
        """Get maximum value from a column (useful for incremental syncs)"""
        target_schema = schema or self.db_schema or 'public'
        table_name = f"{target_schema}.{table}"
        
        query = f"SELECT MAX({column}) FROM {table_name}"
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                return result[0] if result else None

    def create_schema_if_not_exists(self, schema: str):
        """Create schema if it doesn't exist"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            conn.commit()
            self._logger.info(f"Created schema {schema} if not exists")

    def health_check(self) -> bool:
        """Check if database connection is healthy"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return cursor.fetchone()[0] == 1
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False

    def get_incremental_data(self, table: str, timestamp_column: str, 
                           last_sync_time: Optional[Any] = None, 
                           batch_size: int = 10000, 
                           schema: Optional[str] = None) -> pd.DataFrame:
        """Get incremental data based on timestamp column"""
        target_schema = schema or self.db_schema or 'public'
        table_name = f"{target_schema}.{table}"
        
        if last_sync_time:
            query = f"""
                SELECT * FROM {table_name} 
                WHERE {timestamp_column} > %s 
                ORDER BY {timestamp_column}
            """
            params = (last_sync_time,)
        else:
            query = f"SELECT * FROM {table_name} ORDER BY {timestamp_column}"
            params = None
        
        return self.execute_query(query, params, fetch_size=batch_size)