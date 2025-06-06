import logging
from typing import Tuple, List, Any, Union, Optional, Dict, Iterator
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import connection, cursor
from psycopg2.extras import execute_values
from contextlib import contextmanager
from airflow.providers.postgres.hooks.postgres import PostgresHook as AirflowPostgresHook
from datetime import datetime

# Import constants
from plugins.utils.constants.v1.constants import CONNECTION_IDS

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class PostgresHook:
    """
    Reusable PostgreSQL hook for Airflow DAGs to:
    - Verify database connections
    - Check if tables exist
    - Create tables if they don't exist
    - Retrieve table schema
    - Add columns to existing tables
    - Upsert rows with conflict handling
    Uses connection IDs defined in plugins/utils/constants.py.
    """
    
    def __init__(
        self,
        conn_id: str = None,
        connect_timeout: Optional[int] = None
    ):
        if not conn_id:
            raise ValueError("Connection ID must be provided.")
        if conn_id not in CONNECTION_IDS.values():
            raise ValueError(f"conn_id '{conn_id}' not found in CONNECTION_IDS: {CONNECTION_IDS.values()}")
        
        self.conn_id = conn_id
        self.connect_timeout = connect_timeout
        
    def _get_conn_params(self) -> dict:
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
        conn_params = self._get_conn_params()
        conn = None
        try:
            logger.debug(f"Attempting connection to PostgreSQL database: {conn_params.get('dbname')}")
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
            logger.error(f"Error connecting to PostgreSQL database {conn_params.get('dbname')}: {e}")
            raise
        finally:
            if conn:
                conn.close()
                logger.debug(f"PostgreSQL connection to database {conn_params.get('dbname')} closed")
                
    @contextmanager
    def get_cursor(self) -> Iterator[cursor]:
        with self.get_conn() as conn:
            cur = conn.cursor()
            try:
                yield cur
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Error executing query: {e}")
                raise
            finally:
                cur.close()
    
    def test_connection(self) -> Tuple[bool, str]:
        try:
            with self.get_cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                database = self._get_conn_params().get('dbname')
                if result and result[0] == 1:
                    logger.info(f"Successfully connected to PostgreSQL database: {database}")
                    return True, "Connection successful"
                return False, "Connection test returned unexpected result"
        except Exception as e:
            database = self._get_conn_params().get('dbname')
            logger.error(f"Failed to connect to PostgreSQL database {database}: {str(e)}")
            return False, f"Connection failed: {str(e)}"
        
    def table_exists(self, table_name: str, schema: str = "public") -> bool:
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
            logger.error(f"Error checking if table exists: {e}")
            raise
        
    def create_table_if_not_exists(
        self,
        table_name: str,
        columns: List[str],
        schema: str = "public"
    ) -> bool:
        if self.table_exists(table_name, schema):
            logger.info(f"Table {schema}.{table_name} already exists, skipping creation")
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
                    columns=sql.SQL(', ').join(map(sql.SQL, columns))
                )
                cur.execute(create_table_query)
                logger.info(f"Table {schema}.{table_name} created successfully")
                return True
        except Exception as e:
            logger.error(f"Error creating table: {e}")
            raise
    
    def get_table_columns(self, schema: str, table_name: str) -> List[Dict[str, str]]:
        try:
            query = """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
            """
            with self.get_cursor() as cur:
                cur.execute(query, (schema, table_name))
                results = cur.fetchall()
                return [{"column_name": row[0], "data_type": row[1]} for row in results]
        except Exception as e:
            logger.error(f"Error retrieving table columns: {e}")
            raise
    
    def add_column(
        self,
        schema: str,
        table_name: str,
        column_name: str,
        column_type: str,
        is_primary_key: bool = False
    ) -> None:
        try:
            column_def = f"{column_name} {column_type}"
            if is_primary_key:
                column_def += " PRIMARY KEY"
            alter_query = sql.SQL("""
                ALTER TABLE {schema}.{table}
                ADD COLUMN {column_def}
            """).format(
                schema=sql.Identifier(schema),
                table=sql.Identifier(table_name),
                column_def=sql.SQL(column_def)
            )
            with self.get_cursor() as cur:
                cur.execute(alter_query)
                logger.info(f"Added column {column_name} to {schema}.{table_name}")
        except Exception as e:
            logger.error(f"Error adding column {column_name}: {e}")
            raise
    
    def execute_query(
        self,
        query: str,
        params: Optional[Union[tuple, dict]] = None,
        fetch: bool = False
    ) -> Union[List[Any], int]:
        try:
            with self.get_cursor() as cur:
                cur.execute(query, params)
                if fetch and cur.description:
                    return cur.fetchall()
                return cur.rowcount
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def insert_rows(
        self,
        table_name: str,
        rows: List[Dict[str, Any]],
        schema: str = "public"
    ) -> int:
        if not rows:
            return 0
        
        try:
            columns = list(rows[0].keys())
            insert_query = sql.SQL("""
                INSERT INTO {schema}.{table} ({columns})
                VALUES %s
            """).format(
                schema=sql.Identifier(schema),
                table=sql.Identifier(table_name),
                columns=sql.SQL(', ').join(map(sql.Identifier, columns))
            )
            values = [tuple(row[col] for col in columns) for row in rows]
            
            with self.get_cursor() as cur:
                execute_values(cur, insert_query.as_string(cur), values)
            
            return len(rows)
        except Exception as e:
            logger.error(f"Error inserting rows: {e}")
            raise
    
    def upsert_rows(
        self,
        table_name: str,
        rows: List[Dict[str, Any]],
        schema: str = "public",
        upsert_conditions: List[str] = None,
        update_condition: str = None
    ) -> int:
        if not rows:
            logger.warning("No rows to upsert")
            return 0
        
        if not upsert_conditions:
            raise ValueError("upsert_conditions must be provided for upsert operation")
        
        try:
            columns = list(rows[0].keys())
            update_columns = [col for col in columns if col not in upsert_conditions]
            insert_query = sql.SQL("""
                INSERT INTO {schema}.{table} ({columns})
                VALUES %s
                ON CONFLICT ({conflict_cols})
                DO UPDATE SET {column_updates}
            """).format(
                schema=sql.Identifier(schema),
                table=sql.Identifier(table_name),
                columns=sql.SQL(', ').join(map(sql.Identifier, columns)),
                conflict_cols=sql.SQL(', ').join(map(sql.Identifier, upsert_conditions)),
                column_updates=sql.SQL(', ').join(
                    sql.SQL(f"{sql.Identifier(col)} = EXCLUDED.{sql.Identifier(col)}")
                    for col in update_columns
                )
            )
            
            if update_condition:
                insert_query = sql.SQL(f"{insert_query} WHERE {update_condition}")
            
            values = []
            for row in rows:
                row_values = []
                for col in columns:
                    value = row.get(col)
                    if col in ['start_date', 'end_date', 'created_date', 'complete_date', 'sync_time'] and value is not None:
                        try:
                            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except ValueError:
                            logger.warning(f"Invalid timestamp format for {col}: {value}. Setting to None.")
                            value = None
                    row_values.append(value)
                values.append(tuple(row_values))
            
            with self.get_cursor() as cur:
                execute_values(cur, insert_query.as_string(cur), values)
                rows_affected = cur.rowcount
                logger.info(f"Upserted {rows_affected} rows to {schema}.{table_name}")
                return rows_affected
        except Exception as e:
            logger.error(f"Error upserting rows: {e}")
            raise