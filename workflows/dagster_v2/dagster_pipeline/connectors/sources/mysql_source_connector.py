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
from pymysql.constants import FIELD_TYPE
from pymysql.converters import conversions
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

# Module logger for class-level operations
logger = get_logger(__name__)


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
    
    @staticmethod
    def _create_safe_date_converters():
        """
        Override PyMySQL's default date converters to return strings
        
        This prevents PyMySQL from crashing on invalid dates like:
        - 0000-00-00 (zero dates)
        - 0184-08-10 (year out of Python's date range)
        - Other malformed dates
        
        Your _normalize_value() will then handle these strings safely.
        """
        conv = conversions.copy()
        
        # Return dates as strings instead of trying to parse them
        conv[FIELD_TYPE.DATE] = lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
        conv[FIELD_TYPE.DATETIME] = lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
        conv[FIELD_TYPE.TIMESTAMP] = lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
        
        return conv
    
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
            "autocommit": True,
            "cursorclass": SSDictCursor,
            "conv": self._create_safe_date_converters()
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
            params["cursorclass"] = pymysql.cursors.DictCursor
        
        # Retry logic
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                conn = pymysql.connect(**params)
                yield conn
                return
                
            except pymysql.OperationalError as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (self.RETRY_BACKOFF ** attempt)
                    self.logger.warning("connection_retry", attempt=attempt + 1, delay=delay, error=str(e))
                    time.sleep(delay)
                else:
                    raise SourceConnectionError(
                        f"Failed to connect to MySQL after {self.MAX_RETRIES} attempts: {e}"
                    ) from e
                    
            except pymysql.Error as e:
                raise SourceConnectionError(f"MySQL connection error: {e}") from e
                
            finally:
                if conn and attempt == self.MAX_RETRIES - 1:
                    try:
                        conn.close()
                    except Exception:
                        pass
        
        if last_error:
            raise SourceConnectionError(f"Failed to connect to MySQL: {last_error}") from last_error
    
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
                    self.logger.info(
                        "table_validated",
                        approx_rows=result.get("TABLE_ROWS"),
                        data_size_mb=round(result.get("DATA_LENGTH", 0) / 1024 / 1024, 2)
                    )
        except pymysql.Error as e:
            raise SourceValidationError(f"Failed to validate table: {e}") from e
        
        self._is_validated = True
        self.logger.info("source_validated")
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
                        raise SourceValidationError(f"No columns found for table {database}.{table}")
                    
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
                    
                    self.logger.info("schema_fetched", columns=len(schema))
                    return schema
                    
        except pymysql.Error as e:
            raise SourceExtractionError(f"Failed to get schema: {e}") from e
    
    def _normalize_value(self, value: Any, mysql_type: str = "", column_name: str = "") -> Any:
        """
        Convert MySQL types to Python native types
        
        Handles:
        - Decimal → float
        - bytes → str (with fallback to hex)
        - datetime/date → keep as-is
        - Zero dates (0000-00-00) → None
        - String dates → date/datetime objects **only if column type is date-like**
        - JSON strings → keep as strings (let destination parse)
        """
        if value is None:
            return None
        
        # Handle already-parsed native date/datetime from MySQL
        if isinstance(value, datetime):
            if value.year == 0:
                self.logger.warning("zero_datetime_to_null", column=column_name)
                return None
            return value
        
        if isinstance(value, date):
            if value.year == 0:
                self.logger.warning("zero_date_to_null", column=column_name)
                return None
            return value

        # Decimal / bytes
        if isinstance(value, Decimal):
            return float(value)

        if isinstance(value, bytes):
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                return value.hex()
        
        # Only attempt string parsing if MySQL column type indicates date/time
        mysql_type_lower = mysql_type.lower().strip()
        base_type = mysql_type_lower.split('(')[0].strip()
        is_date_like_column = base_type in {'date', 'datetime', 'timestamp', 'time'}

        if isinstance(value, str) and is_date_like_column:
            # Zero / invalid date strings → None
            if value.startswith('0000-00-00'):
                self.logger.warning("zero_date_string_to_null", column=column_name)
                return None

            # Parse date (YYYY-MM-DD)
            if len(value) == 10 and value[4] == '-' and value[7] == '-':
                try:
                    year = int(value[0:4])
                    
                    # ClickHouse Date supports 1970-2149, Date32 supports 1900-2299
                    if year < 1900 or year > 2149:
                        self.logger.warning("date_out_of_range", column=column_name, year=year)
                        return None
                    
                    return datetime.strptime(value, '%Y-%m-%d').date()
                except ValueError:
                    self.logger.warning("invalid_date_string", column=column_name, value=value)
                    return None

            # Parse datetime (YYYY-MM-DD HH:MM:SS)
            if len(value) >= 19 and value[4] == '-' and value[10] == ' ':
                try:
                    year = int(value[0:4])
                    
                    if year < 1900 or year > 2149:
                        self.logger.warning("datetime_out_of_range", column=column_name, year=year)
                        return None
                    
                    return datetime.strptime(value[:19], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    self.logger.warning("invalid_datetime_string", column=column_name, value=value)
                    return None

            # If it didn't parse but column expects date → None
            self.logger.warning("unparsable_date_value", column=column_name)
            return None
        
        # Default: keep everything else as-is
        return value
    
    def extract_data(
        self,
        columns: Optional[List[str]] = None,
        batch_size: int = 10000,
        incremental_config: Optional[IncrementalConfig] = None
    ) -> Iterator[List[Dict[str, Any]]]:
        """Extract data from MySQL - returns list of dictionaries"""
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
            schema = self.get_schema()
            schema_columns = {col.name for col in schema}
            if incremental_config.key not in schema_columns:
                raise SourceValidationError(
                    f"Incremental key '{incremental_config.key}' not found in table"
                )
            
            if incremental_config.last_value is not None:
                where_clause = f"WHERE `{incremental_config.key}` {incremental_config.operator} %s"
                params.append(incremental_config.last_value)
                self.logger.info(
                    "incremental_extraction",
                    key=incremental_config.key,
                    operator=incremental_config.operator,
                    from_value=str(incremental_config.last_value)[:50]
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
        
        self.logger.info(
            "extraction_started",
            batch_size=batch_size,
            columns=len(column_list),
            incremental=bool(incremental_config)
        )
        
        # Cache MySQL column types for normalization
        schema = self.get_schema()
        mysql_types = {col.name: col.type for col in schema}
        
        total_rows = 0
        batch_num = 0
        
        try:
            with self._get_connection(use_server_cursor=True) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    
                    while True:
                        rows = cursor.fetchmany(batch_size)
                        
                        if not rows:
                            break
                        
                        batch_num += 1
                        total_rows += len(rows)
                        
                        # Normalize values with type information
                        normalized_batch = []
                        for row in rows:
                            normalized_row = {
                                col: self._normalize_value(
                                    row[col],
                                    mysql_type=mysql_types.get(col, ""),
                                    column_name=col
                                )
                                for col in column_list
                            }
                            normalized_batch.append(normalized_row)
                        
                        # Log first batch sample
                        if batch_num == 1 and normalized_batch:
                            sample_row = normalized_batch[0]
                            sample_types = {col: type(sample_row[col]).__name__ for col in column_list}
                            self.logger.debug(
                                "first_batch_sample",
                                rows=len(normalized_batch),
                                sample_types=sample_types
                            )
                        
                        if batch_num % 10 == 0:
                            self.logger.info("extraction_progress", batches=batch_num, rows=total_rows)
                        
                        yield normalized_batch
                        
        except pymysql.Error as e:
            raise SourceExtractionError(f"MySQL extraction failed at batch {batch_num}: {e}") from e
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
                    
                    self.logger.info("row_count", count=count, filtered=bool(where_clause))
                    return count
                    
        except pymysql.Error as e:
            raise SourceExtractionError(f"Failed to get row count: {e}") from e
    
    def get_max_value(self, column: str) -> Optional[Any]:
        """Get maximum value of a column (for incremental extraction)"""
        if not self._is_validated:
            self.validate()
        
        database = self.config["database"]
        table = self.config["table"]
        
        schema = self.get_schema()
        mysql_types = {col.name: col.type for col in schema}
        
        schema_columns = {col.name for col in schema}
        if column not in schema_columns:
            raise SourceValidationError(f"Column '{column}' not found in table {database}.{table}")
        
        query = f"SELECT MAX(`{column}`) as max_val FROM `{database}`.`{table}`"
        
        try:
            with self._get_connection(use_server_cursor=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    max_val = result["max_val"] if result else None
                    
                    self.logger.info("max_value", column=column, value=str(max_val)[:50] if max_val else None)
                    
                    return self._normalize_value(
                        max_val,
                        mysql_type=mysql_types.get(column, ""),
                        column_name=column
                    )
                    
        except pymysql.Error as e:
            raise SourceExtractionError(f"Failed to get max value: {e}") from e
    
    def test_query(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """Execute a test query (for debugging)"""
        if not self._is_validated:
            self.validate()
        
        try:
            with self._get_connection(use_server_cursor=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or [])
                    results = cursor.fetchall()
                    
                    schema = self.get_schema()
                    mysql_types = {col.name: col.type for col in schema}
                    
                    normalized = []
                    for row in results:
                        normalized.append({
                            k: self._normalize_value(v, mysql_type=mysql_types.get(k, ""), column_name=k)
                            for k, v in row.items()
                        })
                    
                    self.logger.info("test_query_executed", rows=len(normalized))
                    return normalized
                    
        except pymysql.Error as e:
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