from airflow.decorators import dag, task
from datetime import datetime
from airflow.utils.dates import days_ago
from airflow.models import Variable
from plugins.hooks.mysql.v1.mysql_hook import MySqlHook
from plugins.hooks.clickhouse.v1.clickhouse_hook import ClickHouseCloudHook
from plugins.utils.schema_loader.v2.schema_loader import SchemaLoader
from plugins.utils.add_sync_time.v1.add_sync_time import add_sync_time
from plugins.utils.constants.v1.constants import SYNC_CONFIGS
from plugins.utils.defaults.v1.defaults import DEFAULT_ARGS
from typing import List, Dict, Any

import logging
logger = logging.getLogger(__name__)

# Sync key for this DAG
SYNC_KEY = 'mysql_amt_customers_to_clickhouse_cloud'

@dag(
    dag_id='sync_mysql_amt_customers_to_ch_cloud',
    default_args=DEFAULT_ARGS,
    start_date=days_ago(1),
    schedule=None,
    catchup=False,
)
def sync_mysql_amt_customers_to_ch_cloud():
    """
    A DAG that syncs customers data from MySQL to ClickHouse using TaskFlow API.
    Fetches data from MySQL in batches and inserts into ClickHouse.
    Tracks updatedAt for incremental refreshes using Airflow Variables.
    Maps MySQL camelCase columns (e.g., phoneNumber) to ClickHouse snake_case (e.g., phone_number).
    Respects active source columns and handles auto-generated columns (e.g., sync_time).
    Validates MySQL source table and skips missing columns.
    """
    
    @task
    def validate_schema():
        logger.info("Validating schema compatibility")
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        source_config = sync_config['source']
        target_config = sync_config['target']
        
        # Load schema using table_name from SYNC_CONFIGS
        schema = SchemaLoader.load_schema(
            source_type=source_config['source_type'],
            source_subpath=source_config['source_subpath'],
            table_name=source_config['table'],
            target_type=target_config['target_type']
        )
        
        # Build config with schema and SYNC_CONFIGS
        config = {
            "table": schema['table'],
            "source": schema.get("source", {}),
            "target": {
                **schema.get("target", {}),
                "database": target_config['database'],
                "database_type": target_config['target_type'],
                "engine": target_config['engine'],
                "order_by": target_config['order_by'],
                "partition_by": target_config['partition_by'],
            },
            "mappings": schema.get("mappings", [])
        }
        
        logger.debug(f"Schema config: {config}")
        logger.info("Schema validation successful")
        return config
    
    @task
    def test_mysql_connection():
        logger.info("Testing MySQL connection")
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        hook = MySqlHook(conn_id=sync_config['source']['connection_id'], log_level='DEBUG', connect_timeout=10)
        success, message = hook.test_connection()
        if not success:
            raise Exception(f"MySQL connection failed: {message}")
        logger.info("MySQL connection successful")
        return message
    
    @task
    def test_clickhouse_connection():
        logger.info("Testing ClickHouse connection")
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        hook = ClickHouseCloudHook(clickhouse_conn_id=sync_config['target']['connection_id'], log_level='DEBUG', connect_timeout=10)
        success, message = hook.test_connection()
        if not success:
            raise Exception(f"ClickHouse connection failed: {message}")
        logger.info("ClickHouse connection successful")
        return message
    
    @task
    def validate_mysql_table(config: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Validating MySQL source table")
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        hook = MySqlHook(conn_id=sync_config['source']['connection_id'], log_level='DEBUG', connect_timeout=10)
        source_config = config["source"]
        mappings = config["mappings"]
        
        table_name = config["table"]
        
        # Verify table existence
        if not hook.table_exists(table_name):
            logger.error(f"Table {table_name} does not exist in the default database")
            raise ValueError(f"Table {table_name} does not exist")
        
        # Build target-to-source mapping for active columns
        target_to_source = {}
        for m in mappings:
            if m.get("auto_generated", False):
                continue
            if m.get("source_active", True):  # Respect active flag
                target_to_source[m["target"]] = m["source"] or m["target"]
        
        expected_columns = set(target_to_source.values())
        logger.debug(f"Expected source columns: {expected_columns}")
        logger.debug(f"Target-to-source mapping: {target_to_source}")
        
        # Get existing table columns
        try:
            existing_columns = hook.get_table_columns(table_name)
            if not existing_columns:
                logger.error(f"No columns found in table {table_name}")
                raise ValueError(f"No columns found in table {table_name}")
            existing_column_names = {c["column_name"].lower() for c in existing_columns}
            logger.debug(f"Existing MySQL columns: {existing_column_names}")
            
            # Identify missing columns
            missing_columns = {c for c in expected_columns if c.lower() not in existing_column_names}
            if missing_columns:
                logger.warning(f"Missing columns in {table_name}: {missing_columns}. These will be treated as NULL.")
            else:
                logger.info(f"All expected columns found in {table_name}")
        except Exception as e:
            logger.error(f"Failed to validate MySQL table: {e}")
            raise
        
        logger.info(f"MySQL table {table_name} validated")
        return {
            "table_name": table_name,
            "available_columns": existing_column_names,
            "target_to_source": target_to_source
        }
    
    @task
    def fetch_mysql_data(config: Dict[str, Any], mysql_table_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info("Fetching data from MySQL")
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        hook = MySqlHook(conn_id=sync_config['source']['connection_id'], log_level='DEBUG', connect_timeout=10)
        source_config = config["source"]
        mappings = config["mappings"]
        available_columns = mysql_table_info.get("available_columns", set())
        target_to_source = mysql_table_info.get("target_to_source", {})
        
        # Build columns list for active and available columns
        columns = []
        skipped_columns = []
        for m in mappings:
            if m.get("auto_generated", False) or not m.get("source_active", True):
                continue
            source_col = target_to_source.get(m["target"], m["target"])
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
        incremental_col = next(
            (m["source"] for m in mappings if m.get("source_incremental", False) and m.get("source_active", True)),
            "updatedAt"
        )
        last_updated_at_str = Variable.get("customers_last_updated_at_clickhouse", default_var="1970-01-01 00:00:00")
        last_updated_at = datetime.strptime(last_updated_at_str, "%Y-%m-%d %H:%M:%S")
        logger.info(f"Fetching records with {incremental_col} > {last_updated_at}")
        
        query = f"SELECT {columns_str} FROM {config['table']} WHERE {incremental_col} > %s ORDER BY {incremental_col}"
        params = (last_updated_at,)
        
        all_rows = []
        max_updated_at = last_updated_at
        
        for batch in hook.execute_query(query, params, fetch_batch=True, batch_size=5000, schema=config):
            mapped_batch = []
            for row in batch:
                mapped_row = {}
                for m in mappings:
                    if m.get("auto_generated", False):
                        continue
                    target_col = m["target"]
                    source_col = target_to_source.get(target_col, target_col)
                    if source_col.lower() in {c.lower() for c in columns}:
                        value = row[source_col]
                        if m["target_type"].startswith("Nullable(UInt32)") and value is not None:
                            value = int(value)
                        mapped_row[target_col] = value
                    else:
                        mapped_row[target_col] = None
                mapped_batch.append(mapped_row)
            
            all_rows.extend(mapped_batch)
            if batch:
                batch_max_updated_at = max(row[incremental_col] for row in batch)
                max_updated_at = max(max_updated_at, batch_max_updated_at)
            
            if mapped_batch:
                sample = mapped_batch[0]
                sample_types = {
                    "id": type(sample.get("id")),
                    "phone_number": type(sample.get("phone_number")),
                    "created_by": type(sample.get("created_by"))
                }
                truncated_sample = {
                    k: (f"{str(v)[:10]}..." if v is not None and len(str(v)) > 10 else "NULL" if v is None else v)
                    for k, v in sample.items()
                }
                logger.debug(f"Sample row types: {sample_types}")
                logger.debug(f"Sample row (truncated): {truncated_sample}")
        
        logger.info(f"Fetched {len(all_rows)} total rows from MySQL")
        
        if all_rows:
            sample_size = min(3, len(all_rows))
            logger.info(f"Sample of first {sample_size} rows (truncated):")
            for i in range(sample_size):
                sample = all_rows[i]
                truncated_sample = {
                    k: (str(v)[:20] + '...' if isinstance(v, str) and len(str(v)) > 20 else v)
                    for k, v in sample.items()
                }
                logger.info(f"Sample row {i+1}: {truncated_sample}")
        
        if all_rows:
            max_updated_at_str = max_updated_at.strftime("%Y-%m-%d %H:%M:%S")
            Variable.set("customers_last_updated_at_clickhouse", max_updated_at_str)
            logger.info(f"Updated customers_last_updated_at_clickhouse to {max_updated_at_str}")
        
        return all_rows
    
    @task
    def create_clickhouse_table(config: Dict[str, Any]):
        logger.info("Creating or updating table in ClickHouse")
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        hook = ClickHouseCloudHook(clickhouse_conn_id=sync_config['target']['connection_id'], log_level='DEBUG', connect_timeout=10)
        target_config = config["target"]
        mappings = config["mappings"]
        
        table_name = config["table"]
        database = target_config["database"]
        schema = [
            {"name": m["target"], "type": m["target_type"], "nullable": m["target_nullable"]}
            for m in mappings
        ]
        
        try:
            existing_columns = hook.get_table_columns(database, table_name)
            existing_column_names = {c["name"] for c in existing_columns}
            for s in schema:
                if s["name"] not in existing_column_names:
                    logger.info(f"Adding column {s['name']} to {database}.{table_name}")
                    column_type = s["type"] if s["type"].startswith("Nullable") or not s["nullable"] else f"Nullable({s['type']})"
                    alter_query = f"ALTER TABLE {database}.{table_name} ADD COLUMN `{s['name']}` {column_type}"
                    hook.execute_query(alter_query)
                    logger.info(f"Added column {s['name']}")
        except Exception as e:
            logger.warning(f"Failed to check or alter table schema: {e}. Proceeding with table creation.")
        
        created = hook.create_table(
            table_name=table_name,
            schema=schema,
            database=database,
            engine=target_config.get("engine", "ReplacingMergeTree(updated_at)"),
            order_by=target_config.get("order_by", "id"),
            partition_by=target_config.get("partition_by", "toYYYYMM(updated_at)")
        )
        logger.info(f"Table {database}.{table_name} creation status: {'Created' if created else 'Already exists or updated'}")
        return {"table_name": table_name, "database": database}
    
    @task
    def insert_into_clickhouse(table_info: Dict[str, str], rows: List[Dict[str, Any]], config: Dict[str, Any]):
        logger.info(f"Inserting data into ClickHouse table {table_info['database']}.{table_info['table_name']}")
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        hook = ClickHouseCloudHook(clickhouse_conn_id=sync_config['target']['connection_id'], log_level='DEBUG', connect_timeout=10)
        if not rows:
            logger.warning("No rows to insert")
            return 0
        
        add_sync_time(rows, config["target"])
        
        num_inserted = hook.insert_rows(
            table_name=table_info['table_name'],
            rows=rows,
            database=table_info['database']
        )
        logger.info(f"Inserted {num_inserted} rows into {table_info['database']}.{table_info['table_name']}")
        return num_inserted
    
    config = validate_schema()
    mysql_conn_test = test_mysql_connection()
    clickhouse_conn_test = test_clickhouse_connection()
    mysql_table_info = validate_mysql_table(config)
    mysql_data = fetch_mysql_data(config, mysql_table_info)
    table_info = create_clickhouse_table(config)
    inserted = insert_into_clickhouse(table_info, mysql_data, config)
    
    config >> [mysql_conn_test, clickhouse_conn_test, mysql_table_info]
    mysql_conn_test >> mysql_table_info
    mysql_table_info >> mysql_data
    clickhouse_conn_test >> table_info
    [mysql_data, table_info] >> inserted
    
dag = sync_mysql_amt_customers_to_ch_cloud()