from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.hooks.base import BaseHook
from airflow.models import Variable
import clickhouse_connect
from airflow.utils.dates import days_ago
from plugins.utils.constants.v1.constants import DEFAULT_ARGS
import pendulum


import logging
logger = logging.getLogger(__name__)

# Reusable PostgresHook function
def get_postgres_hook():
    """
    Return a PostgresHook instance for the users database.
    """
    return PostgresHook(postgres_conn_id='postgres_users_db')

# Reusable ClickHouse client function
def get_clickhouse_client():
    """
    Return a ClickHouse client instance using Airflow connection.
    Uses connection 'clickhouse_default' with secure setting from extra field.
    """
    try:
        conn = BaseHook.get_connection('clickhouse_default') 
        # Parse extra field for secure setting
        client = clickhouse_connect.get_client(
            host=conn.host,
            port=conn.port,
            username=conn.login,
            password=conn.password,
            database=conn.schema or 'default',  # Fallback to 'default' if schema is empty
            secure=False  # Matches your non-SSL setup
        )
        # Optional: Test connection
        client.ping()  # Raises exception if connection fails
        logger.info("Successfully connected to ClickHouse.")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to ClickHouse: {str(e)}")
        raise



# Function to create the quotes table in ClickHouse
def create_clickhouse_table():
    """Create or update the quotes table in ClickHouse to include sync_at."""
    client = get_clickhouse_client()
    check_query = "EXISTS quotes"
    table_exists = client.query(check_query).result_rows[0][0]
    logger.info(f"Table 'quotes' exists in ClickHouse: {bool(table_exists)}")

    if not table_exists:
        create_query = """
        CREATE TABLE quotes (
            id UInt32,
            content String,
            author String,
            inserted_at DateTime DEFAULT now(),
            sync_at DateTime DEFAULT now()
        ) ENGINE = ReplacingMergeTree()
        ORDER BY (id, inserted_at)
        """
        client.command(create_query)
        logger.info("Table 'quotes' created in ClickHouse with sync_at column.")
    else:
        # Check if sync_at column exists
        schema_query = "DESCRIBE quotes"
        schema = client.query(schema_query).result_rows
        columns = [row[0] for row in schema]
        if 'sync_at' not in columns:
            alter_query = "ALTER TABLE quotes ADD COLUMN sync_at DateTime DEFAULT now()"
            client.command(alter_query)
            logger.info("Added sync_at column to existing quotes table.")
        else:
            logger.info("Table 'quotes' already has sync_at column, no changes needed.")

# Function to fetch from Postgres and insert into ClickHouse
def sync_quotes_to_clickhouse():
    """Sync quotes from Postgres to ClickHouse incrementally, adding sync_at."""
    batch_size = 1000
    try:
        pg_hook = get_postgres_hook()
        last_synced_at = Variable.get(
            "quotes_last_synced_at",
            default_var="1970-01-01 00:00:00"
        )
        # Parse last_synced_at to datetime if it's a string
        if isinstance(last_synced_at, str):
            last_synced_at = pendulum.parse(last_synced_at)
        offset = 0
        total_records = 0
        max_inserted_at = None

        with pg_hook.get_conn() as conn, conn.cursor() as cursor:
            while True:
                select_query = """
                SELECT id, content, author, inserted_at
                FROM quotes
                WHERE inserted_at > %s
                ORDER BY inserted_at
                LIMIT %s OFFSET %s
                """
                cursor.execute(select_query, (last_synced_at, batch_size, offset))
                records = cursor.fetchall()
                if not records:
                    logger.info("No more records to fetch.")
                    break

                # Validate and transform data
                transformed_records = []
                sync_time = pendulum.now('UTC')  # Set sync_at to current UTC time
                for record in records:
                    id_val, content, author, inserted_at = record
                    # Validate id for UInt32
                    if not isinstance(id_val, int) or id_val < 0 or id_val > 4294967295:
                        logger.warning(f"Skipping invalid id: {id_val}")
                        continue
                    # Keep inserted_at as datetime (or parse if string)
                    if isinstance(inserted_at, str):
                        try:
                            inserted_at = pendulum.parse(inserted_at)
                        except Exception as e:
                            logger.warning(f"Skipping invalid inserted_at: {inserted_at}, error: {e}")
                            continue
                    # Update max_inserted_at
                    if max_inserted_at is None or inserted_at > max_inserted_at:
                        max_inserted_at = inserted_at
                    # Add sync_at to record
                    transformed_records.append((id_val, str(content), str(author), inserted_at, sync_time))

                if transformed_records:
                    try:
                        client = get_clickhouse_client()
                        client.insert(
                            'quotes',
                            transformed_records,
                            column_names=['id', 'content', 'author', 'inserted_at', 'sync_at']
                        )
                        total_records += len(transformed_records)
                        logger.info(f"Inserted {len(transformed_records)} records into ClickHouse (batch at offset {offset}).")
                    except Exception as e:
                        logger.error(f"Failed to insert batch at offset {offset}: {str(e)}")
                        raise

                offset += batch_size

        if total_records > 0 and max_inserted_at:
            # Update last_synced_at as ISO string
            Variable.set("quotes_last_synced_at", max_inserted_at.isoformat())
            logger.info(f"Inserted total {total_records} records. Updated last_synced_at to {max_inserted_at}")
        else:
            logger.info("No new records to sync.")

    except Exception as e:
        logger.error(f"Failed to sync quotes: {str(e)}")
        raise

# Define the DAG
with DAG(
    'sync_quotes_from_postgres_to_clickhouse',
    default_args=DEFAULT_ARGS,
    description='Syncs quotes from Postgres to ClickHouse hourly for analytics.',
    schedule='*/30 5-22 * * *', # Every 30 mins from 5am to 10pm
    start_date=days_ago(1),
    catchup=False,
    tags=['sync', 'quotes', 'clickhouse'],
) as dag:
    dag.doc_md = """
    # Sync Quotes from Postgres to ClickHouse

    This DAG synchronizes the `quotes` table from PostgreSQL (`postgres_users_db`)
    to ClickHouse (`clickhouse_default`) hourly for analytics.

    ## Workflow
    1. **create_clickhouse_table**: Creates or updates `quotes` table with sync_at column.
    2. **sync_quotes_to_clickhouse**: Syncs new records incrementally, adding sync_at.

    ## Table Schema
    - **id**: UInt32, quote ID.
    - **content**: String, quote text.
    - **author**: String, quote author.
    - **inserted_at**: DateTime, when record was added to PostgreSQL (from API).
    - **sync_at**: DateTime, when record was loaded into ClickHouse.

    ## Connections
    - **postgres_users_db**: PostgreSQL connection.
    - **clickhouse_default**: ClickHouse connection (HTTP, port 8123).

    ## Notes
    - Uses `ReplacingMergeTree` for idempotency.
    - Processes records in batches of 1000.
    - Sends email alerts on failure.
    """

    create_table_task = PythonOperator(
        task_id='create_clickhouse_table',
        python_callable=create_clickhouse_table,
    )

    sync_task = PythonOperator(
        task_id='sync_quotes_to_clickhouse',
        python_callable=sync_quotes_to_clickhouse,
    )

    # Dependencies
    create_table_task >> sync_task