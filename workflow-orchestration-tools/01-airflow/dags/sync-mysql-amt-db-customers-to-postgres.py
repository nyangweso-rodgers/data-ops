from plugins.utils import (
    default_args, 
    DAG, 
    AirflowException,
    PythonOperator, 
    Variable,
    days_ago, 
    datetime,
    logging,
    pendulum,
    get_mysql_amtdb_hook,
    get_postgres_ep_stage_hook
)

from typing import List, Optional, Tuple
from psycopg2 import extras
import time

# Set up logging
logger = logging.getLogger(__name__)

# ================== CONFIGURATION ==================
SOURCE_CONFIG = {
    'mysql_db': 'amtdb',
    'mysql_table': 'customers',
    'mysql_schema': None  # None uses default schema
}

TARGET_CONFIG = {
    'postgres_schema': 'public',
    'postgres_table': 'customers_v2'
}

# These can be overridden via Airflow Variables if needed
BATCH_CONFIG = {
    'batch_size': 1000,
    'batch_delay': 0.0,
    'lookback_hours': 24
}

def verify_connections(**kwargs) -> None:
    """Verify all DB connections and table accessibility."""
    try:
        # Verify MySQL
        mysql_hook = get_mysql_amtdb_hook()
        table_ref = SOURCE_CONFIG['mysql_table']
        if SOURCE_CONFIG['mysql_schema']:
            table_ref = f"{SOURCE_CONFIG['mysql_schema']}.{table_ref}"
            
        with mysql_hook.get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT 1 FROM {table_ref} LIMIT 1")
        logger.info(f"MySQL connection and table {table_ref} verified")
        
        # Verify PostgreSQL
        pg_hook = get_postgres_ep_stage_hook()
        pg_table_ref = f"{TARGET_CONFIG['postgres_schema']}.{TARGET_CONFIG['postgres_table']}"
        with pg_hook.get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT 1 FROM {pg_table_ref} LIMIT 1")
        logger.info(f"PostgreSQL connection and table {pg_table_ref} verified")
        
    except Exception as e:
        logger.error(f"Connection verification failed: {str(e)}")
        raise AirflowException(f"Connection verification failed: {str(e)}")

def check_if_table_exists(**kwargs) -> bool:
    """Check if table exists in PostgreSQL using TARGET_CONFIG."""
    postgres_hook = get_postgres_ep_stage_hook()
    
    schema = TARGET_CONFIG['postgres_schema']
    table = TARGET_CONFIG['postgres_table']
    
    check_table_sql = """
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = %s 
        AND table_name = %s
    );
    """
    try:
        table_exists = postgres_hook.get_first(check_table_sql, parameters=(schema, table))[0]
        logger.info(f"Table {schema}.{table} exists: {table_exists}")
        return table_exists
    except Exception as e:
        logger.error(f"Failed to check {schema}.{table}: {str(e)}")
        raise AirflowException(f"Table existence check failed: {str(e)}")

