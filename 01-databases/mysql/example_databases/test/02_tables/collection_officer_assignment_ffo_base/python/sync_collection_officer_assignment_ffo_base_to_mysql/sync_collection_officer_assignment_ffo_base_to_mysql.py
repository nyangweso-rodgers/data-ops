from dotenv import load_dotenv

load_dotenv()

import os
import logging
import argparse
from typing import Any, Dict, List

import pandas as pd
import pymysql
from pymysql import Error

from datetime import datetime, timezone

# ============================================================================
# Setup logging configuration
# ============================================================================
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# MySQL Database Configuration
# ============================================================================
MYSQL_DB_CONFIGS = {
    "type": "mysql",
    # "host": os.getenv("LOCAL_MYSQL_DB_HOST", "localhost"),
    "host": "localhost",
    "database": "test",
    "username": os.getenv("LOCAL_MYSQL_DB_USERNAME"),
    "password": os.getenv("LOCAL_MYSQL_DB_PASSWORD"),
    "port": int(os.getenv("MYSQL_DB_PORT", "3306")),
}

# ============================================================================
# Target Table Configuration
# ============================================================================
MYSQL_TABLE_CONFIG = {
    "table_name": "collection_officer_assignment_ffo_base",
    "batch_size": 1000,
    # Rows are upserted on this key so re-running the sync for the same
    # assignment period is idempotent, while different periods accumulate.
    "primary_key": ["account_ref", "assignment_start"],
}

# ============================================================================
# File Path Configuration
# ============================================================================
excel_file_path = "../../../../../../../../data/Kitui Aug Allocation.xlsx"

# ============================================================================
# Field Mapping Configuration
# ============================================================================
FIELD_MAPPING = {
    "Account Ref": {
        "mysql_field": "account_ref",
        "mysql_type": "VARCHAR(50)",
        "nullable": False,
    },
    "FFO Full Name": {
        "mysql_field": "ffo",
        "mysql_type": "VARCHAR(255)",
        "nullable": True,
    },
}

# ============================================================================
# Sync Metadata Columns
# ============================================================================
# Columns added by the sync process itself — not sourced from MySQL,
# so they're kept out of FIELD_MAPPING (which only describes source fields).
SYNC_METADATA_COLUMNS = {
    "_synced_at": {
        "mysql_field": "_synced_at",
        "mysql_type": "DATETIME",
        "nullable": False,
    },
    "assignment_start": {
        "mysql_field": "assignment_start",
        "mysql_type": "DATETIME",
        "nullable": False,
        "default": "2026-08-01 00:00:00",  # Default value for assignment_start
    },
    "assignment_end": {
        "mysql_field": "assignment_end",
        "mysql_type": "DATETIME",
        "nullable": False,
        "default": "2026-08-31 23:59:59",  # Default value for assignment_end
    },
}


# ============================================================================
# MySQL Database Connection
# ============================================================================
def establish_connection_mysql_db(config):
    """
    Establish connection to MySQL database.

    Uses a server-side cursor (SSDictCursor) rather than the default
    buffered DictCursor. With a buffered cursor, execute() pulls the
    *entire* result set into client memory immediately and fetchmany()
    just slices that in-memory list — no real streaming. SSDictCursor
    keeps the result set on the MySQL server and streams rows over the
    wire as fetchmany()/fetchone() are called, so memory use stays
    bounded by batch_size regardless of table size.

    Args:
        config: Database configuration dictionary

    Returns:
        pymysql.connections.Connection: Active database connection or None
    """
    try:
        connection_params = {
            "host": config["host"],
            "port": config["port"],
            "user": config["username"],
            "password": config["password"],
            "database": config["database"],
            "charset": "utf8mb4",
            "cursorclass": pymysql.cursors.SSDictCursor,
        }

        connection = pymysql.connect(**connection_params)

        if connection.open:
            logger.info(f"Connected to MySQL: {config['database']} @ {config['host']}")
            return connection

    except Error as e:
        logger.error(f"Failed to connect to MySQL {config['database']}: {e}")
        return None


# ============================================================================
# Default value resolution
# ============================================================================
def _resolve_default(default_spec):
    """
    Resolve a FIELD_MAPPING 'default' spec into a concrete Python value.

    Supports a small set of dynamic tokens (currently just "now()");
    anything else is returned as-is (a literal default value).
    """
    if default_spec == "now()":
        return datetime.now(timezone.utc).replace(tzinfo=None)
    return default_spec


# ============================================================================
# Value coercion
# ============================================================================
def _coerce_value(value, mysql_type: str):
    """
    Coerce a raw pandas cell value to a type suitable for a pymysql
    parameter, based on the target field's declared mysql_type.
    """
    if value is None or pd.isna(value):
        return None

    sql_type = mysql_type.upper()

    if "CHAR" in sql_type or "TEXT" in sql_type:
        # Excel stores whole numbers (e.g. account refs) as floats like
        # 123456.0 — avoid writing "123456.0" into a string column.
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value).strip()

    if "INT" in sql_type:
        return int(value)

    if "DATETIME" in sql_type or sql_type == "DATE":
        if isinstance(value, datetime):
            return value
        return pd.to_datetime(value).to_pydatetime()

    return value


