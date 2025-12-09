# dagster_pipeline/resources/postgres_resource.py
"""
PostgreSQL resource for Dagster
Provides connection configuration to PostgreSQL source/destination connectors
"""

from dagster import ConfigurableResource
from pydantic import Field
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


class PostgreSQLResource(ConfigurableResource):
    """
    PostgreSQL connection configuration
    
    Provides connection details to PostgreSQL connectors.
    Does NOT implement database logic - that's in the connectors.
    
    Usage in definitions.py:
        resources = {
            "postgres_resource": PostgreSQLResource(
                host=EnvVar("POSTGRES_HOST"),
                port=5432,
                user=EnvVar("POSTGRES_USER"),
                password=EnvVar("POSTGRES_PASSWORD"),
                database=EnvVar("POSTGRES_DB")
            )
        }
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
    
    connect_timeout: int = Field(
        default=30,
        description="Connection timeout in seconds"
    )
    
    sslmode: Optional[str] = Field(
        default=None,
        description="SSL mode (e.g., 'require', 'verify-full', 'disable')"
    )
    
    # RENAMED: schema -> pg_schema to avoid shadowing parent class attribute
    pg_schema: Optional[str] = Field(
        default="public",
        description="PostgreSQL schema (defaults to 'public')"
    )
    
    application_name: Optional[str] = Field(
        default="dagster",
        description="Application name for PostgreSQL connection"
    )
    
    def get_config(self) -> dict:
        """
        Get configuration dict for connectors
        
        Returns:
            Configuration dict suitable for PostgreSQLSourceConnector or PostgreSQLDestinationConnector
        """
        config = {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "connect_timeout": self.connect_timeout,
            "application_name": self.application_name,
            "schema": self.pg_schema,  # Map pg_schema -> schema for connectors
        }
        
        # Add optional parameters only if they are not None
        if self.sslmode:
            config["sslmode"] = self.sslmode
            
        return config
    
    def validate_connection(self) -> bool:
        """
        Test PostgreSQL connection (optional - for debugging)
        
        Returns:
            True if connection succeeds
        """
        try:
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                connect_timeout=self.connect_timeout,
                **({"sslmode": self.sslmode} if self.sslmode else {})
            )
            conn.close()
            logger.info("postgres_connection_validated", host=self.host, database=self.database)
            return True
        except ImportError:
            logger.error("psycopg2_not_installed")
            raise
        except Exception as e:
            logger.error(
                "postgres_connection_validation_failed",
                host=self.host,
                database=self.database,
                error=str(e)
            )
            return False