from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def add_sync_time(rows: List[Dict[str, Any]], target_config: Dict[str, Any], sync_time_col: str = "sync_time") -> None:
    """
    Add a sync_time value to each row if the target schema defines it as a generated column,
    formatting the value based on the target database and column data type.

    Args:
        rows: List of rows to modify (each row is a dict mapping target columns to values).
        target_config: Target schema configuration (from SchemaLoader.get_combined_schema()["target"]).
        sync_time_col: Name of the sync_time column (default: "sync_time").

    Returns:
        None (modifies rows in place).
    """
    # Check if sync_time is defined in target schema
    column_mappings = target_config.get("column_mappings", {})
    if sync_time_col not in column_mappings or not column_mappings[sync_time_col].get("generated", False):
        logger.debug(f"Skipping sync_time addition: '{sync_time_col}' not defined as generated in target schema")
        return

    # Get the column type
    sync_time_type = column_mappings[sync_time_col].get("type", "String").lower()
    database_type = target_config.get("database_type", "clickhouse").lower()

    # Generate sync_time (UTC)
    sync_time_dt = datetime.utcnow()

    # Format sync_time based on database and column type
    sync_time = None
    if database_type == "clickhouse":
        if sync_time_type.startswith("datetime64"):
            # High precision (milliseconds)
            sync_time = sync_time_dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # e.g., 2025-05-17 10:26:00.123
        elif sync_time_type.startswith("datetime"):
            # Standard ClickHouse DateTime
            sync_time = sync_time_dt.strftime("%Y-%m-%d %H:%M:%S")  # e.g., 2025-05-17 10:26:00
        else:
            # Fallback to ISO 8601 string
            sync_time = sync_time_dt.isoformat()  # e.g., 2025-05-17T10:26:00.123456

    elif database_type == "postgres":
        if sync_time_type in ["timestamp", "timestamp with time zone", "timestamptz"]:
            # Postgres expects ISO 8601 with timezone or native format
            sync_time = sync_time_dt.isoformat() + "+00"  # e.g., 2025-05-17T10:26:00.123456+00
        else:
            # Fallback to string
            sync_time = sync_time_dt.isoformat()

    elif database_type == "mysql":
        if sync_time_type in ["datetime", "timestamp"]:
            # MySQL expects YYYY-MM-DD HH:MM:SS
            sync_time = sync_time_dt.strftime("%Y-%m-%d %H:%M:%S")  # e.g., 2025-05-17 10:26:00
        else:
            # Fallback to string
            sync_time = sync_time_dt.isoformat()

    else:
        # Fallback for unknown databases (e.g., Snowflake, Redshift)
        logger.warning(f"Unknown database type '{database_type}' for {sync_time_col}, using ISO 8601 string")
        sync_time = sync_time_dt.isoformat()

    logger.debug(f"Adding {sync_time_col}={sync_time} (type: {sync_time_type}, db: {database_type}) to {len(rows)} rows")

    # Add sync_time to each row
    for row in rows:
        row[sync_time_col] = sync_time