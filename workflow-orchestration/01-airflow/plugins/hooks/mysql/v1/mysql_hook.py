import logging
from typing import List, Any, Optional, Union, Dict, Iterator, Tuple
import mysql.connector
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor
from contextlib import contextmanager
from airflow.providers.mysql.hooks.mysql import MySqlHook as AirflowMySqlHook
from plugins.utils.constants import CONNECTION_IDS, LOG_LEVELS

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
        log_level: str = 'INFO',
        connect_timeout: Optional[int] = None
    ):
        """
        Initialize the MySqlHook with an Airflow connection ID.
        
        Args:
            conn_id: Airflow connection ID. Must match a key in CONNECTION_IDS.
            log_level: Logging level (e.g., 'DEBUG', 'INFO'). Must be a key in LOG_LEVELS.
            connect_timeout: Connection timeout in seconds (optional).
        """
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
        """
        Get connection parameters from Airflow's connection store.
        
        Returns:
            Dictionary containing MySQL connection parameters
        """
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
        """
        Context manager for MySQL connections.
        
        Yields:
            mysql.connector.MySQLConnection object
        """
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
    def get_cursor(self) -> Iterator[MySQLCursor]:
        """
        Context manager for MySQL cursors.
        
        Yields:
            mysql.connector.cursor.MySQLCursor object
        """
        with self.get_conn() as conn:
            cur = conn.cursor(dictionary=True, buffered=False)
            try:
                yield cur
                conn.commit()
            except Exception as e:
                conn.rollback()
                self.logger.error(f"Error executing query: {e}")
                raise
            finally:
                cur.close()

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the MySQL connection.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with self.get_cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                if result and result['1'] == 1:
                    return True, "Connection successful"
                return False, "Connection test returned unexpected result"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def table_exists(self, table_name: str, database: Optional[str] = None) -> bool:
        """
        Check if a table exists in the database.
        
        Args:
            table_name: Name of the table to check
            database: Database name (optional, defaults to connection's database)
            
        Returns:
            True if table exists, False otherwise
        """
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
            self.logger.error(f"Error checking if table exists: {e}")
            raise

    def create_table_if_not_exists(
        self,
        table_name: str,
        columns: List[str],
        database: Optional[str] = None
    ) -> bool:
        """
        Create a table if it doesn't exist.
        
        Args:
            table_name: Name of the table to create
            columns: List of column definitions (e.g., ["id INT PRIMARY KEY", "name VARCHAR(255)"])
            database: Database name (optional, defaults to connection's database)
            
        Returns:
            True if table was created, False if it already existed
        """
        if self.table_exists(table_name, database):
            self.logger.info(f"Table {table_name} already exists, skipping creation")
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
                self.logger.info(f"Table {database}.{table_name} created successfully")
                return True
        except Exception as e:
            self.logger.error(f"Error creating table: {e}")
            raise

    def get_table_columns(self, table_name: str, database: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Retrieve the columns of a table from the database.
        
        Args:
            table_name: Name of the table
            database: Database name (optional, defaults to connection's database)
            
        Returns:
            List of dictionaries with column_name and data_type
        """
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
            self.logger.error(f"Error retrieving table columns: {e}")
            raise

    def add_column(
        self,
        table_name: str,
        column_name: str,
        column_type: str,
        database: Optional[str] = None,
        is_primary_key: bool = False
    ) -> None:
        """
        Add a column to an existing table.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column to add
            column_type: SQL type of the column (e.g., 'VARCHAR(100)', 'INT')
            database: Database name (optional, defaults to connection's database)
            is_primary_key: If True, adds PRIMARY KEY constraint
        """
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
                self.logger.info(f"Added column {column_name} to {database}.{table_name}")
        except Exception as e:
            self.logger.error(f"Error adding column {column_name}: {e}")
            raise

    def execute_query(
        self, 
        query: str, 
        params: Optional[Union[tuple, dict]] = None,
        fetch_batch: bool = False,
        batch_size: int = 500,
        schema: Optional[Dict[str, Any]] = None
    ) -> Union[List[Dict[str, Any]], Iterator[List[Dict[str, Any]]], int]:
        """
        Execute a query and return results, optionally in batches, respecting active columns and target mappings in schema.
        
        Args:
            query: SQL query to execute
            params: Parameters to pass to the query
            fetch_batch: If True, yield results in batches
            batch_size: Number of rows per batch (default: 500)
            schema: Schema dictionary from SchemaLoader (optional, to filter active columns and apply target mappings)
            
        Returns:
            List of rows if fetch_batch=False and query returns results,
            iterator of batches if fetch_batch=True,
            or number of affected rows for non-SELECT queries
        """
        try:
            with self.get_cursor() as cur:
                # If schema provided, filter columns by source_active and apply target mappings
                if schema and 'source' in schema and 'columns' in schema['source']:
                    active_columns = []
                    column_aliases = {}
                    for col, config in schema['source']['columns'].items():
                        if config.get('source_active', True):
                            source_col = col
                            target_col = config.get('target', col)  # Use target name if defined, else source name
                            active_columns.append(source_col)
                            if target_col != source_col:
                                column_aliases[source_col] = target_col
                    
                    if "SELECT" in query.upper() and "FROM" in query.upper():
                        # Replace SELECT * or column list with aliased active columns
                        if 'SELECT *' in query.upper() or not any(col in query for col in active_columns):
                            columns_str = ', '.join(
                                [f"`{col}` AS `{column_aliases.get(col, col)}`" if col in column_aliases else f"`{col}`"
                                 for col in active_columns]
                            )
                            query = query.replace('SELECT *', f'SELECT {columns_str}')
                            self.logger.debug(f"Modified query with active columns and target aliases: {query}")
                
                cur.execute(query, params)
                if not cur.description:  # Non-SELECT query (e.g., INSERT, UPDATE)
                    return cur.rowcount
                
                if fetch_batch:
                    while True:
                        batch = cur.fetchmany(batch_size)
                        if not batch:
                            break
                        self.logger.info(f"Fetched batch of {len(batch)} rows")
                        # Remap column names to target names in each batch
                        if column_aliases:
                            remapped_batch = [
                                {column_aliases.get(k, k): v for k, v in row.items()}
                                for row in batch
                            ]
                            yield remapped_batch
                        else:
                            yield batch
                else:
                    results = cur.fetchall()
                    # Remap column names to target names in results
                    if column_aliases:
                        return [
                            {column_aliases.get(k, k): v for k, v in row.items()}
                            for row in results
                        ]
                    return results
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            raise