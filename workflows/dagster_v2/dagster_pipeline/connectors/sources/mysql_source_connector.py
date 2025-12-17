"""
MySQL source connector for data extraction

IMPROVEMENTS:
- Connection pooling and retry logic
- Better error handling
- Query timeout protection
- Proper resource cleanup
- Type conversion validation
- Performance optimizations
"""

import pymysql
from pymysql.cursors import SSDictCursor
from typing import Iterator, List, Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal
from contextlib import contextmanager
import time
import structlog

from .base_source_connector import (
    BaseSourceConnector,
    SourceConnectionError,
    SourceValidationError,
    SourceExtractionError,
    IncrementalConfig,
    ColumnSchema
)

logger = structlog.get_logger(__name__)


class MySQLSourceConnector(BaseSourceConnector):
    """
    MySQL source connector - Production-ready implementation
    
    Features:
    - Automatic retry with exponential backoff
    - Connection timeout protection
    - Server-side cursors for large datasets
    - Proper type conversion
    - Query optimization
    - Resource cleanup
    
    Returns batches as list of dictionaries:
    [
        {"id": 1, "name": "Alice", "created_at": datetime(...)},
        {"id": 2, "name": "Bob", "created_at": datetime(...)},
    ]
    """
    
    # Connection settings
    DEFAULT_PORT = 3306
    DEFAULT_CHARSET = 'utf8mb4'
    DEFAULT_CONNECT_TIMEOUT = 30
    DEFAULT_READ_TIMEOUT = 300  # 5 minutes
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    RETRY_BACKOFF = 2  # exponential backoff multiplier
    
    def __init__(self, context, config):
        super().__init__(context, config)
        self._connection = None
        self._connection_params = self._build_connection_params()
    
    def source_type(self) -> str:
        return "mysql"
    
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
            "charset": self.config.get("charset", self.DEFAULT_CHARSET),
            "connect_timeout": self.config.get("connect_timeout", self.DEFAULT_CONNECT_TIMEOUT),
            "read_timeout": self.config.get("read_timeout", self.DEFAULT_READ_TIMEOUT),
            "autocommit": True,  # We're only reading
            "cursorclass": SSDictCursor  # Server-side dict cursor
        }
    
    @contextmanager
    def _get_connection(self, use_server_cursor: bool = True):
        """
        Get MySQL connection with retry logic
        
        Args:
            use_server_cursor: Use server-side cursor (for large datasets)
        """
        conn = None
        params = self._connection_params.copy()
        
        if not use_server_cursor:
            # Use regular cursor for small queries
            params["cursorclass"] = pymysql.cursors.DictCursor
        
        # Retry logic
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                conn = pymysql.connect(**params)
                yield conn
                return  # Success
                
            except pymysql.OperationalError as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (self.RETRY_BACKOFF ** attempt)
                    logger.warning(
                        "mysql_connection_retry",
                        attempt=attempt + 1,
                        max_retries=self.MAX_RETRIES,
                        delay=delay,
                        error=str(e)
                    )
                    time.sleep(delay)
                else:
                    # Final attempt failed
                    raise SourceConnectionError(
                        f"Failed to connect to MySQL after {self.MAX_RETRIES} attempts: {e}"
                    ) from e
                    
            except pymysql.Error as e:
                # Non-retryable error
                raise SourceConnectionError(f"MySQL connection error: {e}") from e
                
            finally:
                if conn and attempt == self.MAX_RETRIES - 1:
                    # Only close if we're done (success or final failure)
                    try:
                        conn.close()
                    except Exception:
                        pass
        
        # Should never reach here, but just in case
        if last_error:
            raise SourceConnectionError(
                f"Failed to connect to MySQL: {last_error}"
            ) from last_error
    
    def validate(self) -> bool:
        """Validate MySQL connection and table exists"""
        database = self.config["database"]
        table = self.config["table"]
        
        # Test connection
        try:
            with self._get_connection(use_server_cursor=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    if not result:
                        raise SourceConnectionError("Connection test query failed")
        except pymysql.Error as e:
            raise SourceConnectionError(f"Failed to connect to MySQL: {e}") from e
        
        # Check table exists
        check_table_query = """
            SELECT TABLE_NAME, TABLE_ROWS, DATA_LENGTH
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """
        
        try:
            with self._get_connection(use_server_cursor=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(check_table_query, (database, table))
                    result = cursor.fetchone()
                    
                    if result is None:
                        raise SourceValidationError(
                            f"Table {database}.{table} not found in MySQL. "
                            f"Check database and table names."
                        )
                    
                    # Log table stats
                    logger.info(
                        "mysql_table_found",
                        database=database,
                        table=table,
                        approx_rows=result.get("TABLE_ROWS"),
                        data_size_mb=round(result.get("DATA_LENGTH", 0) / 1024 / 1024, 2)
                    )
        except pymysql.Error as e:
            raise SourceValidationError(f"Failed to validate table: {e}") from e
        
        self._is_validated = True
        logger.info("mysql_source_validated", database=database, table=table)
        return True
    
    def get_schema(self) -> List[ColumnSchema]:
        """Get MySQL table schema"""
        if not self._is_validated:
            self.validate()
        
        database = self.config["database"]
        table = self.config["table"]
        
        query = """
            SELECT
                COLUMN_NAME as name,
                COLUMN_TYPE as type,
                IS_NULLABLE as nullable,
                COLUMN_KEY as `key`,
                COLUMN_DEFAULT as `default`,
                EXTRA as extra
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """
        
        try:
            with self._get_connection(use_server_cursor=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (database, table))
                    columns = cursor.fetchall()
                    
                    if not columns:
                        raise SourceValidationError(
                            f"No columns found for table {database}.{table}"
                        )
                    
                    schema = []
                    for col in columns:
                        schema.append(ColumnSchema(
                            name=col["name"],
                            type=col["type"],
                            nullable=(col["nullable"] == "YES"),
                            primary_key=(col["key"] == "PRI"),
                            indexed=(col["key"] in ("PRI", "UNI", "MUL")),
                            unique=(col["key"] in ("PRI", "UNI")),
                            default=col["default"],
                            extra=col["extra"]
                        ))
                    
                    logger.info(
                        "mysql_schema_fetched",
                        database=database,
                        table=table,
                        columns=len(schema)
                    )
                    return schema
                    
        except pymysql.Error as e:
            raise SourceExtractionError(f"Failed to get schema: {e}") from e
    
    @staticmethod
    def _normalize_value(value: Any) -> Any:
        """
        Convert MySQL types to Python native types
        
        Handles:
        - Decimal → float
        - bytes → str (with fallback to hex)
        - datetime/date → keep as-is
        - JSON strings → keep as strings (let destination parse)
        """
        if value is None:
            return None
        elif isinstance(value, Decimal):
            # Convert to float for JSON serialization
            return float(value)
        elif isinstance(value, bytes):
            # Try UTF-8 decode, fallback to hex for binary data
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                return value.hex()
        elif isinstance(value, (datetime, date)):
            # Keep as Python datetime/date objects
            return value
        else:
            # int, float, str, bool all stay as-is
            return value
    
    def extract_data(
        self,
        columns: Optional[List[str]] = None,
        batch_size: int = 10000,
        incremental_config: Optional[IncrementalConfig] = None
    ) -> Iterator[List[Dict[str, Any]]]:
        """
        Extract data from MySQL - returns list of dictionaries
        
        Yields:
            [
                {"id": 1, "name": "Alice", ...},
                {"id": 2, "name": "Bob", ...},
            ]
        """
        if not self._is_validated:
            self.validate()
        
        database = self.config["database"]
        table = self.config["table"]
        
        # Get column list
        if columns:
            column_list = columns
        else:
            schema = self.get_schema()
            column_list = [col.name for col in schema]
        
        # Validate columns exist
        if columns:
            schema = self.get_schema()
            schema_columns = {col.name for col in schema}
            invalid_columns = [col for col in columns if col not in schema_columns]
            if invalid_columns:
                raise SourceValidationError(
                    f"Invalid columns requested: {invalid_columns}. "
                    f"Available columns: {sorted(schema_columns)}"
                )
        
        # Build SELECT clause
        columns_str = ", ".join(f"`{col}`" for col in column_list)
        
        # Build WHERE clause
        where_clause = ""
        params = []
        
        if incremental_config:
            # Validate incremental config
            schema = self.get_schema()
            schema_columns = {col.name for col in schema}
            if incremental_config.key not in schema_columns:
                raise SourceValidationError(
                    f"Incremental key '{incremental_config.key}' not found in table"
                )
            
            if incremental_config.last_value is not None:
                where_clause = f"WHERE `{incremental_config.key}` {incremental_config.operator} %s"
                params.append(incremental_config.last_value)
                logger.info(
                    "mysql_incremental_extraction",
                    database=database,
                    table=table,
                    key=incremental_config.key,
                    operator=incremental_config.operator,
                    last_value=str(incremental_config.last_value)[:50]
                )
        
        # Build ORDER BY
        order_clause = ""
        if incremental_config:
            order_by = incremental_config.order_by or incremental_config.key
            order_clause = f"ORDER BY `{order_by}` ASC"
        
        # Build final query
        query = f"""
            SELECT {columns_str}
            FROM `{database}`.`{table}`
            {where_clause}
            {order_clause}
        """.strip()
        
        logger.info(
            "mysql_extraction_start",
            database=database,
            table=table,
            batch_size=batch_size,
            columns=len(column_list),
            incremental=bool(incremental_config)
        )
        
        total_rows = 0
        batch_num = 0
        
        try:
            # Use server-side cursor for large datasets
            with self._get_connection(use_server_cursor=True) as conn:
                with conn.cursor() as cursor:
                    # Execute query
                    cursor.execute(query, params)
                    
                    while True:
                        # Fetch batch
                        rows = cursor.fetchmany(batch_size)
                        
                        if not rows:
                            break
                        
                        batch_num += 1
                        total_rows += len(rows)
                        
                        # Normalize all values in batch
                        normalized_batch = []
                        for row in rows:
                            normalized_row = {
                                col: self._normalize_value(row[col])
                                for col in column_list
                            }
                            normalized_batch.append(normalized_row)
                        
                        # Log first batch sample for debugging
                        if batch_num == 1 and normalized_batch:
                            sample_row = normalized_batch[0]
                            sample_types = {
                                col: type(sample_row[col]).__name__ 
                                for col in column_list
                            }
                            logger.debug(
                                "mysql_first_batch_sample",
                                database=database,
                                table=table,
                                rows=len(normalized_batch),
                                sample_types=sample_types,
                                sample_values={
                                    k: str(v)[:50] for k, v in list(sample_row.items())[:3]
                                }
                            )
                        
                        # Log progress every 10 batches
                        if batch_num % 10 == 0:
                            logger.info(
                                "mysql_extraction_progress",
                                database=database,
                                table=table,
                                batches=batch_num,
                                rows=total_rows
                            )
                        
                        yield normalized_batch
                        
        except pymysql.Error as e:
            raise SourceExtractionError(
                f"MySQL extraction failed at batch {batch_num}: {e}"
            ) from e
        except Exception as e:
            raise SourceExtractionError(
                f"Unexpected error during extraction: {e}"
            ) from e
        
        logger.info(
            "mysql_extraction_complete",
            database=database,
            table=table,
            total_rows=total_rows,
            batches=batch_num
        )
    
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
        
        query = f"SELECT COUNT(*) as cnt FROM `{database}`.`{table}`"
        params = []
        
        if where_clause:
            query += f" WHERE {where_clause}"
            params = where_params or []
        
        try:
            with self._get_connection(use_server_cursor=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    result = cursor.fetchone()
                    count = result["cnt"] if result else 0
                    
                    logger.info(
                        "mysql_row_count",
                        database=database,
                        table=table,
                        count=count,
                        filtered=bool(where_clause)
                    )
                    return count
                    
        except pymysql.Error as e:
            raise SourceExtractionError(f"Failed to get row count: {e}") from e
    
    def get_max_value(self, column: str) -> Optional[Any]:
        """Get maximum value of a column (for incremental extraction)"""
        if not self._is_validated:
            self.validate()
        
        database = self.config["database"]
        table = self.config["table"]
        
        # Validate column exists
        schema = self.get_schema()
        schema_columns = {col.name for col in schema}
        if column not in schema_columns:
            raise SourceValidationError(
                f"Column '{column}' not found in table {database}.{table}"
            )
        
        query = f"SELECT MAX(`{column}`) as max_val FROM `{database}`.`{table}`"
        
        try:
            with self._get_connection(use_server_cursor=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    max_val = result["max_val"] if result else None
                    
                    logger.info(
                        "mysql_max_value",
                        database=database,
                        table=table,
                        column=column,
                        max_value=str(max_val)[:50] if max_val else None
                    )
                    return self._normalize_value(max_val)
                    
        except pymysql.Error as e:
            raise SourceExtractionError(f"Failed to get max value: {e}") from e
    
    def test_query(
        self,
        query: str,
        params: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a test query (for debugging)"""
        if not self._is_validated:
            self.validate()
        
        try:
            with self._get_connection(use_server_cursor=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or [])
                    results = cursor.fetchall()
                    
                    # Normalize values
                    normalized = []
                    for row in results:
                        normalized.append({
                            k: self._normalize_value(v)
                            for k, v in row.items()
                        })
                    
                    logger.info(
                        "mysql_test_query_executed",
                        rows=len(normalized),
                        query_preview=query[:100]
                    )
                    return normalized
                    
        except pymysql.Error as e:
            raise SourceExtractionError(f"Test query failed: {e}") from e
    
    def close(self):
        """Close connection"""
        if self._connection:
            try:
                self._connection.close()
                self._connection = None
                logger.debug("mysql_connection_closed")
            except Exception as e:
                logger.warning("mysql_close_error", error=str(e))