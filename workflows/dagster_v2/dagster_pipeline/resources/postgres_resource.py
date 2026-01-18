"""
PostgreSQL resource for application databases (non-Dagster metadata)

This is for connecting to your own PostgreSQL databases like FMA, etc.
"""

from dagster import ConfigurableResource
from pydantic import Field
from contextlib import contextmanager
import psycopg2

# Use centralized logging
from dagster_pipeline.utils.logging_config import get_logger

# Get module-level logger
logger = get_logger(__name__)


class PostgreSQLResource(ConfigurableResource):
    """
    PostgreSQL connection for application databases
    
    Used for connecting to your own PostgreSQL databases (not Dagster metadata).
    
    Usage:
        postgres_fma = PostgreSQLResource(
            host=EnvVar("SC_EP_PG_DB_HOST"),
            port=5432,
            user=EnvVar("SC_EP_PG_DB_USER"),
            password=EnvVar("SC_EP_PG_DB_PASSWORD"),
            database=EnvVar("SC_EP_PG_DB_NAME"),
            db_schema="public",  # Schema where your tables live
        )
    """
    
    host: str = Field(
        description="PostgreSQL host address"
    )
    
    port: int = Field(
        default=5432,
        description="PostgreSQL port"
    )
    
    user: str = Field(
        description="PostgreSQL username"
    )
    
    password: str = Field(
        description="PostgreSQL password"
    )
    
    database: str = Field(
        description="Database name"
    )
    
    db_schema: str = Field(
        description="PostgreSQL schema (e.g., 'public', 'fma')"
    )
    
    connect_timeout: int = Field(
        default=30,
        description="Connection timeout in seconds"
    )
    
    application_name: str = Field(
        default="dagster-etl-pipeline",
        description="Application name for connection tracking"
    )
    
    def model_post_init(self, __context):
        """Initialize instance-specific logger with context (called after Pydantic init)"""
        super().model_post_init(__context)
        
        # Create logger with resource context bound
        self._logger = get_logger(
            __name__,
            context={
                "resource_type": "postgresql",
                "database": self.database,
                "schema": self.db_schema,
                "host": self.host
            }
        )
        
        self._logger.debug(
            "postgres_resource_initialized",
            port=self.port,
            application_name=self.application_name
        )
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection to the PostgreSQL database
        
        Automatically sets search_path to use the specified schema.
        
        Yields:
            psycopg2 connection object
        
        Example:
            with postgres_fma.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM your_table")
        """
        conn = None
        try:
            # Connect with search_path set to our schema first, then public
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                connect_timeout=self.connect_timeout,
                application_name=self.application_name,
                options=f'-c search_path={self.db_schema},public'
            )
            
            self._logger.debug("connection_opened")
            
            yield conn
            
        except psycopg2.OperationalError as e:
            self._logger.error(
                "connection_failed",
                error=str(e),
                error_type="OperationalError",
                exc_info=True
            )
            raise
        except psycopg2.Error as e:
            self._logger.error(
                "postgres_error",
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
    
    def test_connection(self) -> bool:
        """
        Test the database connection
        
        Returns:
            True if connection succeeds
        
        Raises:
            Exception if connection fails
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    
                    self._logger.info(
                        "connection_test_successful",
                        result=result[0] if result else None
                    )
                    return True
                    
        except Exception as e:
            self._logger.error(
                "connection_test_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
    
    def execute_query(self, query: str, params: tuple = None) -> list:
        """
        Execute a SELECT query and return results
        
        Args:
            query: SQL query to execute
            params: Query parameters (for parameterized queries)
        
        Returns:
            List of result tuples
        
        Example:
            results = postgres_fma.execute_query(
                "SELECT * FROM premises WHERE id = %s",
                (123,)
            )
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    self._logger.debug(
                        "executing_query",
                        query_preview=query[:100] + "..." if len(query) > 100 else query,
                        has_params=params is not None
                    )
                    
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    
                    self._logger.debug(
                        "query_executed",
                        rows_returned=len(results)
                    )
                    
                    return results
                    
        except Exception as e:
            self._logger.error(
                "query_execution_failed",
                query_preview=query[:100] + "..." if len(query) > 100 else query,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
    
    def get_table_info(self, table_name: str) -> dict:
        """
        Get basic information about a table
        
        Args:
            table_name: Name of the table
        
        Returns:
            Dictionary with table info (row count, columns)
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Get row count
                    cursor.execute(
                        f"SELECT COUNT(*) FROM {self.db_schema}.{table_name}"
                    )
                    row_count = cursor.fetchone()[0]
                    
                    # Get column info
                    cursor.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_schema = %s AND table_name = %s
                        ORDER BY ordinal_position
                    """, (self.db_schema, table_name))
                    
                    columns = [
                        {"name": row[0], "type": row[1]} 
                        for row in cursor.fetchall()
                    ]
                    
                    info = {
                        "table_name": table_name,
                        "schema": self.db_schema,
                        "row_count": row_count,
                        "column_count": len(columns),
                        "columns": columns
                    }
                    
                    self._logger.info(
                        "table_info_retrieved",
                        table=table_name,
                        rows=row_count,
                        columns=len(columns)
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