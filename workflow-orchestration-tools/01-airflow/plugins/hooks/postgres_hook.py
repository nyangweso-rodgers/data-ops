import logging
from typing import Tuple, List, Any, Union, Optional, Dict, Iterator
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import connection, cursor
from psycopg2.extras import execute_values
from contextlib import contextmanager
from airflow.providers.postgres.hooks.postgres import PostgresHook as AirflowPostgresHook

# Import constants
from plugins.utils.constants import CONNECTION_IDS, LOG_LEVELS

class PostgresHook:
    """
    Reusable PostgreSQL hook for Airflow DAGs to:
    - Verify database connections
    - Check if tables exist
    - Create tables if they don't exist
    """
    
    def __init__(
        self, 
        conn_id: str = None,
        log_level: str = 'INFO',
        connect_timeout: Optional[int] = None
    ):
        """
        Initialize the PostgresHook with an Airflow connection ID.
        
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
            Dictionary containing PostgreSQL connection parameters
        """
        airflow_hook = AirflowPostgresHook(postgres_conn_id=self.conn_id)
        conn = airflow_hook.get_connection(self.conn_id)
        return {
            'host': conn.host,
            'dbname': conn.schema,
            'user': conn.login,
            'password': conn.password,
            'port': str(conn.port or 5432)
        }
    @contextmanager
    def get_conn(self) -> Iterator[connection]:
        """
        Context manager for PostgreSQL connections.
        
        Yields:
            psycopg2 connection object
        """
        conn_params = self._get_conn_params()
        conn = None
        try:
            self.logger.info(f"Connecting to PostgreSQL database: {conn_params.get('dbname')} on {conn_params.get('host')}")
            conn = psycopg2.connect(
                host=conn_params.get('host'),
                dbname=conn_params.get('dbname'),
                user=conn_params.get('user'),
                password=conn_params.get('password'),
                port=conn_params.get('port'),
                connect_timeout=self.connect_timeout
            )
            yield conn
        except Exception as e:
            self.logger.error(f"Error connecting to PostgreSQL: {e}")
            raise
        finally:
            if conn:
                conn.close()
                self.logger.info("PostgreSQL connection closed")
                
    @contextmanager
    def get_cursor(self) -> Iterator[cursor]:
        """
        Context manager for PostgreSQL cursors.
        
        Yields:
            psycopg2 cursor object
        """
        with self.get_conn() as conn:
            cur = conn.cursor()
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
        Test the PostgreSQL connection.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with self.get_cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                if result and result[0] == 1:
                    return True, "Connection successful"
                return False, "Connection test returned unexpected result"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
        
    def table_exists(self, table_name: str, schema: str = "public") -> bool:
        """
        Check if a table exists in the database.
        
        Args:
            table_name: Name of the table to check
            schema: Database schema (default: public)
            
        Returns:
            True if table exists, False otherwise
        """
        try:
            with self.get_cursor() as cur:
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = %s AND table_name = %s
                    )
                    """,
                    (schema, table_name)
                )
                return cur.fetchone()[0]
        except Exception as e:
            self.logger.error(f"Error checking if table exists: {e}")
            raise
        
    def create_table_if_not_exists(
        self, 
        table_name: str, 
        columns: List[str],
        schema: str = "public"
    ) -> bool:
        """
        Create a table if it doesn't exist.
        
        Args:
            table_name: Name of the table to create
            columns: List of column definitions (e.g., ["id SERIAL PRIMARY KEY", "name TEXT NOT NULL"])
            schema: Database schema (default: public)
            
        Returns:
            True if table was created, False if it already existed
        """
        if self.table_exists(table_name, schema):
            self.logger.info(f"Table {schema}.{table_name} already exists, skipping creation")
            return False
        
        try:
            with self.get_cursor() as cur:
                create_table_query = sql.SQL("""
                    CREATE TABLE {schema}.{table} (
                        {columns}
                    )
                """).format(
                    schema=sql.Identifier(schema),
                    table=sql.Identifier(table_name),
                    columns=sql.SQL(', '.join(columns))
                )
                cur.execute(create_table_query)
                self.logger.info(f"Table {schema}.{table_name} created successfully")
                return True
        except Exception as e:
            self.logger.error(f"Error creating table: {e}")
            raise
    def execute_query(
        self, 
        query: str, 
        params: Optional[Union[tuple, dict]] = None
    ) -> List[Any]:
        """
        Execute a query and return all results.
        
        Args:
            query: SQL query to execute
            params: Parameters to pass to the query
            
        Returns:
            List of query results
        """
        try:
            with self.get_cursor() as cur:
                cur.execute(query, params)
                if cur.description:  # Query returns results
                    return cur.fetchall()
                return cur.rowcount  # Query affects rows (e.g., UPDATE, DELETE)
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            raise
    
    def insert_rows(
        self,
        table_name: str,
        rows: List[Dict[str, Any]],
        schema: str = "public"
    ) -> int:
        """
        Insert multiple rows into a table using bulk insertion.
        
        Args:
            table_name: Name of the table
            rows: List of dictionaries with column:value pairs
            schema: Database schema (default: public)
            
        Returns:
            Number of rows inserted
        """
        if not rows:
            return 0
        
        try:
            # Get column names from first row
            columns = list(rows[0].keys())
            
            # Prepare the query
            insert_query = sql.SQL("""
                INSERT INTO {schema}.{table} ({columns})
                VALUES %s
            """).format(
                schema=sql.Identifier(schema),
                table=sql.Identifier(table_name),
                columns=sql.SQL(', ').join(map(sql.Identifier, columns))
            )
            
            # Convert rows to list of tuples for execute_values
            values = [tuple(row[col] for col in columns) for row in rows]
            
            with self.get_cursor() as cur:
                execute_values(cur, insert_query.as_string(cur), values)
            
            return len(rows)
        except Exception as e:
            self.logger.error(f"Error inserting rows: {e}")
            raise