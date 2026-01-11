# dagster_pipeline/resources/clickhouse_resource.py
"""
ClickHouse resource for Dagster
"""

from dagster import ConfigurableResource
from pydantic import Field
import structlog
from typing import Optional
from contextlib import contextmanager

logger = structlog.get_logger(__name__)


class ClickHouseResource(ConfigurableResource):
    """
    ClickHouse connection configuration and client manager
    
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
    
    Usage in assets:
        def my_asset(context, clickhouse_resource: ClickHouseResource):
            client = clickhouse_resource.get_client()
            result = client.query("SELECT 1")
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
    
    connect_timeout: int = Field(
        default=10,
        description="Connection timeout in seconds"
    )
    
    send_receive_timeout: int = Field(
        default=300,
        description="Send/receive timeout in seconds"
    )
    
    # Private attribute to cache client
    _client: Optional[object] = None
    
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
    
    def get_client(self):
        """
        Get or create ClickHouse client connection
        
        Uses clickhouse-connect library (recommended for Dagster)
        
        Returns:
            ClickHouse client instance
        """
        if self._client is None:
            try:
                import clickhouse_connect
                
                logger.info(
                    "creating_clickhouse_connection",
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                )
                
                self._client = clickhouse_connect.get_client(
                    host=self.host,
                    port=self.port,
                    username=self.user,
                    password=self.password,
                    database=self.database,
                    secure=self.secure,
                    connect_timeout=self.connect_timeout,
                    send_receive_timeout=self.send_receive_timeout,
                )
                
                # Test connection
                result = self._client.query("SELECT 1")
                logger.info("clickhouse_connection_successful")
                
            except ImportError:
                logger.error("clickhouse_connect_not_installed")
                raise ImportError(
                    "clickhouse-connect is not installed. "
                    "Install it with: pip install clickhouse-connect"
                )
            except Exception as e:
                logger.error("clickhouse_connection_failed", error=str(e))
                raise ConnectionError(
                    f"Failed to connect to ClickHouse at {self.host}:{self.port}: {e}"
                )
        
        return self._client
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for getting a ClickHouse client
        
        Usage:
            with clickhouse_resource.get_connection() as client:
                result = client.query("SELECT 1")
        """
        client = self.get_client()
        try:
            yield client
        finally:
            # clickhouse-connect clients don't need explicit cleanup
            # but you can add cleanup logic here if needed
            pass
    
    def close(self):
        """Close the ClickHouse connection"""
        if self._client is not None:
            try:
                if hasattr(self._client, 'close'):
                    self._client.close()
                logger.info("clickhouse_connection_closed")
            except Exception as e:
                logger.warning("error_closing_clickhouse_connection", error=str(e))
            finally:
                self._client = None
    
    def ping(self) -> bool:
        """
        Test if ClickHouse connection is alive
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            client = self.get_client()
            client.query("SELECT 1")
            return True
        except Exception as e:
            logger.error("clickhouse_ping_failed", error=str(e))
            return False
    
    def execute_query(self, query: str, parameters: Optional[dict] = None):
        """
        Execute a query and return results
        
        Args:
            query: SQL query string
            parameters: Query parameters
        
        Returns:
            Query result
        """
        client = self.get_client()
        return client.query(query, parameters=parameters)
    
    def execute_command(self, command: str, parameters: Optional[dict] = None):
        """
        Execute a command (DDL/DML without result)
        
        Args:
            command: SQL command string
            parameters: Command parameters
        """
        client = self.get_client()
        return client.command(command, parameters=parameters)