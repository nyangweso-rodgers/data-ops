# dagster_pipeline/connectors/sources/base_source.py
"""
Abstract base class for all source connectors
Defines the interface that every source must implement
"""

from abc import ABC, abstractmethod
from typing import Iterator, List, Dict, Any, Optional
from enum import Enum
import pandas as pd
from dagster import AssetExecutionContext
import structlog

logger = structlog.get_logger(__name__)


class SourceType(Enum):
    """Supported source types"""
    MYSQL = "mysql"
    POSTGRES = "postgres"
    S3 = "s3"
    API = "api"
    CLICKHOUSE = "clickhouse"


class BaseSourceConnector(ABC):
    """
    Abstract base class for source connectors
    
    Every source connector (MySQL, Postgres, S3, etc.) must implement this interface.
    This ensures consistency across all data sources.
    
    Lifecycle:
        1. __init__() - Initialize with config
        2. validate() - Check connection and permissions
        3. get_schema() - Discover table schema
        4. extract_data() - Stream data in batches
        5. close() - Clean up resources
    
    Usage:
        connector = MySQLSourceConnector(config)
        connector.validate()
        schema = connector.get_schema()
        
        for batch in connector.extract_data(columns=["id", "name"]):
            process(batch)
        
        connector.close()
    """
    
    def __init__(
        self,
        context: AssetExecutionContext,
        config: Dict[str, Any]
    ):
        """
        Initialize source connector
        
        Args:
            context: Dagster execution context
            config: Source-specific configuration
                Common keys:
                - database: Database name
                - table: Table name
                - host, port, user, password (for DB sources)
                - bucket, prefix (for S3 sources)
        """
        self.context = context
        self.config = config
        self._connection = None
        
        logger.info(
            "source_connector_initialized",
            source_type=self.source_type(),
            database=config.get("database"),
            table=config.get("table")
        )
    
    @abstractmethod
    def source_type(self) -> str:
        """
        Return source type identifier
        
        Returns:
            "mysql", "postgres", "s3", etc.
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """
        Validate source connection and permissions
        
        Should check:
        - Connection can be established
        - Database/table exists
        - User has read permissions
        
        Returns:
            True if valid
        
        Raises:
            ConnectionError: If connection fails
            PermissionError: If insufficient permissions
            ValueError: If database/table doesn't exist
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> List[Dict[str, Any]]:
        """
        Get schema of the source table
        
        Returns:
            List of column definitions:
            [
                {
                    "name": "id",
                    "type": "bigint",
                    "nullable": False,
                    "primary_key": True
                },
                ...
            ]
        """
        pass
    
    @abstractmethod
    def extract_data(
        self,
        columns: Optional[List[str]] = None,
        batch_size: int = 10000,
        incremental_config: Optional[Dict[str, Any]] = None
    ) -> Iterator[pd.DataFrame]:
        """
        Extract data from source in batches
        
        Args:
            columns: Columns to extract (None = all columns)
            batch_size: Rows per batch
            incremental_config: For incremental extraction:
                {
                    "key": "updated_at",
                    "last_value": "2024-12-01 00:00:00",
                    "operator": ">"
                }
        
        Yields:
            DataFrame per batch
        
        Note:
            Should use streaming/cursor to avoid loading entire table in memory
        """
        pass
    
    @abstractmethod
    def get_row_count(
        self,
        where_clause: Optional[str] = None
    ) -> int:
        """
        Get total row count from source
        
        Args:
            where_clause: Optional filter
        
        Returns:
            Row count
        """
        pass
    
    def close(self) -> None:
        """
        Clean up resources (connections, file handles, etc.)
        
        Optional to override - default does nothing
        """
        if self._connection:
            try:
                self._connection.close()
                logger.debug(
                    "source_connection_closed",
                    source_type=self.source_type()
                )
            except Exception as e:
                logger.warning(
                    "source_close_error",
                    source_type=self.source_type(),
                    error=str(e)
                )
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.close()