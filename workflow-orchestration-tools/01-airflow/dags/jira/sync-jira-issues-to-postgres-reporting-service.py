from airflow.decorators import dag, task
from datetime import datetime
from airflow.utils.dates import days_ago
from airflow.models import Variable
from plugins.hooks.postgres_hook import PostgresHook
from plugins.hooks.jira_api_hook import JiraApiHook
from plugins.utils.schema_loader import SchemaLoader
from plugins.utils.add_sync_time import add_sync_time
from plugins.utils.constants import CONNECTION_IDS, DEFAULT_ARGS
import logging
from typing import List, Dict, Any
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)

# Environment-specific configuration
TARGET_SCHEMA_NAME = Variable.get("postgres_target_schema", default_var="jira")
DATABASE_TYPE = "postgres"

@dag(
    dag_id="sync_jira_issues_to_postgres_reporting_service",
    default_args=DEFAULT_ARGS,
    start_date=days_ago(1),
    schedule=None,
    catchup=False,
)
def sync_jira_issues_to_postgres_reporting_service():
    """
    A DAG that syncs Jira issues to PostgreSQL using TaskFlow API.
    Uses JiraApiHook to fetch data and upserts into PostgreSQL.
    Tracks updated timestamp for incremental refreshes using Airflow Variables.
    Uses add_sync_time for consistent sync time tracking.
    Supports advanced column mappings (e.g., createdAt → created_at).
    """
    
    @task 
    def validate_schema():
        logger.info("Validating schema compatibility")
        config = SchemaLoader.get_combined_schema(
            source_type="jira",
            source_subpath="",
            target_type="postgres",
            table_name="jira_issues",
            source_table_name="issues",
            target_subpath="reporting_service"
        )
        # Inject environment-specific settings
        config["target"]["schema_name"] = TARGET_SCHEMA_NAME
        config["target"]["database_type"] = DATABASE_TYPE
        logger.info("Schema validation successful")
        return config
    
    @task
    def test_connections():
        logger.info("Testing connections")
        
        pg_hook = PostgresHook(conn_id=CONNECTION_IDS['postgres_reporting_service'], log_level='INFO', connect_timeout=10)
        pg_success, pg_message = pg_hook.test_connection()
        if not pg_success:
            raise Exception(f"PostgreSQL connection failed: {pg_message}")
        
        try:
            jira_url = Variable.get("jira_url")
            jira_email = Variable.get("jira_email")
            jira_api_token = Variable.get("jira_api_token")
            jira_project_keys = Variable.get("jira_project_keys")
        except KeyError as e:
            missing_var = str(e).strip("'")
            logger.error(f"Missing Airflow Variable: {missing_var}")
            raise KeyError(f"Airflow Variable '{missing_var}' is not set")
        
        if not jira_project_keys:
            logger.error("jira_project_keys cannot be empty")
            raise ValueError("Airflow Variable 'jira_project_keys' is empty")
        
        project_keys = [key.strip() for key in jira_project_keys.split(",")]
        
        jira_hook = JiraApiHook(
            url=jira_url,
            email=jira_email,
            api_token=jira_api_token,
            project_keys=project_keys
        )
        jira_success, jira_message = jira_hook.test_connection()
        if not jira_success:
            raise Exception(f"Jira API connection failed: {jira_message}")
        
        logger.info("All connections successful")
        return {"postgres": pg_message, "jira": jira_message}
    
    @task
    def fetch_jira_issues(config: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info("Fetching data from Jira API")
        mappings = config["mappings"]
        
        try:
            jira_url = Variable.get("jira_url")
            jira_email = Variable.get("jira_email")
            jira_api_token = Variable.get("jira_api_token")
            jira_project_keys = Variable.get("jira_project_keys")
        except KeyError as e:
            missing_var = str(e).strip("'")
            logger.error(f"Missing Airflow Variable: {missing_var}")
            raise KeyError(f"Airflow Variable '{missing_var}' is not set")
        
        if not jira_project_keys:
            logger.error("jira_project_keys cannot be empty")
            raise ValueError("Airflow Variable 'jira_project_keys' is empty")
        
        project_keys = [key.strip() for key in jira_project_keys.split(",")]
        
        jira_hook = JiraApiHook(
            url=jira_url,
            email=jira_email,
            api_token=jira_api_token,
            project_keys=project_keys
        )
        
        jira_fields = []
        for mapping in mappings:
            if mapping.get("generated", False):
                continue
            source_path = mapping.get("source_path")
            if source_path and source_path.startswith("fields."):
                api_field = source_path.split(".", 1)[1].split(".", 1)[0]
                jira_fields.append(api_field)
        jira_fields = list(set(jira_fields))
        logger.info(f"Requesting Jira fields: {jira_fields}")
        
        last_sync_str = Variable.get("jira_last_sync_timestamp", default_var=None)
        
        issues = jira_hook.fetch_issues(fields=jira_fields, last_sync_timestamp=last_sync_str)
        
        all_records = []
        for issue in issues:
            record = {}
            for mapping in mappings:
                if mapping.get("generated", False):
                    continue
                field_name = mapping["target"]
                source_path = mapping.get("source_path")
                
                try:
                    value = issue
                    for key in source_path.split("."):
                        value = value.get(key, None) if isinstance(value, dict) else None
                        if value is None:
                            break
                    
                    expected_type = mapping["source_type"]
                    if expected_type == "string" and not isinstance(value, (str, type(None))):
                        logger.warning(f"Field {field_name} expected string, got {type(value).__name__}. Setting to None.")
                        value = None
                    elif expected_type == "timestamp" and not isinstance(value, (str, type(None))):
                        logger.warning(f"Field {field_name} expected timestamp, got {type(value).__name__}. Setting to None.")
                        value = None
                    elif expected_type == "boolean" and not isinstance(value, (bool, type(None))):
                        logger.warning(f"Field {field_name} expected boolean, got {type(value).__name__}. Setting to False.")
                        value = False
                    
                    record[field_name] = value
                
                except Exception as e:
                    logger.warning(f"Failed to extract {source_path} for issue {issue.get('key')}: {str(e)}")
                    record[field_name] = None
            
            all_records.append(record)
        
        if all_records:
            current_sync = datetime.utcnow().isoformat() + "Z"
            Variable.set("jira_last_sync_timestamp", current_sync)
            logger.info(f"Updated jira_last_sync_timestamp to {current_sync}")
        
        logger.info(f"Processed {len(all_records)} total records from Jira")
        return all_records
    
    @task
    def create_postgres_table(config: Dict[str, Any]):
        logger.info(f"Creating or updating table {config['target']['schema_name']}.jira_issues in PostgreSQL")
        hook = PostgresHook(conn_id=CONNECTION_IDS['postgres_reporting_service'], log_level='INFO', connect_timeout=10)
        mappings = config["mappings"]
        
        table_name = "jira_issues"
        schema_name = config["target"]["schema_name"]
        columns = [
            f"{m['target']} {m['target_type']}{' PRIMARY KEY' if m['target'] == 'issue_key' else ''}"
            for m in mappings
        ]
        
        # Check existing table schema
        try:
            existing_columns = hook.get_table_columns(schema_name, table_name)
            expected_columns = {m["target"] for m in mappings}
            existing_column_names = {c["column_name"] for c in existing_columns}
            
            # Add missing columns
            for m in mappings:
                if m["target"] not in existing_column_names:
                    logger.info(f"Adding column {m['target']} to {schema_name}.{table_name}")
                    column_def = f"{m['target']} {m['target_type']}"
                    if m["target"] == "issue_key":
                        column_def += " PRIMARY KEY"
                    alter_query = f"ALTER TABLE {schema_name}.{table_name} ADD COLUMN {column_def}"
                    hook.execute_query(alter_query)
                    logger.info(f"Added column {m['target']}")
        except Exception as e:
            logger.warning(f"Failed to check or alter table schema: {e}. Proceeding with table creation.")
        
        # Create table if it doesn't exist
        created = hook.create_table_if_not_exists(
            table_name=table_name,
            columns=columns,
            schema=schema_name
        )
        logger.info(f"Table {schema_name}.{table_name} creation status: {'Created' if created else 'Already exists or updated'}")
        return {"table_name": table_name, "schema_name": schema_name}
    
    @task
    def upsert_to_postgres(table_info: Dict[str, str], records: List[Dict[str, Any]], config: Dict[str, Any]):
        logger.info(f"Upserting data into PostgreSQL table {table_info['schema_name']}.{table_info['table_name']}")
        hook = PostgresHook(conn_id=CONNECTION_IDS['postgres_reporting_service'], log_level='INFO', connect_timeout=10)
        mappings = config["mappings"]
        
        if not records:
            logger.warning("No records to upsert")
            return 0
        
        # Add sync_time using utility
        add_sync_time(records, config["target"])
        
        columns = [m["target"] for m in mappings]
        upsert_conditions = config["target"].get("upsert_conditions", ["issue_key"])
        
        # Prepare values for upsert
        values = []
        for record in records:
            row = []
            for col in columns:
                value = record.get(col)
                # Ensure timestamp format for Postgres
                if col in ["created", "resolutiondate", "updated", "sync_time"] and value:
                    try:
                        # Convert ISO 8601 to Postgres-compatible format
                        value = datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
                    except ValueError:
                        logger.warning(f"Invalid timestamp format for {col}: {value}. Setting to None.")
                        value = None
                row.append(value)
            values.append(tuple(row))
        
        update_cols = [col for col in columns if col not in upsert_conditions]
        insert_query = f"""
            INSERT INTO {table_info['schema_name']}.{table_info['table_name']} ({', '.join(columns)})
            VALUES %s
            ON CONFLICT ({', '.join(upsert_conditions)})
            DO UPDATE SET
                {', '.join(f"{col} = EXCLUDED.{col}" for col in update_cols)}
        """
        
        batch_size = 100
        total_records = len(values)
        rows_affected = 0
        
        try:
            with hook.get_conn() as conn:
                with conn.cursor() as cur:
                    for i in range(0, total_records, batch_size):
                        batch = values[i:i + batch_size]
                        execute_values(cur, insert_query, batch)
                        rows_affected += cur.rowcount
                        logger.info(f"Upserted batch {i // batch_size + 1} with {len(batch)} records")
                conn.commit()
            logger.info(f"Upserted {rows_affected} rows into {table_info['schema_name']}.{table_info['table_name']}")
            return rows_affected
        except Exception as e:
            logger.error(f"Failed to upsert records: {str(e)}")
            raise
    
    config = validate_schema()
    conn_test = test_connections()
    jira_data = fetch_jira_issues(config)
    table_info = create_postgres_table(config)
    upserted = upsert_to_postgres(table_info, jira_data, config)
    
    config >> conn_test
    conn_test >> table_info
    config >> jira_data
    table_info >> upserted

dag = sync_jira_issues_to_postgres_reporting_service()