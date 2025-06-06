import logging
from typing import Iterator, Tuple, List, Any, Optional, Union, Dict
import mysql.connector
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor
from contextlib import contextmanager
from airflow.providers.mysql.hooks.mysql import MySqlHook as AirflowMySqlHook
from plugins.utils.constants.v1.constants import CONNECTION_IDS

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class MySqlHook:
    """
    Reusable MySQL hook for Airflow DAGs to:
    - Verify database connections
    - Execute queries and fetch data
    - Check and create tables
    - Retrieve and update table schema
    Uses connection IDs defined in plugins/utils/constants.py.
    """
    
    def __init__(
        self,
        conn_id: str,
        connect_timeout: Optional[int] = None
    ):
        if not conn_id:
            raise ValueError("Connection ID must be provided.")
        if conn_id not in CONNECTION_IDS.values():
            raise ValueError(f"conn_id '{conn_id}' not found in CONNECTION_IDS: {CONNECTION_IDS.values()}")
        
        self.conn_id = conn_id
        self.connect_timeout = connect_timeout

    def _get_conn_params(self) -> dict:
        airflow_hook = AirflowMySqlHook(mysql_conn_id=self.conn_id)
        conn = airflow_hook.get_connection(self.conn_id)
        return {
            'host': conn.host,
            'database': conn.schema,
            'user': conn.login,
            'password': conn.password,
            'port': conn.port or 3306
        }

    @contextmanager
    def get_conn(self) -> Iterator[MySQLConnection]:
        conn_params = self._get_conn_params()
        conn = None
        try:
            logger.debug(f"Attempting connection to MySQL database: {conn_params.get('database')}")
            conn = mysql.connector.connect(
                host=conn_params.get('host'),
                database=conn_params.get('database'),
                user=conn_params.get('user', ''),
                password=conn_params.get('password', ''),
                port=conn_params.get('port', 3306),
                connect_timeout=self.connect_timeout
            )
            yield conn
        except Exception as e:
            logger.error(f"Error connecting to MySQL database {conn_params.get('database')}: {e}")
            raise
        finally:
            if conn:
                conn.close()
                logger.debug(f"MySQL connection to database {conn_params.get('database')} closed")

    @contextmanager
    def get_cursor(self) -> Iterator[MySQLCursor]:
        with self.get_conn() as conn:
            cursor = conn.cursor(dictionary=True, buffered=False)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Error executing query: {e}")
                raise
            finally:
                cursor.close()

    def test_connection(self) -> Tuple[bool, str]:
        try:
            with self.get_cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                database = self._get_conn_params().get('database')
                if result and result.get('1') == 1:
                    logger.info(f"Successfully connected to MySQL database: {database}")
                    return True, "Connection successful"
                return False, "Connection test returned unexpected result"
        except Exception as e:
            database = self._get_conn_params().get('database')
            logger.error(f"Failed to connect to MySQL database {database}: {str(e)}")
            return False, f"Connection failed: {str(e)}"

    def table_exists(self, table_name: str, database: Optional[str] = None) -> bool:
        try:
            with self.get_cursor() as cur:
                query = """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_name = %s
                    AND table_schema = %s
                """
                database = database or self._get_conn_params()['database']
                cur.execute(query, (table_name, database))
                return cur.fetchone()['COUNT(*)'] > 0
        except Exception as e:
            logger.error(f"Error checking if table exists: {e}")
            raise

    def create_table_if_not_exists(
        self,
        table_name: str,
        columns: List[str],
        database: Optional[str] = None
    ) -> bool:
        if self.table_exists(table_name, database):
            logger.info(f"Table {table_name} already exists, skipping creation")
            return False
        
        try:
            with self.get_cursor() as cur:
                database = database or self._get_conn_params()['database']
                create_table_query = f"""
                    CREATE TABLE `{database}`.`{table_name}` (
                        {', '.join(columns)}
                    ) ENGINE=InnoDB
                """
                cur.execute(create_table_query)
                logger.info(f"Table {database}.{table_name} created successfully")
                return True
        except Exception as e:
            logger.error(f"Error creating table: {e}")
            raise

    def get_table_columns(self, table_name: str, database: Optional[str] = None) -> List[Dict[str, str]]:
        try:
            with self.get_cursor() as cur:
                database = database or self._get_conn_params()['database']
                query = """
                    SELECT COLUMN_NAME AS column_name, DATA_TYPE AS data_type
                    FROM information_schema.columns
                    WHERE table_name = %s
                    AND table_schema = %s
                """
                cur.execute(query, (table_name, database))
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Error retrieving table columns: {e}")
            raise

    def add_column(
        self,
        table_name: str,
        column_name: str,
        column_type: str,
        database: Optional[str] = None,
        is_primary_key: bool = False
    ) -> None:
        try:
            with self.get_cursor() as cur:
                database = database or self._get_conn_params()['database']
                column_def = f"`{column_name}` {column_type}"
                if is_primary_key:
                    column_def += " PRIMARY KEY"
                alter_query = f"""
                    ALTER TABLE `{database}`.`{table_name}`
                    ADD {column_def}
                """
                cur.execute(alter_query)
                logger.info(f"Added column {column_name} to {database}.{table_name}")
        except Exception as e:
            logger.error(f"Error adding column {column_name}: {e}")
            raise

    def execute_query(
        self,
        query: str,
        params: Optional[Union[tuple, dict]] = None,
        fetch_batch: bool = False,
        batch_size: int = 500,
        schema: Optional[Dict[str, Any]] = None
    ) -> Union[List[Dict[str, Any]], Iterator[List[Dict[str, Any]]], int]:
        try:
            with self.get_cursor() as cur:
                # Initialize variables to avoid UnboundLocalError
                column_aliases = {}
                active_columns = []
                
                # Apply schema transformations if schema is provided
                if schema and 'source' in schema and 'columns' in schema['source']:
                    for col, config in schema['source']['columns'].items():
                        if config.get('active', True):
                            source_col = col
                            target_col = config.get('target', col)
                            active_columns.append(source_col)
                            if target_col != source_col:
                                column_aliases[source_col] = target_col
                    
                    if "SELECT" in query.upper() and "FROM" in query.upper():
                        if 'SELECT *' in query.upper() or not any(col in query for col in active_columns):
                            columns_str = ', '.join(
                                [f"`{col}` AS `{column_aliases.get(col, col)}`" if col in column_aliases else f"`{col}`"
                                 for col in active_columns]
                            )
                            query = query.replace('SELECT *', f"SELECT {columns_str}")
                            logger.debug(f"Modified query to select active columns and target aliases: {query}")
                
                cur.execute(query, params)
                if not cur.description:
                    return cur.rowcount
                
                if fetch_batch:
                    try:
                        while True:
                            batch = cur.fetchmany(batch_size)
                            if not batch:
                                break
                            logger.info(f"Fetched batch of {len(batch)} rows")
                            if column_aliases:
                                remapped_batch = [
                                    {column_aliases.get(k, k): v for k, v in row.items()}
                                    for row in batch
                                ]
                                yield remapped_batch
                            else:
                                yield batch
                    except Exception as e:
                        while cur.fetchmany(batch_size):
                            pass
                        raise e
                else:
                    results = cur.fetchall()
                    if column_aliases:
                        return [
                            {column_aliases.get(k, k): v for k, v in row.items()}
                            for row in results
                        ]
                    return results
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise