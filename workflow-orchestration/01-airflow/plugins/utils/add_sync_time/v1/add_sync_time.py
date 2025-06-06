from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def add_sync_time(rows: List[Dict[str, Any]], target_config: Dict[str, Any], sync_time_col: str = "sync_time") -> None:
    """
    Add a sync_time value to each row if the target schema defines it as an auto-generated column,
    using appropriate data type based on the target database and column data type.

    Args:
        rows: List of rows to modify (each row is a dict mapping target columns to values).
        target_config: Target schema configuration (from SchemaLoader.load_schema()["target"]).
        sync_time_col: Name of the sync_time column (default: "sync_time").

    Returns:
        None (modifies rows in place).
    """
    # Check if sync_time is defined as auto-generated in target schema
    columns = target_config.get("columns", {})
    if sync_time_col not in columns or not columns[sync_time_col].get("auto_generated", False):
        logger.debug(f"Skipping sync_time addition: '{sync_time_col}' not defined as auto-generated in target schema")
        return

    # Get the column type and database type (case-insensitive)
    sync_time_type = columns[sync_time_col].get("type", "String").lower().replace("nullable(", "").replace(")", "")
    database_type = target_config.get("database_type", "clickhouse").lower()

    # Generate sync_time (UTC)
    sync_time_dt = datetime.utcnow()

    # Assign sync_time based on database and column type
    sync_time = None
    if database_type == "clickhouse":
        if sync_time_type in ("datetime", "datetime64"):
            # Always use datetime object for ClickHouse DateTime/DateTime64
            sync_time = sync_time_dt
        else:
            # Fallback to ISO 8601 string for non-temporal types
            sync_time = sync_time_dt.isoformat()
            logger.warning(f"Unexpected sync_time_type '{sync_time_type}' for ClickHouse, using ISO 8601 string")

    elif database_type == "postgres":
        if sync_time_type in ("timestamp", "timestamp with time zone", "timestamptz"):
            sync_time = sync_time_dt.isoformat() + "+00"  # e.g., 2025-05-18T12:33:31.123456+00
        else:
            sync_time = sync_time_dt.isoformat()

    elif database_type == "mysql":
        if sync_time_type in ("datetime", "timestamp"):
            sync_time = sync_time_dt.strftime("%Y-%m-%d %H:%M:%S")  # e.g., 2025-05-18 12:33:31
        else:
            sync_time = sync_time_dt.isoformat()

    else:
        logger.warning(f"Unknown database type '{database_type}' for {sync_time_col}, using ISO 8601 string")
        sync_time = sync_time_dt.isoformat()

    # Log the type and value of sync_time for debugging
    logger.debug(f"Adding {sync_time_col}={sync_time} (python_type: {type(sync_time).__name__}, sync_time_type: {sync_time_type}, db: {database_type}) to {len(rows)} rows")

    # Add sync_time to each row
    for row in rows:
        row[sync_time_col] = sync_time