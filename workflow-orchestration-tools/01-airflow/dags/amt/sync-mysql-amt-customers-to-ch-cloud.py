from airflow.decorators import dag, task
from datetime import datetime
from airflow.utils.dates import days_ago
from airflow.models import Variable
from plugins.hooks.mysql_hook import MySqlHook
from plugins.hooks.clickhouse_cloud_hook import ClickHouseCloudHook
from plugins.utils.schema_loader import SchemaLoader
from plugins.utils.add_sync_time import add_sync_time
from plugins.utils.constants import CONNECTION_IDS, DEFAULT_ARGS
from typing import List, Dict, Any

import logging
logger = logging.getLogger(__name__)

# Environment-specific configuration
TARGET_DATABASE = "test"  # Your database name
DATABASE_TYPE = "clickhouse"

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
    Supports advanced column mappings (e.g., phoneNumber → phone_number).
    """
    
    @task
    def validate_schema():
        logger.info("Validating schema compatibility")
        config = SchemaLoader.get_combined_schema(
            source_type="mysql",
            source_subpath="amt",
            target_type="clickhouse",
            table_name="customers"
        )
        # Inject environment-specific settings
        config["target"]["database"] = TARGET_DATABASE
        config["target"]["database_type"] = DATABASE_TYPE
        logger.info("Schema validation successful")
        return config
    
    @task
    def test_mysql_connection():
        logger.info("Testing MySQL connection")
        hook = MySqlHook(conn_id=CONNECTION_IDS['mysql_amtdb'], log_level='DEBUG', connect_timeout=10)
        with hook.get_conn() as conn:
            if conn.is_connected():
                logger.info("MySQL connection successful")
                return "MySQL connection successful"
        raise Exception("MySQL connection failed")
    
    @task
    def test_clickhouse_connection():
        logger.info("Testing ClickHouse connection")
        hook = ClickHouseCloudHook(clickhouse_conn_id=CONNECTION_IDS['clickhouse_cloud'], log_level='DEBUG', connect_timeout=10)
        success, message = hook.test_connection()
        if not success:
            raise Exception(f"ClickHouse connection failed: {message}")
        logger.info("ClickHouse connection successful")
        return message
    
    @task
    def fetch_mysql_data(config: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info("Fetching data from MySQL")
        hook = MySqlHook(conn_id=CONNECTION_IDS['mysql_amtdb'], log_level='DEBUG', connect_timeout=10)
        source_config = config["source"]
        mappings = config["mappings"]
        
        columns = []
        for m in mappings:
            if m.get("generated", False) or m["source"] is None:
                continue
            columns.append(m["source"])
        
        if not columns:
            logger.error("No valid source columns found in mappings")
            raise ValueError("No valid source columns found")
        
        logger.debug(f"Source columns for query: {columns}")
        columns_str = ", ".join(columns)
        incremental_col = source_config.get("incremental_column", "updatedAt")
        last_updated_at_str = Variable.get("customers_last_updated_at_clickhouse", default_var="1970-01-01 00:00:00")
        last_updated_at = datetime.strptime(last_updated_at_str, "%Y-%m-%d %H:%M:%S")
        logger.info(f"Fetching records with {incremental_col} > {last_updated_at}")
        
        query = f"SELECT {columns_str} FROM {source_config['table']} WHERE {incremental_col} > %s ORDER BY {incremental_col}"
        params = (last_updated_at,)
        
        all_rows = []
        max_updated_at = last_updated_at
        
        for batch in hook.execute_query(query, params, fetch_batch=True, batch_size=5000):
            mapped_batch = []
            for row in batch:
                mapped_row = {}
                for m in mappings:
                    if m.get("generated", False) or m["source"] is None:
                        continue
                    value = row[m["source"]]
                    if m["target_type"].startswith("Nullable(UInt32)") and value is not None:
                        value = int(value)
                    mapped_row[m["target"]] = value
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
        hook = ClickHouseCloudHook(clickhouse_conn_id=CONNECTION_IDS['clickhouse_cloud'], log_level='DEBUG', connect_timeout=10)
        target_config = config["target"]
        mappings = config["mappings"]
        
        table_name = target_config["table"]
        database = target_config["database"]
        schema = [
            {"name": m["target"], "type": m["target_type"], "nullable": m["target_nullable"]}
            for m in mappings
        ]
        
        # Check existing table schema
        try:
            existing_columns = hook.get_table_columns(database, table_name)
            expected_columns = {s["name"] for s in schema}
            existing_column_names = {c["name"] for c in existing_columns}
            
            # Add missing columns
            for s in schema:
                if s["name"] not in existing_column_names:
                    logger.info(f"Adding column {s['name']} to {database}.{table_name}")
                    alter_query = f"ALTER TABLE {database}.{table_name} ADD COLUMN {s['name']} {s['type']}"
                    if s["nullable"]:
                        alter_query = alter_query.replace(s["type"], f"Nullable({s['type']})")
                    hook.execute_query(alter_query)
                    logger.info(f"Added column {s['name']}")
        except Exception as e:
            logger.warning(f"Failed to check or alter table schema: {e}. Proceeding with table creation.")
        
        # Create table if it doesn't exist
        created = hook.create_table(
            table_name=table_name,
            schema=schema,
            database=database,
            engine=target_config["engine"],
            order_by=target_config["order_by"],
            partition_by=target_config["partition_by"]
        )
        logger.info(f"Table {database}.{table_name} creation status: {'Created' if created else 'Already exists or updated'}")
        return {"table_name": table_name, "database": database}
    
    @task
    def insert_into_clickhouse(table_info: Dict[str, str], rows: List[Dict[str, Any]], config: Dict[str, Any]):
        logger.info(f"Inserting data into ClickHouse table {table_info['database']}.{table_info['table_name']}")
        hook = ClickHouseCloudHook(clickhouse_conn_id=CONNECTION_IDS['clickhouse_cloud'], log_level='DEBUG', connect_timeout=10)
        if not rows:
            logger.warning("No rows to insert")
            return 0
        
        # Add sync_time if defined in target schema
        add_sync_time(rows, config["target"])
        
        num_inserted = hook.insert_rows(
            table_name=table_info['table_name'],
            rows=rows,
            database=table_info['database']
        )
        logger.info(f"Inserted {num_inserted} rows into {table_info['database']}.{table_info['table_name']}")
        return num_inserted
    
    # Define dependencies
    config = validate_schema()
    mysql_conn_test = test_mysql_connection()
    clickhouse_conn_test = test_clickhouse_connection()
    mysql_data = fetch_mysql_data(config)
    table_info = create_clickhouse_table(config)
    inserted = insert_into_clickhouse(table_info, mysql_data, config)
    
    config >> [mysql_conn_test, clickhouse_conn_test, mysql_data, table_info]
    mysql_conn_test >> mysql_data
    clickhouse_conn_test >> table_info
    table_info >> inserted
    
dag = sync_mysql_amt_customers_to_ch_cloud()