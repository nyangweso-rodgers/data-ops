"""
ClickHouse destination connector for data loading

IMPROVEMENTS:
- Retry logic with exponential backoff
- Better error handling
- Connection validation
- Query timeout protection
- Optimized batch inserts
- Proper resource cleanup
"""

import clickhouse_connect
from clickhouse_connect.driver.exceptions import ClickHouseError
from typing import Dict, Any, List, Optional
import time
import structlog

from .base_sink_connector import (
    BaseSinkConnector,
    DestinationConnectionError,
    DestinationValidationError,
    DestinationLoadError
)

logger = structlog.get_logger(__name__)


class ClickHouseSinkConnector(BaseSinkConnector):
    """
    ClickHouse destination connector - Production-ready implementation
    
    Features:
    - Native ClickHouse protocol via clickhouse-connect
    - Retry logic for transient failures
    - Connection pooling
    - Batch inserts with optimization
    - Schema evolution support
    - Native Python type handling
    
    Config:
        {
            "host": "clickhouse.example.com",
            "port": 8443,  # HTTPS port (9440 for native secure)
            "user": "default",
            "password": "password",
            "database": "analytics",
            "secure": True,  # Use HTTPS/TLS
            "verify": True,  # Verify SSL certificate
            "connect_timeout": 30,  # Seconds
            "send_receive_timeout": 300,  # Seconds
            "settings": {
                "max_insert_block_size": 100000,
                "max_execution_time": 300
            }
        }
    """
    
    # Connection settings
    DEFAULT_PORT = 8443  # HTTPS
    DEFAULT_PORT_INSECURE = 8123  # HTTP
    DEFAULT_CONNECT_TIMEOUT = 30
    DEFAULT_SEND_RECEIVE_TIMEOUT = 300
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    RETRY_BACKOFF = 2
    
    def __init__(self, context, config: Dict[str, Any]):
        """Initialize ClickHouse destination connector"""
        super().__init__(context, config)
        
        # Extract connection parameters
        self.host = config["host"]
        self.secure = config.get("secure", True)
        self.port = config.get("port", self.DEFAULT_PORT if self.secure else self.DEFAULT_PORT_INSECURE)
        self.user = config.get("user", "default")
        self.password = config.get("password", "")
        self.database = config.get("database", "default")
        self.verify = config.get("verify", True)
        self.connect_timeout = config.get("connect_timeout", self.DEFAULT_CONNECT_TIMEOUT)
        self.send_receive_timeout = config.get("send_receive_timeout", self.DEFAULT_SEND_RECEIVE_TIMEOUT)
        self.settings = config.get("settings", {})
        
        # Connection client (lazy initialization)
        self._client = None
    
    def destination_type(self) -> str:
        return "clickhouse"
    
    def required_config_keys(self) -> List[str]:
        return ["host"]  # Password optional for localhost
    
    def _get_client(self):
        """
        Get or create ClickHouse client with retry logic
        
        Uses lazy initialization - client created on first use
        """
        if self._client is None:
            last_error = None
            
            for attempt in range(self.MAX_RETRIES):
                try:
                    self._client = clickhouse_connect.get_client(
                        host=self.host,
                        port=self.port,
                        username=self.user,
                        password=self.password,
                        database=self.database,
                        secure=self.secure,
                        verify=self.verify,
                        connect_timeout=self.connect_timeout,
                        send_receive_timeout=self.send_receive_timeout,
                        settings=self.settings
                    )
                    
                    logger.debug(
                        "clickhouse_client_created",
                        database=self.database,
                        host="****",  # Sanitized
                        port=self.port
                    )
                    return self._client
                    
                except Exception as e:
                    last_error = e
                    if attempt < self.MAX_RETRIES - 1:
                        delay = self.RETRY_DELAY * (self.RETRY_BACKOFF ** attempt)
                        logger.warning(
                            "clickhouse_connection_retry",
                            attempt=attempt + 1,
                            max_retries=self.MAX_RETRIES,
                            delay=delay,
                            error=str(e)
                        )
                        time.sleep(delay)
                    else:
                        raise DestinationConnectionError(
                            f"Failed to connect to ClickHouse after {self.MAX_RETRIES} attempts: {e}"
                        ) from e
            
            if last_error:
                raise DestinationConnectionError(
                    f"Failed to connect to ClickHouse: {last_error}"
                ) from last_error
        
        return self._client
    
    def validate(self) -> bool:
        """Validate ClickHouse connection and permissions"""
        try:
            client = self._get_client()
            
            # Test connection
            result = client.query("SELECT version() as version")
            version = result.result_rows[0][0] if result.result_rows else "unknown"
            logger.debug("clickhouse_version", version=version)
            
            # Check database exists or can be created
            databases_query = "SHOW DATABASES"
            databases = client.query(databases_query)
            db_list = [row[0] for row in databases.result_rows]
            
            if self.database not in db_list:
                logger.warning(
                    "clickhouse_database_not_found",
                    database=self.database,
                    available=db_list
                )
                # Try to create database
                try:
                    client.command(f"CREATE DATABASE IF NOT EXISTS `{self.database}`")
                    logger.info("clickhouse_database_created", database=self.database)
                except Exception as e:
                    raise DestinationValidationError(
                        f"Database '{self.database}' doesn't exist and cannot be created: {e}"
                    ) from e
            
            # Test write permissions
            try:
                client.command(f"USE `{self.database}`")
            except Exception as e:
                raise DestinationValidationError(
                    f"Cannot access database '{self.database}': {e}"
                ) from e
            
            self._is_validated = True
            logger.info(
                "clickhouse_destination_validated",
                database=self.database,
                host="****"  # Sanitized
            )
            return True
            
        except DestinationValidationError:
            raise
        except Exception as e:
            raise DestinationConnectionError(
                f"ClickHouse validation failed: {e}"
            ) from e
    
    def table_exists(self, database: str, table: str) -> bool:
        """Check if table exists in ClickHouse"""
        if not self._is_validated:
            self.validate()
        
        client = self._get_client()
        
        query = """
            SELECT count() as cnt
            FROM system.tables
            WHERE database = %(database)s AND name = %(table)s
        """
        
        try:
            result = client.query(
                query,
                parameters={"database": database, "table": table}
            )
            
            exists = result.result_rows[0][0] > 0
            
            logger.debug(
                "clickhouse_table_exists_check",
                database=database,
                table=table,
                exists=exists
            )
            
            return exists
            
        except Exception as e:
            raise DestinationLoadError(
                f"Failed to check if table exists: {e}"
            ) from e
    
    def _ensure_sync_at_column(self, database: str, table: str) -> None:
        """Ensure sync_at column exists with proper default"""
        client = self._get_client()
        
        try:
            # Check if sync_at already exists
            result = client.query(
                "SELECT name, type, default_expression FROM system.columns "
                "WHERE database = %(db)s AND table = %(tbl)s AND name = 'sync_at'",
                parameters={"db": database, "tbl": table}
            )
            
            if result.result_rows:
                logger.debug("sync_at_column_exists", database=database, table=table)
                return
            
            # Add sync_at with high precision and default = now64()
            alter_query = f"""
                ALTER TABLE `{database}`.`{table}`
                ADD COLUMN IF NOT EXISTS `sync_at` DateTime64(3) DEFAULT now64(3)
            """
            
            client.command(alter_query)
            logger.info("sync_at_column_added", database=database, table=table)
            
        except Exception as e:
            # Non-fatal - log warning but don't fail
            logger.warning(
                "sync_at_add_failed",
                database=database,
                table=table,
                error=str(e)
            )
    
    def create_table(
        self,
        database: str,
        table: str,
        schema: List[Dict[str, Any]],
        **options
    ) -> None:
        """
        Create ClickHouse table
        
        Args:
            database: Database name
            table: Table name
            schema: List of column definitions with ClickHouse types
            **options: ClickHouse-specific options:
                - engine: Table engine (default: "MergeTree")
                - order_by: List of columns for ORDER BY
                - partition_by: Partition expression
                - primary_key: List of primary key columns
                - ttl: TTL expression
                - settings: Table settings
        """
        if not self._is_validated:
            self.validate()
        
        client = self._get_client()
        
        # Extract options
        engine = options.get("engine", "MergeTree")
        order_by = options.get("order_by", [])
        partition_by = options.get("partition_by")
        primary_key = options.get("primary_key", [])
        ttl = options.get("ttl")
        settings = options.get("settings", {})
        
        # Build column definitions
        column_defs = []
        for col in schema:
            col_name = col["name"]
            col_type = col.get("destination_type", col.get("type", "String"))
            column_defs.append(f"`{col_name}` {col_type}")
        
        columns_str = ",\n    ".join(column_defs)
        
        # Build clauses
        engine_clause = f"ENGINE = {engine}"
        
        # ORDER BY (required for MergeTree engines)
        if order_by:
            order_by_str = ", ".join(f"`{col}`" for col in order_by)
            order_by_clause = f"ORDER BY ({order_by_str})"
        elif schema:
            # Default: use first column
            order_by_clause = f"ORDER BY `{schema[0]['name']}`"
        else:
            raise DestinationValidationError(
                "ORDER BY is required for MergeTree engines but no columns provided"
            )
        
        # PARTITION BY
        partition_clause = f"PARTITION BY {partition_by}" if partition_by else ""
        
        # PRIMARY KEY
        primary_key_clause = ""
        if primary_key:
            pk_str = ", ".join(f"`{col}`" for col in primary_key)
            primary_key_clause = f"PRIMARY KEY ({pk_str})"
        
        # TTL
        ttl_clause = f"TTL {ttl}" if ttl else ""
        
        # SETTINGS
        settings_clause = ""
        if settings:
            settings_list = [f"{k} = {v}" for k, v in settings.items()]
            settings_clause = f"SETTINGS {', '.join(settings_list)}"
        
        # Build CREATE TABLE statement
        create_query = f"""
            CREATE TABLE IF NOT EXISTS `{database}`.`{table}` (
                {columns_str}
            )
            {engine_clause}
            {partition_clause}
            {order_by_clause}
            {primary_key_clause}
            {ttl_clause}
            {settings_clause}
        """
        
        try:
            client.command(create_query)
            
            # Add sync_at column automatically
            self._ensure_sync_at_column(database, table)
            
            logger.info(
                "clickhouse_table_created",
                database=database,
                table=table,
                engine=engine,
                columns=len(schema)
            )
            
        except Exception as e:
            raise DestinationLoadError(
                f"Failed to create table {database}.{table}: {e}"
            ) from e
    
    def load_data(
        self,
        database: str,
        table: str,
        data: List[Dict[str, Any]],
        mode: str = "append"
    ) -> int:
        """
        Load data to ClickHouse
        
        Args:
            database: Database name
            table: Table name
            data: List of row dictionaries
            mode: "append", "replace", or "upsert"
        
        Returns:
            Number of rows loaded
        """
        if not self._is_validated:
            self.validate()
        
        if not data:
            logger.warning("clickhouse_empty_data", database=database, table=table)
            return 0
        
        client = self._get_client()
        
        # Handle replace mode
        if mode == "replace":
            try:
                client.command(f"TRUNCATE TABLE `{database}`.`{table}`")
                logger.info("clickhouse_table_truncated", database=database, table=table)
            except Exception as e:
                raise DestinationLoadError(
                    f"Failed to truncate table {database}.{table}: {e}"
                ) from e
        
        # Load data with retry logic
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                # Extract column names from first row
                column_names = list(data[0].keys())
                
                # Convert to row format
                rows = [[row[col] for col in column_names] for row in data]
                
                # Insert data
                client.insert(
                    table=f"`{database}`.`{table}`",
                    data=rows,
                    column_names=column_names
                )
                
                rows_loaded = len(data)
                logger.info(
                    "clickhouse_data_loaded",
                    database=database,
                    table=table,
                    rows=rows_loaded,
                    mode=mode
                )
                return rows_loaded
                
            except ClickHouseError as e:
                last_error = e
                if "Too many simultaneous queries" in str(e) and attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (self.RETRY_BACKOFF ** attempt)
                    logger.warning(
                        "clickhouse_load_retry",
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(e)
                    )
                    time.sleep(delay)
                else:
                    break
            except Exception as e:
                last_error = e
                break
        
        # All retries failed
        raise DestinationLoadError(
            f"Failed to load data to {database}.{table} after {self.MAX_RETRIES} attempts: {last_error}"
        ) from last_error
    
    def sync_schema(
        self,
        database: str,
        table: str,
        schema: List[Dict[str, Any]]
    ) -> None:
        """
        Sync schema changes (add new columns)
        
        ClickHouse supports adding columns but not modifying/dropping
        """
        if not self._is_validated:
            self.validate()
        
        client = self._get_client()
        
        try:
            # Get existing columns
            existing_query = """
                SELECT name, type
                FROM system.columns
                WHERE database = %(database)s AND table = %(table)s
            """
            
            result = client.query(
                existing_query,
                parameters={"database": database, "table": table}
            )
            
            existing_columns = {row[0]: row[1] for row in result.result_rows}
            
            # Find new columns
            new_columns = []
            for col in schema:
                col_name = col["name"]
                col_type = col.get("destination_type", col.get("type", "String"))
                
                if col_name not in existing_columns:
                    new_columns.append((col_name, col_type))
            
            # Add new columns
            for col_name, col_type in new_columns:
                alter_query = f"""
                    ALTER TABLE `{database}`.`{table}`
                    ADD COLUMN IF NOT EXISTS `{col_name}` {col_type}
                """
                
                try:
                    client.command(alter_query)
                    logger.info(
                        "clickhouse_column_added",
                        database=database,
                        table=table,
                        column=col_name,
                        type=col_type
                    )
                except Exception as e:
                    logger.warning(
                        "clickhouse_add_column_failed",
                        database=database,
                        table=table,
                        column=col_name,
                        error=str(e)
                    )
            
            if not new_columns:
                logger.debug(
                    "clickhouse_schema_already_synced",
                    database=database,
                    table=table
                )
            
            # Ensure sync_at column exists
            self._ensure_sync_at_column(database, table)
            
        except Exception as e:
            raise DestinationLoadError(
                f"Failed to sync schema for {database}.{table}: {e}"
            ) from e
    
    def get_row_count(self, database: str, table: str) -> int:
        """Get row count from ClickHouse table"""
        if not self._is_validated:
            self.validate()
        
        client = self._get_client()
        
        try:
            query = f"SELECT count() as cnt FROM `{database}`.`{table}`"
            result = client.query(query)
            count = result.result_rows[0][0]
            
            logger.debug(
                "clickhouse_row_count",
                database=database,
                table=table,
                count=count
            )
            return count
            
        except Exception as e:
            raise DestinationLoadError(
                f"Failed to get row count from {database}.{table}: {e}"
            ) from e
    
    def optimize_table(
        self,
        database: str,
        table: str,
        final: bool = False
    ) -> None:
        """
        Optimize ClickHouse table (force merge)
        
        Args:
            database: Database name
            table: Table name
            final: Use OPTIMIZE FINAL (aggressive merge)
        """
        if not self._is_validated:
            self.validate()
        
        client = self._get_client()
        
        final_clause = "FINAL" if final else ""
        query = f"OPTIMIZE TABLE `{database}`.`{table}` {final_clause}"
        
        try:
            client.command(query)
            logger.info(
                "clickhouse_table_optimized",
                database=database,
                table=table,
                final=final
            )
        except Exception as e:
            logger.warning(
                "clickhouse_optimize_failed",
                database=database,
                table=table,
                error=str(e)
            )
    
    def get_table_engine(self, database: str, table: str) -> str:
        """Get table engine type"""
        client = self._get_client()
        
        query = """
            SELECT engine
            FROM system.tables
            WHERE database = %(database)s AND name = %(table)s
        """
        
        result = client.query(
            query,
            parameters={"database": database, "table": table}
        )
        
        return result.result_rows[0][0] if result.result_rows else "Unknown"
    
    def get_table_size(self, database: str, table: str) -> Dict[str, Any]:
        """Get table size statistics"""
        client = self._get_client()
        
        query = """
            SELECT
                sum(rows) as rows,
                sum(bytes) as bytes,
                formatReadableSize(sum(bytes)) as bytes_human,
                count() as parts,
                sum(data_compressed_bytes) as compressed_bytes
            FROM system.parts
            WHERE database = %(database)s AND table = %(table)s AND active
        """
        
        result = client.query(
            query,
            parameters={"database": database, "table": table}
        )
        
        if result.result_rows:
            row = result.result_rows[0]
            return {
                "rows": row[0] or 0,
                "bytes": row[1] or 0,
                "bytes_human": row[2] or "0 B",
                "parts": row[3] or 0,
                "compressed_bytes": row[4] or 0
            }
        return {}
    
    def close(self) -> None:
        """Close ClickHouse client"""
        if self._client:
            try:
                self._client.close()
                logger.debug("clickhouse_client_closed")
            except Exception as e:
                logger.warning("clickhouse_close_error", error=str(e))
            finally:
                self._client = None