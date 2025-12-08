# dagster_pipeline/resources/clickhouse.py
"""
ClickHouse resource for Dagster
"""

from dagster import ConfigurableResource
from pydantic import Field
import structlog

logger = structlog.get_logger(__name__)


class ClickHouseResource(ConfigurableResource):
    """
    ClickHouse connection configuration
    
    Usage in definitions.py:
        resources = {
            "clickhouse_resource": ClickHouseResource(
                host=EnvVar("CLICKHOUSE_HOST"),
                port=8123,
                user=EnvVar("CLICKHOUSE_USER"),
                password=EnvVar("CLICKHOUSE_PASSWORD"),
                database="analytics"
            )
        }
    """
    
    host: str = Field(
        description="ClickHouse host address"
    )
    
    port: int = Field(
        default=8123,
        description="ClickHouse HTTP port (8123) or native port (9000)"
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
        default=False,
        description="Use HTTPS/TLS"
    )
    
    def get_config(self) -> dict:
        """Get configuration dict for ClickHouse connectors"""
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "secure": self.secure
        }