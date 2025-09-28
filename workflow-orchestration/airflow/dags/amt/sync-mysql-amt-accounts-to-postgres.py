from airflow.decorators import dag, task
from datetime import datetime
from airflow.utils.dates import days_ago
from airflow.models import Variable
from plugins.hooks.mysql_hook.v1.mysql_hook import MySqlHook
from plugins.hooks.pg_hook.v2.pg_hook import PostgresHook
from plugins.utils.schema_loader.v2.schema_loader import SchemaLoader
from plugins.utils.add_sync_time.v1.add_sync_time import add_sync_time
from plugins.utils.constants.v1.constants import  SYNC_CONFIGS
from plugins.utils.defaults.v1.defaults import DEFAULT_ARGS
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Sync key for this DAG
SYNC_KEY = 'mysql_amt_accounts_to_postgres'

@dag(
    dag_id='sync_mysql_amt_accounts_to_postgres',
    default_args=DEFAULT_ARGS,
    start_date=days_ago(1),
    schedule=None,
    catchup=False,
)
def sync_mysql_amt_accounts_to_postgres():
    """
    A DAG that syncs accounts data from MySQL to PostgreSQL using TaskFlow API.
    Fetches data from MySQL in batches and upserts directly into PostgreSQL.
    Tracks updated_at for incremental refreshes using Airflow Variables.
    Respects active columns and handles auto-generated columns (e.g., sync_time).
    Validates MySQL source table and skips missing columns.
    """

    @task
    def validate_schema() -> Dict[str, Any]:
        """
        Validate schema compatibility using SchemaLoader.
        
        Returns:
            Schema configuration dictionary.
        """
        logger.info("Validating schema compatibility")
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        source_config = sync_config['source']
        target_config = sync_config['target']
        
        try:
            schema = SchemaLoader.load_schema(
                source_type=source_config['source_type'],
                source_subpath=source_config['source_subpath'],
                table_name=source_config['table'],
                target_type=target_config['target_type']
            )
            config = {
                "table": source_config['table'],
                "source": schema.get("source", {}),
                "target": {
                    **schema.get("target", {}),
                    "database": target_config['database'],
                    "schema": target_config['schema'],
                    "table": target_config['table'],
                    "database_type": target_config['target_type'],
                },
                "mappings": schema.get("mappings", [])
            }
            logger.info(f"Schema validation successful: {len(config['mappings'])} mappings")
            logger.debug(f"Config structure: {config}")
            return config
        except Exception as e:
            logger.error(f"Schema validation failed: {str(e)}")
            raise

    @task
    def test_mysql_connection() -> str:
        """
        Test MySQL connection.
        
        Returns:
            Connection test message.
        """
        logger.info("Testing MySQL connection")
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        hook = MySqlHook(
            conn_id=sync_config['source']['connection_id'],
            log_level='INFO',
            connect_timeout=10
        )
        success, message = hook.test_connection()
        if not success:
            raise ValueError(f"MySQL connection failed: {message}")
        logger.info("MySQL connection successful")
        return message

    @task
    def test_postgres_connection() -> str:
        """
        Test PostgreSQL connection.
        
        Returns:
            Connection test message.
        """
        logger.info("Testing PostgreSQL connection")
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        hook = PostgresHook(
            conn_id=sync_config['target']['connection_id'],
            log_level='INFO'
        )
        success, message = hook.test_connection()
        if not success:
            raise ValueError(f"PostgreSQL connection failed: {message}")
        logger.info("PostgreSQL connection successful")
        return message

    @task
    def validate_mysql_table(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate MySQL source table and columns.
        
        Args:
            config: Schema configuration from validate_schema.
        
        Returns:
            Dictionary with table name, available columns, and target-to-source mapping.
        """
        logger.info("Validating MySQL source table")
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        hook = MySqlHook(
            conn_id=sync_config['source']['connection_id'],
            log_level='INFO',
            connect_timeout=10
        )
        table_name = config["table"]
        
        if not hook.table_exists(table_name, sync_config['source']['database']):
            logger.error(f"Table {table_name} does not exist in database {sync_config['source']['database']}")
            raise ValueError(f"Table {table_name} does not exist")
        
        target_to_source = {}
        source_columns = config["source"].get("columns", {})
        for source_col, props in source_columns.items():
            if props.get("active", True):
                target_col = props.get("target", source_col)
                target_to_source[target_col] = source_col
        
        expected_columns = set(target_to_source.values())
        logger.debug(f"Expected source columns: {expected_columns}")
        
        try:
            existing_columns = hook.get_table_columns(table_name, sync_config['source']['database'])
            existing_column_names = {c["column_name"].lower() for c in existing_columns}
            logger.debug(f"Existing MySQL columns: {existing_column_names}")
            
            missing_columns = {c for c in expected_columns if c.lower() not in existing_column_names}
            if missing_columns:
                logger.warning(f"Missing columns in {table_name}: {missing_columns}. These will be treated as NULL.")
            else:
                logger.info(f"All expected columns found in {table_name}")
        except Exception as e:
            logger.error(f"Failed to validate MySQL table: {str(e)}")
            raise
        
        logger.info(f"MySQL table {table_name} validated")
        return {
            "table_name": table_name,
            "available_columns": existing_column_names,
            "target_to_source": target_to_source
        }

    @task
    def fetch_and_sync_to_postgres(config: Dict[str, Any], mysql_table_info: Dict[str, Any], table_info: Dict[str, str]) -> None:
        """
        Fetch data from MySQL in batches and upsert directly into PostgreSQL.
        
        Args:
            config: Schema configuration from validate_schema.
            mysql_table_info: Table info from validate_mysql_table.
            table_info: Dictionary with table name and schema name.
        """
        logger.info("Fetching and syncing data from MySQL to PostgreSQL")
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        mysql_hook = MySqlHook(
            conn_id=sync_config['source']['connection_id'],
            log_level='INFO',
            connect_timeout=10
        )
        postgres_hook = PostgresHook(
            conn_id=sync_config['target']['connection_id'],
            log_level='INFO'
        )
        
        target_to_source = mysql_table_info.get("target_to_source", {})
        available_columns = mysql_table_info.get("available_columns", set())
        
        columns = []
        skipped_columns = []
        source_columns = config["source"].get("columns", {})
        for target_col, source_col in target_to_source.items():
            if source_col.lower() in {c.lower() for c in available_columns}:
                columns.append(source_col)
            else:
                skipped_columns.append(source_col)
                logger.info(f"Skipping column {source_col} as it does not exist in {config['table']}")
        
        if skipped_columns:
            logger.debug(f"Skipped columns: {skipped_columns}")
        if not columns:
            logger.error(f"No valid source columns found. Expected: {list(target_to_source.values())}, Available: {available_columns}")
            raise ValueError("No valid source columns found")
        
        logger.debug(f"Source columns for query: {columns}")
        columns_str = ", ".join([f"`{col}`" for col in columns])
        incremental_col = "updatedAt"
        last_updated_at_str = Variable.get("accounts_last_updated_at_postgres", default_var="1970-01-01 00:00:00")
        try:
            last_updated_at = datetime.strptime(last_updated_at_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            logger.warning(f"Invalid last_updated_at format: {last_updated_at_str}. Using default.")
            last_updated_at = datetime(1970, 1, 1)
        
        logger.info(f"Fetching records with {incremental_col} > {last_updated_at}")
        query = f"SELECT {columns_str} FROM {config['table']} WHERE {incremental_col} > %s ORDER BY {incremental_col}"
        params = (last_updated_at,)
        
        batch_size = sync_config['source'].get('batch_size', 500)
        logger.info(f"Using batch size: {batch_size}")
        
        total_rows = 0
        max_updated_at = last_updated_at
        
        for batch in mysql_hook.execute_query(query, params, fetch_batch=True, batch_size=batch_size, schema=config):
            if not batch:
                break
            
            mapped_batch = []
            for row in batch:
                mapped_row = {}
                for target_col, source_col in target_to_source.items():
                    if source_col in columns:
                        value = row.get(target_col)
                        target_type = config["target"]["columns"].get(target_col, {}).get("type", "")
                        if target_type == "integer" and value is not None:
                            value = int(value)
                        mapped_row[target_col] = value
                mapped_batch.append(mapped_row)
            
            add_sync_time(mapped_batch, config["target"])
            
            try:
                rows_affected = postgres_hook.upsert_rows(
                    table_name=table_info['table_name'],
                    rows=mapped_batch,
                    schema=table_info['schema_name'],
                    upsert_conditions=["id"],
                    update_condition=None
                )
                total_rows += rows_affected
                logger.info(f"Upserted {rows_affected} rows into {table_info['schema_name']}.{table_info['table_name']} (Total: {total_rows})")
                
                target_updated_at = "updated_at"
                batch_max_updated_at = max(row[target_updated_at] for row in mapped_batch)
                max_updated_at = max(max_updated_at, batch_max_updated_at)
            except Exception as e:
                logger.error(f"Failed to upsert batch: {e}")
                raise
            
        if total_rows > 0:
            max_updated_at_str = max_updated_at.strftime("%Y-%m-%d %H:%M:%S")
            Variable.set("accounts_last_updated_at_postgres", max_updated_at_str)
            logger.info(f"Updated accounts_last_updated_at_postgres to {max_updated_at_str}")
        
        logger.info(f"Completed sync of {total_rows} rows to {table_info['schema_name']}.{table_info['table_name']}")

    @task
    def prepare_postgres_table_schema(config: Dict[str, Any]) -> Dict[str, str]:
        """
        Prepare the PostgreSQL target table by ensuring it exists and its schema is up-to-date.
        Creates the table if it doesn't exist, adds missing columns based on the schema.
        
        Args:
            config: Schema configuration from validate_schema.
        
        Returns:
            Dict with table name and schema name.
        """
        logger.info("Preparing PostgreSQL target table schema")
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        hook = PostgresHook(
            conn_id=sync_config['target']['connection_id'],
            log_level='DEBUG'
        )
        
        target_config = config["target"]
        table_name = config["table"]
        schema_name = sync_config['target']['schema']
        
        logger.debug(f"Using schema: {schema_name}, table: {table_name}")
        
        # Step 1: Define expected columns for table creation
        columns = []
        primary_key_column = None
        for col, props in target_config["columns"].items():
            col_def = f'"{col}" {props["type"]}'
            if not props.get("nullable", True):
                col_def += " NOT NULL"
            if props.get("primary_key", False):
                if primary_key_column is not None:
                    logger.error(f"Multiple primary key columns detected: {primary_key_column} and {col}")
                    raise ValueError("Only one primary key column is allowed")
                primary_key_column = col
                col_def += " PRIMARY KEY"
            columns.append(col_def)
        
        if not primary_key_column:
            logger.warning("No primary key column defined in the target schema")
            # Optionally, you could raise an exception here if a primary key is mandatory
        
        # Step 2: Create table if it doesn't exist
        try:
            created = hook.create_table_if_not_exists(
                table_name=table_name,
                columns=columns,
                schema=schema_name
            )
            logger.info(f"Table {schema_name}.{table_name} {'created' if created else 'verified'}")
        except Exception as e:
            logger.error(f"Failed to create table {schema_name}.{table_name}: {str(e)}")
            raise
        
        # Step 3: Check for missing columns and add them
        try:
            existing_columns = hook.get_table_columns(schema=schema_name, table_name=table_name)
            existing_column_names = {col["column_name"].lower() for col in existing_columns}
            expected_columns = {col.lower(): props for col, props in target_config["columns"].items()}
            
            missing_columns = set(expected_columns.keys()) - existing_column_names
            if missing_columns:
                logger.info(f"Found missing columns in {schema_name}.{table_name}: {missing_columns}")
                for missing_col in missing_columns:
                    props = expected_columns[missing_col]
                    column_type = props["type"]
                    is_nullable = not props.get("nullable", True)
                    is_primary_key = props.get("primary_key", False)
                    
                    # Add the missing column
                    hook.add_column(
                        schema=schema_name,
                        table_name=table_name,
                        column_name=missing_col,
                        column_type=column_type,
                        is_nullable=is_nullable,
                        is_primary_key=is_primary_key
                    )
                    logger.info(f"Added column {missing_col} to {schema_name}.{table_name}")
            else:
                logger.info(f"No missing columns in {schema_name}.{table_name}")
        except Exception as e:
            logger.error(f"Failed to update table schema {schema_name}.{table_name}: {str(e)}")
            raise

        return {"table_name": table_name, "schema_name": schema_name}

    # Define task instances
    config = validate_schema()
    mysql_conn = test_mysql_connection()
    postgres_conn = test_postgres_connection()
    mysql_table_info = validate_mysql_table(config)
    table_info = prepare_postgres_table_schema(config)
    sync_task = fetch_and_sync_to_postgres(config, mysql_table_info, table_info)

    # Set dependencies
    config >> [mysql_conn, postgres_conn, mysql_table_info]
    mysql_conn >> mysql_table_info
    postgres_conn >> table_info
    [mysql_table_info, table_info] >> sync_task

dag = sync_mysql_amt_accounts_to_postgres()