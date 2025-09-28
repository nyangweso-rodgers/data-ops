from airflow.providers.postgres.hooks.postgres import PostgresHook as AirflowPostgresHook
from contextlib import contextmanager
from typing import Iterator, Dict, Any, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import logging
import json
from datetime import datetime

# Configure module-level logger
logger = logging.getLogger(__name__)

class PostgresConnectionError(Exception):
    """Custom exception for PostgreSQL connection failures."""
    pass

class PostgresHook:
    """
    Base Postgres hook for database operations in Airflow DAGs.
    Provides connection and cursor management for source and target operations.

    Args:
        conn_id (str): Airflow connection ID for the PostgreSQL database.
    """
    def __init__(self, conn_id: str):
        self.conn_id = conn_id
        self.airflow_hook = AirflowPostgresHook(pg_conn_id=self.conn_id)

    def _get_pg_conn_params(self) -> Dict[str, Any]:
        """
        Get connection parameters from Airflow connection.

        Returns:
            Dict containing host, database, user, password, and port.

        Raises:
            PostgresConnectionError: If connection parameters are invalid.
        """
        try:
            conn = self.airflow_hook.get_connection(self.conn_id)
            params = {
                'host': conn.host,
                'database': conn.schema,
                'user': conn.login,
                'password': conn.password,
                'port': conn.port or 5432,
                'connect_timeout': 10
            }
            logger.debug(f"Retrieved connection params for conn_id: {self.conn_id}")
            return params
        except Exception as e:
            logger.error(f"Failed to get connection params for conn_id {self.conn_id}: {str(e)}")
            raise PostgresConnectionError(f"Invalid connection parameters for {self.conn_id}: {str(e)}")

    @contextmanager
    def get_pg_connection(self) -> Iterator[psycopg2.extensions.connection]:
        """
        Get a PostgreSQL connection with automatic cleanup.

        Yields:
            psycopg2 connection object.

        Raises:
            PostgresConnectionError: If connection fails.
        """
        conn = None
        try:
            conn = psycopg2.connect(**self._get_pg_conn_params())
            logger.info(f"Established connection to database: {conn.dsn}")
            yield conn
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database with conn_id {self.conn_id}: {str(e)}")
            raise PostgresConnectionError(f"Connection failed for {self.conn_id}: {str(e)}")
        finally:
            if conn:
                conn.close()
                logger.debug(f"Closed connection for conn_id: {self.conn_id}")

    @contextmanager
    def get_pg_cursor(self) -> Iterator[RealDictCursor]:
        """
        Get a PostgreSQL cursor with transaction management.

        Yields:
            RealDictCursor object for querying.

        Raises:
            PostgresConnectionError: If connection or cursor creation fails.
        """
        with self.get_pg_connection() as conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    logger.debug(f"Created cursor for conn_id: {self.conn_id}")
                    yield cursor
                    conn.commit()
            except psycopg2.Error as e:
                conn.rollback()
                logger.error(f"Cursor operation failed for conn_id {self.conn_id}: {str(e)}")
                raise PostgresConnectionError(f"Cursor operation failed: {str(e)}")