def create_table_if_not_exists(**kwargs) -> None:
    """Create table in PostgreSQL if it doesn't exist using TARGET_CONFIG."""
    postgres_hook = get_postgres_ep_stage_hook()
    
    schema = TARGET_CONFIG['postgres_schema']
    table = TARGET_CONFIG['postgres_table']
    
    if check_if_table_exists():
        logger.info(f"Skipping table creation; {schema}.{table} already exists")
        return
    
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {schema}.{table} (
        createdAt TIMESTAMP,
        updatedAt TIMESTAMP,
        id INT PRIMARY KEY,
        companyRegionId INT,
        name VARCHAR(255),
        sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with postgres_hook.get_conn() as conn, conn.cursor() as cursor:
            cursor.execute(create_table_sql)
            conn.commit()
        logger.info(f"Created table {schema}.{table}")
    except Exception as e:
        logger.error(f"Failed to create {schema}.{table}: {str(e)}")
        raise AirflowException(f"Table creation failed: {str(e)}")

def fetch_customers(
    min_update_time: Optional[datetime] = None,
    **kwargs
) -> List[Tuple[datetime, datetime, int, int, str]]:
    """Fetch customers from MySQL in batches using SOURCE_CONFIG and BATCH_CONFIG."""
    # Get configuration values
    mysql_table = SOURCE_CONFIG['mysql_table']
    batch_size = BATCH_CONFIG['batch_size']
    batch_delay = BATCH_CONFIG['batch_delay']
    lookback_hours = BATCH_CONFIG['lookback_hours']
    
    # Calculate minimum update time
    if min_update_time is None:
        try:
            last_sync_str = Variable.get("last_sync_customers_time")
            min_update_time = pendulum.parse(last_sync_str)
        except (pendulum.parsing.exceptions.ParserError, KeyError) as e:
            logger.warning(f"Using default {lookback_hours}h lookback: {str(e)}")
            min_update_time = pendulum.now('UTC').subtract(hours=lookback_hours)
    
    mysql_hook = get_mysql_amtdb_hook()
    base_query = f"""
    SELECT createdAt, updatedAt, id, companyRegionId, name
    FROM {mysql_table}
    WHERE updatedAt >= %(min_update_time)s
    ORDER BY updatedAt, id
    LIMIT %(batch_size)s OFFSET %(offset)s
    """
    
    all_records = []
    offset = 0
    batch_count = 0
    start_time = time.monotonic()
    
    while True:
        params = {
            'batch_size': batch_size,
            'offset': offset,
            'min_update_time': min_update_time
        }
        
        try:
            records = mysql_hook.get_records(base_query, parameters=params)
            if not records:
                break
                
            all_records.extend(records)
            offset += len(records)
            batch_count += 1
            
            if batch_count % 10 == 0:
                elapsed = time.monotonic() - start_time
                logger.info(
                    f"Batch {batch_count}: {len(all_records)} records "
                    f"({elapsed:.1f}s elapsed)"
                )
            
            if batch_delay > 0 and len(records) == batch_size:
                time.sleep(batch_delay)
                
        except Exception as e:
            logger.error(f"Batch failed at offset {offset}: {str(e)}")
            raise AirflowException(f"MySQL fetch failed after {len(all_records)} records")
    
    logger.info(
        f"Fetched {len(all_records)} records in {batch_count} batches "
        f"({time.monotonic() - start_time:.1f}s total)"
    )
    return all_records

def sync_to_postgres(**kwargs) -> None:
    """Sync fetched data to PostgreSQL using TARGET_CONFIG."""
    ti = kwargs['ti']
    records = ti.xcom_pull(task_ids='fetch_customers_task') or []
    
    if not records:
        logger.info("No records to sync")
        return
    
    # Get configuration values
    schema = TARGET_CONFIG['postgres_schema']
    table = TARGET_CONFIG['postgres_table']
    sync_time_var = f"last_sync_{table}_time"  # Dynamic variable name
    
    # Validate record structure
    try:
        sync_time = pendulum.now('UTC')
        data_to_insert = [
            (*record, sync_time) 
            for record in records
            if len(record) == 5  # Validate expected field count
        ]
        
        if len(data_to_insert) != len(records):
            logger.warning(
                f"Dropped {len(records) - len(data_to_insert)} invalid records"
            )
    except Exception as e:
        logger.error(f"Record validation failed: {str(e)}")
        raise AirflowException("Data validation error")
    
    # Build dynamic SQL
    insert_sql = f"""
    INSERT INTO {schema}.{table} (
        createdAt, updatedAt, id, companyRegionId, name, sync_time
    ) VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO UPDATE SET
        updatedAt = EXCLUDED.updatedAt,
        companyRegionId = EXCLUDED.companyRegionId,
        name = EXCLUDED.name,
        sync_time = EXCLUDED.sync_time
    """
    
    # Perform sync
    postgres_hook = get_postgres_ep_stage_hook()
    try:
        start_time = time.monotonic()
        with postgres_hook.get_conn() as conn:
            with conn.cursor() as cursor:
                extras.execute_batch(cursor, insert_sql, data_to_insert)
            conn.commit()
        
        duration = time.monotonic() - start_time
        logger.info(
            f"Synced {len(data_to_insert)} records to {schema}.{table} in {duration:.2f}s "
            f"({len(data_to_insert)/max(duration, 0.1):.1f} records/s)"
        )
        
        Variable.set(sync_time_var, sync_time.isoformat())
        logger.info(f"Updated {sync_time_var} to {sync_time}")
        
    except Exception as e:
        logger.error(f"Sync to {schema}.{table} failed after {len(data_to_insert)} records: {str(e)}")
        raise AirflowException(f"PostgreSQL sync to {table} failed")
    
with DAG(
    "sync_mysql_amtdb_customers_to_postgres",
    default_args=default_args,
    description="Sync MySQL AMTDB customers to Postgres in batches",
    #schedule='*/30 5-22 * * *',
    schedule='0 5-22 * * *',  # Runs at the top of every hour
    start_date=days_ago(1),
    catchup=False,
    tags=["sync", "mysql", "postgres"],
    max_active_runs=1,
    max_active_tasks=1
) as dag:
    
    connection_check = PythonOperator(
    task_id='verify_connections',
    python_callable=verify_connections
    )
    
    check_task = PythonOperator(
        task_id='check_if_table_exists_task',
        python_callable=check_if_table_exists,
    )
    
    create_task = PythonOperator(
        task_id='create_table_if_not_exists_task',
        python_callable=create_table_if_not_exists,
    )
    
    fetch_task = PythonOperator(
        task_id='fetch_customers_task',
        python_callable=fetch_customers,
    )
    
    sync_task = PythonOperator(
        task_id='sync_to_postgres_task',
        python_callable=sync_to_postgres,
    )
    
    connection_check >> check_task >> create_task >> fetch_task >> sync_task