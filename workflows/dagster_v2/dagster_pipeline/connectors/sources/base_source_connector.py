"""
Abstract base class for all source connectors

DESIGN PRINCIPLES:
- Pure Python - NO PANDAS requirement (returns dicts/lists)
- Streaming-first - never load full dataset in memory
- Fail-fast with clear error messages
- Extensible for all source types
"""

from abc import ABC, abstractmethod
from typing import Iterator, List, Dict, Any, Optional, Literal
from enum import Enum
from dagster import AssetExecutionContext
import structlog
from dataclasses import dataclass

logger = structlog.get_logger(__name__)


class SourceType(Enum):
    """Supported source types"""
    MYSQL = "mysql"
    POSTGRES = "postgres"
    S3 = "s3"
    API = "api"
    CLICKHOUSE = "clickhouse"


class SourceConnectionError(Exception):
    """Raised when source connection fails"""
    pass


class SourceValidationError(Exception):
    """Raised when source validation fails"""
    pass


class SourceExtractionError(Exception):
    """Raised when data extraction fails"""
    pass


@dataclass
class IncrementalConfig:
    """
    Configuration for incremental data extraction
    
    Attributes:
        key: Column to use for incremental extraction (e.g., "updated_at", "id")
        last_value: Last value from previous extraction
        operator: Comparison operator (">", ">=", "!=")
        order_by: Column to order results by (defaults to key)
    """
    key: str
    last_value: Any
    operator: Literal[">", ">=", "!="] = ">"
    order_by: Optional[str] = None
    
    def __post_init__(self):
        if self.order_by is None:
            self.order_by = self.key


@dataclass
class ColumnSchema:
    """
    Schema definition for a single column
    
    Matches the structure from SchemaLoader for consistency
    """
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    indexed: bool = False
    unique: bool = False
    default: Optional[Any] = None
    extra: Optional[str] = None


class BaseSourceConnector(ABC):
    """
    Abstract base class for source connectors
    
    Every source connector (MySQL, Postgres, S3, etc.) must implement this interface.
    
    DATA FORMAT:
        All connectors return data as List[Dict[str, Any]] - pure Python!
        [
            {"id": 1, "name": "Alice", "created_at": datetime(...)},
            {"id": 2, "name": "Bob", "created_at": datetime(...)},
        ]
    
    Lifecycle:
        1. __init__() - Initialize with config
        2. validate() - Check connection and permissions
        3. get_schema() - Discover table schema
        4. extract_data() - Stream data in batches
        5. close() - Clean up resources
    
    Usage:
        with MySQLSourceConnector(context, config) as connector:
            connector.validate()
            schema = connector.get_schema()
            
            for batch in connector.extract_data(columns=["id", "name"]):
                # batch is List[Dict[str, Any]]
                process(batch)
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
        self._is_validated = False
        
        # Validate required config keys
        self._validate_config()
        
        logger.info(
            "source_connector_initialized",
            source_type=self.source_type(),
            database=config.get("database"),
            table=config.get("table")
        )
    
    def _validate_config(self):
        """Validate that required config keys are present"""
        required_keys = self.required_config_keys()
        missing_keys = [key for key in required_keys if key not in self.config]
        
        if missing_keys:
            raise SourceValidationError(
                f"Missing required config keys for {self.source_type()}: {missing_keys}"
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
    def required_config_keys(self) -> List[str]:
        """
        Return list of required configuration keys
        
        Returns:
            List of required keys, e.g., ["host", "database", "table", "user", "password"]
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
        - Required columns exist (if specified)
        
        Returns:
            True if valid
        
        Raises:
            SourceConnectionError: If connection fails
            SourceValidationError: If validation fails
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> List[ColumnSchema]:
        """
        Get schema of the source table
        
        Returns:
            List of ColumnSchema objects
        
        Example:
            [
                ColumnSchema(name="id", type="bigint", nullable=False, primary_key=True),
                ColumnSchema(name="name", type="varchar(255)", nullable=True),
                ...
            ]
        """
        pass
    
    @abstractmethod
    def extract_data(
        self,
        columns: Optional[List[str]] = None,
        batch_size: int = 10000,
        incremental_config: Optional[IncrementalConfig] = None
    ) -> Iterator[List[Dict[str, Any]]]:
        """
        Extract data from source in batches
        
        CRITICAL: Returns List[Dict[str, Any]] - NOT pandas DataFrame!
        
        Args:
            columns: Columns to extract (None = all columns)
            batch_size: Rows per batch
            incremental_config: For incremental extraction
        
        Yields:
            List of dictionaries per batch:
            [
                {"id": 1, "name": "Alice", ...},
                {"id": 2, "name": "Bob", ...},
            ]
        
        Raises:
            SourceExtractionError: If extraction fails
        
        Note:
            Must use streaming/cursor to avoid loading entire table in memory
        """
        pass
    
    @abstractmethod
    def get_row_count(
        self,
        where_clause: Optional[str] = None,
        where_params: Optional[List[Any]] = None
    ) -> int:
        """
        Get total row count from source
        
        Args:
            where_clause: Optional SQL WHERE clause (without "WHERE" keyword)
            where_params: Parameters for where_clause (for safe parameterization)
        
        Returns:
            Row count
        
        Example:
            count = connector.get_row_count(
                where_clause="updated_at > %s",
                where_params=["2024-01-01"]
            )
        """
        pass
    
    def get_max_value(
        self,
        column: str
    ) -> Optional[Any]:
        """
        Get maximum value of a column (useful for incremental extraction)
        
        Args:
            column: Column name
        
        Returns:
            Maximum value or None if no data
        
        Note:
            Override if source supports more efficient implementation
        """
        # Default implementation - sources can override for better performance
        raise NotImplementedError(
            f"{self.source_type()} connector does not implement get_max_value(). "
            f"Override this method for better incremental extraction support."
        )
    
    def test_query(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a test query (useful for debugging)
        
        Args:
            query: SQL query or equivalent
            params: Query parameters
        
        Returns:
            Query results as list of dicts
        
        Note:
            Override for database sources, raise NotImplementedError for others
        """
        raise NotImplementedError(
            f"{self.source_type()} connector does not support test_query()"
        )
    
    def close(self) -> None:
        """
        Clean up resources (connections, file handles, etc.)
        
        Should be idempotent - safe to call multiple times
        """
        if self._connection:
            try:
                self._connection.close()
                self._connection = None
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
        """Context manager support - ensures cleanup"""
        self.close()
        return False  # Don't suppress exceptions
    
    def __del__(self):
        """Destructor - ensures cleanup even if context manager not used"""
        try:
            self.close()
        except Exception:
            pass  # Ignore errors in destructor