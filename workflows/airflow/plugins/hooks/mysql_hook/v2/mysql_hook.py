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
    MySQL hook for database operations in Airflow DAGs.
    Uses connection IDs defined in plugins/utils/constants.v1.constants.py.
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
        """Get connection parameters from Airflow connection."""
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
    def get_connection(self) -> Iterator[MySQLConnection]:
        """Get MySQL connection with proper cleanup."""
        conn_params = self._get_conn_params()
        conn = None
        try:
            logger.debug(f"Attempting to connect to MySQL: {conn_params.get('database')} (conn_id: {self.conn_id})")
            conn = mysql.connector.connect(
                host=conn_params['host'],
                database=conn_params['database'],
                user=conn_params.get('user', ''),
                password=conn_params.get('password', ''),
                port=conn_params.get('port'),
                connect_timeout=self.connect_timeout
            )
            yield conn
        except Exception as e:
            logger.error(f"Error connecting to MySQL database {conn_params.get('database')} (conn_id: {self.conn_id}): {e}")
            raise
        finally:
            if conn and conn.is_connected():
                conn.close()
                logger.debug(f"MySQL connection to {conn_params.get('database')} closed (conn_id: {self.conn_id})")

    @contextmanager
    def get_cursor(self) -> Iterator[MySQLCursor]:
        """Get MySQL cursor with transaction management."""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True, buffered=False)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Error executing query (conn_id: {self.conn_id}): {e}")
                raise
            finally:
                cursor.close()

    def test_connection(self) -> Tuple[bool, str]:
        """Test database connection."""
        try:
            with self.get_cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                database = self._get_conn_params().get('database')
                if result and result.get('1') == 1:
                    logger.info(f"Successfully connected to MySQL: {database} (conn_id: {self.conn_id})")
                    return True, "Connection successful"
                return False, "Connection test returned unexpected result"
        except Exception as e:
            database = self._get_conn_params().get('database')
            logger.error(f"Failed to connect to MySQL database {database} (conn_id: {self.conn_id}): {str(e)}")
            return False, f"Connection failed: {str(e)}"

    def table_exists(self, table_name: str, database: Optional[str] = None) -> bool:
        """Check if table exists in database."""
        try:
            with self.get_cursor() as cur:
                query = """
                    SELECT COUNT(*) as count
                    FROM information_schema.tables
                    WHERE table_name = %s
                    AND table_schema = %s
                """
                database = database or self._get_conn_params()['database']
                cur.execute(query, (table_name, database))
                return cur.fetchone()['count'] > 0
        except Exception as e:
            logger.error(f"Error checking if table {table_name} exists (conn_id: {self.conn_id}): {e}")
            raise

    def get_table_columns(self, table_name: str, database: Optional[str] = None) -> List[Dict[str, str]]:
        """Get table column information."""
        try:
            with self.get_cursor() as cur:
                database = database or self._get_conn_params()['database']
                query = """
                    SELECT COLUMN_NAME AS column_name, DATA_TYPE AS data_type
                    FROM information_schema.columns
                    WHERE table_name = %s
                    AND table_schema = %s
                    ORDER BY ORDINAL_POSITION
                """
                cur.execute(query, (table_name, database))
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Error retrieving columns for table {table_name} (conn_id: {self.conn_id}): {e}")
            raise

    def execute_query(
        self,
        query: str,
        params: Optional[Union[tuple, dict]] = None,
        fetch_batch: bool = False,
        batch_size: Optional[int] = None,
        schema: Optional[Dict[str, Any]] = None
    ) -> Union[List[Dict[str, Any]], Iterator[List[Dict[str, Any]]], int]:
        if fetch_batch and batch_size is None:
            raise ValueError(f"batch_size must be provided when fetch_batch=True (conn_id: {self.conn_id})")
        """Execute query with optional batch processing and schema transformation."""
        try:
            with self.get_cursor() as cur:
                # Handle schema-based column selection and aliasing
                column_aliases = {}
                active_columns = []
                
                if schema and 'source' in schema and 'columns' in schema['source']:
                    for col, config in schema['source']['columns'].items():
                        if config.get('active', True):
                            source_col = col
                            target_col = config.get('target', col)
                            active_columns.append(source_col)
                            if target_col != source_col:
                                column_aliases[source_col] = target_col
                    
                    # Modify SELECT * queries to use active columns with aliases
                    if "SELECT" in query.upper() and "FROM" in query.upper():
                        if 'SELECT *' in query.upper() or not any(col in query for col in active_columns):
                            columns_str = ', '.join(
                                [f"`{col}` AS `{column_aliases.get(col, col)}`" if col in column_aliases else f"`{col}`"
                                 for col in active_columns]
                            )
                            query = query.replace('SELECT *', f"SELECT {columns_str}")
                            logger.debug(f"Modified query to select active columns with aliases (conn_id: {self.conn_id}): {query}")
                
                logger.debug(f"Executing query on database {self._get_conn_params()['database']} (conn_id: {self.conn_id}): {query}")
                cur.execute(query, params)
                
                if not cur.description:  # No result set (INSERT, UPDATE, DELETE)
                    return cur.rowcount
                
                if fetch_batch:
                    try:
                        while True:
                            batch = cur.fetchmany(batch_size)
                            if not batch:
                                break
                            logger.info(f"Fetched batch of {len(batch)} rows from database {self._get_conn_params()['database']} (conn_id: {self.conn_id})")
                            
                            # Apply column aliases if configured
                            if column_aliases:
                                remapped_batch = [
                                    {column_aliases.get(k, k): v for k, v in row.items()}
                                    for row in batch
                                ]
                                yield remapped_batch
                            else:
                                yield batch
                    except Exception as e:
                        # Consume remaining results to avoid "Unread result found" error
                        while cur.fetchmany(batch_size):
                            pass
                        logger.error(f"Error fetching batch (conn_id: {self.conn_id}): {e}")
                        raise
                else:
                    results = cur.fetchall()
                    # Apply column aliases if configured
                    if column_aliases:
                        return [
                            {column_aliases.get(k, k): v for k, v in row.items()}
                            for row in results
                        ]
                    return results
                    
        except Exception as e:
            logger.error(f"Error executing query on database {self._get_conn_params()['database']} (conn_id: {self.conn_id}): {e}")
            raise

    def insert_rows(self, table_name: str, rows: List[Dict[str, Any]], replace: bool = False, batch_size: int = None, commit_batch: bool = True) -> int:
        if not rows:
            return 0
        total_inserted = 0
        with self.get_connection() as conn:
            with conn.cursor(dictionary=True, buffered=False) as cur:
                columns = list(rows[0].keys())
                placeholders = ', '.join(['%s'] * len(columns))
                column_names = ', '.join([f"`{col}`" for col in columns])
                insert_type = "REPLACE" if replace else "INSERT"
                query = f"{insert_type} INTO `{table_name}` ({column_names}) VALUES ({placeholders})"
                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i + batch_size]
                    values = [tuple(row[col] for col in columns) for row in batch]
                    cur.executemany(query, values)
                    total_inserted += cur.rowcount
                    if commit_batch:
                        conn.commit()
                    logger.debug(f"Inserted batch of {len(batch)} rows into {table_name} (conn_id: {self.conn_id})")
                logger.info(f"Inserted {total_inserted} rows into {table_name} (conn_id: {self.conn_id})")
                return total_inserted


