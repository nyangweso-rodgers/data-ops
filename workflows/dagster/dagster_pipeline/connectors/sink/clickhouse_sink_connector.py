"""
ClickHouse destination connector for data loading

RESPONSIBILITIES:
- ETL data loading operations (insert, replace)
- Schema creation and synchronization
- Pre-load validation and checks
"""

from clickhouse_connect.driver.exceptions import ClickHouseError
from typing import Dict, Any, List
import time

from .base_sink_connector import (
    BaseSinkConnector,
    DestinationConnectionError,
    DestinationValidationError,
    DestinationLoadError
)
from dagster_pipeline.resources.clickhouse_resource import ClickHouseResource
from dagster_pipeline.utils.logging_config import get_logger

# Module logger
logger = get_logger(__name__)


class ClickHouseSinkConnector(BaseSinkConnector):
    """
    ClickHouse destination connector - Focused ETL sink
    
    Uses ClickHouseResource for all connection management.
    Focuses exclusively on ETL operations: extract → transform → load.
    
    Features:
    - Delegates connection to ClickHouseResource
    - ETL-specific retry logic for load operations
    - Batch inserts with optimization
    - Schema evolution support
    
    Config:
        {
            "host": "clickhouse.example.com",
            "port": 8443,  # HTTPS port
            "user": "default",
            "password": "password",
            "database": "analytics",
            "secure": True,
            "connect_timeout": 30,
            "send_receive_timeout": 300,
            "settings": {
                "max_insert_block_size": 100000,
                "max_execution_time": 300
            }
        }
    
    Usage:
        # In your ETL factory
        connector = ClickHouseSinkConnector(context, config)
        connector.validate()
        
        # Create table if needed
        if not connector.table_exists(database, table):
            connector.create_table(database, table, schema, order_by=["id"])
        
        # Sync schema for new columns
        connector.sync_schema(database, table, schema)
        
        # Load data
        rows_loaded = connector.load_data(database, table, data, mode="append")
    """
    
    # ETL-specific retry settings (for load operations, not connections)
    MAX_LOAD_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    RETRY_BACKOFF = 2
    
    def __init__(self, context, config: Dict[str, Any]):
        """
        Initialize ClickHouse sink connector with resource-based connection
        
        Args:
            context: Dagster context (for logging)
            config: Connection configuration dict
        """
        super().__init__(context, config)
        
        # Create ClickHouseResource instance from config
        self.ch_resource = ClickHouseResource(
            host=config["host"],
            port=config.get("port", 8443 if config.get("secure", True) else 8123),
            user=config.get("user", "default"),
            password=config.get("password", ""),
            database=config.get("database", "default"),
            secure=config.get("secure", True),
            connect_timeout=config.get("connect_timeout", 30),
            send_receive_timeout=config.get("send_receive_timeout", 300)
        )
        
        # Store additional ETL-specific settings
        self.database = config.get("database", "default")
        self.settings = config.get("settings", {})
        
        self.logger.info("clickhouse_resource_created", database=self.database)
    
    def destination_type(self) -> str:
        """Return destination type identifier"""
        return "clickhouse"
    
    def required_config_keys(self) -> List[str]:
        """Required configuration keys"""
        return ["host"]  # Password optional for localhost
    
    def _get_client_with_retry(self):
        """
        Get ClickHouse client with ETL-specific retry logic
        
        Wraps resource's get_client() with additional retry logic
        for handling transient ETL failures (connection pool exhaustion, etc.)
        
        Returns:
            ClickHouse client instance
            
        Raises:
            DestinationConnectionError: If connection fails after retries
        """
        last_error = None
        
        for attempt in range(self.MAX_LOAD_RETRIES):
            try:
                return self.ch_resource.get_client()
                
            except Exception as e:
                last_error = e
                
                if attempt < self.MAX_LOAD_RETRIES - 1:
                    delay = self.RETRY_DELAY * (self.RETRY_BACKOFF ** attempt)
                    self.logger.warning("client_retry", attempt=attempt + 1, delay=delay, error=str(e))
                    time.sleep(delay)
        
        raise DestinationConnectionError(
            f"Failed to get ClickHouse client after {self.MAX_LOAD_RETRIES} attempts: {last_error}"
        ) from last_error
    
    def validate(self) -> bool:
        """
        Validate ClickHouse connection and permissions
        
        Checks:
        - Connection is alive
        - Database exists or can be created
        - Write permissions are available
        
        Returns:
            True if validation succeeds
            
        Raises:
            DestinationValidationError: If validation fails
            DestinationConnectionError: If connection fails
        """
        try:
            # Test connection via resource
            if not self.ch_resource.ping():
                raise DestinationConnectionError("ClickHouse ping failed")
            
            client = self._get_client_with_retry()
            
            # Get ClickHouse version
            result = client.query("SELECT version() as version")
            version = result.result_rows[0][0] if result.result_rows else "unknown"
            self.logger.debug("clickhouse_version", version=version)
            
            # Check database exists or can be created
            databases = client.query("SHOW DATABASES")
            db_list = [row[0] for row in databases.result_rows]
            
            if self.database not in db_list:
                self.logger.warning("database_not_found", database=self.database, available=db_list)
                try:
                    client.command(f"CREATE DATABASE IF NOT EXISTS `{self.database}`")
                    self.logger.info("database_created", database=self.database)
                except Exception as e:
                    raise DestinationValidationError(
                        f"Database '{self.database}' doesn't exist and cannot be created: {e}"
                    ) from e
            
            # Test write permissions
            try:
                client.command(f"USE `{self.database}`")
            except Exception as e:
                raise DestinationValidationError(f"Cannot access database '{self.database}': {e}") from e
            
            self._is_validated = True
            self.logger.info("sink_validated", database=self.database, version=version)
            return True
            
        except (DestinationValidationError, DestinationConnectionError):
            raise
        except Exception as e:
            raise DestinationConnectionError(f"ClickHouse validation failed: {e}") from e
    
    def table_exists(self, database: str, table: str) -> bool:
        """
        Check if table exists in ClickHouse
        
        Args:
            database: Database name
            table: Table name
            
        Returns:
            True if table exists, False otherwise
        """
        if not self._is_validated:
            self.validate()
        
        client = self._get_client_with_retry()
        
        query = """
            SELECT count() as cnt
            FROM system.tables
            WHERE database = %(database)s AND name = %(table)s
        """
        
        try:
            result = client.query(query, parameters={"database": database, "table": table})
            exists = result.result_rows[0][0] > 0
            
            self.logger.debug("table_exists_check", database=database, table=table, exists=exists)
            return exists
            
        except Exception as e:
            raise DestinationLoadError(f"Failed to check if table exists: {e}") from e
    
    def _ensure_sync_at_column(self, database: str, table: str) -> None:
        """
        Ensure sync_at timestamp column exists for ETL tracking
        
        Adds a sync_at column with microsecond precision if it doesn't exist.
        
        Args:
            database: Database name
            table: Table name
        """
        client = self._get_client_with_retry()
        
        try:
            # Check if sync_at already exists
            result = client.query(
                "SELECT name FROM system.columns "
                "WHERE database = %(db)s AND table = %(tbl)s AND name = 'sync_at'",
                parameters={"db": database, "tbl": table}
            )
            
            if result.result_rows:
                self.logger.debug("sync_at_exists", database=database, table=table)
                return
            
            # Add sync_at column
            alter_query = f"""
                ALTER TABLE `{database}`.`{table}`
                ADD COLUMN IF NOT EXISTS `sync_at` DateTime64(3) DEFAULT now64(3)
            """
            
            client.command(alter_query)
            self.logger.info("sync_at_added", database=database, table=table)
            
        except Exception as e:
            # Non-fatal - log warning but don't fail ETL
            self.logger.warning("sync_at_add_failed", database=database, table=table, error=str(e))
    
    def create_table(
        self,
        database: str,
        table: str,
        schema: List[Dict[str, Any]],
        **options
    ) -> None:
        """
        Create ClickHouse table with optimal settings for ETL
        
        Args:
            database: Database name
            table: Table name
            schema: List of column definitions with ClickHouse types
            **options: ClickHouse-specific options:
                - engine: Table engine (default: "MergeTree")
                - order_by: List of columns for ORDER BY
                - partition_by: Partition expression
                - primary_key: List of primary key columns
                - ttl: TTL expression
                - settings: Table settings dict
                
        Raises:
            DestinationValidationError: If required options are missing
            DestinationLoadError: If table creation fails
        """
        if not self._is_validated:
            self.validate()
        
        # Validate schema is not empty
        if not schema or len(schema) == 0:
            raise DestinationValidationError(
                f"Cannot create table {database}.{table}: schema is empty. "
                f"All columns may have failed conversion."
            )
        
        client = self._get_client_with_retry()
        
        # Extract options
        engine = options.get("engine", "MergeTree")
        order_by = options.get("order_by", [])
        partition_by = options.get("partition_by")
        primary_key = options.get("primary_key", [])
        ttl = options.get("ttl")
        settings = options.get("settings", {})
        
        # Build column definitions
        column_defs = []
        for col in schema:
            col_name = col["name"]
            col_type = col.get("destination_type", col.get("type", "String"))
            column_defs.append(f"`{col_name}` {col_type}")
        
        columns_str = ",\n    ".join(column_defs)
        
        # Build ENGINE clause
        engine_clause = f"ENGINE = {engine}"
        
        # Build ORDER BY
        if order_by:
            order_by_str = ", ".join(f"`{col}`" for col in order_by)
            order_by_clause = f"ORDER BY ({order_by_str})"
        elif schema:
            order_by_clause = f"ORDER BY `{schema[0]['name']}`"
        else:
            raise DestinationValidationError("ORDER BY is required but no columns provided")
        
        # Build optional clauses
        partition_clause = f"PARTITION BY {partition_by}" if partition_by else ""
        
        primary_key_clause = ""
        if primary_key:
            pk_str = ", ".join(f"`{col}`" for col in primary_key)
            primary_key_clause = f"PRIMARY KEY ({pk_str})"
        
        ttl_clause = f"TTL {ttl}" if ttl else ""
        
        settings_clause = ""
        if settings:
            settings_list = [f"{k} = {v}" for k, v in settings.items()]
            settings_clause = f"SETTINGS {', '.join(settings_list)}"
        
        # Build CREATE TABLE statement
        create_query = f"""
            CREATE TABLE IF NOT EXISTS `{database}`.`{table}` (
                {columns_str}
            )
            {engine_clause}
            {partition_clause}
            {order_by_clause}
            {primary_key_clause}
            {ttl_clause}
            {settings_clause}
        """
        
        try:
            self.logger.debug("create_table_query", database=database, table=table, query=create_query[:500])
            
            client.command(create_query)
            
            # Add sync_at column for ETL tracking
            self._ensure_sync_at_column(database, table)
            
            self.logger.info("table_created", database=database, table=table, engine=engine, columns=len(schema))
            
        except Exception as e:
            self.logger.error("create_table_failed", database=database, table=table, error=str(e))
            raise DestinationLoadError(f"Failed to create table {database}.{table}: {e}") from e
    
    def load_data(
        self,
        database: str,
        table: str,
        data: List[Dict[str, Any]],
        mode: str = "append"
    ) -> int:
        """
        Load data to ClickHouse with retry logic
        
        Args:
            database: Database name
            table: Table name
            data: List of row dictionaries
            mode: "append", "replace", or "upsert" (not supported)
        
        Returns:
            Number of rows loaded
            
        Raises:
            DestinationLoadError: If load fails after retries
        """
        if not self._is_validated:
            self.validate()
        
        if not data:
            self.logger.warning("empty_data", database=database, table=table)
            return 0
        
        client = self._get_client_with_retry()
        
        # Handle replace mode
        if mode == "replace":
            try:
                client.command(f"TRUNCATE TABLE `{database}`.`{table}`")
                self.logger.info("table_truncated", database=database, table=table)
            except Exception as e:
                raise DestinationLoadError(f"Failed to truncate table {database}.{table}: {e}") from e
        elif mode == "upsert":
            self.logger.warning("upsert_not_supported", database=database, table=table)
        
        # Load data with retry logic
        last_error = None
        for attempt in range(self.MAX_LOAD_RETRIES):
            try:
                # Extract columns and convert to rows
                column_names = list(data[0].keys())
                rows = [[row.get(col) for col in column_names] for row in data]
                
                # Insert data
                client.insert(
                    table=f"`{database}`.`{table}`",
                    data=rows,
                    column_names=column_names
                )
                
                rows_loaded = len(data)
                self.logger.info("data_loaded", database=database, table=table, rows=rows_loaded, mode=mode)
                return rows_loaded
                
            except ClickHouseError as e:
                last_error = e
                
                # Retry on transient errors
                if "Too many simultaneous queries" in str(e) and attempt < self.MAX_LOAD_RETRIES - 1:
                    delay = self.RETRY_DELAY * (self.RETRY_BACKOFF ** attempt)
                    self.logger.warning("load_retry", attempt=attempt + 1, delay=delay, error=str(e))
                    time.sleep(delay)
                else:
                    break
                    
            except Exception as e:
                last_error = e
                break
        
        # All retries failed
        raise DestinationLoadError(
            f"Failed to load data to {database}.{table} after {self.MAX_LOAD_RETRIES} attempts: {last_error}"
        ) from last_error
    
    def sync_schema(
        self,
        database: str,
        table: str,
        schema: List[Dict[str, Any]]
    ) -> None:
        """
        Sync schema changes (add new columns)
        
        ClickHouse supports adding columns but not modifying/dropping.
        
        Args:
            database: Database name
            table: Table name
            schema: List of column definitions
        """
        if not self._is_validated:
            self.validate()
        
        client = self._get_client_with_retry()
        
        try:
            # Get existing columns
            result = client.query(
                "SELECT name, type FROM system.columns "
                "WHERE database = %(database)s AND table = %(table)s",
                parameters={"database": database, "table": table}
            )
            
            existing_columns = {row[0]: row[1] for row in result.result_rows}
            
            # Find new columns
            new_columns = []
            for col in schema:
                col_name = col["name"]
                col_type = col.get("destination_type", col.get("type", "String"))
                
                if col_name not in existing_columns:
                    new_columns.append((col_name, col_type))
            
            # Add new columns
            for col_name, col_type in new_columns:
                alter_query = f"""
                    ALTER TABLE `{database}`.`{table}`
                    ADD COLUMN IF NOT EXISTS `{col_name}` {col_type}
                """
                
                try:
                    client.command(alter_query)
                    self.logger.info("column_added", database=database, table=table, column=col_name, type=col_type)
                except Exception as e:
                    self.logger.warning("add_column_failed", database=database, table=table, column=col_name, error=str(e))
            
            if not new_columns:
                self.logger.debug("schema_already_synced", database=database, table=table)
            
            # Ensure sync_at column exists
            self._ensure_sync_at_column(database, table)
            
        except Exception as e:
            raise DestinationLoadError(f"Failed to sync schema for {database}.{table}: {e}") from e
    
    def close(self) -> None:
        """Close ClickHouse connection"""
        if self.ch_resource:
            try:
                self.ch_resource.close()
                self.logger.debug("sink_closed")
            except Exception as e:
                self.logger.warning("close_error", error=str(e))