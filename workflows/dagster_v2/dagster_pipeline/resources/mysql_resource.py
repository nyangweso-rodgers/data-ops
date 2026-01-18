"""
MySQL resource for Dagster
Provides connection configuration to MySQL source/destination connectors
"""

from dagster import ConfigurableResource
from pydantic import Field
from typing import Optional
from contextlib import contextmanager

# Use centralized logging
from dagster_pipeline.utils.logging_config import get_logger, sanitize_log_data

# Get module-level logger
logger = get_logger(__name__)


class MySQLResource(ConfigurableResource):
    """
    MySQL connection configuration
    
    Provides connection details to MySQL connectors.
    Does NOT implement database logic - that's in the connectors.
    
    Usage in definitions.py:
        resources = {
            "mysql_sales_service": MySQLResource(
                host=EnvVar("MYSQL_HOST"),
                port=3306,
                user=EnvVar("MYSQL_USER"),
                password=EnvVar("MYSQL_PASSWORD"),
                database="sales_service"
            )
        }
    """
    
    host: str = Field(
        description="MySQL host address"
    )
    
    port: int = Field(
        default=3306,
        description="MySQL port"
    )
    
    user: str = Field(
        description="MySQL username"
    )
    
    password: str = Field(
        description="MySQL password"
    )
    
    database: str = Field(
        description="Database name (e.g., 'sales_service', 'amtdb')"
    )
    
    connect_timeout: int = Field(
        default=30,
        description="Connection timeout in seconds"
    )
    
    charset: str = Field(
        default="utf8mb4",
        description="Character set for MySQL connection"
    )
    
    ssl_disabled: bool = Field(
        default=False,
        description="Whether to disable SSL (set to True for local development)"
    )
    
    def model_post_init(self, __context):
        """Initialize instance-specific logger with context (called after Pydantic init)"""
        super().model_post_init(__context)
        
        # Create logger with resource context bound
        self._logger = get_logger(
            __name__,
            context={
                "resource_type": "mysql",
                "database": self.database,
                "host": self.host,
                "port": self.port
            }
        )
        
        self._logger.debug(
            "mysql_resource_initialized",
            charset=self.charset,
            ssl_disabled=self.ssl_disabled
        )
    
    def get_config(self) -> dict:
        """
        Get configuration dict for connectors
        
        Returns:
            Configuration dict suitable for MySQLSourceConnector or MySQLSinkConnector
        
        Example:
            config = mysql_resource.get_config()
            source = MySQLSourceConnector(config)
        """
        config = {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "connect_timeout": self.connect_timeout,
            "charset": self.charset,
            "ssl_disabled": self.ssl_disabled
        }
        
        # Log config (with password sanitized)
        self._logger.debug(
            "config_retrieved",
            config=sanitize_log_data(config)
        )
        
        return config
    
    @contextmanager
    def get_connection(self):
        """
        Get a direct MySQL connection
        
        Use this for quick validation or debugging.
        For production ETL, use MySQLSourceConnector instead.
        
        Yields:
            pymysql connection object
        
        Example:
            with mysql_resource.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM accounts")
                    count = cursor.fetchone()[0]
        """
        import pymysql
        
        conn = None
        try:
            # Build connection kwargs
            conn_kwargs = {
                "host": self.host,
                "port": self.port,
                "user": self.user,
                "password": self.password,
                "database": self.database,
                "connect_timeout": self.connect_timeout,
                "charset": self.charset,
                "cursorclass": pymysql.cursors.DictCursor
            }
            
            # Handle SSL
            if self.ssl_disabled:
                conn_kwargs["ssl"] = {"fake_flag_to_enable_tls": True}
                conn_kwargs["ssl_disabled"] = True
            
            conn = pymysql.connect(**conn_kwargs)
            
            self._logger.debug("connection_opened")
            
            yield conn
            
        except pymysql.OperationalError as e:
            self._logger.error(
                "connection_failed",
                error=str(e),
                error_code=e.args[0] if e.args else None,
                error_type="OperationalError",
                exc_info=True
            )
            raise
        except pymysql.Error as e:
            self._logger.error(
                "mysql_error",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
        except Exception as e:
            self._logger.error(
                "connection_error",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
        finally:
            if conn:
                conn.close()
                self._logger.debug("connection_closed")
    
    def validate_connection(self) -> bool:
        """
        Test MySQL connection
        
        Returns:
            True if connection succeeds
        
        Raises:
            Exception if connection fails
        
        Example:
            if mysql_resource.validate_connection():
                print("Connection OK!")
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    
                    self._logger.info(
                        "connection_validated",
                        result=result
                    )
                    
                    return True
                    
        except Exception as e:
            self._logger.error(
                "connection_validation_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
    
    def get_database_info(self) -> dict:
        """
        Get basic database information
        
        Returns:
            Dictionary with database metadata
        
        Example:
            info = mysql_resource.get_database_info()
            print(f"MySQL version: {info['version']}")
            print(f"Tables: {info['table_count']}")
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Get MySQL version
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()["VERSION()"]
                    
                    # Get table count
                    cursor.execute("""
                        SELECT COUNT(*) as count 
                        FROM information_schema.tables 
                        WHERE table_schema = %s
                    """, (self.database,))
                    table_count = cursor.fetchone()["count"]
                    
                    # Get database size
                    cursor.execute("""
                        SELECT 
                            ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb
                        FROM information_schema.tables
                        WHERE table_schema = %s
                    """, (self.database,))
                    size_mb = cursor.fetchone()["size_mb"] or 0
                    
                    info = {
                        "database": self.database,
                        "version": version,
                        "table_count": table_count,
                        "size_mb": float(size_mb),
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
            info = mysql_resource.get_table_info("accounts")
            print(f"Rows: {info['row_count']}")
            print(f"Columns: {info['column_count']}")
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Get table info from information_schema
                    cursor.execute("""
                        SELECT 
                            table_rows,
                            ROUND((data_length + index_length) / 1024 / 1024, 2) as size_mb,
                            engine,
                            table_collation
                        FROM information_schema.tables
                        WHERE table_schema = %s AND table_name = %s
                    """, (self.database, table_name))
                    
                    table_info = cursor.fetchone()
                    
                    if not table_info:
                        raise ValueError(f"Table '{table_name}' not found in database '{self.database}'")
                    
                    # Get column count
                    cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = %s
                    """, (self.database, table_name))
                    
                    column_count = cursor.fetchone()["count"]
                    
                    info = {
                        "table_name": table_name,
                        "database": self.database,
                        "row_count": table_info["table_rows"],
                        "size_mb": float(table_info["size_mb"] or 0),
                        "engine": table_info["engine"],
                        "collation": table_info["table_collation"],
                        "column_count": column_count
                    }
                    
                    self._logger.info(
                        "table_info_retrieved",
                        table=table_name,
                        rows=info["row_count"],
                        columns=column_count,
                        size_mb=info["size_mb"]
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
            tables = mysql_resource.list_tables()
            print(f"Found {len(tables)} tables")
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = %s
                        ORDER BY table_name
                    """, (self.database,))
                    
                    tables = [row["table_name"] for row in cursor.fetchall()]
                    
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