class MySqlSourceHook(MySqlHook):
    """MySQL hook for source (read) operations in ETL pipelines.
    Use for fetching data from a source database (e.g., amtdb.products).
    Avoid using for write operations; use MySqlTargetHook instead."""
    
    def __init__(self, source_conn_id: str, connect_timeout: Optional[int] = None):
        super().__init__(source_conn_id, connect_timeout)
        self.source_conn_id = self.conn_id  # Alias for clarity
        self.role = 'source'  # Role enforcement
    
    def insert_rows(self, *args, **kwargs):
        raise NotImplementedError("insert_rows not supported in MySqlSourceHook; use MySqlTargetHook")
    
    def get_source_cursor(self) -> Iterator[MySQLCursor]:
        """Get source MySQL cursor."""
        return self.get_cursor()
    
    def test_source_connection(self) -> Tuple[bool, str]:
        """Test source database connection."""
        success, message = self.test_connection()
        return success, message.replace("Connection", "Source connection")
    
    def table_exists_in_source(self, table_name: str, database: Optional[str] = None) -> bool:
        """Check if table exists in source database."""
        return self.table_exists(table_name, database)
    
    def get_source_table_columns(self, table_name: str, database: Optional[str] = None) -> List[Dict[str, str]]:
        """Get source table column information."""
        return self.get_table_columns(table_name, database)
    
    def execute_source_query(
        self,
        query: str,
        params: Optional[Union[tuple, dict]] = None,
        fetch_batch: bool = False,
        batch_size: Optional[int] = None,
        schema: Optional[Dict[str, Any]] = None
    ) -> Union[List[Dict[str, Any]], Iterator[List[Dict[str, Any]]], int]:
        """Execute query on source database."""
        return self.execute_query(query, params, fetch_batch, batch_size, schema)


