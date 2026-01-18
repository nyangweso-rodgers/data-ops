"""
ClickHouse resource for Dagster
"""

from dagster import ConfigurableResource
from pydantic import Field
from typing import Optional, Any
from contextlib import contextmanager
import threading

# Use centralized logging
from dagster_pipeline.utils.logging_config import get_logger, sanitize_log_data

# Get module-level logger
logger = get_logger(__name__)


class ClickHouseResource(ConfigurableResource):
    """
    ClickHouse connection configuration and client manager
    
    Usage in definitions.py:
        resources = {
            "clickhouse_resource": ClickHouseResource(
                host=EnvVar("CLICKHOUSE_HOST"),
                port=8443,
                user=EnvVar("CLICKHOUSE_USER"),
                password=EnvVar("CLICKHOUSE_PASSWORD"),
                database="default"
            )
        }
    
    Usage in assets:
        def my_asset(context, clickhouse_resource: ClickHouseResource):
            with clickhouse_resource.get_connection() as client:
                result = client.query("SELECT 1")
    """
    
    host: str = Field(
        description="ClickHouse host address"
    )
    
    port: int = Field(
        default=8443,
        description="ClickHouse port (8443 for HTTPS, 8123 for HTTP, 9000 for native)"
    )
    
    user: str = Field(
        default="default",
        description="ClickHouse username"
    )
    
    password: str = Field(
        default="",
        description="ClickHouse password"
    )
    
    database: str = Field(
        default="default",
        description="Default ClickHouse database"
    )
    
    secure: bool = Field(
        default=True,
        description="Use HTTPS/TLS (recommended for production)"
    )
    
    connect_timeout: int = Field(
        default=30,
        description="Connection timeout in seconds"
    )
    
    send_receive_timeout: int = Field(
        default=300,
        description="Send/receive timeout in seconds (5 minutes default)"
    )
    
    compression: bool = Field(
        default=True,
        description="Enable compression for data transfer"
    )
    
    # Private attributes
    _client: Optional[Any] = None
    _client_lock: Optional[threading.RLock] = None
    
    def model_post_init(self, __context):
        """Initialize instance-specific logger with context (called after Pydantic init)"""
        super().model_post_init(__context)
        
        # Create logger with resource context bound
        self._logger = get_logger(
            __name__,
            context={
                "resource_type": "clickhouse",
                "database": self.database,
                "host": self.host,
                "port": self.port,
                "secure": self.secure
            }
        )
        
        # Initialize thread lock for client creation
        self._client_lock = threading.RLock()
        
        self._logger.debug(
            "clickhouse_resource_initialized",
            compression=self.compression,
            connect_timeout=self.connect_timeout
        )
    
    def get_config(self) -> dict:
        """
        Get configuration dict for ClickHouse connectors
        
        Returns:
            Configuration dictionary (with password sanitized in logs)
        """
        config = {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "secure": self.secure,
            "compression": self.compression,
            "connect_timeout": self.connect_timeout,
            "send_receive_timeout": self.send_receive_timeout
        }
        
        # Log config (with password sanitized)
        self._logger.debug(
            "config_retrieved",
            config=sanitize_log_data(config)
        )
        
        return config
    
    def get_client(self):
        """
        Get or create ClickHouse client connection (thread-safe)
        
        Uses clickhouse-connect library (recommended for Dagster)
        
        Returns:
            ClickHouse client instance
        
        Raises:
            ImportError: If clickhouse-connect is not installed
            ConnectionError: If connection fails
        """
        # Thread-safe client creation
        with self._client_lock:
            if self._client is None:
                try:
                    import clickhouse_connect
                    
                    self._logger.info("creating_clickhouse_client")
                    
                    self._client = clickhouse_connect.get_client(
                        host=self.host,
                        port=self.port,
                        username=self.user,
                        password=self.password,
                        database=self.database,
                        secure=self.secure,
                        connect_timeout=self.connect_timeout,
                        send_receive_timeout=self.send_receive_timeout,
                        compression=self.compression
                    )
                    
                    # Test connection and get version
                    result = self._client.query("SELECT version()")
                    version = result.first_row[0] if result.row_count > 0 else "unknown"
                    
                    self._logger.info(
                        "clickhouse_client_created",
                        version=version
                    )
                    
                except ImportError:
                    self._logger.error(
                        "clickhouse_connect_not_installed",
                        message="Install with: pip install clickhouse-connect"
                    )
                    raise ImportError(
                        "clickhouse-connect is not installed. "
                        "Install it with: pip install clickhouse-connect"
                    )
                except Exception as e:
                    self._logger.error(
                        "clickhouse_connection_failed",
                        error=str(e),
                        error_type=type(e).__name__,
                        exc_info=True
                    )
                    raise ConnectionError(
                        f"Failed to connect to ClickHouse at {self.host}:{self.port}: {e}"
                    )
            
            return self._client
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for getting a ClickHouse client
        
        Yields:
            ClickHouse client instance
        
        Example:
            with clickhouse_resource.get_connection() as client:
                result = client.query("SELECT COUNT(*) FROM my_table")
                print(f"Rows: {result.first_row[0]}")
        """
        client = self.get_client()
        try:
            self._logger.debug("connection_context_entered")
            yield client
        finally:
            # clickhouse-connect clients are connection pools
            # No need to close on each context exit
            self._logger.debug("connection_context_exited")
    
    def close(self):
        """
        Close the ClickHouse connection
        
        Call this when shutting down or when you need to force a reconnection
        """
        with self._client_lock:
            if self._client is not None:
                try:
                    if hasattr(self._client, 'close'):
                        self._client.close()
                    self._logger.info("clickhouse_client_closed")
                except Exception as e:
                    self._logger.warning(
                        "error_closing_clickhouse_client",
                        error=str(e),
                        error_type=type(e).__name__
                    )
                finally:
                    self._client = None
    
    def ping(self) -> bool:
        """
        Test if ClickHouse connection is alive
        
        Returns:
            True if connection is successful, False otherwise
        
        Example:
            if clickhouse_resource.ping():
                print("ClickHouse is reachable!")
        """
        try:
            with self.get_connection() as client:
                client.query("SELECT 1")
            
            self._logger.debug("ping_successful")
            return True
            
        except Exception as e:
            self._logger.error(
                "ping_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return False
    
    def execute_query(self, query: str, parameters: Optional[dict] = None):
        """
        Execute a SELECT query and return results
        
        Args:
            query: SQL query string
            parameters: Query parameters for parameterized queries
        
        Returns:
            Query result object
        
        Example:
            result = clickhouse_resource.execute_query(
                "SELECT * FROM users WHERE id = {id:UInt64}",
                parameters={"id": 123}
            )
            for row in result.named_results():
                print(row)
        """
        try:
            with self.get_connection() as client:
                self._logger.debug(
                    "executing_query",
                    query_preview=query[:100] + "..." if len(query) > 100 else query,
                    has_parameters=parameters is not None
                )
                
                result = client.query(query, parameters=parameters)
                
                self._logger.debug(
                    "query_executed",
                    rows_returned=result.row_count if hasattr(result, 'row_count') else None
                )
                
                return result
                
        except Exception as e:
            self._logger.error(
                "query_execution_failed",
                query_preview=query[:100] + "..." if len(query) > 100 else query,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
    
    def execute_command(self, command: str, parameters: Optional[dict] = None):
        """
        Execute a DDL/DML command (CREATE, DROP, INSERT, etc.)
        
        Args:
            command: SQL command string
            parameters: Command parameters
        
        Returns:
            Command result (usually summary info)
        
        Example:
            clickhouse_resource.execute_command(
                "CREATE TABLE IF NOT EXISTS test (id UInt64) ENGINE = MergeTree() ORDER BY id"
            )
        """
        try:
            with self.get_connection() as client:
                self._logger.debug(
                    "executing_command",
                    command_preview=command[:100] + "..." if len(command) > 100 else command,
                    has_parameters=parameters is not None
                )
                
                result = client.command(command, parameters=parameters)
                
                self._logger.debug(
                    "command_executed",
                    result=str(result)[:100] if result else None
                )
                
                return result
                
        except Exception as e:
            self._logger.error(
                "command_execution_failed",
                command_preview=command[:100] + "..." if len(command) > 100 else command,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
    
    def get_database_info(self) -> dict:
        """
        Get information about the ClickHouse database
        
        Returns:
            Dictionary with database metadata
        
        Example:
            info = clickhouse_resource.get_database_info()
            print(f"Version: {info['version']}")
            print(f"Tables: {info['table_count']}")
        """
        try:
            with self.get_connection() as client:
                # Get version
                version_result = client.query("SELECT version()")
                version = version_result.first_row[0]
                
                # Get table count in current database
                table_count_result = client.query(
                    "SELECT COUNT(*) FROM system.tables WHERE database = {db:String}",
                    parameters={"db": self.database}
                )
                table_count = table_count_result.first_row[0]
                
                # Get database size
                size_result = client.query(
                    "SELECT formatReadableSize(sum(bytes)) FROM system.parts WHERE database = {db:String}",
                    parameters={"db": self.database}
                )
                size = size_result.first_row[0]
                
                info = {
                    "database": self.database,
                    "version": version,
                    "table_count": table_count,
                    "size": size,
                    "host": self.host,
                    "port": self.port
                }
                
                self._logger.info(
                    "database_info_retrieved",
                    **info
                )
                
                return info
                
        except Exception as e:
            self._logger.error(
                "database_info_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
    
    def get_table_info(self, table_name: str) -> dict:
        """
        Get information about a specific table
        
        Args:
            table_name: Name of the table
        
        Returns:
            Dictionary with table metadata
        
        Example:
            info = clickhouse_resource.get_table_info("sales_service_leads")
            print(f"Rows: {info['row_count']}")
            print(f"Size: {info['size']}")
        """
        try:
            with self.get_connection() as client:
                # Get table info from system.tables
                result = client.query("""
                    SELECT 
                        engine,
                        total_rows,
                        total_bytes,
                        formatReadableSize(total_bytes) as size
                    FROM system.tables
                    WHERE database = {db:String} AND name = {table:String}
                """, parameters={"db": self.database, "table": table_name})
                
                if result.row_count == 0:
                    raise ValueError(
                        f"Table '{table_name}' not found in database '{self.database}'"
                    )
                
                row = result.first_row
                
                # Get column count
                col_result = client.query("""
                    SELECT COUNT(*) 
                    FROM system.columns 
                    WHERE database = {db:String} AND table = {table:String}
                """, parameters={"db": self.database, "table": table_name})
                
                column_count = col_result.first_row[0]
                
                info = {
                    "table_name": table_name,
                    "database": self.database,
                    "engine": row[0],
                    "row_count": row[1],
                    "bytes": row[2],
                    "size": row[3],
                    "column_count": column_count
                }
                
                self._logger.info(
                    "table_info_retrieved",
                    table=table_name,
                    rows=info["row_count"],
                    columns=column_count,
                    size=info["size"]
                )
                
                return info
                
        except Exception as e:
            self._logger.error(
                "table_info_failed",
                table=table_name,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
    
    def list_tables(self) -> list[str]:
        """
        List all tables in the database
        
        Returns:
            List of table names
        
        Example:
            tables = clickhouse_resource.list_tables()
            for table in tables:
                print(f"- {table}")
        """
        try:
            with self.get_connection() as client:
                result = client.query("""
                    SELECT name 
                    FROM system.tables 
                    WHERE database = {db:String}
                    ORDER BY name
                """, parameters={"db": self.database})
                
                tables = [row[0] for row in result.result_rows]
                
                self._logger.debug(
                    "tables_listed",
                    count=len(tables)
                )
                
                return tables
                
        except Exception as e:
            self._logger.error(
                "list_tables_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise