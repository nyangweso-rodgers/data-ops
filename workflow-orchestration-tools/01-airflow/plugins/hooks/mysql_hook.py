import logging
from typing import List, Any, Optional, Union, Dict, Iterator
import mysql.connector
from contextlib import contextmanager
from airflow.providers.mysql.hooks.mysql import MySqlHook as AirflowMySqlHook
from plugins.utils.constants import CONNECTION_IDS, LOG_LEVELS

class MySqlHook:
    """
    Reusable MySQL hook for Airflow DAGs to:
    - Verify database connections
    - Execute queries and fetch data
    Uses connection IDs defined in plugins/utils/constants.py.
    """
    
    def __init__(
        self,
        conn_id: str,
        log_level: str = 'INFO',
        connect_timeout: Optional[int] = None
    ):
        if not conn_id:
            raise ValueError("Connection ID must be provided.")
        if conn_id not in CONNECTION_IDS.values():
            raise ValueError(f"conn_id '{conn_id}' not found in CONNECTION_IDS: {CONNECTION_IDS.values()}")
        
        self.conn_id = conn_id
        self.connect_timeout = connect_timeout
        self.logger = logging.getLogger(__name__)
        if log_level not in LOG_LEVELS:
            raise ValueError(f"Invalid log_level '{log_level}'. Must be one of {list(LOG_LEVELS.keys())}")
        self.logger.setLevel(LOG_LEVELS[log_level])

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
    def get_conn(self) -> Iterator[mysql.connector.MySQLConnection]:
        conn_params = self._get_conn_params()
        conn = None
        try:
            self.logger.info(f"Connecting to MySQL database: {conn_params.get('database')} on {conn_params.get('host')}")
            conn = mysql.connector.connect(
                host=conn_params.get('host'),
                database=conn_params.get('database'),
                user=conn_params.get('user'),
                password=conn_params.get('password'),
                port=conn_params.get('port'),
                connect_timeout=self.connect_timeout
            )
            yield conn
        except Exception as e:
            self.logger.error(f"Error connecting to MySQL: {e}")
            raise
        finally:
            if conn:
                conn.close()
                self.logger.info("MySQL connection closed")

    @contextmanager
    def get_cursor(self) -> Iterator[mysql.connector.cursor.MySQLCursor]:
        with self.get_conn() as conn:
            cur = conn.cursor(dictionary=True)
            try:
                yield cur
                conn.commit()
            except Exception as e:
                conn.rollback()
                self.logger.error(f"Error executing query: {e}")
                raise
            finally:
                cur.close()

    def execute_query(
        self, 
        query: str, 
        params: Optional[Union[tuple, dict]] = None,
        fetch_batch: bool = False,
        batch_size: int = 500
    ) -> Union[List[Dict[str, Any]], Iterator[List[Dict[str, Any]]]]:
        """
        Execute a query and return results, optionally in batches.
        
        Args:
            query: SQL query to execute
            params: Parameters to pass to the query
            fetch_batch: If True, yield results in batches
            batch_size: Number of rows per batch (default: 500)
            
        Returns:
            List of rows if fetch_batch=False, or iterator of batches if fetch_batch=True
        """
        try:
            with self.get_cursor() as cur:
                # Execute the query to get total rows (for batching)
                if fetch_batch:
                    # First, get total count to determine number of batches
                    count_query = f"SELECT COUNT(*) FROM ({query}) AS subquery"
                    cur.execute(count_query, params)
                    total_rows = cur.fetchone()['COUNT(*)']
                    self.logger.info(f"Total rows to fetch: {total_rows}")

                    offset = 0
                    while offset < total_rows:
                        batch_query = f"{query} LIMIT {batch_size} OFFSET {offset}"
                        cur.execute(batch_query, params)
                        batch = cur.fetchall()
                        self.logger.info(f"Fetched batch of {len(batch)} rows at offset {offset}")
                        yield batch
                        offset += batch_size
                else:
                    cur.execute(query, params)
                    if cur.description:
                        return cur.fetchall()
                    return []
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            raise