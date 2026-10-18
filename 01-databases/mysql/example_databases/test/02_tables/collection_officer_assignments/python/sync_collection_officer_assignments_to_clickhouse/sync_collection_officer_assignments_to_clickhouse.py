"""
Sync data from a MySQL table into a ClickHouse table.

Uses:
  - PyMySQL to read rows from MySQL
  - clickhouse-connect to write rows into ClickHouse Cloud

Install deps:
  pip install pymysql clickhouse-connect
"""

from dotenv import load_dotenv

load_dotenv()

import os
import logging

import pymysql
from pymysql import Error
import clickhouse_connect

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
    "host": "localhost",
    "database": "test",
    "username": os.getenv(""),
    "password": os.getenv("LOCAL_MYSQL_DB_PASSWORD"),
    "port": int(os.getenv("LOCAL_MYSQL_DB_PORT", "3306")),
}

# Source: adjust table/query to match your actual MySQL source.
# Only columns present in FIELD_MAPPING are read and synced.
MYSQL_SOURCE_TABLE = os.getenv("MYSQL_SOURCE_TABLE", "collection_officer_assignments")

# Number of rows read from MySQL / inserted into ClickHouse per round-trip.
BATCH_SIZE = int(os.getenv("SYNC_BATCH_SIZE", "10000"))


# ============================================================================
# ClickHouse Cloud Configuration
# ============================================================================
CLICKHOUSE_CONFIG = {
    "host": os.getenv("SC_CLICKHOUSE_CLOUD_HOST"),
    "port": int(os.getenv("SC_CLICKHOUSE_CLOUD_PORT", "8443")),
    "username": os.getenv("SC_CLICKHOUSE_CLOUD_USER"),
    "password": os.getenv("SC_CLICKHOUSE_CLOUD_PASSWORD"),
    "database": os.getenv("SC_CLICKHOUSE_CLOUD_DATABASE", "automations"),
    "secure": True,
    "verify": True,
}

# ============================================================================
# ClickHouse Table Configuration
# ============================================================================
CLICKHOUSE_TABLE_CONFIG = {
    "database": "automations",
    "table": "collection_officer_assignments",
    "engine": "ReplacingMergeTree",
    "version_column": "updated_at",
    "partition_by": "created_at",
    "order_by": ["id"],
}