class PostgresSourceHook(PostgresHook):
    """
    Postgres hook for source (read) operations in ETL pipelines.

    Args:
        conn_id (str): Airflow connection ID for the source PostgreSQL database.
    """
    def __init__(self, conn_id: str):
        super().__init__(conn_id)

    def get_pg_source_connection(self) -> Dict[str, str]:
        """
        Get the Postgres source connection details and test connectivity.

        Returns:
            Dict with status and message (e.g., {"status": "success", "message": "Connection successful"}).

        Example:
            >>> hook = PostgresSourceHook(conn_id="postgres-sunculture-ep-db")
            >>> hook.get_pg_source_connection()
            {"status": "success", "message": "Connection successful to postgres-sunculture-ep-db"}
        """
        try:
            with self.get_pg_connection() as conn:
                summary = {
                    "event": "source_connection_test",
                    "conn_id": self.conn_id,
                    "status": "success",
                    "message": f"Connection successful to {self.conn_id}",
                    "timestamp": datetime.now().isoformat()
                }
                logger.info(f"Source connection summary: {json.dumps(summary)}")
                return summary
        except PostgresConnectionError as e:
            summary = {
                "event": "source_connection_test",
                "conn_id": self.conn_id,
                "status": "failure",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"Source connection summary: {json.dumps(summary)}")
            return summary

    def test_pg_source_connection(self) -> Dict[str, str]:
        """
        Test the Postgres source connection.

        Returns:
            Dict with status and message.

        Example:
            >>> hook = PostgresSourceHook(conn_id="postgres-sunculture-ep-db")
            >>> hook.test_pg_source_connection()
            {"status": "success", "message": "Connection successful to postgres-sunculture-ep-db"}
        """
        return self.get_pg_source_connection()

    def pg_source_table_exists(self, table: str, schema: str) -> bool:
        """
        Check if a table exists in the source database.

        Args:
            table (str): Name of the table to check.
            schema (str): Schema name.

        Returns:
            bool: True if table exists, False otherwise.

        Example:
            >>> hook = PostgresSourceHook(conn_id="postgres-sunculture-ep-db")
            >>> hook.pg_source_table_exists("premises", "public")
            True
        """
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        )
        """
        try:
            with self.get_pg_cursor() as cursor:
                cursor.execute(query, (schema, table))
                exists = cursor.fetchone()['exists']
                logger.info(f"Table {schema}.{table} exists in source: {exists}")
                return exists
        except PostgresConnectionError as e:
            logger.error(f"Failed to check table {schema}.{table} in source: {str(e)}")
            raise

    def fetch_pg_source_rows(self, table: str, columns: List[str], schema: str, batch_size: int, incremental_column: Optional[str] = None, last_updated_at: Optional[str] = None) -> Iterator[Tuple[List[Dict[str, Any]], Optional[str]]]:
        """
        Fetch rows from the source table in batches, optionally filtering by incremental_column.
        Tracks the max incremental_column value (e.g., updated_at) for each batch.

        Args:
            table (str): Name of the source table.
            columns (List[str]): List of column names to fetch.
            schema (str): Schema name.
            batch_size (int): Number of rows per batch.
            incremental_column (Optional[str]): Column for incremental sync (e.g., "updated_at").
            last_updated_at (Optional[str]): Last updated_at timestamp for incremental sync.

        Yields:
            Tuple of (batch rows, max incremental_column value) for immediate processing.

        Example:
            >>> hook = PostgresSourceHook(conn_id="postgres-sunculture-ep-db")
            >>> for batch, max_updated_at in hook.fetch_pg_source_rows("premises", ["id", "updated_at"], "public", 5000, "updated_at", "2025-06-14T00:00:00"):
            >>>     print(len(batch), max_updated_at)
        """
        query = f"SELECT {', '.join([f'\"{col}\"' for col in columns])} FROM {schema}.{table}"
        params = []
        if incremental_column and last_updated_at:
            query += f" WHERE \"{incremental_column}\" >= %s ORDER BY \"{incremental_column}\""
            params.append(last_updated_at)
        
        try:
            with self.get_pg_cursor() as cursor:
                cursor.execute(query, params)
                while True:
                    rows = cursor.fetchmany(batch_size)
                    if not rows:
                        break
                    max_updated_at = max(row[incremental_column] for row in rows).isoformat() if incremental_column in columns else None
                    logger.debug(f"Fetched {len(rows)} rows from {schema}.{table} in source, max {incremental_column}: {max_updated_at}")
                    yield rows, max_updated_at
        except PostgresConnectionError as e:
            logger.error(f"Failed to fetch rows from {schema}.{table} in source: {str(e)}")
            raise

class PostgresTargetHook(PostgresHook):
    """
    Postgres hook for target (write) operations in ETL pipelines.

    Args:
        conn_id (str): Airflow connection ID for the target PostgreSQL database.
    """
    def __init__(self, conn_id: str):
        super().__init__(conn_id)

    def get_pg_target_connection(self) -> Dict[str, str]:
        """
        Get the Postgres target connection details and test connectivity.

        Returns:
            Dict with status and message.

        Example:
            >>> hook = PostgresTargetHook(conn_id="postgres_reporting_service")
            >>> hook.get_pg_target_connection()
            {"status": "success", "message": "Connection successful to postgres_reporting_service"}
        """
        try:
            with self.get_pg_connection() as conn:
                summary = {
                    "event": "target_connection_test",
                    "conn_id": self.conn_id,
                    "status": "success",
                    "message": f"Connection successful to {self.conn_id}",
                    "timestamp": datetime.now().isoformat()
                }
                logger.info(f"Target connection summary: {json.dumps(summary)}")
                return summary
        except PostgresConnectionError as e:
            summary = {
                "event": "target_connection_test",
                "conn_id": self.conn_id,
                "status": "failure",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"Target connection summary: {json.dumps(summary)}")
            return summary

    def test_pg_target_connection(self) -> Dict[str, str]:
        """
        Test the Postgres target connection.

        Returns:
            Dict with status and message.

        Example:
            >>> hook = PostgresTargetHook(conn_id="postgres_reporting_service")
            >>> hook.test_pg_target_connection()
            {"status": "success", "message": "Connection successful to postgres_reporting_service"}
        """
        return self.get_pg_target_connection()

    def pg_target_table_exists(self, table: str, schema: str) -> bool:
        """
        Check if a table exists in the target database.

        Args:
            table (str): Name of the table to check.
            schema (str): Schema name.

        Returns:
            bool: True if table exists, False otherwise.

        Example:
            >>> hook = PostgresTargetHook(conn_id="postgres_reporting_service")
            >>> hook.pg_target_table_exists("premises", "fma")
            True
        """
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        )
        """
        try:
            with self.get_pg_cursor() as cursor:
                cursor.execute(query, (schema, table))
                exists = cursor.fetchone()['exists']
                logger.info(f"Table {schema}.{table} exists in target: {exists}")
                return exists
        except PostgresConnectionError as e:
            logger.error(f"Failed to check table {schema}.{table} in target: {str(e)}")
            raise

    def create_pg_target_table(self, table: str, schema_def: Dict[str, Any], schema: str) -> None:
        """
        Create a table in the target database based on schema definition.

        Args:
            table (str): Name of the table to create.
            schema_def (Dict): Schema definition from premises.yml (targets.postgres.columns).
            schema (str): Schema name.

        Example:
            >>> hook = PostgresTargetHook(conn_id="postgres_reporting_service")
            >>> schema_def = {"id": {"type": "uuid", "primary_key": true}, "createdAt": {"type": "timestamp"}}
            >>> hook.create_pg_target_table("premises", schema_def, "fma")
        """
        try:
            columns = []
            constraints = []
            for col_name, col_def in schema_def.items():
                col_type = col_def["type"]
                col_clause = f'"{col_name}" {col_type}'
                if not col_def.get("nullable", True):
                    col_clause += " NOT NULL"
                columns.append(col_clause)
                if col_def.get("primary_key"):
                    constraints.append(f'PRIMARY KEY ("{col_name}")')
            
            column_clauses = ", ".join(columns + constraints)
            query = f'CREATE TABLE IF NOT EXISTS {schema}.{table} ({column_clauses})'
            
            with self.get_pg_cursor() as cursor:
                cursor.execute(query)
                logger.info(f"Created table {schema}.{table} in target")
        except PostgresConnectionError as e:
            logger.error(f"Failed to create table {schema}.{table} in target: {str(e)}")
            raise

    def upsert_rows_to_pg_target_table(self, table: str, rows: List[Dict[str, Any]], schema_def: Dict[str, Any], schema: str, batch_size: int, upsert_conditions: List[str], incremental_column: str) -> Tuple[int, int]:
        """
        Upsert rows into the target table in batches using ON CONFLICT.
        Counts new (inserted) and updated records based on updated_at comparison.

        Args:
            table (str): Name of the target table.
            rows (List[Dict]): List of rows to upsert (each row is a dict).
            schema_def (Dict): Schema definition (targets.postgres.columns).
            schema (str): Schema name.
            batch_size (int): Number of rows per batch.
            upsert_conditions (List[str]): Columns for ON CONFLICT (e.g., ["id"]).
            incremental_column (str): Column for incremental sync (e.g., "updated_at").

        Returns:
            Tuple of (inserted_count, updated_count) for the batch.

        Example:
            >>> hook = PostgresTargetHook(conn_id="postgres_reporting_service")
            >>> rows = [{"id": "uuid1", "createdAt": "2025-06-15", "updatedAt": "2025-06-15"}, ...]
            >>> schema_def = {"id": {"type": "uuid", "primary_key": true}, "createdAt": {"type": "timestamp"}, "updatedAt": {"type": "timestamp"}}
            >>> inserted, updated = hook.upsert_rows_to_pg_target_table("premises", rows, schema_def, "fma", 5000, ["id"], "updatedAt")
            >>> print(f"Inserted: {inserted}, Updated: {updated}")
        """
        try:
            if not rows:
                logger.info(f"No rows to upsert into {schema}.{table} in target")
                return 0, 0
            
            columns = list(schema_def.keys())
            quoted_columns = [f'"{col}"' for col in columns]
            conflict_clause = ", ".join([f'"{col}"' for col in upsert_conditions])
            update_clause = ", ".join([f'"{col}" = EXCLUDED."{col}"' for col in columns if not schema_def[col].get("auto_generated")])
            query = f"""
            INSERT INTO {schema}.{table} ({", ".join(quoted_columns)})
            VALUES %s
            ON CONFLICT ({conflict_clause}) DO UPDATE
            SET {update_clause}
            WHERE {schema}.{table}."{incremental_column}" < EXCLUDED."{incremental_column}"
            RETURNING {schema}.{table}."{upsert_conditions[0]}", CASE WHEN xmax = 0 THEN 'inserted' ELSE 'updated' END AS action
            """
            
            inserted_count = 0
            updated_count = 0
            for i in range(0, len(rows), batch_size):
                batch_rows = rows[i:i + batch_size]
                values = [tuple(row.get(col) for col in columns) for row in batch_rows]
                
                with self.get_pg_cursor() as cursor:
                    execute_values(cursor, query, values, fetch=True)
                    results = cursor.fetchall()
                    for result in results:
                        if result['action'] == 'inserted':
                            inserted_count += 1
                        elif result['action'] == 'updated':
                            updated_count += 1
                    logger.debug(f"Upserted {len(batch_rows)} rows into {schema}.{table} in target: {inserted_count} inserted, {updated_count} updated")
            
            return inserted_count, updated_count
        except PostgresConnectionError as e:
            logger.error(f"Failed to upsert rows into {schema}.{table} in target: {str(e)}")
            raise

    def add_column_to_pg_target_table(self, table: str, column_name: str, column_type: str, schema: str, nullable: bool = True) -> None:
        """
        Add a column to the target table.

        Args:
            table (str): Name of the target table.
            column_name (str): Name of the column to add.
            column_type (str): SQL type of the column (e.g., "timestamp").
            schema (str): Schema name.
            nullable (bool): Whether the column is nullable (default: True).

        Example:
            >>> hook = PostgresTargetHook(conn_id="postgres_reporting_service")
            >>> hook.add_column_to_pg_target_table("premises", "new_col", "varchar(255)", "fma")
        """
        try:
            nullable_clause = "" if nullable else "NOT NULL"
            query = f'ALTER TABLE {schema}.{table} ADD COLUMN IF NOT EXISTS "{column_name}" {column_type} {nullable_clause}'
            
            with self.get_pg_cursor() as cursor:
                cursor.execute(query)
                logger.info(f"Added column {column_name} to {schema}.{table} in target")
        except PostgresConnectionError as e:
            logger.error(f"Failed to add column {column_name} to {schema}.{table} in target: {str(e)}")
            raise