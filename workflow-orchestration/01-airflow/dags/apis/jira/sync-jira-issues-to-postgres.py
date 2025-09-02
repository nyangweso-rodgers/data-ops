from airflow.decorators import dag, task
from datetime import datetime
from airflow.models import Variable
from plugins.hooks.pg_hook.v2.pg_hook import PostgresHook
from plugins.hooks.jira.v2.jira_hook import JiraApiHook
from plugins.utils.schema_loader.v2.schema_loader import SchemaLoader
import logging
from typing import List, Dict, Any
from plugins.utils.constants.v1.constants import SYNC_CONFIGS
from plugins.utils.defaults.v1.defaults import DEFAULT_ARGS

logger = logging.getLogger(__name__)

# Sync key for this DAG
SYNC_KEY = 'jira_issues_to_postgres'

# Function to add sync_time to records
def add_sync_time(records: List[Dict[str, Any]], target_schema: Dict[str, Any]) -> None:
    """
    Add sync_time to records based on target schema.
    
    Args:
        records: List of dictionaries containing issue data.
        target_schema: Target schema with column definitions.
    """
    sync_time = next((col for col, props in target_schema['columns'].items() if props.get('auto_generated')), None)
    if not sync_time:
        logger.warning("No auto_generated column found in target schema. Skipping sync_time addition.")
        return
    current_time = datetime.utcnow().isoformat() + 'Z'
    for record in records:
        record[sync_time] = current_time