# ============================================================================
# Field Mapping Configuration
# ============================================================================
# ch_type: ClickHouse column type
# nullable: whether the ClickHouse column should be Nullable(...)
# Mirrors the `collection_officer_assignments` MySQL table schema.
FIELD_MAPPING = {
    "id": {
        "ch_type": "Int64",
        "nullable": False,
    },
    "accountId": {
        "ch_type": "Int32",
        "nullable": False,
    },
    "accountRef": {
        "ch_type": "String",
        "nullable": False,
    },
    "accountType": {
        "ch_type": "String",
        "nullable": False,
    },
    "status": {
        "ch_type": "String",
        "nullable": True,
    },
    "funnel_status": {
        "ch_type": "String",
        "nullable": True,
    },
    "product": {
        "ch_type": "String",
        "nullable": False,
    },
    "days_late_current": {
        "ch_type": "Float64",
        "nullable": True,
    },
    "arrears": {
        "ch_type": "Float64",
        "nullable": True,
    },
    "PowerBI_balance": {
        "ch_type": "Float64",
        "nullable": True,
    },
    "companyRegion": {
        "ch_type": "String",
        "nullable": True,
    },
    "latitude": {
        "ch_type": "String",
        "nullable": True,
    },
    "longitude": {
        "ch_type": "String",
        "nullable": True,
    },
    "town": {
        "ch_type": "String",
        "nullable": True,
    },
    "County": {
        "ch_type": "String",
        "nullable": True,
    },
    "region": {
        "ch_type": "String",
        "nullable": True,
    },
    "snapshot_date": {
        "ch_type": "DateTime",
        "nullable": False,
    },
    "assigned_function": {
        "ch_type": "String",
        "nullable": False,
    },
    "assigned_employee_id": {
        "ch_type": "Int32",
        "nullable": True,
    },
    "assigned_employee_name": {
        "ch_type": "String",
        "nullable": True,
    },
    "assignment_start": {
        "ch_type": "DateTime",
        "nullable": False,
    },
    "assignment_end": {
        "ch_type": "DateTime",
        "nullable": False,
    },
    "created_at": {
        "ch_type": "DateTime",
        "nullable": False,
        "default": "now()",
    },
    "created_by": {
        "ch_type": "String",
        "nullable": True,
    },
    "updated_at": {
        "ch_type": "DateTime",
        "nullable": False,
        "default": "now()",
    },
    "updated_by": {
        "ch_type": "String",
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
        "ch_type": "DateTime",
        "nullable": False,
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
# ClickHouse Database Connection
# ============================================================================
def get_clickhouse_client():
    """Create and return a ClickHouse Cloud database connection."""
    try:
        client = clickhouse_connect.get_client(
            host=CLICKHOUSE_CONFIG["host"],
            port=CLICKHOUSE_CONFIG["port"],
            username=CLICKHOUSE_CONFIG["username"],
            password=CLICKHOUSE_CONFIG["password"],
            database=CLICKHOUSE_CONFIG["database"],
            secure=CLICKHOUSE_CONFIG["secure"],
            verify=CLICKHOUSE_CONFIG["verify"],
        )
        # Test connection
        client.command("SELECT 1")
        logger.info("ClickHouse connection established successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to ClickHouse: {e}")
        raise


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
# Validation
# ============================================================================
def validate_field_mapping(row: dict) -> dict:
    """
    Validate and coerce a single MySQL row against FIELD_MAPPING.

    - Drops any keys not present in FIELD_MAPPING (extra MySQL columns).
    - If a field's value is None and the field defines a 'default',
      substitutes the resolved default value before the nullable check.
    - Raises ValueError if a non-nullable field is still None after
      default resolution (i.e. no default was configured for it).
    """
    validated = {}
    for field, spec in FIELD_MAPPING.items():
        value = row.get(field)

        if value is None and "default" in spec:
            value = _resolve_default(spec["default"])

        if value is None and not spec["nullable"]:
            raise ValueError(
                f"Field '{field}' is None but is configured as non-nullable "
                f"(row id={row.get('id')!r})"
            )

        validated[field] = value

    return validated


# ============================================================================
# ClickHouse DDL
# ============================================================================
def _ch_column_type(spec: dict) -> str:
    ch_type = spec["ch_type"]
    return f"Nullable({ch_type})" if spec["nullable"] else ch_type


def _build_create_table_sql() -> str:
    columns_sql_parts = [
        f"`{field}` {_ch_column_type(spec)}" for field, spec in FIELD_MAPPING.items()
    ]
    columns_sql_parts += [
        f"`{field}` {_ch_column_type(spec)}"
        for field, spec in SYNC_METADATA_COLUMNS.items()
    ]
    columns_sql = ",\n    ".join(columns_sql_parts)

    dest = f"{CLICKHOUSE_TABLE_CONFIG['database']}.{CLICKHOUSE_TABLE_CONFIG['table']}"
    order_by = ", ".join(CLICKHOUSE_TABLE_CONFIG["order_by"])

    return f"""
CREATE TABLE IF NOT EXISTS {dest}
(
    {columns_sql}
)
ENGINE = {CLICKHOUSE_TABLE_CONFIG['engine']}({CLICKHOUSE_TABLE_CONFIG['version_column']})
PARTITION BY toYYYYMM({CLICKHOUSE_TABLE_CONFIG['partition_by']})
ORDER BY ({order_by})
""".strip()


def ensure_clickhouse_table(client) -> None:
    """Create the destination database/table in ClickHouse if they don't exist,
    and add any mapped or sync-metadata columns missing from an existing table."""
    client.command(
        f"CREATE DATABASE IF NOT EXISTS {CLICKHOUSE_TABLE_CONFIG['database']}"
    )
    client.command(_build_create_table_sql())

    dest = f"{CLICKHOUSE_TABLE_CONFIG['database']}.{CLICKHOUSE_TABLE_CONFIG['table']}"

    # Handles columns added to FIELD_MAPPING or SYNC_METADATA_COLUMNS after
    # the table already exists — CREATE TABLE IF NOT EXISTS alone won't
    # retroactively add them to a pre-existing table.
    all_columns = {**FIELD_MAPPING, **SYNC_METADATA_COLUMNS}
    for field, spec in all_columns.items():
        client.command(
            f"ALTER TABLE {dest} ADD COLUMN IF NOT EXISTS "
            f"`{field}` {_ch_column_type(spec)}"
        )

    logger.info(f"OK — {dest} ready")


# ============================================================================
# Sync logic
# ============================================================================
def fetch_and_sync_mysql_data(
    mysql_conn, ch_client, batch_size: int = BATCH_SIZE
) -> int:
    sync_started_at = datetime.now(timezone.utc).replace(tzinfo=None)

    mysql_columns = list(FIELD_MAPPING.keys())
    ch_columns = mysql_columns + list(SYNC_METADATA_COLUMNS.keys())
    dest = f"{CLICKHOUSE_TABLE_CONFIG['database']}.{CLICKHOUSE_TABLE_CONFIG['table']}"

    query = f"SELECT {', '.join(mysql_columns)} FROM {MYSQL_SOURCE_TABLE}"

    total_synced = 0

    with mysql_conn.cursor() as cursor:
        cursor.execute(query)

        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break

            batch = []
            for row in rows:
                try:
                    validated = validate_field_mapping(row)
                except ValueError as e:
                    logger.warning(f"Skipping invalid row: {e}")
                    continue
                validated["_synced_at"] = sync_started_at
                batch.append([validated[col] for col in ch_columns])

            if batch:
                ch_client.insert(dest, batch, column_names=ch_columns)
                total_synced += len(batch)
                logger.info(f"Synced {len(batch)} rows (total: {total_synced})")

    return total_synced


# ============================================================================
# Main
# ============================================================================
def main():
    """Main execution entry point."""
    mysql_conn = None
    ch_client = None

    try:
        mysql_conn = establish_connection_mysql_db(MYSQL_DB_CONFIGS)
        if mysql_conn is None:
            logger.error("Aborting sync: could not connect to MySQL")
            return

        ch_client = get_clickhouse_client()

        ensure_clickhouse_table(ch_client)

        total = fetch_and_sync_mysql_data(mysql_conn, ch_client)
        logger.info(f"Sync complete. {total} rows synced to ClickHouse.")

    finally:
        if mysql_conn is not None:
            mysql_conn.close()
        if ch_client is not None:
            ch_client.close()


if __name__ == "__main__":
    main()
