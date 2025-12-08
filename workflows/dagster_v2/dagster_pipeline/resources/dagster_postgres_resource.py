# dagster_pipeline/resources/dagster_postgres.py
"""
Postgres resource for Dagster metadata storage (state management)
"""

from dagster import ConfigurableResource
from pydantic import Field
import pymysql
from contextlib import contextmanager
import structlog

logger = structlog.get_logger(__name__)


class DagsterPostgresResource(ConfigurableResource):
    """
    Postgres connection for Dagster metadata (kvs table)
    
    Used by StateManager to store incremental sync state.
    """
    
    host: str = Field(description="Postgres host")
    port: int = Field(default=5432, description="Postgres port")
    user: str = Field(description="Postgres username")
    password: str = Field(description="Postgres password")
    database: str = Field(description="Dagster metadata database")
    
    @contextmanager
    def get_connection(self):
        """
        Get Postgres connection for state management
        
        Yields:
            psycopg2 connection
        """
        import psycopg2
        
        conn = None
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            yield conn
        except Exception as e:
            logger.error(
                "dagster_postgres_connection_failed",
                host=self.host,
                database=self.database,
                error=str(e)
            )
            raise
        finally:
            if conn:
                conn.close()