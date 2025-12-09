"""
PostgreSQL source connector for data extraction

Pure Python implementation - NO PANDAS, NO NUMPY!
Just native Python dictionaries and lists.
"""

import psycopg2
import psycopg2.extras
from typing import Iterator, List, Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal
from contextlib import contextmanager
from .base_source_connector import BaseSourceConnector
import structlog

logger = structlog.get_logger(__name__)


class PostgresSourceConnector(BaseSourceConnector):
    """
    PostgreSQL source connector - Pure Python (no pandas!)
    
    Returns batches as list of dictionaries:
    [
        {"id": 1, "name": "Alice", "created_at": datetime(...)},
        {"id": 2, "name": "Bob", "created_at": datetime(...)},
        ...
    ]
    
    Key differences from MySQL:
    - Uses psycopg2 instead of pymysql
    - PostgreSQL columns are typically lowercase (updated_at vs updatedAt)
    - Named cursors for server-side iteration
    - Different data type handling
    - NULL arrays converted to [] for ClickHouse compatibility
    """
    
    def source_type(self) -> str:
        return "postgres"
    
    @contextmanager
    def _get_connection(self, use_server_cursor: bool = False, cursor_name: Optional[str] = None):
        """
        Get PostgreSQL connection
        
        Args:
            use_server_cursor: Use server-side cursor for streaming
            cursor_name: Name for server-side cursor (required if use_server_cursor=True)
        """
        conn = None
        cursor = None
        
        try:
            # Create connection
            conn = psycopg2.connect(
                host=self.config["host"],
                port=self.config.get("port", 5432),
                user=self.config["user"],
                password=self.config["password"],
                database=self.config["database"],
                # Use dict cursor for returning rows as dictionaries
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            
            # CRITICAL FIX: Named cursors require transactions
            # Only use autocommit for non-streaming operations
            if use_server_cursor and cursor_name:
                # Named cursor - DO NOT use autocommit (needs transaction)
                conn.autocommit = False
                cursor = conn.cursor(name=cursor_name)
                # Set fetch size for streaming
                cursor.itersize = self.config.get("batch_size", 10000)
            else:
                # Regular cursor - can use autocommit for single queries
                conn.autocommit = True
                cursor = conn.cursor()
            
            yield conn, cursor
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                # Commit any pending transaction before closing
                if not conn.autocommit:
                    try:
                        conn.commit()
                    except Exception as e:
                        logger.warning("postgres_commit_warning", error=str(e))
                conn.close()
    
    def validate(self) -> bool:
        """Validate PostgreSQL connection and table exists"""
        database = self.config["database"]
        table = self.config["table"]
        schema = self.config.get("schema", "public")  # Default to public schema
        
        # Test connection
        try:
            with self._get_connection() as (conn, cursor):
                cursor.execute("SELECT 1")
        except psycopg2.Error as e:
            logger.error("postgres_connection_failed", database="****", error=str(e))
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")
        
        # Check if table exists
        check_table_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
        """
        
        with self._get_connection() as (conn, cursor):
            cursor.execute(check_table_query, (schema, table))
            if cursor.fetchone() is None:
                raise ValueError(f"Table {schema}.{table} not found in PostgreSQL database {database}")
        
        logger.info("postgres_source_validated", database="****", schema=schema, table=table)
        return True
    
    def get_schema(self) -> List[Dict[str, Any]]:
        """Get PostgreSQL table schema"""
        database = self.config["database"]
        table = self.config["table"]
        schema = self.config.get("schema", "public")
        
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
                END as is_primary_key
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
            WHERE c.table_schema = %s 
                AND c.table_name = %s
            ORDER BY c.ordinal_position
        """
        
        with self._get_connection() as (conn, cursor):
            cursor.execute(query, (schema, table, schema, table))
            columns = cursor.fetchall()
            
            schema_list = []
            for col in columns:
                schema_list.append({
                    "name": col["name"],
                    "type": col["type"],
                    "udt_type": col["udt_type"],  # PostgreSQL user-defined type
                    "nullable": (col["nullable"] == "YES"),
                    "primary_key": col["is_primary_key"],
                    "default": col["default_value"]
                })
            
            logger.info("postgres_schema_fetched", database="****", schema=schema, 
                       table=table, columns=len(schema_list))
            return schema_list
    
    @staticmethod
    def _normalize_value(value: Any, column_type: Optional[str] = None) -> Any:
        """
        Convert PostgreSQL types to Python native types
        
        CRITICAL: ClickHouse arrays cannot be NULL!
        - PostgreSQL NULL arrays → empty list []
        - All other NULL values → None
        
        Args:
            value: The value to normalize
            column_type: PostgreSQL column type (e.g., '_int4', 'integer[]', 'text')
        
        psycopg2 already returns native Python types, but we ensure consistency:
        - Decimal → float (for JSON serialization)
        - memoryview/bytes → str (for bytea columns)
        - PostgreSQL arrays → Python lists
        - NULL arrays → [] (for ClickHouse compatibility)
        - Everything else stays as-is
        """
        if value is None:
            # CRITICAL: ClickHouse arrays cannot be NULL
            # Check if this column is an array type
            if column_type and (column_type.startswith('_') or column_type.endswith('[]')):
                return []  # Convert NULL array to empty array
            return None
        
        elif isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, memoryview):
            # PostgreSQL bytea columns return memoryview
            try:
                return bytes(value).decode('utf-8')
            except UnicodeDecodeError:
                return bytes(value).hex()
        elif isinstance(value, bytes):
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                return value.hex()
        elif isinstance(value, (datetime, date)):
            return value  # Keep as Python datetime/date
        elif isinstance(value, list):
            # PostgreSQL arrays - recursively normalize each element
            # Don't pass column_type to recursive calls (elements aren't arrays)
            return [PostgresSourceConnector._normalize_value(item, column_type=None) for item in value]
        elif isinstance(value, dict):
            # PostgreSQL JSON/JSONB - already parsed by psycopg2
            return value
        else:
            return value  # int, float, str, bool all stay as-is
    
    def extract_data(
        self,
        columns: Optional[List[str]] = None,
        batch_size: int = 10000,
        incremental_config: Optional[Dict[str, Any]] = None
    ) -> Iterator[List[Dict[str, Any]]]:
        """
        Extract data from PostgreSQL - returns list of dictionaries
        
        Yields:
            [
                {"id": 1, "name": "Alice", ...},
                {"id": 2, "name": "Bob", ...},
                ...
            ]
        
        NO PANDAS! Just pure Python dicts.
        """
        database = self.config["database"]
        table = self.config["table"]
        schema = self.config.get("schema", "public")
        
        # Get schema info to determine column types (for array handling)
        schema_info = self.get_schema()
        column_types = {col["name"]: col.get("udt_type", col["type"]) for col in schema_info}
        
        # Build SELECT clause
        if columns:
            columns_str = ", ".join(f'"{col}"' for col in columns)
            column_list = columns
        else:
            column_list = [col["name"] for col in schema_info]
            columns_str = ", ".join(f'"{col}"' for col in column_list)
        
        # Build WHERE clause
        where_clause = ""
        params = []
        
        if incremental_config:
            key = incremental_config["key"]
            last_value = incremental_config.get("last_value")
            operator = incremental_config.get("operator", ">")
            
            if last_value is not None:
                where_clause = f'WHERE "{key}" {operator} %s'
                params.append(last_value)
                logger.info("postgres_incremental_extraction", database="****", 
                           schema=schema, table=table, key=key)
        
        # Build ORDER BY
        order_clause = ""
        if incremental_config:
            order_clause = f'ORDER BY "{incremental_config["key"]}" ASC'
        
        # Build query - PostgreSQL uses schema.table notation
        query = f"""
            SELECT {columns_str}
            FROM "{schema}"."{table}"
            {where_clause}
            {order_clause}
        """
        
        logger.info("postgres_extraction_start", database="****", schema=schema, 
                   table=table, batch_size=batch_size)
        
        total_rows = 0
        batch_num = 0
        
        # Use server-side cursor with unique name
        cursor_name = f"cursor_{schema}_{table}_{datetime.now().timestamp()}"
        
        with self._get_connection(use_server_cursor=True, cursor_name=cursor_name) as (conn, cursor):
            # Execute query
            cursor.execute(query, params)
            
            while True:
                # Fetch batch - psycopg2 with RealDictCursor returns list of dicts
                rows = cursor.fetchmany(batch_size)
                
                if not rows:
                    break
                
                batch_num += 1
                total_rows += len(rows)
                
                # Normalize all values in batch
                normalized_batch = []
                for row in rows:
                    normalized_row = {
                        col: self._normalize_value(row[col], column_type=column_types.get(col))
                        for col in column_list
                    }
                    normalized_batch.append(normalized_row)
                
                # Log sample for debugging
                if batch_num == 1 and normalized_batch:
                    sample_types = {
                        col: type(normalized_batch[0][col]).__name__ 
                        for col in column_list
                    }
                    logger.debug("postgres_batch_extracted", 
                               database="****", 
                               schema=schema,
                               table=table,
                               batch=batch_num,
                               rows=len(normalized_batch),
                               sample_types=sample_types)
                
                yield normalized_batch
        
        logger.info("postgres_extraction_complete", database="****", schema=schema,
                   table=table, total_rows=total_rows, batches=batch_num)
    
    def get_row_count(self, where_clause: Optional[str] = None) -> int:
        """Get row count"""
        database = self.config["database"]
        table = self.config["table"]
        schema = self.config.get("schema", "public")
        
        query = f'SELECT COUNT(*) as cnt FROM "{schema}"."{table}"'
        if where_clause:
            query += f" WHERE {where_clause}"
        
        with self._get_connection() as (conn, cursor):
            cursor.execute(query)
            result = cursor.fetchone()
            count = result["cnt"] if result else 0
            logger.info("postgres_row_count", database="****", schema=schema, 
                       table=table, count=count)
            return count