class MySqlTargetHook(MySqlHook):
    """
    MySQL hook for target (write) operations in ETL pipelines.
    Use for writing data to a target database (e.g., target_db.products).
    Example:
        target_hook = MySqlTargetHook(target_conn_id='mysql_db_b')
        target_hook.upsert_rows_to_target(
            table_name='products',
            rows=[{'id': 1, 'name': 'Product A'}],
            key_columns=['id']
        )
    """
    
    def __init__(self, target_conn_id: str, connect_timeout: Optional[int] = None):
        super().__init__(target_conn_id, connect_timeout)
        self.target_conn_id = self.conn_id  # Alias for clarity
    
    def get_target_connection(self) -> Iterator[MySQLConnection]:
        """Get target MySQL connection."""
        return self.get_connection()
    
    def get_target_cursor(self) -> Iterator[MySQLCursor]:
        """Get target MySQL cursor."""
        return self.get_cursor()
    
    def test_target_connection(self) -> Tuple[bool, str]:
        """Test target database connection."""
        success, message = self.test_connection()
        return success, message.replace("Connection", "Target connection")
    
    def table_exists_in_target(self, table_name: str, database: Optional[str] = None) -> bool:
        """Check if table exists in target database."""
        return self.table_exists(table_name, database)
    
    def create_target_table_if_not_exists(
        self,
        table_name: str,
        columns: List[str],
        database: Optional[str] = None,
        engine: Optional[str] = None
    ) -> bool:
        if self.table_exists_in_target(table_name, database):
            logger.info(f"Target table {table_name} already exists in {database or self._get_conn_params()['database']} (conn_id: {self.target_conn_id})")
            return False
        if engine is None:
            raise ValueError(f"engine must be provided for create_target_table_if_not_exists (conn_id: {self.target_conn_id})")
        try:
            with self.get_target_cursor() as cur:
                database = database or self._get_conn_params()['database']
                query = f"CREATE TABLE `{database}`.`{table_name}` ({', '.join(columns)}) ENGINE={engine}"
                cur.execute(query)
                logger.info(f"Created target table {database}.{table_name} with engine {engine} (conn_id: {self.target_conn_id})")
                return True
        except Exception as e:
            logger.error(f"Error creating target table {database}.{table_name} (conn_id: {self.target_conn_id}): {e}")
            raise
    
    def get_target_table_columns(self, table_name: str, database: Optional[str] = None) -> List[Dict[str, str]]:
        """Get target table column information."""
        return self.get_table_columns(table_name, database)
    
    def execute_target_query(
        self,
        query: str,
        params: Optional[Union[tuple, dict, List[tuple]]] = None,
        fetch_batch: bool = False,
        batch_size: Optional[int] = None,
        schema: Optional[Dict[str, Any]] = None
    ) -> Union[List[Dict[str, Any]], Iterator[List[Dict[str, Any]]], int]:
        if isinstance(params, list):
            return self.execute_query(query, params, fetch_batch=False)  # executemany for batch writes
        return self.execute_query(query, params, fetch_batch, batch_size, schema)
    
    def upsert_rows_to_target(
        self,
        table_name: str,
        rows: List[Dict[str, Any]],
        key_columns: List[str],
        database: Optional[str] = None,
        batch_size: int = None,
        commit_batch: bool = True
    ) -> int:
        if not rows:
            return 0
        total_upserted = 0
        with self.get_connection() as conn:
            with conn.cursor(dictionary=True, buffered=False) as cur:
                columns = list(rows[0].keys())
                column_names = ', '.join([f"`{col}`" for col in columns])
                placeholders = ', '.join(['%s'] * len(columns))
                update_clause = ', '.join([f"`{col}` = VALUES(`{col}`)" for col in columns if col not in key_columns])
                database = database or self._get_conn_params()['database']
                query = f"""
                    INSERT INTO `{database}`.`{table_name}` ({column_names})
                    VALUES ({placeholders})
                    ON DUPLICATE KEY UPDATE {update_clause}
                """
                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i + batch_size]
                    values = [tuple(row[col] for col in columns) for row in batch]
                    cur.executemany(query, values)
                    total_upserted += cur.rowcount
                    if commit_batch:
                        conn.commit()
                    logger.debug(f"Upserted batch of {len(batch)} rows into {database}.{table_name} (conn_id: {self.target_conn_id})")
                logger.info(f"Upserted {total_upserted} rows into {database}.{table_name} (conn_id: {self.target_conn_id})")
                return total_upserted
        
    def add_column_to_target_table(
        self,
        table_name: str,
        column_name: str,
        column_type: str,
        database: Optional[str] = None,
        is_primary_key: bool = False
    ) -> None:
        """Add column to target table."""
        try:
            with self.get_target_cursor() as cur:
                database = database or self._get_conn_params()['database']
                column_def = f"`{column_name}` {column_type}"
                if is_primary_key:
                    column_def += " PRIMARY KEY"
                alter_query = f"ALTER TABLE `{database}`.`{table_name}` ADD {column_def}"
                cur.execute(alter_query)
                logger.info(f"Added column {column_name} to target table {database}.{table_name} (conn_id: {self.target_conn_id})")
        except Exception as e:
            logger.error(f"Error adding column {column_name} to target table {table_name} (conn_id: {self.target_conn_id}): {e}")
            raise