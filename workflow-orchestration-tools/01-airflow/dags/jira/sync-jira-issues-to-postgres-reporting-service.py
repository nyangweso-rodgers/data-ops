from plugins.utils import (
    DAG,
    PythonOperator,
    default_args,
    days_ago,
    requests,
    AirflowException,
    Variable,
    load_sql_files,
    load_fields_yml_files,
    append_sync_time  ,
    get_postgres_reporting_service_db_hook
)
from datetime import datetime
from requests.auth import HTTPBasicAuth
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging (use Airflow's logger)
logger = logging.getLogger(__name__)

# ================== CONFIGURATION ==================
# Jira configuration from .env
JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
#JIRA_PROJECT_KEYS = os.getenv("JIRA_PROJECT_KEYS", "SD").split(",")
JIRA_PROJECT_KEYS = [key.strip() for key in os.getenv("JIRA_PROJECT_KEYS", "SD").split(",")]

# Target configuration (Postgres)
TARGET_CONFIG = {
    "postgres_schema": Variable.get("POSTGRES_SCHEMA", default_var="jira"),
    "postgres_table": Variable.get("POSTGRES_TABLE", default_var="jira_issues"),
}

def verify_connections(**kwargs) -> None:
    """Verify PostgreSQL connection."""
    try:
        pg_hook = get_postgres_reporting_service_db_hook()
        with pg_hook.get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        logger.info("PostgreSQL connection verified")
    except Exception as e:
        logger.error(f"Connection verification failed: {str(e)}")
        raise AirflowException(f"Connection verification failed: {str(e)}")
    
def check_and_create_db_table_if_not_exists(**kwargs) -> None:
    pg_hook = get_postgres_reporting_service_db_hook()
    schema = TARGET_CONFIG['postgres_schema']
    table = TARGET_CONFIG['postgres_table']
    
    try:
        check_db_table_sql = load_sql_files("jira", "check-jira-issues-table.sql")
        db_table_exists = pg_hook.get_first(
            check_db_table_sql, parameters=(schema, table)
        )[0]
        if db_table_exists:
            logger.info(f"Database Table {schema}.{table} already exists, skipping creation..............")
            return
        create_db_table_sql = load_sql_files("jira", "create-jira-issues-table.sql").format(schema=schema, table=table)
        pg_hook.run(create_db_table_sql)
        logger.info(f"Created database table {schema}.{table}")
    except Exception as e:
        logger.error(f"Failed to check/create table {schema}.{table}: {str(e)}")
        raise AirflowException(f"Table creation failed: {str(e)}")

def fetch_jira_issues(**kwargs) -> dict:
    """Fetch issues from multiple Jira projects with pagination."""
    logger.info(f"🔍 JIRA_URL from env: {JIRA_URL}")
    logger.info(f"✅ Project keys to sync: {JIRA_PROJECT_KEYS}")
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    headers = {"Accept": "application/json"}
    
    # Load fields from fields.yml
    fields_config = load_fields_yml_files("jira", "fields.yml")
    jira_issues_fields = fields_config.get("jira_issues_fields", [])
    
    # Extract base field names for JQL query
    jira_fields = []
    for field in jira_issues_fields:
        source = field["source"]
        if source == "constant.utcnow":
            continue
        # Take the parent field for API (e.g., 'fields.priority.name' -> 'priority')
        api_field = source.split(".", 2)[1] if source.startswith("fields.") else source
        jira_fields.append(api_field)
    jira_fields = list(set(jira_fields))  # Remove duplicates
    
    logger.info(f"Requesting Jira fields: {jira_fields}")
    
    all_records = []

    for project_key in JIRA_PROJECT_KEYS:
        start_at = 0
        max_results = 100
        while True:
            try:
                url = f"{JIRA_URL}/rest/api/3/search"
                query = {
                    "jql": f"project = {project_key}",
                    "fields": ",".join(jira_fields),
                    "maxResults": max_results,
                    "startAt": start_at
                }
                response = requests.get(url, headers=headers, params=query, auth=auth)
                response.raise_for_status()
                data = response.json()
                
                issues = data.get("issues", [])
                if not issues:
                    break

                for issue in issues:
                    record = {}
                    for field in jira_issues_fields:
                        field_name = field["name"]
                        source = field["source"]
                        field_type = field["type"]
                        
                        if source == "constant.utcnow":
                            continue
                        
                        try:
                            value = issue
                            for key in source.split("."):
                                value = value.get(key, None) if isinstance(value, dict) else None
                                if value is None:
                                    break
                            
                            # Type validation based on field_type
                            if field_type.startswith("VARCHAR") or field_type == "TEXT":
                                if not isinstance(value, (str, type(None))):
                                    logger.warning(
                                        f"Field {field_name} ({source}) expected str, got {type(value).__name__} for issue {issue.get('key')}. Setting to None."
                                    )
                                    record[field_name] = None
                                else:
                                    record[field_name] = value
                            elif field_type == "BOOLEAN":
                                if not isinstance(value, (bool, type(None))):
                                    logger.warning(
                                        f"Field {field_name} ({source}) expected bool, got {type(value).__name__} for issue {issue.get('key')}. Setting to False."
                                    )
                                    record[field_name] = False
                                else:
                                    record[field_name] = value if value is not None else False
                            elif field_type == "TIMESTAMP":
                                if not isinstance(value, (str, type(None))) or (isinstance(value, str) and not value.startswith("20")):
                                    logger.warning(
                                        f"Field {field_name} ({source}) expected timestamp, got {type(value).__name__} for issue {issue.get('key')}. Setting to None."
                                    )
                                    record[field_name] = None
                                else:
                                    record[field_name] = value
                            else:
                                record[field_name] = value
                        
                        except Exception as e:
                            logger.warning(f"Failed to extract {source} for issue {issue.get('key')}: {str(e)}")
                            record[field_name] = None
                    
                    all_records.append(record)
                
                start_at += max_results
                
            except Exception as e:
                logger.error(f"❌ Failed to fetch issues for project {project_key}: {str(e)}")
                raise AirflowException(f"Failed to fetch issues for project {project_key}: {str(e)}")

    # Push records to XCom for downstream tasks
    logger.info(f"✅ Total records fetched: {len(all_records)}")
    kwargs["ti"].xcom_push(key="jira_issues", value=all_records)
    
    # Return a summary instead of the full records
    return {"total_records": len(all_records), "project_keys": JIRA_PROJECT_KEYS}

def sync_jira_issues_to_postgres(ti, **kwargs) -> None:
    """Sync fetched Jira issues to PostgreSQL."""
    # Pull XCom key
    records = ti.xcom_pull(key="jira_issues", task_ids="fetch_jira_issues")
    if not records:
        logger.info("No jira issues records to sync to PostgreSQL.")
        return
    
    # Load fields from fields.yml
    fields_config = load_fields_yml_files("jira", "fields.yml")
    jira_issues_fields = fields_config.get("jira_issues_fields", [])
    
    # Exclude sync_time from field_names since it's added by append_sync_time
    field_names = [field["name"] for field in jira_issues_fields if field["name"] != "sync_time"]
    
    # Convert records to tuples matching the table structure (excluding sync_time)
    records_tuples = [
        tuple(record.get(field, None) for field in field_names)
        for record in records
    ]
    
    # Append sync_time timestamp to each record
    records_with_sync_time = append_sync_time(records_tuples)
    
    pg_hook = get_postgres_reporting_service_db_hook()
    schema = TARGET_CONFIG['postgres_schema']
    table = TARGET_CONFIG['postgres_table']
    
    upsert_query = load_sql_files("jira", "upsert-jira-issues.sql").format(schema=schema, table=table)
    
    try:
        with pg_hook.get_conn() as conn:
            with conn.cursor() as cur:
                execute_values(cur, upsert_query, records_with_sync_time)
            conn.commit()
        logger.info(f"Synced {len(records_with_sync_time)} records to {schema}.{table}")
    except Exception as e:
        logger.error(f"Failed to sync jira issues to {schema}.{table}: {e}")
        raise AirflowException(f"Sync failed: {e}")

with DAG(
    dag_id="sync-jira-issues-to-postgres-reporting-service",
    default_args=default_args,
    start_date=days_ago(1),
    schedule=None,
    catchup=False,
) as dag:

    # Task to verify connections
    verify_conn_task = PythonOperator(
        task_id="verify_connections",
        python_callable=verify_connections,
    )

    # Task to create table
    check_and_create_db_table_if_not_exists_task = PythonOperator(
        task_id="check_and_create_db_table_if_not_exists",
        python_callable=check_and_create_db_table_if_not_exists,
    )

    # Task to fetch Jira issues
    fetch_jira_issues_task = PythonOperator(
        task_id="fetch_jira_issues",
        python_callable=fetch_jira_issues,
    )

    # Task to sync to Postgres
    sync_jira_issues_to_postgres_task = PythonOperator(
        task_id="sync_jira_issues_to_postgres",
        python_callable=sync_jira_issues_to_postgres,
    )

    # Set task dependencies
    verify_conn_task >> check_and_create_db_table_if_not_exists_task >> fetch_jira_issues_task >> sync_jira_issues_to_postgres_task