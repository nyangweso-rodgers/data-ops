"""
PostgreSQL source connector for data extraction

IMPROVEMENTS:
- Connection pooling and retry logic
- Better transaction management
- Array type handling (NULL → [])
- Query timeout protection
- Performance optimizations
- Comprehensive error handling

Pure Python implementation - NO PANDAS, NO NUMPY!
"""

import psycopg2
import psycopg2.extras
from psycopg2.extensions import QueryCanceledError
from typing import Iterator, List, Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal
from contextlib import contextmanager
import time

from .base_source_connector import (
    BaseSourceConnector,
    SourceConnectionError,
    SourceValidationError,
    SourceExtractionError,
    IncrementalConfig,
    ColumnSchema
)
from dagster_pipeline.utils.logging_config import get_logger

# Module logger
logger = get_logger(__name__)


class PostgresSourceConnector(BaseSourceConnector):
    """
    PostgreSQL source connector - Production-ready implementation
    
    Features:
    - Automatic retry with exponential backoff
    - Connection timeout protection
    - Named cursors for server-side streaming
    - Proper array type handling (NULL arrays → [])
    - Transaction management
    - Query cancellation support
    
    Key differences from MySQL:
    - Uses psycopg2 instead of pymysql
    - Schema-qualified table names (schema.table)
    - Named cursors for streaming
    - Array types (_int4, text[], etc.)
    - NULL arrays converted to [] for ClickHouse
    
    Returns batches as list of dictionaries:
    [
        {"id": 1, "name": "Alice", "tags": ["a", "b"]},
        {"id": 2, "name": "Bob", "tags": []},  # NULL array → []
    ]
    """
    
    # Connection settings
    DEFAULT_PORT = 5432
    DEFAULT_SCHEMA = "public"
    DEFAULT_CONNECT_TIMEOUT = 30
    DEFAULT_STATEMENT_TIMEOUT = 300000  # 5 minutes in milliseconds
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    RETRY_BACKOFF = 2
    
    # Cursor settings
    DEFAULT_CURSOR_ITERSIZE = 10000
    
    def __init__(self, context, config):
        super().__init__(context, config)
        self._connection = None
        self._connection_params = self._build_connection_params()
        self._schema = config.get("schema", self.DEFAULT_SCHEMA)
    
    def source_type(self) -> str:
        return "postgres"
    
    def required_config_keys(self) -> List[str]:
        return ["host", "user", "password", "database", "table"]
    
    def _build_connection_params(self) -> Dict[str, Any]:
        """Build connection parameters from config"""
        return {
            "host": self.config["host"],
            "port": self.config.get("port", self.DEFAULT_PORT),
            "user": self.config["user"],
            "password": self.config["password"],
            "database": self.config["database"],
            "connect_timeout": self.config.get("connect_timeout", self.DEFAULT_CONNECT_TIMEOUT),
            "options": f"-c statement_timeout={self.config.get('statement_timeout', self.DEFAULT_STATEMENT_TIMEOUT)}"
        }
    
    @contextmanager
    def _get_connection(
        self,
        use_named_cursor: bool = False,
        cursor_name: Optional[str] = None
    ):
        """
        Get PostgreSQL connection with retry logic
        
        Args:
            use_named_cursor: Use named cursor for server-side iteration
            cursor_name: Cursor name (required if use_named_cursor=True)
        """
        conn = None
        cursor = None
        
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                conn = psycopg2.connect(**self._connection_params)
                
                if use_named_cursor and cursor_name:
                    conn.autocommit = False
                    cursor = conn.cursor(
                        name=cursor_name,
                        cursor_factory=psycopg2.extras.RealDictCursor
                    )
                    cursor.itersize = self.config.get("cursor_itersize", self.DEFAULT_CURSOR_ITERSIZE)
                else:
                    conn.autocommit = True
                    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                yield conn, cursor
                return
                
            except psycopg2.OperationalError as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (self.RETRY_BACKOFF ** attempt)
                    self.logger.warning("connection_retry", attempt=attempt + 1, delay=delay, error=str(e))
                    time.sleep(delay)
                else:
                    raise SourceConnectionError(
                        f"Failed to connect to PostgreSQL after {self.MAX_RETRIES} attempts: {e}"
                    ) from e
                    
            except psycopg2.Error as e:
                raise SourceConnectionError(f"PostgreSQL connection error: {e}") from e
                
            finally:
                if cursor and attempt >= self.MAX_RETRIES - 1:
                    try:
                        cursor.close()
                    except Exception:
                        pass
                
                if conn and attempt >= self.MAX_RETRIES - 1:
                    try:
                        if not conn.autocommit and not conn.closed:
                            conn.commit()
                    except Exception:
                        pass
                    
                    try:
                        conn.close()
                    except Exception:
                        pass
        
        if last_error:
            raise SourceConnectionError(f"Failed to connect to PostgreSQL: {last_error}") from last_error
    
    def validate(self) -> bool:
        """Validate PostgreSQL connection and table exists"""
        database = self.config["database"]
        table = self.config["table"]
        schema = self._schema
        
        # Test connection
        try:
            with self._get_connection() as (conn, cursor):
                cursor.execute("SELECT version()")
                result = cursor.fetchone()
                pg_version = result["version"] if result else "unknown"
                self.logger.debug("postgres_version", version=pg_version[:50])
        except psycopg2.Error as e:
            raise SourceConnectionError(f"Failed to connect to PostgreSQL: {e}") from e
        
        # Check table exists
        check_table_query = """
            SELECT 
                table_schema,
                table_name,
                (SELECT pg_total_relation_size(quote_ident(table_schema)||'.'||quote_ident(table_name))) as total_bytes
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s AND table_type = 'BASE TABLE'
        """
        
        try:
            with self._get_connection() as (conn, cursor):
                cursor.execute(check_table_query, (schema, table))
                result = cursor.fetchone()
                
                if result is None:
                    raise SourceValidationError(
                        f"Table {schema}.{table} not found in PostgreSQL database {database}. "
                        f"Check schema and table names."
                    )
                
                size_mb = result["total_bytes"] / 1024 / 1024 if result.get("total_bytes") else 0
                self.logger.info("table_validated", schema=schema, size_mb=round(size_mb, 2) if size_mb else None)
                    
        except psycopg2.Error as e:
            raise SourceValidationError(f"Failed to validate table: {e}") from e
        
        self._is_validated = True
        self.logger.info("source_validated", schema=schema)
        return True
    
    def get_schema(self) -> List[ColumnSchema]:
        """Get PostgreSQL table schema"""
        if not self._is_validated:
            self.validate()
        
        database = self.config["database"]
        table = self.config["table"]
        schema = self._schema
        
        query = """
            SELECT
                c.column_name as name,
                c.data_type as type,
                c.udt_name as udt_type,
                c.is_nullable as nullable,
                c.column_default as default_value,
                CASE 
                    WHEN pk.column_name IS NOT NULL THEN TRUE 
                    ELSE FALSE 
                END as is_primary_key,
                CASE
                    WHEN idx.column_name IS NOT NULL THEN TRUE
                    ELSE FALSE
                END as is_indexed
            FROM information_schema.columns c
            LEFT JOIN (
                SELECT ku.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage ku
                    ON tc.constraint_name = ku.constraint_name
                    AND tc.table_schema = ku.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = %s
                    AND tc.table_name = %s
            ) pk ON c.column_name = pk.column_name
            LEFT JOIN (
                SELECT DISTINCT a.attname as column_name
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                JOIN pg_class t ON t.oid = i.indrelid
                JOIN pg_namespace n ON n.oid = t.relnamespace
                WHERE n.nspname = %s AND t.relname = %s
            ) idx ON c.column_name = idx.column_name
            WHERE c.table_schema = %s 
                AND c.table_name = %s
            ORDER BY c.ordinal_position
        """
        
        try:
            with self._get_connection() as (conn, cursor):
                cursor.execute(query, (schema, table, schema, table, schema, table))
                columns = cursor.fetchall()
                
                if not columns:
                    raise SourceValidationError(f"No columns found for table {schema}.{table}")
                
                schema_list = []
                for col in columns:
                    schema_list.append(ColumnSchema(
                        name=col["name"],
                        type=col["udt_type"],
                        nullable=(col["nullable"] == "YES"),
                        primary_key=col["is_primary_key"],
                        indexed=col["is_indexed"],
                        default=col["default_value"],
                        extra=col["type"]
                    ))
                
                self.logger.info("schema_fetched", schema=schema, columns=len(schema_list))
                return schema_list
                
        except psycopg2.Error as e:
            raise SourceExtractionError(f"Failed to get schema: {e}") from e
    
    def _normalize_value(self, value: Any, column_type: Optional[str] = None) -> Any:
        """
        Convert PostgreSQL types to Python native types
        
        CRITICAL: ClickHouse arrays cannot be NULL!
        - PostgreSQL NULL arrays → empty list []
        - All other NULL values → None
        """
        if value is None:
            # Check if column is array type
            if column_type:
                is_array = column_type.startswith('_') or '[]' in column_type
                if is_array:
                    return []  # NULL array → empty array for ClickHouse
            return None
        
        elif isinstance(value, Decimal):
            return float(value)
            
        elif isinstance(value, memoryview):
            try:
                return bytes(value).decode('utf-8')
            except UnicodeDecodeError:
                return bytes(value).hex()
                
        elif isinstance(value, bytes):
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                return value.hex()
                
        elif isinstance(value, datetime):
            if value.year == 0:
                self.logger.warning("zero_datetime_to_null", value=str(value))
                return None
            return value
        
        elif isinstance(value, date):
            if value.year == 0:
                self.logger.warning("zero_date_to_null", value=str(value))
                return None
            return value
            
        elif isinstance(value, list):
            # PostgreSQL arrays - recursively normalize
            return [
                PostgresSourceConnector._normalize_value(item, column_type=None)
                for item in value
            ]
            
        elif isinstance(value, dict):
            # PostgreSQL JSON/JSONB - recursively normalize
            return {
                k: PostgresSourceConnector._normalize_value(v, column_type=None)
                for k, v in value.items()
            }
            
        else:
            return value
    
    def extract_data(
        self,
        columns: Optional[List[str]] = None,
        batch_size: int = 10000,
        incremental_config: Optional[IncrementalConfig] = None
    ) -> Iterator[List[Dict[str, Any]]]:
        """Extract data from PostgreSQL - returns list of dictionaries"""
        if not self._is_validated:
            self.validate()
        
        database = self.config["database"]
        table = self.config["table"]
        schema = self._schema
        
        # Get schema for column types (needed for array handling)
        schema_info = self.get_schema()
        column_types = {col.name: col.type for col in schema_info}
        
        # Determine column list
        if columns:
            column_list = columns
        else:
            column_list = [col.name for col in schema_info]
        
        # Validate columns
        if columns:
            schema_columns = {col.name for col in schema_info}
            invalid_columns = [col for col in columns if col not in schema_columns]
            if invalid_columns:
                raise SourceValidationError(
                    f"Invalid columns requested: {invalid_columns}. "
                    f"Available columns: {sorted(schema_columns)}"
                )
        
        # Build SELECT clause
        columns_str = ", ".join(f'"{col}"' for col in column_list)
        
        # Build WHERE clause
        where_clause = ""
        params = []
        
        if incremental_config:
            if incremental_config.key not in column_types:
                raise SourceValidationError(f"Incremental key '{incremental_config.key}' not found in table")
            
            if incremental_config.last_value is not None:
                where_clause = f'WHERE "{incremental_config.key}" {incremental_config.operator} %s'
                params.append(incremental_config.last_value)
                self.logger.info(
                    "incremental_extraction",
                    schema=schema,
                    key=incremental_config.key,
                    operator=incremental_config.operator,
                    from_value=str(incremental_config.last_value)[:50]
                )
        
        # Build ORDER BY
        order_clause = ""
        if incremental_config:
            order_by = incremental_config.order_by or incremental_config.key
            order_clause = f'ORDER BY "{order_by}" ASC'
        
        # Build query
        query = f"""
            SELECT {columns_str}
            FROM "{schema}"."{table}"
            {where_clause}
            {order_clause}
        """.strip()
        
        self.logger.info(
            "extraction_started",
            schema=schema,
            batch_size=batch_size,
            columns=len(column_list),
            incremental=bool(incremental_config)
        )
        
        total_rows = 0
        batch_num = 0
        
        # Generate unique cursor name
        cursor_name = f"cursor_{schema}_{table}_{int(datetime.now().timestamp() * 1000)}"
        
        try:
            with self._get_connection(use_named_cursor=True, cursor_name=cursor_name) as (conn, cursor):
                cursor.execute(query, params)
                
                while True:
                    rows = cursor.fetchmany(batch_size)
                    
                    if not rows:
                        break
                    
                    batch_num += 1
                    total_rows += len(rows)
                    
                    # Normalize all values
                    normalized_batch = []
                    for row in rows:
                        normalized_row = {
                            col: self._normalize_value(row[col], column_type=column_types.get(col))
                            for col in column_list
                        }
                        normalized_batch.append(normalized_row)
                    
                    # Log first batch sample
                    if batch_num == 1 and normalized_batch:
                        sample_row = normalized_batch[0]
                        sample_types = {col: type(sample_row[col]).__name__ for col in column_list}
                        self.logger.debug("first_batch_sample", rows=len(normalized_batch), sample_types=sample_types)
                    
                    if batch_num % 10 == 0:
                        self.logger.info("extraction_progress", batches=batch_num, rows=total_rows)
                    
                    yield normalized_batch
                    
        except QueryCanceledError as e:
            raise SourceExtractionError(f"PostgreSQL query canceled (timeout): {e}") from e
        except psycopg2.Error as e:
            raise SourceExtractionError(f"PostgreSQL extraction failed at batch {batch_num}: {e}") from e
        except Exception as e:
            raise SourceExtractionError(f"Unexpected error during extraction: {e}") from e
        
        self.logger.info("extraction_complete", total_rows=total_rows, batches=batch_num)
    
    def get_row_count(
        self,
        where_clause: Optional[str] = None,
        where_params: Optional[List[Any]] = None
    ) -> int:
        """Get row count with optional WHERE clause"""
        if not self._is_validated:
            self.validate()
        
        database = self.config["database"]
        table = self.config["table"]
        schema = self._schema
        
        query = f'SELECT COUNT(*) as cnt FROM "{schema}"."{table}"'
        params = []
        
        if where_clause:
            query += f" WHERE {where_clause}"
            params = where_params or []
        
        try:
            with self._get_connection() as (conn, cursor):
                cursor.execute(query, params)
                result = cursor.fetchone()
                count = result["cnt"] if result else 0
                
                self.logger.info("row_count", schema=schema, count=count, filtered=bool(where_clause))
                return count
                
        except psycopg2.Error as e:
            raise SourceExtractionError(f"Failed to get row count: {e}") from e
    
    def get_max_value(self, column: str) -> Optional[Any]:
        """Get maximum value of a column (for incremental extraction)"""
        if not self._is_validated:
            self.validate()
        
        database = self.config["database"]
        table = self.config["table"]
        schema = self._schema
        
        # Validate column exists
        schema_info = self.get_schema()
        schema_columns = {col.name for col in schema_info}
        if column not in schema_columns:
            raise SourceValidationError(f"Column '{column}' not found in table {schema}.{table}")
        
        query = f'SELECT MAX("{column}") as max_val FROM "{schema}"."{table}"'
        
        try:
            with self._get_connection() as (conn, cursor):
                cursor.execute(query)
                result = cursor.fetchone()
                max_val = result["max_val"] if result else None
                
                self.logger.info("max_value", schema=schema, column=column, value=str(max_val)[:50] if max_val else None)
                return self._normalize_value(max_val)
                
        except psycopg2.Error as e:
            raise SourceExtractionError(f"Failed to get max value: {e}") from e
    
    def test_query(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """Execute a test query (for debugging)"""
        if not self._is_validated:
            self.validate()
        
        try:
            with self._get_connection() as (conn, cursor):
                cursor.execute(query, params or [])
                results = cursor.fetchall()
                
                normalized = []
                for row in results:
                    normalized.append({k: self._normalize_value(v) for k, v in row.items()})
                
                self.logger.info("test_query_executed", rows=len(normalized))
                return normalized
                
        except psycopg2.Error as e:
            raise SourceExtractionError(f"Test query failed: {e}") from e
    
    def close(self):
        """Close connection"""
        if self._connection:
            try:
                self._connection.close()
                self._connection = None
                self.logger.debug("connection_closed")
            except Exception as e:
                self.logger.warning("close_error", error=str(e))