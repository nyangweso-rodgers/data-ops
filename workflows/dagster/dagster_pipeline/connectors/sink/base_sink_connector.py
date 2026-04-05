"""
Abstract base class for all destination connectors

IMPROVEMENTS:
- No pandas dependency (uses List[Dict])
- Custom exception types
- Config validation
- Better type hints
- Consistent interface
- Centralized structured logging
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dagster import AssetExecutionContext
from dagster_pipeline.utils.logging_config import get_logger

logger = get_logger(__name__)


class DestinationConnectionError(Exception):
    """Raised when destination connection fails"""
    pass


class DestinationValidationError(Exception):
    """Raised when destination validation fails"""
    pass


class DestinationLoadError(Exception):
    """Raised when data loading fails"""
    pass


class BaseSinkConnector(ABC):
    """
    Abstract base class for destination connectors
    
    Every destination connector (ClickHouse, BigQuery, Snowflake) must implement this interface.
    
    DATA FORMAT:
        All connectors accept data as List[Dict[str, Any]] - pure Python!
        [
            {"id": 1, "name": "Alice", "created_at": datetime(...)},
            {"id": 2, "name": "Bob", "created_at": datetime(...)},
        ]
    
    Lifecycle:
        1. __init__() - Initialize with config
        2. validate() - Check connection and permissions
        3. table_exists() - Check if table exists
        4. create_table() - Create table if needed
        5. load_data() - Load data (insert/upsert)
        6. close() - Clean up
    
    Usage:
        with ClickHouseSinkConnector(context, config) as dest:
            dest.validate()
            
            if not dest.table_exists("analytics", "accounts"):
                dest.create_table("analytics", "accounts", schema)
            
            rows = dest.load_data("analytics", "accounts", data, mode="append")
            print(f"Loaded {rows} rows")
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
        self._is_validated = False
        
        # Create connector-specific logger
        self.logger = get_logger(
            self.__class__.__name__,
            context={
                "destination_type": self.destination_type(),
            }
        )
        
        # Validate required config keys
        self._validate_config()
        
        self.logger.info("connector_initialized")
    
    def _validate_config(self):
        """Validate that required config keys are present"""
        required_keys = self.required_config_keys()
        missing_keys = [key for key in required_keys if key not in self.config]
        
        if missing_keys:
            self.logger.error("config_validation_failed", missing_keys=missing_keys, required_keys=required_keys)
            raise DestinationValidationError(
                f"Missing required config keys for {self.destination_type()}: {missing_keys}"
            )
        
        self.logger.debug("config_validated", keys=list(self.config.keys()))
    
    @abstractmethod
    def destination_type(self) -> str:
        """
        Return destination type identifier
        
        Returns:
            "clickhouse", "bigquery", "snowflake", etc.
        """
        pass
    
    @abstractmethod
    def required_config_keys(self) -> List[str]:
        """
        Return list of required configuration keys
        
        Returns:
            List of required keys, e.g., ["host", "user", "password", "database"]
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """
        Validate destination connection and permissions
        
        Should check:
        - Connection can be established
        - Database exists (or can be created)
        - User has write permissions
        
        Returns:
            True if valid
        
        Raises:
            DestinationConnectionError: If connection fails
            DestinationValidationError: If validation fails
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
            True if exists, False otherwise
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
            schema: List of column definitions (destination types):
                [
                    {
                        "name": "id",
                        "destination_type": "Int64",
                        "nullable": False,
                        "primary_key": True
                    },
                    ...
                ]
            **options: Destination-specific options
                e.g., engine="MergeTree", order_by=["id"] for ClickHouse
        
        Raises:
            DestinationLoadError: If table creation fails
        """
        pass
    
    @abstractmethod
    def load_data(
        self,
        database: str,
        table: str,
        data: List[Dict[str, Any]],
        mode: str = "append"
    ) -> int:
        """
        Load data to destination
        
        CRITICAL: Accepts List[Dict[str, Any]] - NOT pandas DataFrame!
        
        Args:
            database: Database name
            table: Table name
            data: List of row dictionaries
            mode: "append", "replace", or "upsert"
        
        Returns:
            Number of rows loaded
        
        Raises:
            DestinationLoadError: If loading fails
        
        Example:
            >>> data = [
            ...     {"id": 1, "name": "Alice", "created_at": datetime.now()},
            ...     {"id": 2, "name": "Bob", "created_at": datetime.now()},
            ... ]
            >>> rows = dest.load_data("analytics", "users", data, mode="append")
            >>> print(f"Loaded {rows} rows")
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
        Sync schema changes (add new columns, modify types if supported)
        
        Args:
            database: Database name
            table: Table name
            schema: New schema (should include all columns)
        
        Note:
            Most destinations only support adding columns, not modifying/dropping.
            Override in subclass with destination-specific logic.
        """
        self.logger.warning("schema_sync_not_implemented")
    
    def get_row_count(self, database: str, table: str) -> int:
        """
        Get row count from table
        
        Optional to implement - useful for validation
        
        Args:
            database: Database name
            table: Table name
        
        Returns:
            Row count
        """
        self.logger.warning("get_row_count_not_implemented", database=database, table=table)
        raise NotImplementedError(
            f"{self.destination_type()} connector does not implement get_row_count()"
        )
    
    def close(self) -> None:
        """
        Clean up resources (connections, clients, etc.)
        
        Should be idempotent - safe to call multiple times
        """
        if self._connection:
            try:
                self._connection.close()
                self._connection = None
                self.logger.debug("connection_closed")
            except Exception as e:
                self.logger.warning("close_error", error=str(e))
    
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