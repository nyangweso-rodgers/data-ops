# dagster_pipeline/resources/mysql.py
"""
MySQL resource for Dagster
Provides connection configuration to MySQL source/destination connectors
"""

from dagster import ConfigurableResource
from pydantic import Field
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


class MySQLResource(ConfigurableResource):
    """
    MySQL connection configuration
    
    Provides connection details to MySQL connectors.
    Does NOT implement database logic - that's in the connectors.
    
    Usage in definitions.py:
        resources = {
            "mysql_resource": MySQLResource(
                host=EnvVar("MYSQL_HOST"),
                port=3306,
                user=EnvVar("MYSQL_USER"),
                password=EnvVar("MYSQL_PASSWORD")
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
    
    connect_timeout: int = Field(
        default=30,
        description="Connection timeout in seconds"
    )
    
    def get_config(self) -> dict:
        """
        Get configuration dict for connectors
        
        Returns:
            Configuration dict suitable for MySQLSourceConnector or MySQLDestinationConnector
        """
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "connect_timeout": self.connect_timeout
        }
    
    def validate_connection(self) -> bool:
        """
        Test MySQL connection (optional - for debugging)
        
        Returns:
            True if connection succeeds
        """
        import pymysql
        
        try:
            conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                connect_timeout=self.connect_timeout
            )
            conn.close()
            logger.info("mysql_connection_validated", host=self.host)
            return True
        except Exception as e:
            logger.error(
                "mysql_connection_validation_failed",
                host=self.host,
                error=str(e)
            )
            return False