from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from plugins.utils.schema_loader.load_yaml_schema.v2.load_yaml_schema import LoadYamlSchema
from plugins.utils.schema_validation.validate_yaml_schema.v2.validate_yaml_schema import ValidateYamlSchema
from plugins.hooks.pg_hook.v3.pg_hook import PostgresSourceHook, PostgresTargetHook
from plugins.utils.defaults.v1.defaults import DEFAULT_ARGS
from airflow.models import Variable
import logging
import yaml
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

# Configure logging for this DAG module
logger = logging.getLogger(__name__)

@dag(
    dag_id='sync_pg_sunculture_ep_premises_to_pg_reporting_service',
    default_args=DEFAULT_ARGS,
    start_date=days_ago(1),
    schedule=None,
    catchup=False,
)
def sync_pg_sunculture_ep_premises_to_pg_reporting_service():
    """
    DAG to synchronize the premises table from PostgreSQL sunculture_ep to reporting-service.
    Validates connections, tables, and syncs data incrementally.
    """
    
    @task
    def load_sync_config(ti=None) -> Dict[str, Any]:
        """
        Load the sync job config file for premises.yml.
        Pushes config to XCom.
        """
        try:
            # Define config directory
            configs_dir = Path(os.getenv("CONFIGS_DIR", "/opt/airflow/configs/sync_configs"))
            job_path = "sync_pg_sunculture_ep_to_pg_reporting_service/premises"
            config_path = configs_dir / f"{job_path}.yml"
            logger.info(f"Attempting to load config from: {config_path}")

            # Check file existence
            if not config_path.exists():
                raise FileNotFoundError(f"Config file not found: {config_path}")

            # Load config
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            if config is None:
                raise ValueError(f"Config file {config_path} is empty")

            # Validate required fields
            required_fields = {
                "job_id": [],
                "source": ["airflow_connection_id", "database", "schema", "table", "batch_size", "incremental_column"],
                "target": ["airflow_connection_id", "database", "schema", "table", "batch_size", "upsert_conditions"],
                "schemas": ["source"],
                "schemas.source": ["filesystem"]
            }
            for section, fields in required_fields.items():
                parts = section.split(".")
                current = config
                for part in parts:
                    if part not in current:
                        raise ValueError(f"Missing {section} in config")
                    current = current[part]
                for field in fields:
                    if field not in current:
                        raise ValueError(f"Missing {field} in {section} config")

            logger.info(f"Loaded sync job config: {config['job_id']}")

            # Push to XCom
            ti.xcom_push(key="config", value=config)
            return {"config_job_id": config["job_id"], "config_path": str(config_path)}
        except Exception as e:
            logger.error(f"Error in load_sync_config: {str(e)}")
            raise

    @task
    def load_yaml_schema_file(ti=None) -> Dict[str, Any]:
        """
        Load the schema file specified in the sync config.
        Pushes schema to XCom.
        """
        try:
            config = ti.xcom_pull(task_ids="load_sync_config", key="config")
            if config is None:
                raise ValueError("No config found in XCom for task load_sync_config")

            # Get schema path
            schema_path = config["schemas"]["source"]["filesystem"]
            config_path = Path(os.getenv("CONFIGS_DIR", "/opt/airflow/configs/sync_configs")) / "sync_pg_sunculture_ep_to_pg_reporting_service/premises.yml"
            logger.info(f"Attempting to load schema from: {schema_path}")

            # Load schema
            schema = LoadYamlSchema.load_yaml_schema(schema_path, config_path)
            logger.info(f"Schema loaded from: {schema_path}")

            # Push to XCom
            ti.xcom_push(key="schema", value=schema)
            return {"schema_path": schema_path}
        except Exception as e:
            logger.error(f"Error in load_yaml_schema_file: {str(e)}")
            raise

    @task
    def validate_yaml_schema(ti=None) -> Dict[str, str]:
        """
        Validate the schema loaded from premises.yml.
        """
        try:
            schema = ti.xcom_pull(task_ids="load_yaml_schema_file", key="schema")
            schema_path = ti.xcom_pull(task_ids="load_yaml_schema_file")["schema_path"]
            if schema is None:
                raise ValueError("No schema found in XCom for task load_yaml_schema_file")

            ValidateYamlSchema.validate_schema(schema)
            logger.info("Schema validation completed successfully")
            return {"schema_path": schema_path, "validation_status": "success"}
        except Exception as e:
            logger.error(f"Error in validate_yaml_schema: {str(e)}")
            raise

    @task
    def validate_source_db_connection(ti=None) -> Dict[str, str]:
        """
        Validate the source database connection (postgres-sunculture-ep-db).
        """
        try:
            config = ti.xcom_pull(task_ids="load_sync_config", key="config")
            if config is None:
                raise ValueError("No config found in XCom for task load_sync_config")

            conn_id = config["source"]["airflow_connection_id"]
            hook = PostgresSourceHook(conn_id=conn_id)
            result = hook.test_pg_source_connection()
            logger.info(f"Source DB connection test: {result['message']}")
            return result
        except Exception as e:
            logger.error(f"Error in validate_source_db_connection: {str(e)}")
            raise

    @task
    def validate_target_db_connection(ti=None) -> Dict[str, str]:
        """
        Validate the target database connection (postgres_reporting_service).
        """
        try:
            config = ti.xcom_pull(task_ids="load_sync_config", key="config")
            if config is None:
                raise ValueError("No config found in XCom for task load_sync_config")

            conn_id = config["target"]["airflow_connection_id"]
            hook = PostgresTargetHook(conn_id=conn_id)
            result = hook.test_pg_target_connection()
            logger.info(f"Target DB connection test: {result['message']}")
            return result
        except Exception as e:
            logger.error(f"Error in validate_target_db_connection: {str(e)}")
            raise

    @task
    def validate_source_table(ti=None) -> Dict[str, Any]:
        """
        Validate that the source table (public.premises) exists.
        """
        try:
            config = ti.xcom_pull(task_ids="load_sync_config", key="config")
            if config is None:
                raise ValueError("No config found in XCom for task load_sync_config")
            source_config = config["source"]

            hook = PostgresSourceHook(conn_id=source_config["airflow_connection_id"])
            exists = hook.pg_source_table_exists(source_config["table"], source_config["schema"])
            if not exists:
                raise ValueError(f"Source table {source_config['schema']}.{source_config['table']} does not exist")
            logger.info(f"Source table {source_config['schema']}.{source_config['table']} exists")
            return {"table": source_config["table"], "schema": source_config["schema"], "exists": exists}
        except Exception as e:
            logger.error(f"Error in validate_source_table: {str(e)}")
            raise

    @task
    def validate_target_table(ti=None) -> Dict[str, Any]:
        """
        Validate that the target table (fma.premises) exists.
        """
        try:
            config = ti.xcom_pull(task_ids="load_sync_config", key="config")
            if config is None:
                raise ValueError("No config found in XCom for task load_sync_config")
            target_config = config["target"]

            hook = PostgresTargetHook(conn_id=target_config["airflow_connection_id"])
            exists = hook.pg_target_table_exists(target_config["table"], target_config["schema"])
            logger.info(f"Target table {target_config['schema']}.{target_config['table']} exists: {exists}")
            return {"table": target_config["table"], "schema": target_config["schema"], "exists": exists}
        except Exception as e:
            logger.error(f"Error in validate_target_table: {str(e)}")
            raise

    @task
    def create_target_table(ti=None) -> Dict[str, Any]:
        """
        Create the target table (fma.premises) if it does not exist.
        """
        try:
            config = ti.xcom_pull(task_ids="load_sync_config", key="config")
            schema = ti.xcom_pull(task_ids="load_yaml_schema_file", key="schema")
            if config is None or schema is None:
                raise ValueError("No config or schema found in XCom")
            target_config = config["target"]
            target_exists = ti.xcom_pull(task_ids="validate_target_table")["exists"]

            hook = PostgresTargetHook(conn_id=target_config["airflow_connection_id"])
            if not target_exists:
                target_schema = schema["targets"]["postgres"]["columns"]
                hook.create_pg_target_table(target_config["table"], target_schema, target_config["schema"])
                logger.info(f"Created target table {target_config['schema']}.{target_config['table']}")
                return {"table": target_config["table"], "schema": target_config["schema"], "created": True}
            logger.info(f"Target table {target_config['schema']}.{target_config['table']} already exists")
            return {"table": target_config["table"], "schema": target_config["schema"], "created": False}
        except Exception as e:
            logger.error(f"Error in create_target_table: {str(e)}")
            raise

    @task
    def fetch_source_records(ti=None) -> Dict[str, Any]:
        """
        Fetch records from the source table (public.premises) incrementally.
        Updates pg_premises_last_updated_at per batch.
        """
        try:
            config = ti.xcom_pull(task_ids="load_sync_config", key="config")
            schema = ti.xcom_pull(task_ids="load_yaml_schema_file", key="schema")
            if config is None or schema is None:
                raise ValueError("No config or schema found in XCom")
            source_config = config["source"]

            hook = PostgresSourceHook(conn_id=source_config["airflow_connection_id"])
            source_schema = schema["source"]["postgres"]["columns"]
            source_cols = [col for col, col_def in source_schema.items() if col_def.get("active")]

            last_updated_key = f"pg_{source_config['table']}_last_updated_at"
            last_updated_at = Variable.get(last_updated_key, default_var=None)

            total_rows = 0
            max_updated_at = last_updated_at
            batches = []

            for batch, batch_max_updated_at in hook.fetch_pg_source_rows(
                source_config["table"],
                source_cols,
                source_config["schema"],
                source_config["batch_size"],
                source_config["incremental_column"],
                last_updated_at
            ):
                total_rows += len(batch)
                batches.append(batch)
                if batch_max_updated_at:
                    max_updated_at = batch_max_updated_at
                    Variable.set(last_updated_key, max_updated_at)
                logger.debug(f"Fetched batch of {len(batch)} rows, max {source_config['incremental_column']}: {batch_max_updated_at}")

            ti.xcom_push(key="batches", value=batches)
            logger.info(f"Fetched {total_rows} total records from {source_config['schema']}.{source_config['table']}")
            return {"table": source_config["table"], "schema": source_config["schema"], "rows_fetched": total_rows}
        except Exception as e:
            logger.error(f"Error in fetch_source_records: {str(e)}")
            raise

    @task
    def upsert_records(ti=None) -> Dict[str, Any]:
        """
        Upsert fetched records to the target table (fma.premises).
        Updates pg_premises_last_sync_time per batch and logs inserted/updated counts.
        """
        try:
            config = ti.xcom_pull(task_ids="load_sync_config", key="config")
            schema = ti.xcom_pull(task_ids="load_yaml_schema_file", key="schema")
            batches = ti.xcom_pull(task_ids="fetch_source_records", key="batches")
            if config is None or schema is None or batches is None:
                raise ValueError("No config, schema, or batches found in XCom")

            source_config = config["source"]
            target_config = config["target"]
            source_schema = schema["source"]["postgres"]["columns"]
            target_schema = schema["targets"]["postgres"]["columns"]

            source_cols = [col for col, col_def in source_schema.items() if col_def.get("active")]
            target_cols = [col_def["target"] for col, col_def in source_schema.items() if col_def.get("active")]

            hook = PostgresTargetHook(conn_id=target_config["airflow_connection_id"])

            total_inserted = 0
            total_updated = 0

            for batch in batches:
                rows = [{target_cols[i]: row[source_cols[i]] for i in range(len(source_cols))} for row in batch]
                inserted, updated = hook.upsert_rows_to_pg_target_table(
                    target_config["table"],
                    rows,
                    target_schema,
                    target_config["schema"],
                    target_config["batch_size"],
                    target_config["upsert_conditions"],
                    source_config["incremental_column"]
                )
                total_inserted += inserted
                total_updated += updated

                last_sync_key = f"pg_{target_config['table']}_last_sync_time"
                current_time = datetime.now(timezone.utc).isoformat()
                Variable.set(last_sync_key, current_time)

                logger.info(f"Fetched and synced {updated} updated records and {inserted} new records to {target_config['schema']}.{target_config['table']}")

            logger.info(f"Completed sync to {target_config['schema']}.{target_config['table']}: {total_updated} updated, {total_inserted} new")
            return {
                "table": target_config["table"],
                "schema": target_config["schema"],
                "inserted": total_inserted,
                "updated": total_updated
            }
        except Exception as e:
            logger.error(f"Error in upsert_records: {str(e)}")
            raise

    # Define tasks
    load_config_task = load_sync_config()
    load_schema_task = load_yaml_schema_file()
    validate_schema_task = validate_yaml_schema()
    validate_source_conn_task = validate_source_db_connection()
    validate_target_conn_task = validate_target_db_connection()
    validate_source_table_task = validate_source_table()
    validate_target_table_task = validate_target_table()
    create_target_table_task = create_target_table()
    fetch_source_task = fetch_source_records()
    upsert_task = upsert_records()

    # Set dependencies
    load_config_task >> [validate_source_conn_task, validate_target_conn_task]
    load_config_task >> load_schema_task >> validate_schema_task
    validate_source_conn_task >> validate_source_table_task
    validate_target_conn_task >> validate_target_table_task >> create_target_table_task
    [validate_source_table_task, create_target_table_task, validate_schema_task] >> fetch_source_task >> upsert_task

dag = sync_pg_sunculture_ep_premises_to_pg_reporting_service()