# ============================================================================
# Excel extraction
# ============================================================================
def read_excel_data(file_path: str) -> pd.DataFrame:
    """
    Read the source Excel file and validate that every column referenced by
    FIELD_MAPPING is present.
    """
    logger.info(f"Reading Excel file: {file_path}")
    df = pd.read_excel(file_path)
    logger.info(f"Read {len(df)} row(s); columns: {df.columns.tolist()}")

    missing_columns = [col for col in FIELD_MAPPING if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing expected column(s) in Excel file: {missing_columns}")

    return df


# ============================================================================
# Transform
# ============================================================================
def transform_rows(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Map each Excel row onto the target MySQL columns via FIELD_MAPPING and
    stamp on SYNC_METADATA_COLUMNS. Rows missing a required (non-nullable)
    field are dropped.
    """
    synced_at = datetime.now(timezone.utc).replace(tzinfo=None)
    assignment_start = _resolve_default(
        SYNC_METADATA_COLUMNS["assignment_start"]["default"]
    )
    assignment_end = _resolve_default(
        SYNC_METADATA_COLUMNS["assignment_end"]["default"]
    )

    records: List[Dict[str, Any]] = []
    skipped = 0

    for _, row in df.iterrows():
        record: Dict[str, Any] = {}
        missing_required = False

        for source_col, spec in FIELD_MAPPING.items():
            value = _coerce_value(row[source_col], spec["mysql_type"])
            if value is None and not spec["nullable"]:
                missing_required = True
                break
            record[spec["mysql_field"]] = value

        if missing_required:
            skipped += 1
            continue

        record["_synced_at"] = synced_at
        record["assignment_start"] = assignment_start
        record["assignment_end"] = assignment_end
        records.append(record)

    if skipped:
        logger.warning(f"Skipped {skipped} row(s) missing a required field")
    logger.info(f"Transformed {len(records)} row(s) for sync")

    return records


# ============================================================================
# Target table DDL
# ============================================================================
def ensure_mysql_table(connection, table_name: str) -> None:
    """
    Create the target MySQL table if it doesn't already exist, deriving
    column definitions from FIELD_MAPPING and SYNC_METADATA_COLUMNS.
    """
    column_defs = []
    for spec in list(FIELD_MAPPING.values()) + list(SYNC_METADATA_COLUMNS.values()):
        col = spec["mysql_field"]
        sql_type = spec["mysql_type"]
        null_clause = "NOT NULL" if not spec.get("nullable", True) else "NULL"
        column_defs.append(f"`{col}` {sql_type} {null_clause}")

    pk_cols = MYSQL_TABLE_CONFIG["primary_key"]
    pk_clause = ",\n    PRIMARY KEY (" + ", ".join(f"`{c}`" for c in pk_cols) + ")"

    ddl = (
        f"CREATE TABLE IF NOT EXISTS `{table_name}` (\n    "
        + ",\n    ".join(column_defs)
        + pk_clause
        + "\n)"
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(ddl)
        connection.commit()
        logger.info(f"Ensured MySQL table `{table_name}` exists")
    except Error as e:
        connection.rollback()
        logger.error(f"Failed to create MySQL table `{table_name}`: {e}")
        raise


# ============================================================================
# Load
# ============================================================================
def sync_records_to_mysql(
    connection, table_name: str, records: List[Dict[str, Any]], batch_size: int
) -> int:
    """
    Batch upsert records into the target MySQL table using
    INSERT ... ON DUPLICATE KEY UPDATE, keyed on MYSQL_TABLE_CONFIG['primary_key'].
    """
    if not records:
        logger.warning("No records to sync")
        return 0

    columns = list(records[0].keys())
    pk_cols = set(MYSQL_TABLE_CONFIG["primary_key"])

    col_list = ", ".join(f"`{c}`" for c in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    update_cols = [c for c in columns if c not in pk_cols]
    update_clause = ", ".join(f"`{c}`=VALUES(`{c}`)" for c in update_cols)

    insert_sql = (
        f"INSERT INTO `{table_name}` ({col_list}) VALUES ({placeholders}) "
        f"ON DUPLICATE KEY UPDATE {update_clause}"
    )

    total = 0
    try:
        with connection.cursor() as cursor:
            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]
                values = [tuple(record[col] for col in columns) for record in batch]
                cursor.executemany(insert_sql, values)
                connection.commit()
                total += len(batch)
                logger.info(f"Synced {total}/{len(records)} row(s)")
    except Error as e:
        connection.rollback()
        logger.error(f"Error syncing records to MySQL: {e}")
        raise

    logger.info(f"Finished syncing {total} row(s) to `{table_name}`")
    return total


# ============================================================================
# Sync logic
# ============================================================================
def fetch_csv_data_and_sync_to_mysql(
    file_path: str, table_name: str, batch_size: int
) -> int:
    """
    End-to-end sync: read the Excel file, transform rows to the target
    schema, and upsert them into MySQL.
    """
    df = read_excel_data(file_path)
    records = transform_rows(df)

    connection = establish_connection_mysql_db(MYSQL_DB_CONFIGS)
    if connection is None:
        raise RuntimeError("Could not establish MySQL connection")

    try:
        ensure_mysql_table(connection, table_name)
        return sync_records_to_mysql(connection, table_name, records, batch_size)
    finally:
        connection.close()
        logger.info("MySQL connection closed")


# ============================================================================
# Entry point
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Sync collection officer assignment data from Excel to MySQL"
    )
    parser.add_argument(
        "--file", type=str, default=excel_file_path, help="Path to the Excel file"
    )
    parser.add_argument(
        "--table",
        type=str,
        default=MYSQL_TABLE_CONFIG["table_name"],
        help="Target MySQL table name",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=MYSQL_TABLE_CONFIG["batch_size"],
        help="Batch size for inserts",
    )
    args = parser.parse_args()

    try:
        total = fetch_csv_data_and_sync_to_mysql(args.file, args.table, args.batch_size)
        logger.info(f"Sync complete: {total} row(s) synced to `{args.table}`")
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise


if __name__ == "__main__":
    main()
