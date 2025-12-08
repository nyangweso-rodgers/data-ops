# dagster_pipeline/connectors/sources/mysql_source.py
"""
MySQL source connector for data extraction

Pure Python implementation - NO PANDAS, NO NUMPY!
Just native Python dictionaries and lists.
"""

import pymysql
from typing import Iterator, List, Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal
from contextlib import contextmanager
from .base_source_connector import BaseSourceConnector
import structlog

logger = structlog.get_logger(__name__)


class MySQLSourceConnector(BaseSourceConnector):
    """
    MySQL source connector - Pure Python (no pandas!)
    
    Returns batches as list of dictionaries:
    [
        {"id": 1, "name": "Alice", "created_at": datetime(...)},
        {"id": 2, "name": "Bob", "created_at": datetime(...)},
        ...
    ]
    """
    
    def source_type(self) -> str:
        return "mysql"
    
    @contextmanager
    def _get_connection(self, use_server_cursor: bool = False):
        """Get MySQL connection"""
        cursor_class = pymysql.cursors.SSDictCursor
        
        conn = None
        try:
            conn = pymysql.connect(
                host=self.config["host"],
                port=self.config.get("port", 3306),
                user=self.config["user"],
                password=self.config["password"],
                database=self.config["database"],
                charset='utf8mb4',
                cursorclass=cursor_class
            )
            yield conn
        finally:
            if conn:
                conn.close()
    
    def validate(self) -> bool:
        """Validate MySQL connection and table exists"""
        database = self.config["database"]
        table = self.config["table"]
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
        except pymysql.Error as e:
            logger.error("mysql_connection_failed", database="****", error=str(e))
            raise ConnectionError(f"Failed to connect to MySQL: {e}")
        
        check_table_query = """
            SELECT TABLE_NAME
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(check_table_query, (database, table))
                if cursor.fetchone() is None:
                    raise ValueError(f"Table {database}.{table} not found in MySQL")
        
        logger.info("mysql_source_validated", database="****", table=table)
        return True
    
    def get_schema(self) -> List[Dict[str, Any]]:
        """Get MySQL table schema"""
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
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (database, table))
                columns = cursor.fetchall()
                
                schema = []
                for col in columns:
                    schema.append({
                        "name": col["name"],
                        "type": col["type"],
                        "nullable": (col["nullable"] == "YES"),
                        "primary_key": (col["key"] == "PRI"),
                        "default": col["default"],
                        "extra": col["extra"]
                    })
                
                logger.info("mysql_schema_fetched", database="****", table=table, columns=len(schema))
                return schema
    
    @staticmethod
    def _normalize_value(value: Any) -> Any:
        """
        Convert MySQL types to Python native types
        
        PyMySQL already returns native Python types, but we ensure consistency:
        - Decimal → float (for JSON serialization)
        - bytes → str (for varbinary columns)
        - Everything else stays as-is
        """
        if value is None:
            return None
        elif isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, bytes):
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                return value.hex()  # Return hex string for binary data
        elif isinstance(value, (datetime, date)):
            return value  # Keep as Python datetime/date
        else:
            return value  # int, float, str, bool all stay as-is
    
    def extract_data(
        self,
        columns: Optional[List[str]] = None,
        batch_size: int = 10000,
        incremental_config: Optional[Dict[str, Any]] = None
    ) -> Iterator[List[Dict[str, Any]]]:
        """
        Extract data from MySQL - returns list of dictionaries
        
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
        
        # Build SELECT clause
        if columns:
            columns_str = ", ".join(f"`{col}`" for col in columns)
            column_list = columns
        else:
            schema = self.get_schema()
            column_list = [col["name"] for col in schema]
            columns_str = ", ".join(f"`{col}`" for col in column_list)
        
        # Build WHERE clause
        where_clause = ""
        params = []
        
        if incremental_config:
            key = incremental_config["key"]
            last_value = incremental_config.get("last_value")
            operator = incremental_config.get("operator", ">")
            
            if last_value is not None:
                where_clause = f"WHERE `{key}` {operator} %s"
                params.append(last_value)
                logger.info("mysql_incremental_extraction", database="****", table=table, key=key)
        
        # Build ORDER BY
        order_clause = ""
        if incremental_config:
            order_clause = f"ORDER BY `{incremental_config['key']}` ASC"
        
        # Build query
        query = f"""
            SELECT {columns_str}
            FROM `{database}`.`{table}`
            {where_clause}
            {order_clause}
        """
        
        logger.info("mysql_extraction_start", database="****", table=table, batch_size=batch_size)
        
        total_rows = 0
        batch_num = 0
        
        # Use server-side cursor
        with self._get_connection(use_server_cursor=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                
                while True:
                    # Fetch batch - PyMySQL with DictCursor returns list of dicts
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
                    
                    # Log sample for debugging
                    if batch_num == 1 and normalized_batch:
                        sample_types = {
                            col: type(normalized_batch[0][col]).__name__ 
                            for col in column_list
                        }
                        logger.debug("mysql_batch_extracted", 
                                   database="****", 
                                   table=table,
                                   batch=batch_num,
                                   rows=len(normalized_batch),
                                   sample_types=sample_types)
                    
                    yield normalized_batch
        
        logger.info("mysql_extraction_complete", database="****", table=table, 
                   total_rows=total_rows, batches=batch_num)
    
    def get_row_count(self, where_clause: Optional[str] = None) -> int:
        """Get row count"""
        database = self.config["database"]
        table = self.config["table"]
        
        query = f"SELECT COUNT(*) as cnt FROM `{database}`.`{table}`"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                count = result["cnt"] if result else 0
                logger.info("mysql_row_count", database="****", table=table, count=count)
                return count