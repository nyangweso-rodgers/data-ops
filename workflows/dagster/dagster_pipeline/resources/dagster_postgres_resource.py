"""
PostgreSQL resource specifically for Dagster metadata storage

This is used by StateManager to access the kvs table where Dagster stores
key-value pairs for incremental sync state.
"""

from dagster import ConfigurableResource
from pydantic import Field, field_validator
from contextlib import contextmanager
import psycopg2

# Use centralized logging
from dagster_pipeline.utils.logging_config import get_logger

# Get module-level logger
logger = get_logger(__name__)


class DagsterPostgresResource(ConfigurableResource):
    """
    PostgreSQL connection for Dagster metadata storage
    
    Used by StateManager to store/retrieve incremental sync state from kvs table.
    
    REQUIRED: Must explicitly specify db_schema where Dagster metadata is stored.
    
    Usage:
        dagster_postgres = DagsterPostgresResource(
            host=EnvVar("DAGSTER_PG_DB_HOST"),
            port=5432,
            user=EnvVar("DAGSTER_PG_DB_USER"),
            password=EnvVar("DAGSTER_PG_DB_PASSWORD"),
            database=EnvVar("DAGSTER_PG_DB_NAME"),
            db_schema="dagster",  # ← Where kvs table lives
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
        description="Dagster metadata database name"
    )
    
    db_schema: str = Field(
        description="PostgreSQL schema where Dagster metadata is stored (REQUIRED)"
    )
    
    connect_timeout: int = Field(
        default=30,
        description="Connection timeout in seconds"
    )
    
    application_name: str = Field(
        default="dagster-state-manager",
        description="Application name for connection tracking"
    )
    
    @field_validator('db_schema')
    @classmethod
    def validate_schema(cls, v: str) -> str:
        """Validate that schema is provided and not empty"""
        if not v or not v.strip():
            raise ValueError(
                "Schema must be explicitly specified for Dagster metadata storage. "
                "Example: db_schema='dagster' or db_schema='metadata'"
            )
        
        # Info message if using 'public' schema
        if v.lower() == 'public':
            logger.info(
                "using_public_schema_for_dagster",
                schema=v,
                message="Using 'public' schema for Dagster metadata. "
                        "This is fine if your Dagster installation uses public schema."
            )
        
        return v.strip()
    
    def model_post_init(self, __context):
        """Initialize instance-specific logger with context (called after Pydantic init)"""
        super().model_post_init(__context)
        
        # Create logger with resource context bound
        self._logger = get_logger(
            __name__,
            context={
                "resource_type": "dagster_postgresql",
                "database": self.database,
                "schema": self.db_schema,
                "host": self.host,
                "purpose": "metadata_storage"
            }
        )
        
        self._logger.debug(
            "dagster_postgres_resource_initialized",
            port=self.port,
            application_name=self.application_name
        )
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection to Dagster's PostgreSQL database
        
        Automatically sets search_path to use the specified schema.
        
        Yields:
            psycopg2 connection object
        
        Example:
            with dagster_postgres.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM kvs WHERE key = %s", (key,))
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
        Test the database connection and verify kvs table exists
        
        Returns:
            True if connection succeeds and kvs table exists
        
        Raises:
            Exception if connection fails or kvs table not found
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Test basic connectivity
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    
                    # Verify kvs table exists in the schema
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = %s 
                            AND table_name = 'kvs'
                        )
                    """, (self.db_schema,))
                    
                    kvs_exists = cursor.fetchone()[0]
                    
                    if not kvs_exists:
                        self._logger.warning(
                            "kvs_table_not_found",
                            message=f"kvs table not found in schema '{self.db_schema}'. "
                                   "This resource is meant for Dagster metadata storage."
                        )
                    
                    self._logger.info(
                        "connection_test_successful",
                        kvs_table_exists=kvs_exists
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
    
    def get_kvs_value(self, key: str) -> str | None:
        """
        Get a value from the Dagster kvs table
        
        Args:
            key: Key to retrieve
        
        Returns:
            Value as string, or None if key doesn't exist
        
        Example:
            value = dagster_postgres.get_kvs_value("etl_sync_state:mysql:amtdb:accounts")
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT value FROM kvs WHERE key = %s",
                        (key,)
                    )
                    result = cursor.fetchone()
                    
                    if result:
                        self._logger.debug(
                            "kvs_value_retrieved",
                            key=key,
                            value_length=len(result[0]) if result[0] else 0
                        )
                        return result[0]
                    else:
                        self._logger.debug(
                            "kvs_key_not_found",
                            key=key
                        )
                        return None
                        
        except Exception as e:
            self._logger.error(
                "kvs_get_failed",
                key=key,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
    
    def set_kvs_value(self, key: str, value: str) -> bool:
        """
        Set a value in the Dagster kvs table
        
        Args:
            key: Key to set
            value: Value to store (as string)
        
        Returns:
            True if successful
        
        Example:
            dagster_postgres.set_kvs_value(
                "etl_sync_state:mysql:amtdb:accounts",
                '{"last_value": "2026-01-17 10:00:00"}'
            )
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Use INSERT ... ON CONFLICT (upsert)
                    cursor.execute("""
                        INSERT INTO kvs (key, value)
                        VALUES (%s, %s)
                        ON CONFLICT (key) 
                        DO UPDATE SET value = EXCLUDED.value
                    """, (key, value))
                    
                    conn.commit()
                    
                    self._logger.debug(
                        "kvs_value_set",
                        key=key,
                        value_length=len(value)
                    )
                    
                    return True
                    
        except Exception as e:
            self._logger.error(
                "kvs_set_failed",
                key=key,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
    
    def delete_kvs_value(self, key: str) -> bool:
        """
        Delete a value from the Dagster kvs table
        
        Args:
            key: Key to delete
        
        Returns:
            True if key was deleted, False if key didn't exist
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM kvs WHERE key = %s",
                        (key,)
                    )
                    rows_deleted = cursor.rowcount
                    conn.commit()
                    
                    self._logger.debug(
                        "kvs_value_deleted",
                        key=key,
                        existed=rows_deleted > 0
                    )
                    
                    return rows_deleted > 0
                    
        except Exception as e:
            self._logger.error(
                "kvs_delete_failed",
                key=key,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
    
    def list_kvs_keys(self, prefix: str = None) -> list[str]:
        """
        List all keys in the kvs table, optionally filtered by prefix
        
        Args:
            prefix: Optional prefix to filter keys (e.g., "etl_sync_state:")
        
        Returns:
            List of keys
        
        Example:
            # Get all ETL sync state keys
            keys = dagster_postgres.list_kvs_keys("etl_sync_state:")
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    if prefix:
                        cursor.execute(
                            "SELECT key FROM kvs WHERE key LIKE %s ORDER BY key",
                            (f"{prefix}%",)
                        )
                    else:
                        cursor.execute("SELECT key FROM kvs ORDER BY key")
                    
                    keys = [row[0] for row in cursor.fetchall()]
                    
                    self._logger.debug(
                        "kvs_keys_listed",
                        prefix=prefix,
                        count=len(keys)
                    )
                    
                    return keys
                    
        except Exception as e:
            self._logger.error(
                "kvs_list_failed",
                prefix=prefix,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise