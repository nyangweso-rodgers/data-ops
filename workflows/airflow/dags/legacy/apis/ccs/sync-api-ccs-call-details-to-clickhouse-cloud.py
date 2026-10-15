from airflow import DAG

from plugins.utils import (
    get_clickhouse_cloud_client
)

from plugins.utils.defaults.v1.defaults import DEFAULT_ARGS, LOG_LEVELS


import os
from dotenv import load_dotenv

import logging
import requests
from datetime import datetime, timedelta

from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow import DAG

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

# CCS object schema and fields
ccs_object_schema = {
    "call_details_list": {
        "call_key": "String",
        "call_id": "String",
        "is_answered": "Nullable(UInt8)",
        "is_assigned": "Nullable(UInt8)",
        "is_abandoned": "Nullable(UInt8)",
        "queue_date": "Nullable(DateTime)",
        "call_date": "Nullable(DateTime)",
        "talk_date": "Nullable(DateTime)",
        "hangup_date": "Nullable(DateTime)",
        "wait_duration": "Nullable(Int32)",
        "duration": "Nullable(Int32)",
        "is_short_call": "Nullable(UInt8)",
        "caller_id": "Nullable(String)",
        "called_number": "Nullable(String)",
        "queue_name": "Nullable(String)",
        "is_inbound": "Nullable(UInt8)",
        "agent_name": "Nullable(String)",
        "agent_email": "Nullable(String)",
        "hold_duration": "Nullable(Int32)",
        "has_voicemail": "Nullable(UInt8)",
        "unique_id": "Nullable(String)",
        "local_release": "Nullable(UInt8)",
        "answered_by": "Nullable(String)",
        "status": "Nullable(String)",
        "wrapup_code": "Nullable(String)",
        "voicemail_duration": "Nullable(Int32)",
        "disposition": "Nullable(String)",
        "has_csat": "Nullable(UInt8)",
        "csat_score": "Nullable(Int32)",
        "csat_completed": "Nullable(UInt8)",
        "csat_answers": "Nullable(String)",
        "csat": "Nullable(UInt8)",
        "black_list": "Nullable(UInt8)",
        "source_tenant": "Nullable(String)",
        "hangup_cause": "Nullable(String)",
        "transferred": "Nullable(UInt8)",
        "attendant_overflow": "Nullable(UInt8)",
        "campaign_name": "Nullable(String)",
        "channel": "Nullable(String)",
        "is_click2call": "Nullable(UInt8)",
        "is_ivr_click2call": "Nullable(UInt8)"
    }
}
ccs_object_fields = {"call_details_list": list(ccs_object_schema["call_details_list"].keys())}

def generate_api_access_token(**context):
    """Generate a new access token and store it in XCom."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Tenant": os.getenv("CCS_TENANT")
    }
    payload = {
        "client_id": os.getenv("CCS_CLIENT_ID"),
        "client_secret": os.getenv("CCS_CLIENT_SECRET")
    }
    try:
        response = requests.post(TOKEN_URL, headers=headers, json=payload)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data.get("access_token")
        logger.info("New access token retrieved.")
        context['ti'].xcom_push(key='access_token', value=access_token)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error generating access token: {e}")
        raise

def fetch_api_records(**context):
    """Fetch call records using the access token and dynamic date range."""
    access_token = context['ti'].xcom_pull(key='access_token', task_ids='generate_api_access_token')
    if not access_token:
        logger.error("No access token available.")
        raise ValueError("No access token provided.")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "tenant": os.getenv("CCS_TENANT")
    }
    # Dynamic date range: last hour
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(hours=1)
    base_params = {
        "start_date": start_date.strftime("%Y-%m-%d %H:%M:%S"),
        "finish_date": end_date.strftime("%Y-%m-%d %H:%M:%S"),
        "limit": 100
    }

    all_records = []
    cursor = None
    request_count = 0

    while True:
        request_count += 1
        params = base_params.copy()
        if cursor:
            params["cursor"] = cursor
        try:
            logger.info(f"Fetching request {request_count} with cursor: {cursor or 'None'}...")
            response = requests.get(CALLS_URL, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            call_data = data.get("call_details_list", [])
            if not call_data:
                logger.info("No more records to fetch.")
                break
            filtered_data = [{k: record.get(k) for k in ccs_object_fields["call_details_list"]} for record in call_data]
            all_records.extend(filtered_data)
            logger.info(f"Fetched {len(call_data)} records. Total: {len(all_records)}.")
            cursor = data.get("cursor")
            if not cursor:
                logger.info("No cursor returned; end of data.")
                break
            if len(call_data) < base_params["limit"]:
                logger.info("Fewer records than limit; end of data.")
                break
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching records on request {request_count}: {e}")
            raise
    context['ti'].xcom_push(key='call_records', value=all_records)
    logger.info(f"Total records fetched: {len(all_records)}.")

def check_if_clickhouse_table_exists(**context):
    """Check if the ClickHouse table exists."""
    client = get_clickhouse_cloud_client()
    table_name = "call_records"
    query = f"EXISTS TABLE {table_name}"
    result = client.command(query)
    context['ti'].xcom_push(key='table_exists', value=bool(result))
    logger.info(f"Table '{table_name}' exists: {bool(result)}.")

def create_clickhouse_table_if_not_exists(**context):
    """Create the ClickHouse table if it doesn't exist."""
    table_exists = context['ti'].xcom_pull(key='table_exists', task_ids='check_if_clickhouse_table_exists')
    if table_exists:
        logger.info("Table already exists, skipping creation.")
        return

    client = get_clickhouse_cloud_client()
    table_name = "call_records"
    columns = [f"{field} {field_type}" for field, field_type in ccs_object_schema["call_details_list"].items()]
    columns.append("inserted_at DateTime DEFAULT now()")
    create_table_query = f"""
    CREATE TABLE {table_name}
    (
        {', '.join(columns)}
    )
    ENGINE = MergeTree()
    ORDER BY (call_id, inserted_at)
    """
    try:
        client.command(create_table_query)
        logger.info(f"Created table '{table_name}' in ClickHouse.")
    except Exception as e:
        logger.error(f"Failed to create table '{table_name}': {str(e)}")
        raise

def sync_api_records_to_clickhouse(**context):
    """Sync fetched records to ClickHouse."""
    call_records = context['ti'].xcom_pull(key='call_records', task_ids='fetch_api_records')
    if not call_records:
        logger.warning("No records to sync to ClickHouse.")
        return

    client = get_clickhouse_cloud_client()
    table_name = "call_records"
    datetime_fields = {
        field for field, field_type in ccs_object_schema["call_details_list"].items()
        if "DateTime" in field_type
    }
    column_names = list(ccs_object_schema["call_details_list"].keys())
    data_to_insert = []
    invalid_datetime_count = 0

    for record in call_records:
        transformed_record = {}
        for col in column_names:
            value = record.get(col)
            if col in datetime_fields:
                if value == "None" or value is None:
                    transformed_record[col] = None
                else:
                    try:
                        transformed_record[col] = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
                    except (ValueError, TypeError):
                        transformed_record[col] = None
                        invalid_datetime_count += 1
            else:
                transformed_record[col] = value
        row = [transformed_record[col] for col in column_names]
        data_to_insert.append(row)

    if invalid_datetime_count > 0:
        logger.warning(f"Encountered {invalid_datetime_count} invalid datetime values, set to None.")
    
    try:
        client.insert(table_name, data_to_insert, column_names=column_names)
        logger.info(f"Synced {len(call_records)} records to ClickHouse table '{table_name}'.")
    except Exception as e:
        logger.error(f"Error syncing records to ClickHouse: {str(e)}")
        raise

with DAG(
    'sync_api_ccs_call_records_to_ch_cloud',
    default_args=DEFAULT_ARGS,
    description='Fetch CCS call records and sync to ClickHouse every hour',
    schedule='0 6-21 * * 1-5',
    start_date=days_ago(1),
    catchup=False,
) as dag:
    generate_api_access_token_task = PythonOperator(
        task_id='generate_api_access_token',
        python_callable=generate_api_access_token,
        provide_context=True,
    )

    fetch_api_records_task = PythonOperator(
        task_id='fetch_api_records',
        python_callable=fetch_api_records,
        provide_context=True,
    )

    check_if_clickhouse_table_exists_task = PythonOperator(
        task_id='check_if_clickhouse_table_exists',
        python_callable=check_if_clickhouse_table_exists,
        provide_context=True,
    )

    create_clickhouse_table_if_not_exists_task = PythonOperator(
        task_id='create_clickhouse_table_if_not_exists',
        python_callable=create_clickhouse_table_if_not_exists,
        provide_context=True,
    )

    sync_api_records_to_clickhouse_task = PythonOperator(
        task_id='sync_api_records_to_clickhouse',
        python_callable=sync_api_records_to_clickhouse,
        provide_context=True,
    )

    # Task dependencies
    (
        generate_api_access_token_task
        >> fetch_api_records_task
        >> check_if_clickhouse_table_exists_task
        >> create_clickhouse_table_if_not_exists_task
        >> sync_api_records_to_clickhouse_task
    )