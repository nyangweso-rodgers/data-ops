# dagster_pipeline/utils/state_manager.py
"""
State management for incremental ETL syncs using Dagster's built-in kvs table

Features:
- Tracks last synced value per table (timestamp, integer, etc.)
- No additional tables required (uses Dagster's kvs)
- Type-safe serialization/deserialization
- Supports full refresh (clear state)
- Monitoring capabilities
"""

from typing import Dict, Any, Optional, Union
from datetime import datetime, date
from decimal import Decimal
import json
from dagster import AssetExecutionContext
import structlog

logger = structlog.get_logger(__name__)


class StateManager:
    """
    Manages incremental ETL state using Dagster's kvs table
    
    The kvs table is automatically created by Dagster and has structure:
        CREATE TABLE kvs (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    
    Usage:
        # Save state after sync
        StateManager.save_incremental_state(
            context,
            dagster_postgres_resource,
            source_type="mysql",
            source_database="amt",
            source_table="accounts",
            incremental_key="updated_at",
            last_value=datetime(2024, 12, 6, 10, 30, 0)
        )
        
        # Load state for next sync
        state = StateManager.load_incremental_state(
            context,
            dagster_postgres_resource,
            source_type="mysql",
            source_database="amt",
            source_table="accounts"
        )
        # Returns: {'last_value': datetime(2024, 12, 6, 10, 30, 0), 'key': 'updated_at', ...}
    """
    
    # Key prefix for all ETL states
    STATE_PREFIX = "etl_sync_state"
    
    @staticmethod
    def _get_state_key(source_type: str, source_database: str, source_table: str) -> str:
        """
        Generate unique key for kvs table
        
        Format: etl_sync_state:mysql:amt:accounts
        """
        return f"{StateManager.STATE_PREFIX}:{source_type}:{source_database}:{source_table}"
    
    @staticmethod
    def _serialize_value(value: Any) -> str:
        """
        Serialize value to string for storage in kvs
        
        Handles:
        - datetime objects
        - date objects
        - Decimal objects
        - int, float, str
        - None
        """
        if value is None:
            return "null"
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, date):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return str(value)
        elif isinstance(value, (int, float, str)):
            return str(value)
        else:
            # Fallback to string representation
            logger.warning(
                "unsupported_type_serialization",
                type=type(value).__name__,
                value=str(value)
            )
            return str(value)
    
    @staticmethod
    def _deserialize_value(value_str: str, value_type: Optional[str] = None) -> Any:
        """
        Deserialize value from string
        
        Args:
            value_str: Serialized value
            value_type: Hint about original type (optional)
        
        Returns:
            Deserialized value (attempts to infer correct type)
        """
        if value_str == "null":
            return None
        
        # Try to infer type from string format
        # ISO datetime: 2024-12-06T10:30:00
        if 'T' in value_str and ':' in value_str:
            try:
                return datetime.fromisoformat(value_str)
            except ValueError:
                pass
        
        # ISO date: 2024-12-06
        if value_str.count('-') == 2 and 'T' not in value_str:
            try:
                return datetime.strptime(value_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Try integer
        if value_str.isdigit() or (value_str.startswith('-') and value_str[1:].isdigit()):
            return int(value_str)
        
        # Try float
        try:
            return float(value_str)
        except ValueError:
            pass
        
        # Return as string
        return value_str
    
    @staticmethod
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
                - key: Incremental key column name
                - source_type: Source type
                - source_database: Source database
                - source_table: Source table
                - synced_at: When this state was saved
            
            Returns None if no state exists (first run)
        
        Example:
            >>> state = StateManager.load_incremental_state(
            ...     context, postgres_resource, "mysql", "amt", "accounts"
            ... )
            >>> if state:
            ...     print(f"Last synced: {state['last_value']}")
            ...     # Last synced: 2024-12-06 10:30:00
        """
        key = StateManager._get_state_key(source_type, source_database, source_table)
        
        query = """
            SELECT value FROM kvs
            WHERE key = %s
        """
        
        try:
            with dagster_postgres_resource.get_connection() as conn:
                with conn.cursor() as cursor:
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
                    state = json.loads(result[0])
                    
                    # Deserialize last_value
                    if 'last_value' in state:
                        state['last_value'] = StateManager._deserialize_value(
                            state['last_value']
                        )
                    
                    # Convert synced_at if present
                    if 'synced_at' in state:
                        state['synced_at'] = StateManager._deserialize_value(
                            state['synced_at']
                        )
                    
                    logger.info(
                        "state_loaded",
                        source_type=source_type,
                        database=source_database,
                        table=source_table,
                        last_value=state.get('last_value'),
                        incremental_key=state.get('key')
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
    def save_incremental_state(
        context: AssetExecutionContext,
        dagster_postgres_resource,
        source_type: str,
        source_database: str,
        source_table: str,
        incremental_key: str,
        last_value: Any,
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
            last_value: Last synced value (datetime, int, etc.)
            additional_metadata: Extra metadata to store (optional)
        
        Returns:
            True if successful, False otherwise
        
        Example:
            >>> success = StateManager.save_incremental_state(
            ...     context,
            ...     postgres_resource,
            ...     source_type="mysql",
            ...     source_database="amt",
            ...     source_table="accounts",
            ...     incremental_key="updated_at",
            ...     last_value=datetime(2024, 12, 6, 10, 30, 0),
            ...     additional_metadata={"rows_synced": 1500}
            ... )
        """
        key = StateManager._get_state_key(source_type, source_database, source_table)
        
        # Build state dictionary
        state = {
            'last_value': StateManager._serialize_value(last_value),
            'key': incremental_key,
            'source_type': source_type,
            'source_database': source_database,
            'source_table': source_table,
            'synced_at': StateManager._serialize_value(datetime.now()),
        }
        
        # Add additional metadata if provided
        if additional_metadata:
            state['metadata'] = additional_metadata
        
        state_json = json.dumps(state, default=str)
        
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
                    cursor.execute(upsert_query, (key, state_json))
                    conn.commit()
                    
                    logger.info(
                        "state_saved",
                        source_type=source_type,
                        database=source_database,
                        table=source_table,
                        incremental_key=incremental_key,
                        last_value=last_value
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
        if source_type:
            pattern = f"{StateManager.STATE_PREFIX}:{source_type}:%"
            query = """
                SELECT key, value FROM kvs
                WHERE key LIKE %s
                ORDER BY key
            """
            params = (pattern,)
        else:
            query = """
                SELECT key, value FROM kvs
                WHERE key LIKE %s
                ORDER BY key
            """
            params = (f"{StateManager.STATE_PREFIX}:%",)
        
        try:
            with dagster_postgres_resource.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    
                    states = {}
                    for row in rows:
                        key = row[0]
                        try:
                            state = json.loads(row[1])
                            
                            # Deserialize values
                            if 'last_value' in state:
                                state['last_value'] = StateManager._deserialize_value(
                                    state['last_value']
                                )
                            if 'synced_at' in state:
                                state['synced_at'] = StateManager._deserialize_value(
                                    state['synced_at']
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
        dagster_postgres_resource
    ) -> Dict[str, Any]:
        """
        Get summary statistics of all ETL states
        
        Returns:
            {
                "total_tables": 60,
                "by_source": {
                    "mysql": 35,
                    "postgres": 25
                },
                "oldest_sync": datetime(...),
                "newest_sync": datetime(...),
                "tables": [...]
            }
        """
        states = StateManager.get_all_states(context, dagster_postgres_resource)
        
        if not states:
            return {
                "total_tables": 0,
                "by_source": {},
                "tables": []
            }
        
        # Analyze states
        by_source = {}
        sync_times = []
        
        for key, state in states.items():
            source_type = state.get('source_type', 'unknown')
            by_source[source_type] = by_source.get(source_type, 0) + 1
            
            if 'synced_at' in state and isinstance(state['synced_at'], datetime):
                sync_times.append(state['synced_at'])
        
        summary = {
            "total_tables": len(states),
            "by_source": by_source,
            "tables": list(states.keys())
        }
        
        if sync_times:
            summary["oldest_sync"] = min(sync_times)
            summary["newest_sync"] = max(sync_times)
        
        return summary
    
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
        
        if source_type:
            pattern = f"{StateManager.STATE_PREFIX}:{source_type}:%"
            delete_query = """
                DELETE FROM kvs WHERE key LIKE %s
            """
            params = (pattern,)
        else:
            delete_query = """
                DELETE FROM kvs WHERE key LIKE %s
            """
            params = (f"{StateManager.STATE_PREFIX}:%",)
        
        try:
            with dagster_postgres_resource.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(delete_query, params)
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