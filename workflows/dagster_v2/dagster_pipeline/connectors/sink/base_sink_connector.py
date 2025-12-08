# dagster_pipeline/connectors/destinations/base_destination.py
"""
Abstract base class for all destination connectors
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd
from dagster import AssetExecutionContext
import structlog

logger = structlog.get_logger(__name__)


class BaseDestinationConnector(ABC):
    """
    Abstract base class for destination connectors
    
    Every destination connector (ClickHouse, BigQuery, MySQL) must implement this interface.
    
    Lifecycle:
        1. __init__() - Initialize with config
        2. validate() - Check connection and permissions
        3. table_exists() - Check if table exists
        4. create_table() - Create table if needed
        5. load_data() - Load data (insert/upsert)
        6. close() - Clean up
    
    Usage:
        connector = ClickHouseDestinationConnector(context, config)
        connector.validate()
        
        if not connector.table_exists("analytics", "accounts"):
            connector.create_table("analytics", "accounts", schema)
        
        connector.load_data("analytics", "accounts", df, mode="append")
        connector.close()
    """
    
    def __init__(
        self,
        context: AssetExecutionContext,
        config: Dict[str, Any]
    ):
        """
        Initialize destination connector
        
        Args:
            context: Dagster execution context
            config: Destination-specific configuration
        """
        self.context = context
        self.config = config
        self._connection = None
        
        logger.info(
            "destination_connector_initialized",
            destination_type=self.destination_type()
        )
    
    @abstractmethod
    def destination_type(self) -> str:
        """
        Return destination type identifier
        
        Returns:
            "clickhouse", "bigquery", "mysql", etc.
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """
        Validate destination connection and permissions
        
        Returns:
            True if valid
        
        Raises:
            ConnectionError, PermissionError, etc.
        """
        pass
    
    @abstractmethod
    def table_exists(self, database: str, table: str) -> bool:
        """
        Check if table exists in destination
        
        Args:
            database: Database name
            table: Table name
        
        Returns:
            True if exists
        """
        pass
    
    @abstractmethod
    def create_table(
        self,
        database: str,
        table: str,
        schema: List[Dict[str, Any]],
        **options
    ) -> None:
        """
        Create table in destination
        
        Args:
            database: Database name
            table: Table name
            schema: List of column definitions (destination types)
            options: Destination-specific options
                e.g., engine="MergeTree" for ClickHouse
        """
        pass
    
    @abstractmethod
    def load_data(
        self,
        database: str,
        table: str,
        data: pd.DataFrame,
        mode: str = "append"
    ) -> int:
        """
        Load data to destination
        
        Args:
            database: Database name
            table: Table name
            data: Data to load
            mode: "append", "replace", or "upsert"
        
        Returns:
            Number of rows loaded
        """
        pass
    
    @abstractmethod
    def sync_schema(
        self,
        database: str,
        table: str,
        schema: List[Dict[str, Any]]
    ) -> None:
        """
        Sync schema changes (add new columns)
        
        Optional to implement - default does nothing
        """
        logger.warning(
            "schema_sync_not_implemented",
            destination_type=self.destination_type()
        )
    
    def close(self) -> None:
        """Clean up resources"""
        if self._connection:
            try:
                self._connection.close()
                logger.debug(
                    "destination_connection_closed",
                    destination_type=self.destination_type()
                )
            except Exception as e:
                logger.warning(
                    "destination_close_error",
                    destination_type=self.destination_type(),
                    error=str(e)
                )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()