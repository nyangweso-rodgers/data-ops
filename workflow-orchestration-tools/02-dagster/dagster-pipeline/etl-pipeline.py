# workflow-orchestration-tools/02-dagster/dagster-pipeline/etl-pipeline.py
from dagster import asset, job, ScheduleDefinition, DefaultScheduleStatus, repository, RunsFilter
from sqlalchemy import create_engine, text
import clickhouse_connect
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Track last run timestamp in Dagster instance storage
def get_last_run_timestamp(context):
    last_run = context.instance.get_run_records(
        filters=RunsFilter(tags={"pipeline": "postgres_to_clickhouse"}),
        limit=1
    )
    if last_run:
        last_run_ts = last_run[0].start_time
        # Uncomment for daily full load at 5 AM
        # now = datetime.utcnow()
        # if now.hour == 5 and now.minute < 15 and last_run_ts.date() < now.date():
        #     return None
        return last_run[0].start_time if last_run else None
    return None

@asset
def setup_clickhouse_table():
    """Create the ClickHouse table with ReplacingMergeTree."""
    client = clickhouse_connect.get_client(host="clickhouse-server", port=8123, username="default", password="")
    client.command("""
        CREATE TABLE IF NOT EXISTS users.customers (
            id String,
            created_by String,
            updated_by String,
            created_at DateTime,
            updated_at DateTime
        ) ENGINE = ReplacingMergeTree(updated_at)
        ORDER BY id
    """)
    logger.debug("Created or verified ClickHouse customers table")
    return True

@asset
def postgres_initial_load(context):
    """Fetch all records on first run."""
    engine = create_engine("postgresql://postgres:<password>@postgres-db:5432/<database-name>")
    with engine.connect() as connection:
        result = connection.execute(text("SELECT id, created_by, updated_by, created_at, updated_at FROM customers"))
        data = [(str(row[0]), row[1], row[2], row[3], row[4]) for row in result.fetchall()]
        logger.debug(f"Initial load: Fetched {len(data)} rows from Postgres")
        return data

@asset
def postgres_new_records(context):
    """Fetch records created since last run."""
    last_run_ts = get_last_run_timestamp(context)
    if not last_run_ts:
        return []  # Skip if no prior run (initial load handles it)
    engine = create_engine("postgresql://postgres:<password>@postgres-db:5432/<database-name>")
    with engine.connect() as connection:
        query = text("SELECT id, created_by, updated_by, created_at, updated_at FROM customers WHERE created_at > :last_run")
        result = connection.execute(query, {"last_run": last_run_ts})
        data = [(str(row[0]), row[1], row[2], row[3], row[4]) for row in result.fetchall()]
        logger.debug(f"New records: Fetched {len(data)} rows since {last_run_ts}")
        return data

@asset
def postgres_updated_records(context):
    """Fetch records updated since last run."""
    last_run_ts = get_last_run_timestamp(context)
    if not last_run_ts:
        return []  # Skip if no prior run
    engine = create_engine("postgresql://postgres:<password>@postgres-db:5432/<database-name>")
    with engine.connect() as connection:
        query = text("SELECT id, created_by, updated_by, created_at, updated_at FROM customers WHERE updated_at > :last_run AND created_at <= :last_run")
        result = connection.execute(query, {"last_run": last_run_ts})
        data = [(str(row[0]), row[1], row[2], row[3], row[4]) for row in result.fetchall()]
        logger.debug(f"Updated records: Fetched {len(data)} rows since {last_run_ts}")
        return data

@asset
def clickhouse_load(context, postgres_initial_load, postgres_new_records, postgres_updated_records):
    """Load data into ClickHouse with ReplacingMergeTree."""
    client = clickhouse_connect.get_client(host="clickhouse-server", port=8123, username="default", password="")
    
    # Combine data: initial (first run), new, and updated
    all_data = postgres_initial_load if not get_last_run_timestamp(context) else (postgres_new_records + postgres_updated_records)
    if not all_data:
        logger.debug("No data to load into ClickHouse")
        return False
    
    try:
        client.insert(
            "users.customers",
            all_data,
            column_names=["id", "created_by", "updated_by", "created_at", "updated_at"]
        )
        logger.debug(f"Inserted {len(all_data)} rows into ClickHouse")
        return True
    except Exception as e:
        logger.error(f"Failed to insert into ClickHouse: {str(e)}", exc_info=True)
        raise

@job
def postgres_to_clickhouse():
    """Job to run all assets."""
    setup = setup_clickhouse_table()
    initial = postgres_initial_load()
    new = postgres_new_records()
    updated = postgres_updated_records()
    clickhouse_load(setup, initial, new, updated)

# Schedule to run every 5 minutes
postgres_to_clickhouse_schedule = ScheduleDefinition(
    job=postgres_to_clickhouse,
    cron_schedule="*/15 5-23 * * 1-7",
    default_status=DefaultScheduleStatus.RUNNING
)

@repository
def etl_repository():
    return [postgres_to_clickhouse, postgres_to_clickhouse_schedule]