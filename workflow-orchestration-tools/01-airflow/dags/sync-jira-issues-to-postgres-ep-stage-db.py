from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from plugins.utils import (
    default_args,
    requests,
    AirflowException,
    Variable,
    get_postgres_ep_stage_hook
)
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
from psycopg2.extras import execute_values

# Load environment variables from .env file
load_dotenv()

# Configure logging (use Airflow's logger)
logger = logging.getLogger(__name__)

# ================== CONFIGURATION ==================
# Jira configuration from .env
JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEYS = os.getenv("JIRA_PROJECT_KEYS", "SD").split(",")

# Target configuration (Postgres)
TARGET_CONFIG = {
    "postgres_schema": Variable.get("POSTGRES_SCHEMA", default_var="public"),
    "postgres_table": Variable.get("POSTGRES_TABLE", default_var="jira_issues"),
}

def verify_connections(**kwargs) -> None:
    """Verify PostgreSQL connection."""
    try:
        pg_hook = get_postgres_ep_stage_hook()
        with pg_hook.get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        logger.info("PostgreSQL connection verified")
    except Exception as e:
        logger.error(f"Connection verification failed: {str(e)}")
        raise AirflowException(f"Connection verification failed: {str(e)}")

def create_table_if_not_exists(**kwargs) -> None:
    """Create Jira issues table if it doesn't exist."""
    pg_hook = get_postgres_ep_stage_hook()
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
        table_exists = pg_hook.get_first(check_table_sql, parameters=(schema, table))[0]
        if table_exists:
            logger.info(f"Table {schema}.{table} already exists, skipping creation.")
            return

        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {schema}.{table} (
            issue_key VARCHAR(50) PRIMARY KEY,
            summary TEXT,
            issue_type VARCHAR(50),
            status VARCHAR(50),
            created TIMESTAMP,
            updated TIMESTAMP,
            priority VARCHAR(50),
            assignee VARCHAR(100),
            project_key VARCHAR(50),
            sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        pg_hook.run(create_table_sql)
        logger.info(f"Created table {schema}.{table}")
    except Exception as e:
        logger.error(f"Failed to check/create table {schema}.{table}: {str(e)}")
        raise AirflowException(f"Table creation failed: {str(e)}")
    
def fetch_jira_issues(**kwargs) -> list:
    """Fetch issues from multiple Jira projects with pagination."""
    logger.info(f"🔍 JIRA_URL from env: {JIRA_URL}")
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    headers = {"Accept": "application/json"}
    all_records = []

    for project_key in JIRA_PROJECT_KEYS:
        start_at = 0
        max_results = 100
        while True:
            try:
                url = f"{JIRA_URL}/rest/api/3/search"
                query = {
                    "jql": f"project = {project_key}",
                    "fields": "key,summary,issuetype,status,created,updated,priority,assignee,project",
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
                    fields = issue.get("fields") or {}

                    # Safely extract nested fields with .get and fallback to None
                    issue_key = issue.get("key")
                    summary = fields.get("summary")
                    issuetype = (fields.get("issuetype") or {}).get("name")
                    status = (fields.get("status") or {}).get("name")
                    created = fields.get("created")
                    updated = fields.get("updated")
                    priority = (fields.get("priority") or {}).get("name")
                    assignee = (fields.get("assignee") or {}).get("displayName")
                    project = (fields.get("project") or {}).get("key")

                    all_records.append((
                        issue_key,
                        summary,
                        issuetype,
                        status,
                        created,
                        updated,
                        priority,
                        assignee,
                        project,
                        datetime.utcnow()  # Current timestamp
                    ))

                start_at += max_results

            except Exception as e:
                logger.error(f"❌ Failed to fetch issues for project {project_key}: {str(e)}")
                raise AirflowException(f"Failed to fetch issues for project {project_key}: {str(e)}")

    logger.info(f"✅ Total records fetched: {len(all_records)}")
    return all_records

def sync_to_postgres(ti, **kwargs) -> None:
    """Sync fetched Jira issues to PostgreSQL."""
    records = ti.xcom_pull(task_ids="fetch_jira_issues")
    if not records:
        logger.info("No records to sync")
        return

    pg_hook = get_postgres_ep_stage_hook()
    schema = TARGET_CONFIG['postgres_schema']
    table = TARGET_CONFIG['postgres_table']

    upsert_query = f"""
    INSERT INTO {schema}.{table} (
        issue_key, summary, issue_type, status, 
        created, updated, priority, assignee, project_key, sync_time
    )
    VALUES %s
    ON CONFLICT (issue_key)
    DO UPDATE SET
        summary = EXCLUDED.summary,
        issue_type = EXCLUDED.issue_type,
        status = EXCLUDED.status,
        created = EXCLUDED.created,
        updated = EXCLUDED.updated,
        priority = EXCLUDED.priority,
        assignee = EXCLUDED.assignee,
        project_key = EXCLUDED.project_key,
        sync_time = CURRENT_TIMESTAMP;
    """

    try:
        with pg_hook.get_conn() as conn:
            with conn.cursor() as cur:
                execute_values(cur, upsert_query, records)
            conn.commit()
        logger.info(f"Synced {len(records)} records to {schema}.{table}")
    except Exception as e:
        logger.error(f"Failed to sync to {schema}.{table}: {e}")
        raise AirflowException(f"Sync failed: {e}")

with DAG(
    dag_id="sync_jira_issues_to_postgres_ep_stage_db",
    default_args=default_args,
    start_date=days_ago(1),
    schedule="@daily",
    catchup=False,
) as dag:

    # Task to verify connections
    verify_conn_task = PythonOperator(
        task_id="verify_connections",
        python_callable=verify_connections,
    )

    # Task to create table
    create_table_task = PythonOperator(
        task_id="create_table_if_not_exists",
        python_callable=create_table_if_not_exists,
    )

    # Task to fetch Jira issues
    fetch_task = PythonOperator(
        task_id="fetch_jira_issues",
        python_callable=fetch_jira_issues,
    )

    # Task to sync to Postgres
    sync_task = PythonOperator(
        task_id="sync_to_postgres",
        python_callable=sync_to_postgres,
    )

    # Set task dependencies
    verify_conn_task >> create_table_task >> fetch_task >> sync_task