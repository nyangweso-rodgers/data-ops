from datetime import datetime
from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.operators.python import get_current_context
from plugins.utils.schema_loader.v2.schema_loader import SchemaLoader
from plugins.hooks.jira.v2.jira_hook import JiraApiHook
from plugins.hooks.pg_hook.v2.pg_hook import PostgresHook
import logging
from typing import List, Dict, Any
from requests.exceptions import HTTPError

from plugins.utils.constants.v1.constants import  SYNC_CONFIGS
from plugins.utils.defaults.v1.defaults import DEFAULT_ARGS

logger = logging.getLogger(__name__)

# Sync key for this DAG
SYNC_KEY = 'jira_sprints_to_postgres'

# Utility to add sync_time to records
def add_sync_time(records: List[Dict[str, Any]], target_schema: Dict[str, Any]) -> None:
    """
    Add sync_time to records based on target schema.
    
    Args:
        records: List of dictionaries containing sprint data.
        target_schema: Target schema with column definitions.
    """
    sync_time = next((col for col, props in target_schema['columns'].items() if props.get('auto_generated')), None)
    if sync_time:
        current_time = datetime.utcnow().isoformat() + 'Z'
        for record in records:
            record[sync_time] = current_time

@dag(
    dag_id='sync_jira_sprints_to_postgres',
    default_args=DEFAULT_ARGS,
    description='Sync Jira sprints to PostgreSQL using TaskFlow API',
    #schedule=None,
    schedule="0 9 * * 1-5",  # Runs at 09:00 UTC (12:00 EAT) Mon-Fri
    start_date=datetime(2025, 5, 26),
    catchup=False,
    tags=['jira', 'postgres', 'sync']
)
def sync_jira_sprints_to_postgres():
    """
    DAG to fetch Jira sprints (active, closed, future) from all boards and sync to PostgreSQL.
    """
    
    @task
    def validate_schema():
        """
        Validate the sprints.yml schema and return schema info.
        """
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        source_config = sync_config['source']
        target_config = sync_config['target']
        
        try:
            schema = SchemaLoader.load_schema(
                source_type=source_config['source_type'],
                source_subpath=source_config.get('source_subpath'),
                table_name=source_config['table'],
                target_type=target_config['target_type']
            )
            if not schema.get('target', {}).get('columns'):
                raise ValueError("Schema missing target.columns")
            
            # Return only the dynamic schema information
            schema_info = {
                "columns": schema.get("target", {}).get("columns", {}),
                "mappings": schema.get("mappings", [])
            }
            
            logger.info(f"Schema validation successful for sprints.yml: {len(schema_info['mappings'])} mappings")
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
        pg_hook = PostgresHook(
            conn_id=sync_config['target']['connection_id']
        )
        success, message = pg_hook.test_connection()
        logger.info(f"PostgreSQL connection test: {message}")
        if not success:
            raise ValueError(f"PostgreSQL connection failed: {message}")

    @task
    def fetch_boards():
        """
        Fetch all boards for configured project keys.
        
        Returns:
            List of board IDs.
        """
        jira_hook = JiraApiHook(log_level='INFO')
        project_keys = [key.strip() for key in Variable.get('jira_project_keys', default_var='').split(',')]
        boards = jira_hook.get_boards(project_keys)
        board_ids = [board['id'] for board in boards]
        logger.info(f"Fetched {len(board_ids)} boards: {board_ids}")
        return board_ids

    @task
    def fetch_sprints(schema_info: Dict[str, Any], board_ids: List[int]):
        """
        Fetch sprints from specified boards, filtering by created_date and complete_date.
        
        Args:
            schema_info: Schema information with mappings.
            board_ids: List of board IDs.
        
        Returns:
            Number of sprint batches pushed to XCom.
        """
        # Build config for jira_hook.fetch_sprints
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        config = {
            "table": sync_config['source']['table'],
            "source": sync_config['source'],
            "target": {
                **schema_info,
                "database": sync_config['target']['database'],
                "database_type": sync_config['target']['target_type'],
                "schema_name": sync_config['target']['schema'],
                "table_name": sync_config['target']['table'],
            },
            "mappings": schema_info['mappings']
        }
        
        jira_hook = JiraApiHook(log_level='INFO')
        context = get_current_context()
        ti = context['ti']
        
        last_sync_timestamp = Variable.get('jira_sprints_last_sync', None)
        logger.info(f"Last sync timestamp: {last_sync_timestamp}")
        
        batches = []
        batch_index = 0
        for board_id in board_ids:
            try:
                for batch in jira_hook.fetch_sprints(
                    schema=config,
                    board_id=board_id,
                    state='active,closed,future',
                    last_sync_timestamp=last_sync_timestamp,
                    batch_size=100
                ):
                    valid_batch = []
                    for record in batch:
                        if not isinstance(record, dict) or 'id' not in record or record['id'] is None:
                            logger.warning(f"Skipping invalid sprint record from board {board_id}: {record}")
                            continue
                        try:
                            record['id'] = int(record['id']) if isinstance(record['id'], str) else record['id']
                            if 'original_board_id' in record and record['original_board_id']:
                                record['original_board_id'] = int(record['original_board_id']) if isinstance(record['original_board_id'], str) else record['original_board_id']
                            # Filter based on created_date and complete_date
                            if last_sync_timestamp and 'created_date' in record and record['created_date']:
                                try:
                                    created_dt = datetime.fromisoformat(record['created_date'].replace('Z', '+00:00'))
                                    last_sync_dt = datetime.fromisoformat(last_sync_timestamp.replace('Z', '+00:00'))
                                    if created_dt <= last_sync_dt and record.get('complete_date'):
                                        logger.debug(f"Skipping finalized sprint {record['id']} with created_date {record['created_date']}")
                                        continue  # Skip finalized sprints
                                except ValueError:
                                    logger.warning(f"Invalid created_date: {record['created_date']}")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Skipping record due to invalid format from board {board_id}: {record}, error: {str(e)}")
                            continue
                        valid_batch.append(record)
                    
                    if valid_batch:
                        batches.append(valid_batch)
                        ti.xcom_push(key=f'sprint_batch_{batch_index}', value=valid_batch)
                        logger.info(f"Pushed batch {batch_index} with {len(valid_batch)} sprints from board {board_id} to XCom")
                        batch_index += 1
            except HTTPError as e:
                logger.warning(f"Skipping board {board_id} due to error: {str(e)}")
                continue
        
        logger.info(f"Fetched {len(batches)} batches of sprints")
        return batch_index

    @task
    def ensure_table(schema_info: Dict[str, Any]):
        """
        Ensure the jira.sprints table exists.
        
        Args:
            schema_info: Schema information with columns.
        """
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        pg_hook = PostgresHook(
            conn_id=sync_config['target']['connection_id']
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
        
        created = pg_hook.create_table_if_not_exists(
            table_name=table_name,
            columns=columns,
            schema=schema_name
        )
        logger.info(f"Table {schema_name}.{table_name} {'created' if created else 'already exists'}")

    @task
    def sync_to_postgres(schema_info: Dict[str, Any], batch_count: int):
        """
        Upsert fetched sprints to PostgreSQL.
        
        Args:
            schema_info: Schema information with columns and mappings.
            batch_count: Number of batches from fetch_sprints.
        
        Returns:
            Latest complete_date for updating last_sync_timestamp.
        """
        sync_config = SYNC_CONFIGS[SYNC_KEY]
        pg_hook = PostgresHook(
            conn_id=sync_config['target']['connection_id']
        )
        context = get_current_context()
        ti = context['ti']
        
        table_name = sync_config['target']['table']
        schema_name = sync_config['target']['schema']
        upsert_conditions = ["id"]  # Primary key for upsert
        update_condition = None  # Remove for now to avoid ambiguous column error
        mappings = schema_info['mappings']
        latest_complete_date = None
        
        for i in range(batch_count):
            batch = ti.xcom_pull(key=f'sprint_batch_{i}', task_ids='fetch_sprints')
            if not batch:
                logger.warning(f"No data for batch {i}")
                continue
            
            for record in batch:
                if not all(key in record and record[key] is not None for key in ['id', 'name', 'state']):
                    logger.error(f"Invalid record in batch {i}: {record}")
                    raise ValueError(f"Invalid record missing required fields: {record}")
            
            # Add sync_time
            add_sync_time(batch, {'columns': schema_info['columns']})
            
            # Prepare rows using mappings
            rows = []
            columns = [m['target'] for m in mappings]
            for record in batch:
                row = {col: record.get(col) for col in columns}
                rows.append(row)
            
            rows_affected = pg_hook.upsert_rows(
                table_name=table_name,
                rows=rows,
                schema=schema_name,
                upsert_conditions=upsert_conditions,
                update_condition=update_condition
            )
            logger.info(f"Upserted {rows_affected} sprint records into {schema_name}.{table_name}")
            
            for record in batch:
                complete_date = record.get('complete_date')
                if complete_date:
                    try:
                        complete_dt = datetime.fromisoformat(complete_date.replace('Z', '+00:00'))
                        if not latest_complete_date or complete_dt > datetime.fromisoformat(latest_complete_date.replace('Z', '+00:00')):
                            latest_complete_date = complete_date
                    except ValueError:
                        logger.warning(f"Invalid complete_date in record: {complete_date}")
        
        if latest_complete_date:
            Variable.set('jira_sprints_last_sync', latest_complete_date)
            logger.info(f"Updated last_sync_timestamp to {latest_complete_date}")
        else:
            logger.info("No new complete_date found, last_sync_timestamp unchanged")
        
        return latest_complete_date

    # Define tasks
    schema_info = validate_schema()
    jira_conn = check_jira_connection()
    pg_conn = check_postgres_connection()
    board_ids = fetch_boards()
    batch_count = fetch_sprints(schema_info, board_ids)
    table = ensure_table(schema_info)
    sync = sync_to_postgres(schema_info, batch_count)

    # Define dependencies
    [schema_info, jira_conn, pg_conn] >> board_ids >> batch_count >> table >> sync

# Instantiate DAG
dag = sync_jira_sprints_to_postgres()