@dag(
    dag_id="sync_jira_issues_to_postgres",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2025, 6, 2),
    #schedule=None,
    schedule="0 9 * * 1-5",  # Runs at 09:00 UTC (12:00 EAT) Mon-Fri
    catchup=False,
    tags=['jira', 'postgres', 'sync']
)
def sync_jira_issues_to_postgres():
    """
    Sync Jira issues to PostgreSQL using TaskFlow API.
    Fetches issues for configured project keys and upserts into PostgreSQL.
    Tracks sync time using jira_last_sync_timestamp_issues.
    Includes schema validation and connection checks for robustness.
    """

    @task
    def validate_schema() -> Dict:
        """
        Validate the issues.yml schema and return schema info.
        """
        if SYNC_KEY not in SYNC_CONFIGS:
            logger.error(f"Configuration for {SYNC_KEY} not found in SYNC_CONFIGS")
            raise KeyError(f"Configuration for {SYNC_KEY} not found in SYNC_CONFIGS")
        
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        if 'source' not in sync_config or 'target' not in sync_config:
            logger.error(f"Invalid configuration for {SYNC_KEY}: 'source' and 'target' are required")
            raise ValueError(f"Invalid configuration for {SYNC_KEY}")
        
        source_config = sync_config['source']
        target_config = sync_config['target']
        
        try:
            schema = SchemaLoader.load_schema(
                source_type=source_config['source_type'],
                source_subpath=source_config.get('source_subpath'),
                table_name=source_config['table'],
                target_type=target_config['target_type']
            )
            schema_info = {
                "columns": schema['target']['columns'],
                "mappings": schema['mappings']
            }
            
            logger.info(f"Schema validation successful for issues.yml: {len(schema_info['mappings'])} mappings")
            return schema_info
        except Exception as e:
            logger.error(f"Schema validation failed: {str(e)}")
            raise

    @task
    def check_jira_connection():
        """
        Test Jira API connection.
        """
        jira_hook = JiraApiHook(log_level='INFO')
        success, message = jira_hook.test_connection()
        logger.info(f"Jira connection test: {message}")
        if not success:
            raise ValueError(f"Jira connection failed: {message}")

    @task
    def check_postgres_connection():
        """
        Test PostgreSQL connection.
        """
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        if 'target' not in sync_config:
            logger.error(f"Invalid configuration for {SYNC_KEY}: 'target' is required")
            raise ValueError(f"Invalid configuration for {SYNC_KEY}")
        
        pg_hook = PostgresHook(
            conn_id=sync_config['target']['connection_id']
            #log_level='INFO'
        )
        success, message = pg_hook.test_connection()
        logger.info(f"PostgreSQL connection test: {message}")
        if not success:
            raise ValueError(f"PostgreSQL connection failed: {message}")

    @task
    def fetch_issues(schema_info: Dict) -> List[Dict]:
        """
        Fetch issues for configured project keys.
        
        Args:
            schema_info: Schema information from validate_schema.
        
        Returns:
            List of issue records.
        """
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        jira_hook = JiraApiHook(log_level='INFO')
        project_keys = [key.strip() for key in Variable.get('jira_project_keys', default_var='').split(',')]
        if not project_keys or all(not key for key in project_keys):
            raise ValueError("jira_project_keys is empty or invalid")
        last_sync_timestamp = Variable.get("jira_last_sync_timestamp_issues", default_var=None)
        
        all_issues = []
        try:
            for batch in jira_hook.fetch_issues(
                schema=schema_info,
                project_keys=project_keys,
                last_sync_timestamp=last_sync_timestamp,
                batch_size=50
            ):
                all_issues.extend(batch)
                logger.info(f"Processed batch of {len(batch)} issues")
        except Exception as e:
            logger.error(f"Failed to fetch issues: {str(e)}")
            raise
        
        if all_issues:
            current_sync = datetime.utcnow().isoformat() + "Z"
            Variable.set("jira_last_sync_timestamp_issues", current_sync)
            logger.info(f"Updated jira_last_sync_timestamp_issues to {current_sync}")
        
        logger.info(f"Fetched {len(all_issues)} total issues")
        return all_issues

    @task
    def ensure_table(issues: List[Dict], schema_info: Dict) -> Dict[str, str]:
        """
        Ensure the target table exists in PostgreSQL.
        
        Args:
            issues: List of issue records.
            schema_info: Schema information from validate_schema.
        
        Returns:
            Dictionary with table_name and schema_name.
        """
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        pg_hook = PostgresHook(
            conn_id=sync_config['target']['connection_id']
            #log_level='INFO'
        )
        table_name = sync_config['target']['table']
        schema_name = sync_config['target']['schema']
        
        columns = []
        for col, props in schema_info['columns'].items():
            col_def = f"{col} {props['type']}"
            if not props.get('nullable', True):
                col_def += " NOT NULL"
            if props.get('primary_key', False):
                col_def += " PRIMARY KEY"
            columns.append(col_def)
        
        try:
            created = pg_hook.create_table_if_not_exists(
                table_name=table_name,
                columns=columns,
                schema=schema_name
            )
            logger.info(f"Table {schema_name}.{table_name} {'created' if created else 'already exists'}")
        except Exception as e:
            logger.error(f"Failed to create table {schema_name}.{table_name}: {str(e)}")
            raise
        return {"table_name": table_name, "schema_name": schema_name}

    @task
    def sync_to_postgres(table_info: Dict[str, str], issues: List[Dict], schema_info: Dict):
        """
        Sync issues to PostgreSQL.
        
        Args:
            table_info: Dictionary with table_name and schema_name.
            issues: List of issue records.
            schema_info: Schema information from validate_schema.
        """
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        pg_hook = PostgresHook(
            conn_id=sync_config['target']['connection_id']
            #log_level='INFO'
        )
        
        if not issues:
            logger.warning("No issues to sync")
            return
        
        add_sync_time(issues, schema_info)
        
        try:
            rows_affected = pg_hook.upsert_rows(
                table_name=table_info['table_name'],
                rows=issues,
                schema=table_info['schema_name'],
                upsert_conditions=sync_config['target']['upsert_conditions']
            )
            logger.info(f"Upserted {rows_affected} issue records into {table_info['schema_name']}.{table_info['table_name']}")
        except Exception as e:
            logger.error(f"Failed to upsert issues: {str(e)}")
            raise

    # Define task instances
    schema_info = validate_schema()
    jira_conn = check_jira_connection()
    pg_conn = check_postgres_connection()
    issues = fetch_issues(schema_info)
    table_info = ensure_table(issues, schema_info)
    sync_task = sync_to_postgres(table_info, issues, schema_info)

    # Set dependencies
    [schema_info, jira_conn, pg_conn] >> issues
    issues >> table_info
    table_info >> sync_task

dag = sync_jira_issues_to_postgres()