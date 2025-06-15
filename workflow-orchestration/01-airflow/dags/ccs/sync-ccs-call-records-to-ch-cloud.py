from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
import os
from dotenv import load_dotenv
import logging
import requests
from datetime import datetime
import time
from airflow.utils.dates import days_ago
from airflow.exceptions import AirflowException
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import constants
from plugins.utils.defaults.v1.defaults import DEFAULT_ARGS, LOG_LEVELS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API endpoints
TOKEN_URL = "https://api.callcenterstudio.com/application/access_token/"
CALLS_URL = "https://api.callcenterstudio.com/v3/calls"

# Configuration
DAG_NAME = "ccs"
TARGET_CONFIG = {
    "ch_cloud_db_name": "ccs",
    "ch_table_name": "call_records",
}

def generate_api_access_token(**context):
    """Generate a new access token and store it in XCom."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Tenant": os.getenv("CCS_TENANT"),
    }
    payload = {
        "client_id": os.getenv("CCS_CLIENT_ID"),
        "client_secret": os.getenv("CCS_CLIENT_SECRET"),
    }
    try:
        response = requests.post(TOKEN_URL, headers=headers, json=payload)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data.get("access_token")
        logger.info("New access token retrieved.")
        context["ti"].xcom_push(key="access_token", value=access_token)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error generating access token: {e}")
        raise AirflowException(f"Error generating access token: {e}")

def fetch_api_records(**context):
    """Fetch call records using the access token and dynamic date range."""
    start_time = datetime.utcnow()
    access_token = context["ti"].xcom_pull(key="access_token", task_ids="generate_api_access_token")
    if not access_token:
        logger.error("No access token available.")
        raise AirflowException("No access token provided.")

    # Configure session with retries
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))

    def refresh_token():
        """Refresh access token."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Tenant": os.getenv("CCS_TENANT"),
        }
        payload = {
            "client_id": os.getenv("CCS_CLIENT_ID"),
            "client_secret": os.getenv("CCS_CLIENT_SECRET"),
        }
        try:
            response = session.post(TOKEN_URL, headers=headers, json=payload)
            response.raise_for_status()
            token_data = response.json()
            new_token = token_data.get("access_token")
            logger.info("Refreshed access token.")
            context["ti"].xcom_push(key="access_token", value=new_token)
            return new_token
        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing access token: {e}")
            raise AirflowException(f"Error refreshing access token: {e}")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "tenant": os.getenv("CCS_TENANT"),
    }
    base_params = {
        "start_date": "2025-04-21 12:00:00",  # Keep for testing
        "finish_date": "2025-04-27 11:59:00",
        "limit": 100,
    }

    # Log headers and parameters
    logger.info(f"Headers: Accept=application/json, Authorization=Bearer [masked], tenant={os.getenv('CCS_TENANT')}")
    logger.info(f"Parameters: start_date={base_params['start_date']}, finish_date={base_params['finish_date']}, limit={base_params['limit']}")

    # Load fields from fields.yml
    fields_config = load_fields_yml_files(DAG_NAME, "fields.yml")
    call_fields = fields_config.get("call_details_list", [])
    api_fields = [field["source"] for field in call_fields if field["source"] != "constant.utcnow"]
    logger.info(f"API fields: {api_fields}")

    all_records = []
    cursor = None
    request_count = 0
    token_refreshed = False
    invalid_datetime_values = set()  # Track unique invalid DateTime values to reduce log clutter

    while True:
        request_count += 1
        params = base_params.copy()
        if cursor:
            params["cursor"] = cursor
        try:
            logger.info(f"Fetching request {request_count} with cursor: {cursor or 'None'}, params: {params}")
            response = session.get(CALLS_URL, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            logger.info(f"API response keys: {list(data.keys())}")
            call_data = data.get("call_details_list", [])
            if not call_data:
                logger.info("No more records to fetch.")
                break

            # Transform and validate records
            for record in call_data:
                transformed_record = {}
                for field in call_fields:
                    field_name = field["name"]
                    source = field["source"]
                    field_type = field["type"]

                    if source == "constant.utcnow":
                        continue

                    value = record.get(source)
                    try:
                        if field_type.startswith("Nullable(String)"):
                            transformed_record[field_name] = str(value) if value is not None else None
                        elif field_type.startswith("Nullable(UInt8)"):
                            transformed_record[field_name] = int(value) if value in (0, 1, True, False) else None
                        elif field_type.startswith("Nullable(Int32)"):
                            transformed_record[field_name] = int(value) if isinstance(value, (int, float)) else None
                        elif field_type.startswith("Nullable(DateTime)"):
                            if value and isinstance(value, str):
                                try:
                                    # Use the format without microseconds, as API returns YYYY-MM-DD HH:MM:SS
                                    transformed_record[field_name] = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                                except ValueError as e:
                                    # Log only unique invalid values to reduce clutter
                                    if value not in invalid_datetime_values:
                                        logger.warning(f"Invalid DateTime for {field_name}: {value}, setting to None")
                                        invalid_datetime_values.add(value)
                                    transformed_record[field_name] = None
                            else:
                                transformed_record[field_name] = None
                        else:
                            transformed_record[field_name] = value
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to process {field_name} ({source}): {e}, setting to None")
                        transformed_record[field_name] = None

                all_records.append(transformed_record)

            logger.info(f"Fetched {len(call_data)} records. Total: {len(all_records)}.")
            cursor = data.get("cursor")
            if not cursor or len(call_data) < base_params["limit"]:
                logger.info("End of data reached.")
                break
            time.sleep(1)  # Delay to avoid rate limiting
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching records on request {request_count}: {e}")
            if isinstance(e, requests.exceptions.ConnectionError) and not token_refreshed:
                logger.info("Connection error detected, attempting to refresh token.")
                access_token = refresh_token()
                headers["Authorization"] = f"Bearer {access_token}"
                token_refreshed = True
                continue
            raise AirflowException(f"Error fetching records: {e}")

    # Log summary of invalid DateTime values
    if invalid_datetime_values:
        logger.info(f"Encountered {len(invalid_datetime_values)} unique invalid DateTime values: {invalid_datetime_values}")

    context["ti"].xcom_push(key="call_records", value=all_records)
    logger.info(f"Total records fetched: {len(all_records)} in {(datetime.utcnow() - start_time).total_seconds():.2f} seconds.")
    return {"total_records": len(all_records)}

def check_and_create_clickhouse_table(**context):
    """Check if ClickHouse table exists and create it if not."""
    client = get_clickhouse_cloud_client(database=TARGET_CONFIG["ch_cloud_db_name"])
    database = TARGET_CONFIG["ch_cloud_db_name"]
    table = TARGET_CONFIG["ch_table_name"]
    # Load check query (uses %s placeholders for parameterization)
    check_query = load_sql_files(DAG_NAME, "check-call-records-db-table.sql")
    # Load and format create query
    create_query = load_sql_files(DAG_NAME, "create-call-records-db-table.sql", database=database, table=table)
    try:
        client.command(f"CREATE DATABASE IF NOT EXISTS {database}")  # Ensure database exists
        # Log query and parameters for debugging
        logger.info(f"Executing check query: {check_query}")
        logger.info(f"Parameters: {database}, {table}")
        # Execute query and access result
        query_result = client.query(check_query, parameters=[database, table])
        logger.info(f"Query result: {query_result.result_rows}")
        result = query_result.result_rows[0][0]
        logger.info(f"Table '{database}.{table}' exists: {bool(result)}.")
        if not result:
            client.command(create_query)
            logger.info(f"Created table '{database}.{table}' in ClickHouse.")
        else:
            logger.info("Table already exists, skipping creation.")
    except Exception as e:
        logger.error(f"Failed to check/create table '{database}.{table}': {str(e)}")
        raise AirflowException(f"Table check/creation failed: {str(e)}")

def sync_api_records_to_clickhouse(**context):
    """Sync fetched records to ClickHouse and update last sync_time."""
    start_time = datetime.utcnow()
    call_records = context["ti"].xcom_pull(key="call_records", task_ids="fetch_api_records")
    if not call_records:
        logger.info("No records to sync to ClickHouse.")
        return

    # Load fields from fields.yml
    fields_config = load_fields_yml_files(DAG_NAME, "fields.yml")
    call_fields = fields_config.get("call_details_list", [])
    # Include all field names, including sync_time
    column_names = [field["name"] for field in call_fields]
    # Exclude sync_time for field_names used in transformation
    field_names = [field["name"] for field in call_fields if field["name"] != "sync_time"]

    records_tuples = []
    max_sync_time = datetime.utcnow()
    for record in call_records:
        if not isinstance(record, dict):
            logger.warning(f"Skipping invalid record (not a dict): {type(record).__name__}: {record}")
            continue
        try:
            record_values = tuple(record.get(field, None) for field in field_names)
            records_tuples.append(record_values)
        except Exception as e:
            logger.warning(f"Failed to process record {record.get('call_id', 'unknown')}: {str(e)}")
            continue

    if not records_tuples:
        logger.info("No valid records to sync after processing.")
        return

    records_with_timestamp = append_sync_time(records_tuples)
    logger.info(f"Sample record with timestamp: {records_with_timestamp[0]}")
    logger.info(f"Column names: {column_names}, length: {len(column_names)}")

    client = get_clickhouse_cloud_client(database=TARGET_CONFIG["ch_cloud_db_name"])
    database = TARGET_CONFIG["ch_cloud_db_name"]
    table = TARGET_CONFIG["ch_table_name"]

    batch_size = 100
    total_records = len(records_with_timestamp)
    try:
        for i in range(0, total_records, batch_size):
            batch = records_with_timestamp[i : i + batch_size]
            logger.info(f"Inserting batch {i // batch_size + 1} with {len(batch)} records")
            client.insert(
                database=database,
                table=table,
                data=batch,
                column_names=column_names
            )
            logger.info(f"Synced batch {i // batch_size + 1} with {len(batch)} records to ClickHouse.")
        logger.info(
            f"Synced {total_records} records to ClickHouse table '{database}.{table}' "
            f"in {(datetime.utcnow() - start_time).total_seconds():.2f} seconds."
        )
        # Update last sync_time in Airflow Variable
        Variable.set("ccs_last_sync_time", max_sync_time.strftime("%Y-%m-%d %H:%M:%S"))
        logger.info(f"Updated ccs_last_sync_time to {max_sync_time.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        logger.error(f"Error syncing records to ClickHouse: {str(e)}")
        raise AirflowException(f"Sync failed: {str(e)}")


with DAG(
    "sync-ccs-call-records-to-ch-cloud",
    default_args=DEFAULT_ARGS,
    description="Fetch CCS call records and sync to ClickHouse every hour",
    #schedule="0 6-21 * * 1-5",
    schedule=None,
    start_date=days_ago(1),
    catchup=False,
) as dag:
    generate_api_access_token_task = PythonOperator(
        task_id="generate_api_access_token",
        python_callable=generate_api_access_token,
        provide_context=True,
    )

    fetch_api_records_task = PythonOperator(
        task_id="fetch_api_records",
        python_callable=fetch_api_records,
        provide_context=True,
    )

    check_and_create_clickhouse_table_task = PythonOperator(
        task_id="check_and_create_clickhouse_table",
        python_callable=check_and_create_clickhouse_table,
        provide_context=True,
    )

    sync_api_records_to_clickhouse_task = PythonOperator(
        task_id="sync_api_records_to_clickhouse",
        python_callable=sync_api_records_to_clickhouse,
        provide_context=True,
    )

    # Task dependencies
    (
        generate_api_access_token_task
        >> fetch_api_records_task
        >> check_and_create_clickhouse_table_task
        >> sync_api_records_to_clickhouse_task
    )