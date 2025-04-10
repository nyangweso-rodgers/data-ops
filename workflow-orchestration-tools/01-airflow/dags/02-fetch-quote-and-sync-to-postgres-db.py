from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago
import requests
import logging

# Set up logging
logger = logging.getLogger(__name__)

def get_postgres_hook():
    """Return a PostgresHook instance for the users database."""
    return PostgresHook(postgres_conn_id='postgres_users_db')

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

# Function to check if table exists and create it if not
def check_and_create_table():
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Check if table exists
    check_query = """
    SELECT EXISTS (
        SELECT FROM pg_tables
        WHERE schemaname = 'public' AND tablename = 'quotes'
    );
    """
    table_exists = pg_hook.get_first(check_query)[0]
    logger.info(f"Table 'quotes' exists: {table_exists}")

    # Create table if it doesn't exist
    if not table_exists:
        create_query = """
        CREATE TABLE quotes (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            author VARCHAR(255),
            inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        pg_hook.run(create_query)
        logger.info("Table 'quotes' created successfully.")
    else:
        logger.info("Table 'quotes' already exists, skipping creation.")

# Function to fetch a quote and insert it into the table
def fetch_and_insert_quote():
    pg_hook = get_postgres_hook()  # Use the new function

    # Fetch random quote
    try:
        response = requests.get("http://api.quotable.io/random", timeout=5)
        response.raise_for_status()  # Raise exception for bad HTTP status
        data = response.json()
        quote_content = data['content']
        quote_author = data['author']
        logger.info(f"Quote fetched: '{quote_content}' by {quote_author}")
    except Exception as e:
        logger.error(f"Failed to fetch quote: {str(e)}")
        raise  # Re-raise to fail the task and trigger retries

    # Insert quote into the table
    insert_query = """
    INSERT INTO quotes (content, author)
    VALUES (%s, %s);
    """
    pg_hook.run(insert_query, parameters=(quote_content, quote_author))
    logger.info("Quote inserted into database successfully.")

# Define the DAG
with DAG(
    'quote_fetcher_dag',
    default_args=default_args,
    description='A DAG to check/create a table and insert random quotes',
    schedule_interval='0 * * * *',  # Runs daily; adjust as needed
    start_date=days_ago(1),
    catchup=False,
) as dag:

    # Task 1: Check and create table
    check_table_task = PythonOperator(
        task_id='check_and_create_table',
        python_callable=check_and_create_table,
    )

    # Task 2: Fetch and insert quote
    fetch_quote_task = PythonOperator(
        task_id='fetch_and_insert_quote',
        python_callable=fetch_and_insert_quote,
    )

    # Set task dependencies
    check_table_task >> fetch_quote_task