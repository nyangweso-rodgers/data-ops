# dagster_pipeline/connectors/destinations/clickhouse_destination.py
"""
ClickHouse destination connector for data loading

Supports:
- Table creation with various engines (MergeTree, ReplacingMergeTree, etc.)
- Batch inserts (append mode)
- Upserts via ReplacingMergeTree
- Schema synchronization (adding new columns)
- Optimized for ClickHouse-specific features
- Sanitized logging (no connection strings)
"""

import clickhouse_connect
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from .base_destination import BaseDestinationConnector
import structlog

logger = structlog.get_logger(__name__)


class ClickHouseDestinationConnector(BaseDestinationConnector):
    """
    ClickHouse destination connector
    
    Features:
    - Native ClickHouse protocol via clickhouse-connect
    - Support for various table engines
    - Batch inserts with configurable batch size
    - Automatic type mapping
    - Column addition for schema evolution
    - Native Python type handling (no numpy)
    
    Config:
        {
            "host": "clickhouse.example.com",
            "port": 8123,  # HTTP port (9000 for native)
            "user": "default",
            "password": "password",
            "database": "analytics",  # Default database
            "secure": False,  # Use HTTPS/TLS
            "verify": True,  # Verify SSL certificate
            "settings": {  # Optional ClickHouse settings
                "max_insert_block_size": 100000,
                "max_execution_time": 300
            }
        }
    
    Example:
        >>> config = {...}
        >>> with ClickHouseDestinationConnector(context, config) as dest:
        ...     dest.validate()
        ...     
        ...     if not dest.table_exists("analytics", "accounts"):
        ...         dest.create_table(
        ...             "analytics", "accounts", schema,
        ...             engine="ReplacingMergeTree",
        ...             order_by=["id"]
        ...         )
        ...     
        ...     rows = dest.load_data("analytics", "accounts", df, mode="append")
        ...     print(f"Loaded {rows} rows")
    """
    
    def __init__(
        self,
        context,
        config: Dict[str, Any]
    ):
        """Initialize ClickHouse destination connector"""
        super().__init__(context, config)
        
        # Extract connection parameters
        self.host = config["host"]
        self.port = config.get("port", 8123)
        self.user = config.get("user", "default")
        self.password = config.get("password", "")
        self.database = config.get("database", "default")
        self.secure = config.get("secure", False)
        self.verify = config.get("verify", True)
        self.settings = config.get("settings", {})
        
        # Connection pool (lazy initialization)
        self._client = None
    
    def destination_type(self) -> str:
        return "clickhouse"
    
    def _get_client(self):
        """Get or create ClickHouse client (lazy initialization)"""
        if self._client is None:
            try:
                self._client = clickhouse_connect.get_client(
                    host=self.host,
                    port=self.port,
                    username=self.user,
                    password=self.password,
                    database=self.database,
                    secure=self.secure,
                    verify=self.verify,
                    settings=self.settings
                )
                
                logger.debug(
                    "clickhouse_client_created",
                    database=self.database,
                    host="****",  # Sanitized
                    port=self.port
                )
            except Exception as e:
                logger.error(
                    "clickhouse_client_creation_failed",
                    error=str(e)
                )
                raise ConnectionError(f"Failed to connect to ClickHouse: {e}")
        
        return self._client
    
    def validate(self) -> bool:
        """Validate ClickHouse connection"""
        try:
            client = self._get_client()
            
            # Test connection with simple query
            result = client.query("SELECT 1")
            
            # Check database exists
            databases_query = "SHOW DATABASES"
            databases = client.query(databases_query)
            db_list = [row[0] for row in databases.result_rows]
            
            if self.database not in db_list:
                logger.warning(
                    "clickhouse_database_not_found",
                    database=self.database
                )
                # Database doesn't exist, but connection works
                # We can create it if needed
            
            logger.info(
                "clickhouse_destination_validated",
                database=self.database,
                host="****"  # Sanitized
            )
            return True
            
        except Exception as e:
            logger.error(
                "clickhouse_validation_failed",
                database=self.database,
                error=str(e)
            )
            raise ConnectionError(f"ClickHouse validation failed: {e}")
    
    def table_exists(self, database: str, table: str) -> bool:
        """Check if table exists in ClickHouse"""
        client = self._get_client()
        
        query = """
            SELECT count() as cnt
            FROM system.tables
            WHERE database = %(database)s AND name = %(table)s
        """
        
        result = client.query(
            query,
            parameters={"database": database, "table": table}
        )
        
        exists = result.result_rows[0][0] > 0
        
        logger.debug(
            "clickhouse_table_exists_check",
            database=database,
            table=table,
            exists=exists
        )
        
        return exists
    
    def _ensure_sync_at_column(self, database: str, table: str) -> None:
        """Ensure sync_at column exists with proper default"""
        client = self._get_client()
        
        # Check if sync_at already exists
        result = client.query(
            "SELECT name, type, default_expression FROM system.columns "
            "WHERE database = %(db)s AND table = %(tbl)s AND name = 'sync_at'",
            parameters={"db": database, "tbl": table}
        )
        
        if result.result_rows:
            logger.debug("sync_at_column_exists", database=database, table=table)
            return
        
        # Add sync_at with high precision and default = now64()
        alter_query = f"""
            ALTER TABLE `{database}`.`{table}`
            ADD COLUMN `sync_at` DateTime64(3) DEFAULT now64(3)
        """
        try:
            client.command(alter_query)
            logger.info("sync_at_column_added", database=database, table=table)
        except Exception as e:
            if "column already exists" not in str(e).lower():
                logger.warning("sync_at_add_failed", database=database, table=table, error=str(e))
    
    def create_table(
        self,
        database: str,
        table: str,
        schema: List[Dict[str, Any]],
        **options
    ) -> None:
        """
        Create ClickHouse table
        
        Args:
            database: Database name
            table: Table name
            schema: List of column definitions with ClickHouse types:
                [
                    {
                        "name": "id",
                        "destination_type": "Int64",  # ClickHouse type
                        "nullable": False,
                        "primary_key": True
                    },
                    ...
                ]
            **options: ClickHouse-specific options:
                - engine: Table engine (default: "MergeTree")
                - order_by: List of columns for ORDER BY
                - partition_by: Partition expression
                - primary_key: List of primary key columns
                - ttl: TTL expression
                - settings: Table settings
        
        Supported Engines:
            - MergeTree: General purpose, fast inserts
            - ReplacingMergeTree: Deduplication by ORDER BY key
            - SummingMergeTree: Aggregate numeric columns
            - AggregatingMergeTree: Pre-aggregated data
        
        Example:
            >>> schema = [
            ...     {"name": "id", "destination_type": "Int64", "nullable": False},
            ...     {"name": "name", "destination_type": "String", "nullable": True},
            ...     {"name": "updated_at", "destination_type": "DateTime", "nullable": False}
            ... ]
            >>> dest.create_table(
            ...     "analytics", "accounts", schema,
            ...     engine="ReplacingMergeTree(updated_at)",  # Dedup by updated_at
            ...     order_by=["id"],
            ...     partition_by="toYYYYMM(updated_at)"
            ... )
        """
        client = self._get_client()
        
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
            
            # Note: ClickHouse Nullable is already in the type string
            # e.g., "Nullable(Int64)" or "Int64"
            column_defs.append(f"`{col_name}` {col_type}")
        
        columns_str = ",\n    ".join(column_defs)
        
        # Build ENGINE clause
        engine_clause = f"ENGINE = {engine}"
        
        # Build ORDER BY clause (required for MergeTree engines)
        if order_by:
            order_by_str = ", ".join(f"`{col}`" for col in order_by)
            order_by_clause = f"ORDER BY ({order_by_str})"
        else:
            # Use first column as default
            if schema:
                order_by_clause = f"ORDER BY `{schema[0]['name']}`"
            else:
                raise ValueError("ORDER BY is required for MergeTree engines")
        
        # Build PARTITION BY clause
        partition_clause = ""
        if partition_by:
            partition_clause = f"PARTITION BY {partition_by}"
        
        # Build PRIMARY KEY clause
        primary_key_clause = ""
        if primary_key:
            pk_str = ", ".join(f"`{col}`" for col in primary_key)
            primary_key_clause = f"PRIMARY KEY ({pk_str})"
        
        # Build TTL clause
        ttl_clause = ""
        if ttl:
            ttl_clause = f"TTL {ttl}"
        
        # Build SETTINGS clause
        settings_clause = ""
        if settings:
            settings_list = [f"{k} = {v}" for k, v in settings.items()]
            settings_clause = f"SETTINGS {', '.join(settings_list)}"
        
        # Build CREATE TABLE statement
        create_query = f"""
            CREATE TABLE `{database}`.`{table}` (
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
            client.command(create_query)
            
            # AUTOMATICALLY ADD sync_at AFTER table creation
            self._ensure_sync_at_column(database, table)
            
            logger.info(
                "clickhouse_table_created",
                database=database,
                table=table,
                engine=engine,
                columns=len(schema)
            )
        except Exception as e:
            logger.error(
                "clickhouse_table_creation_failed",
                database=database,
                table=table,
                error=str(e)
            )
            raise
    
    def load_data(
        self,
        database: str,
        table: str,
        data: List[Dict[str, Any]],  # Changed from pd.DataFrame
        mode: str = "append"
    ) -> int:
        """
        Load data to ClickHouse - accepts list of dictionaries
        
        Args:
            database: Database name
            table: Table name
            data: List of dictionaries [{"id": 1, "name": "Alice"}, ...]
            mode: "append", "replace", or "upsert"
        
        Returns:
            Number of rows loaded
        """
        if not data:
            logger.warning("clickhouse_empty_data", database=database, table=table)
            return 0

        client = self._get_client()

        if mode == "replace":
            logger.warning("clickhouse_replace_mode", database=database, table=table)
            client.command(f"TRUNCATE TABLE `{database}`.`{table}`")

        try:
            # Extract column names from first row
            column_names = list(data[0].keys())
            
            # Convert to row format: [[val1, val2, ...], [val1, val2, ...]]
            rows = [
                [row[col] for col in column_names]
                for row in data
            ]
            
            # ClickHouse insert - works perfectly with native Python types!
            client.insert(
                table=f"`{database}`.`{table}`",
                data=rows,
                column_names=column_names
            )
            
            rows_loaded = len(data)
            logger.info("clickhouse_data_loaded", database=database, table=table, 
                    rows=rows_loaded, mode=mode)
            return rows_loaded

        except Exception as e:
            logger.error("clickhouse_data_load_failed", database=database, table=table,
                        rows=len(data), error=str(e))
            raise   
    
    def sync_schema(
        self,
        database: str,
        table: str,
        schema: List[Dict[str, Any]]
    ) -> None:
        """
        Sync schema changes (add new columns)
        
        ClickHouse supports adding columns but NOT modifying/dropping
        in certain table engines.
        
        Args:
            database: Database name
            table: Table name
            schema: New schema (must include all columns)
        """
        client = self._get_client()
        
        # Get existing columns
        existing_query = f"""
            SELECT name, type
            FROM system.columns
            WHERE database = %(database)s AND table = %(table)s
        """
        
        result = client.query(
            existing_query,
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
        if new_columns:
            for col_name, col_type in new_columns:
                alter_query = f"""
                    ALTER TABLE `{database}`.`{table}`
                    ADD COLUMN `{col_name}` {col_type}
                """
                
                try:
                    client.command(alter_query)
                    logger.info(
                        "clickhouse_column_added",
                        database=database,
                        table=table,
                        column=col_name,
                        type=col_type
                    )
                except Exception as e:
                    logger.error(
                        "clickhouse_add_column_failed",
                        database=database,
                        table=table,
                        column=col_name,
                        error=str(e)
                    )
                    # Continue adding other columns even if one fails
        else:
            logger.debug(
                "clickhouse_schema_already_synced",
                database=database,
                table=table
            )
        self._ensure_sync_at_column(database, table)
    
    def get_row_count(self, database: str, table: str) -> int:
        """
        Get row count from ClickHouse table
        
        Note: For ReplacingMergeTree, this includes duplicates.
        Use COUNT() with FINAL for deduplicated count.
        """
        client = self._get_client()
        
        query = f"SELECT count() as cnt FROM `{database}`.`{table}`"
        
        result = client.query(query)
        count = result.result_rows[0][0]
        
        logger.debug(
            "clickhouse_row_count",
            database=database,
            table=table,
            count=count
        )
        
        return count
    
    def optimize_table(
        self,
        database: str,
        table: str,
        final: bool = False
    ) -> None:
        """
        Optimize ClickHouse table (force merge)
        
        Args:
            database: Database name
            table: Table name
            final: Use OPTIMIZE FINAL (aggressive merge, slower)
        
        Use cases:
            - After bulk inserts to trigger merges
            - For ReplacingMergeTree to deduplicate
            - To reduce number of parts
        
        Note:
            OPTIMIZE is asynchronous and may take time for large tables
        """
        client = self._get_client()
        
        final_clause = "FINAL" if final else ""
        query = f"OPTIMIZE TABLE `{database}`.`{table}` {final_clause}"
        
        try:
            client.command(query)
            logger.info(
                "clickhouse_table_optimized",
                database=database,
                table=table,
                final=final
            )
        except Exception as e:
            logger.warning(
                "clickhouse_optimize_failed",
                database=database,
                table=table,
                error=str(e)
            )
    
    def get_table_engine(self, database: str, table: str) -> str:
        """Get table engine type"""
        client = self._get_client()
        
        query = f"""
            SELECT engine
            FROM system.tables
            WHERE database = %(database)s AND name = %(table)s
        """
        
        result = client.query(
            query,
            parameters={"database": database, "table": table}
        )
        
        if result.result_rows:
            return result.result_rows[0][0]
        return "Unknown"
    
    def get_table_size(self, database: str, table: str) -> Dict[str, Any]:
        """
        Get table size statistics
        
        Returns:
            {
                "rows": 1000000,
                "bytes": 5242880,
                "bytes_human": "5.00 MB",
                "parts": 12,
                "compressed_bytes": 1048576
            }
        """
        client = self._get_client()
        
        query = f"""
            SELECT
                sum(rows) as rows,
                sum(bytes) as bytes,
                formatReadableSize(sum(bytes)) as bytes_human,
                count() as parts,
                sum(data_compressed_bytes) as compressed_bytes
            FROM system.parts
            WHERE database = %(database)s AND table = %(table)s AND active
        """
        
        result = client.query(
            query,
            parameters={"database": database, "table": table}
        )
        
        if result.result_rows:
            row = result.result_rows[0]
            return {
                "rows": row[0],
                "bytes": row[1],
                "bytes_human": row[2],
                "parts": row[3],
                "compressed_bytes": row[4]
            }
        return {}
    
    def close(self) -> None:
        """Close ClickHouse client"""
        if self._client:
            try:
                self._client.close()
                logger.debug("clickhouse_client_closed")
            except Exception as e:
                logger.warning(
                    "clickhouse_close_error",
                    error=str(e)
                )
            finally:
                self._client = None