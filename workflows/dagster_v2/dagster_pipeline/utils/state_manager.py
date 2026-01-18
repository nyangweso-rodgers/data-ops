"""
State management for incremental ETL syncs using Dagster's built-in kvs table

Enhanced Features:
- Explicit UTC timezone handling with warnings
- Type-safe serialization with enums
- Validation on save operations
- Flatter, more readable JSON structure
- Better monitoring capabilities
"""

from typing import Dict, Any, Optional, Union
from datetime import datetime, date, timezone
from decimal import Decimal
from enum import Enum
import json
from dagster import AssetExecutionContext
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class StateValueType(str, Enum):
    """Supported types for state values"""
    DATETIME = "datetime"
    DATE = "date"
    DECIMAL = "decimal"
    INTEGER = "int"
    FLOAT = "float"
    STRING = "str"
    NULL = "null"


# Type alias for supported state values
StateValue = Union[datetime, date, Decimal, int, float, str, None]


class StateManager:
    """
    Manages incremental ETL state using Dagster's kvs table
    
    The kvs table is automatically created by Dagster and has structure:
        CREATE TABLE kvs (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    
    Storage Format (Flattened for Readability):
    {
        "version": "1.0",
        "last_value": "2025-11-18T19:13:21+00:00",  # ISO string, not nested JSON
        "last_value_type": "datetime",               # Explicit type
        "incremental_key": "updatedAt",
        "source_type": "mysql",
        "source_database": "sales-service",
        "source_table": "forms",
        "synced_at": "2026-01-05T09:19:20.226586+00:00",
        "synced_at_type": "datetime",
        "metadata": {
            "rows_synced": 6,
            "asset_name": "mysql_sales_service_forms_to_clickhouse"
        }
    }
    
    Usage:
        # Save state after sync
        StateManager.save_incremental_state(
            context,
            dagster_postgres_resource,
            source_type="mysql",
            source_database="amt",
            source_table="accounts",
            incremental_key="updated_at",
            last_value=datetime(2024, 12, 6, 10, 30, 0, tzinfo=timezone.utc)
        )
        
        # Load state for next sync
        state = StateManager.load_incremental_state(
            context,
            dagster_postgres_resource,
            source_type="mysql",
            source_database="amt",
            source_table="accounts"
        )
    """
    
    # Key prefix for all ETL states
    STATE_PREFIX = "etl_sync_state"
    STATE_VERSION = "1.0"
    
    @staticmethod
    def _get_state_key(source_type: str, source_database: str, source_table: str) -> str:
        """
        Generate unique key for kvs table
        
        Format: etl_sync_state:mysql:amt:accounts
        """
        return f"{StateManager.STATE_PREFIX}:{source_type}:{source_database}:{source_table}"
    
    @staticmethod
    def _validate_value_type(value: Any) -> None:
        """
        Validate that value is a supported type
        
        Raises:
            TypeError: If value type is not supported
        """
        if value is None:
            return
        
        supported_types = (datetime, date, Decimal, int, float, str)
        if not isinstance(value, supported_types):
            raise TypeError(
                f"Unsupported state value type: {type(value).__name__}. "
                f"Supported types: datetime, date, Decimal, int, float, str, None"
            )
    
    @staticmethod
    def _ensure_utc_datetime(dt: datetime) -> datetime:
        """
        Ensure datetime has UTC timezone info
        
        Args:
            dt: Datetime object (naive or aware)
        
        Returns:
            Timezone-aware datetime in UTC
        
        Raises:
            ValueError: If datetime is timezone-aware but not UTC
        """
        if dt.tzinfo is None:
            # Naive datetime - assume UTC and warn
            logger.warning(
                "naive_datetime_converted_to_utc",
                datetime_str=str(dt),
                message="Naive datetime assumed to be UTC. Consider passing timezone-aware datetimes."
            )
            return dt.replace(tzinfo=timezone.utc)
        
        # Already timezone-aware - convert to UTC if needed
        if dt.tzinfo != timezone.utc:
            logger.info(
                "datetime_converted_to_utc",
                original_timezone=str(dt.tzinfo),
                message="Converting datetime to UTC for storage"
            )
            return dt.astimezone(timezone.utc)
        
        return dt
    
    @staticmethod
    def _serialize_value(value: StateValue) -> tuple[str, StateValueType]:
        """
        Serialize value to string with explicit type
        
        Returns:
            Tuple of (serialized_value, value_type)
        
        Examples:
            datetime(2024, 1, 1, tzinfo=utc) -> ("2024-01-01T00:00:00+00:00", StateValueType.DATETIME)
            42 -> ("42", StateValueType.INTEGER)
            None -> ("null", StateValueType.NULL)
        """
        if value is None:
            return ("null", StateValueType.NULL)
        
        if isinstance(value, datetime):
            # Ensure UTC timezone
            value = StateManager._ensure_utc_datetime(value)
            return (value.isoformat(), StateValueType.DATETIME)
        
        elif isinstance(value, date):
            return (value.isoformat(), StateValueType.DATE)
        
        elif isinstance(value, Decimal):
            return (str(value), StateValueType.DECIMAL)
        
        elif isinstance(value, bool):
            # Handle bool before int (bool is subclass of int)
            raise TypeError("Boolean values not supported. Use 0/1 or 'true'/'false' strings instead.")
        
        elif isinstance(value, int):
            return (str(value), StateValueType.INTEGER)
        
        elif isinstance(value, float):
            return (str(value), StateValueType.FLOAT)
        
        elif isinstance(value, str):
            return (value, StateValueType.STRING)
        
        else:
            raise TypeError(f"Unsupported type for serialization: {type(value).__name__}")
    
    @staticmethod
    def _deserialize_value(value_str: str, value_type: str) -> StateValue:
        """
        Deserialize value from string using explicit type
        
        Args:
            value_str: Serialized value
            value_type: Type identifier (from StateValueType)
        
        Returns:
            Deserialized value with correct type
        """
        try:
            value_type_enum = StateValueType(value_type)
        except ValueError:
            logger.warning(
                "unknown_value_type",
                type=value_type,
                message="Unknown type, treating as string"
            )
            return value_str
        
        if value_type_enum == StateValueType.NULL:
            return None
        
        elif value_type_enum == StateValueType.DATETIME:
            dt = datetime.fromisoformat(value_str)
            # Ensure UTC (should already be, but double-check)
            return StateManager._ensure_utc_datetime(dt)
        
        elif value_type_enum == StateValueType.DATE:
            return datetime.strptime(value_str, '%Y-%m-%d').date()
        
        elif value_type_enum == StateValueType.DECIMAL:
            return Decimal(value_str)
        
        elif value_type_enum == StateValueType.INTEGER:
            return int(value_str)
        
        elif value_type_enum == StateValueType.FLOAT:
            return float(value_str)
        
        elif value_type_enum == StateValueType.STRING:
            return value_str
        
        else:
            logger.warning(
                "unhandled_value_type",
                type=value_type,
                message="Unhandled type, returning as string"
            )
            return value_str

    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def load_incremental_state(
        context: AssetExecutionContext,
        dagster_postgres_resource,
        source_type: str,
        source_database: str,
        source_table: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load incremental state from Dagster's kvs table
        
        Args:
            context: Dagster asset execution context
            dagster_postgres_resource: Postgres resource for Dagster metadata DB
            source_type: "mysql" or "postgres"
            source_database: Database name (e.g., "amt")
            source_table: Table name (e.g., "accounts")
        
        Returns:
            State dict with keys:
                - last_value: Last synced value (typed, not string)
                - incremental_key: Column name used for incremental sync
                - source_type: Source type
                - source_database: Source database
                - source_table: Source table
                - synced_at: When this state was saved (datetime)
                - version: State format version
                - metadata: Additional metadata (optional)
            
            Returns None if no state exists (first run)
        
        Example:
            >>> state = StateManager.load_incremental_state(
            ...     context, postgres_resource, "mysql", "amt", "accounts"
            ... )
            >>> if state:
            ...     print(f"Last synced: {state['last_value']}")
            ...     # Last synced: 2024-12-06 10:30:00+00:00
        """
        key = StateManager._get_state_key(source_type, source_database, source_table)
        
        query = """
            SELECT value FROM kvs
            WHERE key = %s
        """
        
        try:
            with dagster_postgres_resource.get_connection() as conn:
                with conn.cursor() as cursor:
                    logger.debug(
                        "loading_state",
                        key=key
                    )
                    cursor.execute(query, (key,))
                    result = cursor.fetchone()
                    
                    if result is None:
                        logger.info(
                            "no_previous_state",
                            source_type=source_type,
                            database=source_database,
                            table=source_table,
                            message="First sync - no previous state"
                        )
                        return None
                    
                    # Parse JSON
                    raw_state = json.loads(result[0])
                    
                    # Validate state structure
                    if not StateManager._validate_state_structure(raw_state):
                        logger.error(
                            "invalid_state_structure",
                            key=key,
                            state_keys=list(raw_state.keys())
                        )
                        return None
                    
                    # Deserialize typed values
                    state = {
                        'version': raw_state.get('version', 'legacy'),
                        'incremental_key': raw_state.get('incremental_key') or raw_state.get('key'),  # Backward compat
                        'source_type': raw_state['source_type'],
                        'source_database': raw_state['source_database'],
                        'source_table': raw_state['source_table'],
                    }
                    
                    # Deserialize last_value
                    if 'last_value' in raw_state:
                        state['last_value'] = StateManager._deserialize_value(
                            raw_state['last_value'],
                            raw_state.get('last_value_type', StateValueType.STRING)
                        )
                    
                    # Deserialize synced_at
                    if 'synced_at' in raw_state:
                        state['synced_at'] = StateManager._deserialize_value(
                            raw_state['synced_at'],
                            raw_state.get('synced_at_type', StateValueType.DATETIME)
                        )
                    
                    # Include metadata if present
                    if 'metadata' in raw_state:
                        state['metadata'] = raw_state['metadata']
                    
                    logger.info(
                        "state_loaded",
                        source_type=source_type,
                        database=source_database,
                        table=source_table,
                        last_value=state.get('last_value'),
                        incremental_key=state.get('incremental_key'),
                        version=state.get('version', 'legacy')
                    )
                    
                    return state
                    
        except json.JSONDecodeError as e:
            logger.error(
                "state_parse_error",
                key=key,
                error=str(e),
                message="Failed to parse state JSON"
            )
            return None
        except Exception as e:
            logger.error(
                "state_load_error",
                key=key,
                error=str(e),
                error_type=type(e).__name__
            )
            return None
    
    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def save_incremental_state(
        context: AssetExecutionContext,
        dagster_postgres_resource,
        source_type: str,
        source_database: str,
        source_table: str,
        incremental_key: str,
        last_value: StateValue,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save incremental state to Dagster's kvs table
        
        Args:
            context: Dagster asset execution context
            dagster_postgres_resource: Postgres resource for Dagster metadata DB
            source_type: "mysql" or "postgres"
            source_database: Database name
            source_table: Table name
            incremental_key: Column used for incremental sync (e.g., "updated_at")
            last_value: Last synced value (datetime, int, etc.) - must be timezone-aware for datetime
            additional_metadata: Extra metadata to store (optional)
        
        Returns:
            True if successful, False otherwise
        
        Raises:
            TypeError: If last_value is not a supported type
        
        Example:
            >>> success = StateManager.save_incremental_state(
            ...     context,
            ...     postgres_resource,
            ...     source_type="mysql",
            ...     source_database="amt",
            ...     source_table="accounts",
            ...     incremental_key="updated_at",
            ...     last_value=datetime(2024, 12, 6, 10, 30, 0, tzinfo=timezone.utc),
            ...     additional_metadata={"rows_synced": 1500}
            ... )
        """
        # Validate value type
        StateManager._validate_value_type(last_value)
        
        key = StateManager._get_state_key(source_type, source_database, source_table)
        
        # Serialize values with explicit types
        last_value_str, last_value_type = StateManager._serialize_value(last_value)
        synced_at = datetime.now(timezone.utc)
        synced_at_str, synced_at_type = StateManager._serialize_value(synced_at)
        
        # Build flattened state dictionary (no nested JSON!)
        state = {
            'version': StateManager.STATE_VERSION,
            'last_value': last_value_str,
            'last_value_type': last_value_type.value,
            'incremental_key': incremental_key,
            'source_type': source_type,
            'source_database': source_database,
            'source_table': source_table,
            'synced_at': synced_at_str,
            'synced_at_type': synced_at_type.value,
        }
        
        # Add additional metadata if provided
        if additional_metadata:
            state['metadata'] = additional_metadata
        
        state_json = json.dumps(state, indent=2)  # Pretty-print for readability
        
        # Upsert into kvs table
        upsert_query = """
            INSERT INTO kvs (key, value)
            VALUES (%s, %s)
            ON CONFLICT (key)
            DO UPDATE SET value = EXCLUDED.value
        """
        
        try:
            with dagster_postgres_resource.get_connection() as conn:
                with conn.cursor() as cursor:
                    logger.debug(
                        "saving_state",
                        key=key,
                        last_value=last_value,
                        last_value_type=last_value_type.value
                    )
                    cursor.execute(upsert_query, (key, state_json))
                    conn.commit()
                    
                    logger.info(
                        "state_saved",
                        source_type=source_type,
                        database=source_database,
                        table=source_table,
                        incremental_key=incremental_key,
                        last_value=last_value,
                        metadata=additional_metadata
                    )
                    
                    return True
                    
        except Exception as e:
            logger.error(
                "state_save_error",
                key=key,
                error=str(e),
                error_type=type(e).__name__
            )
            return False
    
    @staticmethod
    def _validate_state_structure(state: Dict[str, Any]) -> bool:
        """
        Validate that state has required fields
        
        Args:
            state: State dictionary to validate
        
        Returns:
            True if valid, False otherwise
        """
        # Support both old 'key' and new 'incremental_key' field names
        required_fields = ['last_value', 'source_type', 'source_database', 'source_table']
        missing_fields = [field for field in required_fields if field not in state]
        
        # Check for incremental_key (or legacy 'key' field)
        if 'incremental_key' not in state and 'key' not in state:
            missing_fields.append('incremental_key')
        
        if missing_fields:
            logger.warning(
                "invalid_state_missing_fields",
                missing=missing_fields,
                present=list(state.keys())
            )
            return False
        
        return True
    
    @staticmethod
    def is_first_run(
        context: AssetExecutionContext,
        dagster_postgres_resource,
        source_type: str,
        source_database: str,
        source_table: str
    ) -> bool:
        """
        Check if this is the first run (no state exists)
        
        Returns:
            True if no state exists (first run or cleared), False otherwise
        
        Example:
            >>> if StateManager.is_first_run(context, postgres_resource, 
            ...                               "mysql", "amt", "accounts"):
            ...     print("Performing full refresh")
            ... else:
            ...     print("Performing incremental sync")
        """
        state = StateManager.load_incremental_state(
            context, dagster_postgres_resource, 
            source_type, source_database, source_table
        )
        return state is None
    
    @staticmethod
    def clear_incremental_state(
        context: AssetExecutionContext,
        dagster_postgres_resource,
        source_type: str,
        source_database: str,
        source_table: str
    ) -> bool:
        """
        Clear state for a table (triggers full refresh on next sync)
        
        Use cases:
        - Force full refresh
        - Data quality issue requires re-sync
        - Schema change requires reload
        
        Returns:
            True if successful, False otherwise
        
        Example:
            >>> # Force full refresh of accounts table
            >>> StateManager.clear_incremental_state(
            ...     context, postgres_resource, "mysql", "amt", "accounts"
            ... )
        """
        key = StateManager._get_state_key(source_type, source_database, source_table)
        
        delete_query = """
            DELETE FROM kvs WHERE key = %s
        """
        
        try:
            with dagster_postgres_resource.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(delete_query, (key,))
                    rows_deleted = cursor.rowcount
                    conn.commit()
                    
                    if rows_deleted > 0:
                        logger.info(
                            "state_cleared",
                            source_type=source_type,
                            database=source_database,
                            table=source_table,
                            message="State cleared - next sync will be full refresh"
                        )
                    else:
                        logger.warning(
                            "state_not_found",
                            source_type=source_type,
                            database=source_database,
                            table=source_table,
                            message="No state to clear"
                        )
                    
                    return True
                    
        except Exception as e:
            logger.error(
                "state_clear_error",
                key=key,
                error=str(e),
                error_type=type(e).__name__
            )
            return False
    
    @staticmethod
    def get_all_states(
        context: AssetExecutionContext,
        dagster_postgres_resource,
        source_type: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get all ETL sync states (for monitoring/debugging)
        
        Args:
            context: Dagster context
            dagster_postgres_resource: Postgres resource
            source_type: Filter by source type (optional)
        
        Returns:
            Dictionary mapping table keys to their states
        
        Example:
            >>> states = StateManager.get_all_states(context, postgres_resource)
            >>> for key, state in states.items():
            ...     print(f"{key}: last synced {state['last_value']}")
            
            >>> # Filter by source type
            >>> mysql_states = StateManager.get_all_states(
            ...     context, postgres_resource, source_type="mysql"
            ... )
        """
        pattern = f"{StateManager.STATE_PREFIX}:{source_type}:%" if source_type else f"{StateManager.STATE_PREFIX}:%"
        query = """
            SELECT key, value FROM kvs
            WHERE key LIKE %s
            ORDER BY key
        """
        
        try:
            with dagster_postgres_resource.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (pattern,))
                    rows = cursor.fetchall()
                    
                    states = {}
                    for row in rows:
                        key = row[0]
                        try:
                            raw_state = json.loads(row[1])
                            
                            # Deserialize typed values
                            state = dict(raw_state)  # Copy
                            
                            if 'last_value' in raw_state:
                                state['last_value'] = StateManager._deserialize_value(
                                    raw_state['last_value'],
                                    raw_state.get('last_value_type', StateValueType.STRING)
                                )
                            
                            if 'synced_at' in raw_state:
                                state['synced_at'] = StateManager._deserialize_value(
                                    raw_state['synced_at'],
                                    raw_state.get('synced_at_type', StateValueType.DATETIME)
                                )
                            
                            states[key] = state
                        except json.JSONDecodeError:
                            logger.warning(
                                "state_parse_error",
                                key=key,
                                message="Failed to parse state"
                            )
                    
                    logger.info(
                        "states_retrieved",
                        count=len(states),
                        source_type=source_type
                    )
                    
                    return states
                    
        except Exception as e:
            logger.error(
                "get_all_states_error",
                error=str(e),
                error_type=type(e).__name__
            )
            return {}
    
    @staticmethod
    def get_state_summary(
        context: AssetExecutionContext,
        dagster_postgres_resource,
        stale_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get summary statistics of all ETL states
        
        Args:
            stale_hours: Hours after which a sync is considered stale
        
        Returns:
            {
                "total_tables": 60,
                "by_source": {"mysql": 35, "postgres": 25},
                "oldest_sync": datetime(...),
                "newest_sync": datetime(...),
                "stale_tables": [...],  # Tables not synced in stale_hours
                "tables": [...]
            }
        """
        states = StateManager.get_all_states(context, dagster_postgres_resource)
        
        if not states:
            return {
                "total_tables": 0,
                "by_source": {},
                "tables": [],
                "stale_tables": []
            }
        
        # Analyze states
        by_source = {}
        sync_times = []
        stale_tables = []
        now = datetime.now(timezone.utc)
        
        for key, state in states.items():
            source_type = state.get('source_type', 'unknown')
            by_source[source_type] = by_source.get(source_type, 0) + 1
            
            if 'synced_at' in state and isinstance(state['synced_at'], datetime):
                sync_time = state['synced_at']
                sync_times.append(sync_time)
                
                # Check for stale syncs
                age_hours = (now - sync_time).total_seconds() / 3600
                if age_hours > stale_hours:
                    stale_tables.append({
                        'key': key,
                        'last_sync': sync_time,
                        'age_hours': round(age_hours, 1)
                    })
        
        summary = {
            "total_tables": len(states),
            "by_source": by_source,
            "tables": list(states.keys()),
            "stale_tables": stale_tables,
            "stale_threshold_hours": stale_hours
        }
        
        if sync_times:
            summary["oldest_sync"] = min(sync_times)
            summary["newest_sync"] = max(sync_times)
            summary["avg_age_hours"] = round(
                sum((now - t).total_seconds() / 3600 for t in sync_times) / len(sync_times),
                1
            )
        
        return summary
    
    @staticmethod
    def get_incremental_filter_sql(
        state: Optional[Dict[str, Any]],
        incremental_column: str,
        table_alias: Optional[str] = None
    ) -> str:
        """
        Generate SQL WHERE clause for incremental sync
        
        Args:
            state: State dict from load_incremental_state (or None for full refresh)
            incremental_column: Column name to filter on
            table_alias: Optional table alias (e.g., "t" for "t.updated_at")
        
        Returns:
            SQL WHERE clause string
        
        Example:
            >>> state = StateManager.load_incremental_state(...)
            >>> where_clause = StateManager.get_incremental_filter_sql(
            ...     state, "updated_at", table_alias="t"
            ... )
            >>> query = f"SELECT * FROM accounts t WHERE {where_clause}"
            # "SELECT * FROM accounts t WHERE t.updated_at > '2024-12-06T10:30:00+00:00'"
        """
        if state is None:
            return "1=1"  # Full refresh - no filter
        
        last_value = state.get('last_value')
        if last_value is None:
            return "1=1"
        
        # Add table alias if provided
        column = f"{table_alias}.{incremental_column}" if table_alias else incremental_column
        
        # Generate appropriate SQL based on type
        if isinstance(last_value, datetime):
            # Use ISO format for timestamps
            return f"{column} > '{last_value.isoformat()}'"
        
        elif isinstance(last_value, date):
            return f"{column} > '{last_value.isoformat()}'"
        
        elif isinstance(last_value, str):
            # Escape single quotes in string values
            escaped_value = last_value.replace("'", "''")
            return f"{column} > '{escaped_value}'"
        
        elif isinstance(last_value, (int, float, Decimal)):
            return f"{column} > {last_value}"
        
        else:
            logger.warning(
                "unsupported_filter_type",
                type=type(last_value).__name__,
                message="Falling back to full refresh"
            )
            return "1=1"
    
    @staticmethod
    def reset_all_states(
        context: AssetExecutionContext,
        dagster_postgres_resource,
        source_type: Optional[str] = None,
        confirm: bool = False
    ) -> int:
        """
        DANGEROUS: Clear all ETL states (forces full refresh of all tables)
        
        Args:
            confirm: Must be True to execute (safety check)
            source_type: Only clear specific source type (optional)
        
        Returns:
            Number of states cleared
        
        Example:
            >>> # Clear all MySQL states
            >>> count = StateManager.reset_all_states(
            ...     context,
            ...     postgres_resource,
            ...     source_type="mysql",
            ...     confirm=True
            ... )
            >>> print(f"Cleared {count} states")
        """
        if not confirm:
            logger.warning(
                "reset_not_confirmed",
                message="reset_all_states requires confirm=True"
            )
            return 0
        
        pattern = f"{StateManager.STATE_PREFIX}:{source_type}:%" if source_type else f"{StateManager.STATE_PREFIX}:%"
        delete_query = """
            DELETE FROM kvs WHERE key LIKE %s
        """
        
        try:
            with dagster_postgres_resource.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(delete_query, (pattern,))
                    rows_deleted = cursor.rowcount
                    conn.commit()
                    
                    logger.warning(
                        "all_states_reset",
                        count=rows_deleted,
                        source_type=source_type,
                        message=f"RESET {rows_deleted} ETL states - full refresh will occur"
                    )
                    
                    return rows_deleted
                    
        except Exception as e:
            logger.error(
                "reset_all_states_error",
                error=str(e),
                error_type=type(e).__name__
            )
            return 0
    
    @staticmethod
    def validate_state_freshness(
        state: Dict[str, Any],
        max_age_hours: int = 24
    ) -> bool:
        """
        Check if state is not too old (for monitoring)
        
        Args:
            state: State dict from load_incremental_state
            max_age_hours: Maximum acceptable age in hours
        
        Returns:
            True if state is fresh, False if stale or missing synced_at
        
        Example:
            >>> state = StateManager.load_incremental_state(...)
            >>> if not StateManager.validate_state_freshness(state, max_age_hours=12):
            ...     logger.warning("State is stale, may need to investigate")
        """
        if 'synced_at' not in state:
            return True  # No timestamp, can't validate
        
        synced_at = state['synced_at']
        if not isinstance(synced_at, datetime):
            return True  # Invalid type, can't validate
        
        age = datetime.now(timezone.utc) - synced_at
        age_hours = age.total_seconds() / 3600
        
        return age_hours < max_age_hours


# Convenience function for backward compatibility
def needs_full_refresh(*args, **kwargs) -> bool:
    """
    DEPRECATED: Use is_first_run() instead
    
    This function is kept for backward compatibility but will be removed in future versions.
    """
    logger.warning(
        "deprecated_function",
        message="needs_full_refresh() is deprecated, use is_first_run() instead"
    )
    return StateManager.is_first_run(*args, **kwargs)