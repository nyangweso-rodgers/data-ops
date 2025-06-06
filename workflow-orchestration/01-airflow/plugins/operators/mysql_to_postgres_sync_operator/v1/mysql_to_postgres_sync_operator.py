from airflow.models.baseoperator import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.models import Variable
from plugins.hooks.mysql.v1.mysql_hook import MySqlHook
from plugins.hooks.postgres.v2.postgres_hook import PostgresHook
from plugins.utils.schema_loader.v3.schema_loader import SchemaLoader
from plugins.utils.add_sync_time.v1.add_sync_time import add_sync_time
from plugins.utils.constants.v1.constants import SYNC_CONFIGS
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class MySQLToPostgresSyncOperator(BaseOperator):
    @apply_defaults
    def __init__(self, sync_key, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sync_key = sync_key
        self.sync_config = SYNC_CONFIGS[sync_key]
        self.source_config = self.sync_config['source']
        self.target_config = self.sync_config['target']

    def execute(self, context):
        logger.info(f"Starting sync process for {self.sync_key}")
        
        # Validate schema
        schema = self._validate_schema()
        config = {
            "table": self.source_config['table'],
            "source": schema.get("source", {}),
            "target": {
                **schema.get("target", {}),
                "database": self.target_config['database'],
                "schema": self.target_config['schema'],
                "table": self.target_config['table'],
                "database_type": self.target_config['target_type'],
            },
            "mappings": schema.get("mappings", [])
        }
        logger.debug(f"Config structure: {config}")

        # Test connections
        self._test_mysql_connection()
        self._test_postgres_connection()

        # Validate MySQL table
        mysql_table_info = self._validate_mysql_table(config)

        # Prepare PostgreSQL table schema
        table_info = self._prepare_postgres_table_schema(config)

        # Fetch and sync data
        self._fetch_and_sync_to_postgres(config, mysql_table_info, table_info)

    def _validate_schema(self):
        logger.info("Validating schema compatibility")
        try:
            schema = SchemaLoader.load_schema(
                source_type=self.source_config['source_type'],
                source_subpath=self.source_config['source_subpath'],
                table_name=self.source_config['table'],
                target_type=self.target_config['target_type']
            )
            logger.info(f"Schema validation successful for {self.source_config['table']}")
            return schema
        except Exception as e:
            logger.error(f"Schema validation failed: {str(e)}")
            raise

    def _test_mysql_connection(self):
        logger.info("Testing MySQL connection")
        hook = MySqlHook(
            conn_id=self.source_config['connection_id'],
            connect_timeout=10
        )
        success, message = hook.test_connection()
        if not success:
            raise ValueError(f"MySQL connection failed: {message}")
        logger.info("MySQL connection successful")

    def _test_postgres_connection(self):
        logger.info("Testing PostgreSQL connection")
        hook = PostgresHook(
            conn_id=self.target_config['connection_id'],
        )
        success, message = hook.test_connection()
        if not success:
            raise ValueError(f"PostgreSQL connection failed: {message}")
        logger.info("PostgreSQL connection successful")

    def _validate_mysql_table(self, config):
        logger.info("Validating MySQL source table")
        hook = MySqlHook(
            conn_id=self.source_config['connection_id'],
            connect_timeout=10
        )
        table_name = config["table"]
        
        if not hook.table_exists(table_name, self.source_config['database']):
            logger.error(f"Table {table_name} does not exist in database {self.source_config['database']}")
            raise ValueError(f"Table {table_name} does not exist")
        
        target_to_source = {}
        source_columns = config["source"].get("columns", {})
        for source_col, props in source_columns.items():
            if props.get("active", True):
                target_col = props.get("target", source_col)
                target_to_source[target_col] = source_col
        
        expected_columns = set(target_to_source.values())
        logger.debug(f"Expected source columns: {expected_columns}")
        
        try:
            existing_columns = hook.get_table_columns(table_name, self.source_config['database'])
            existing_column_names = {c["column_name"].lower() for c in existing_columns}
            logger.debug(f"Existing MySQL columns: {existing_column_names}")
            
            missing_columns = {c for c in expected_columns if c.lower() not in existing_column_names}
            if missing_columns:
                logger.warning(f"Missing columns in {table_name}: {missing_columns}. These will be treated as NULL.")
        except Exception as e:
            logger.error(f"Failed to validate MySQL table: {str(e)}")
            raise
        
        logger.info(f"MySQL table {table_name} validated")
        return {
            "table_name": table_name,
            "available_columns": existing_column_names,
            "target_to_source": target_to_source
        }

    def _prepare_postgres_table_schema(self, config):
        logger.info("Preparing PostgreSQL target table schema")
        hook = PostgresHook(
            conn_id=self.target_config['connection_id']
        )
        
        target_config = config["target"]
        table_name = config["table"]
        schema_name = self.target_config['schema']
        
        logger.debug(f"Using schema: {schema_name}, table: {table_name}")
        
        columns = []
        primary_key_column = None
        for col, props in target_config["columns"].items():
            col_def = f'"{col}" {props["type"]}'
            if not props.get("nullable", True):
                col_def += " NOT NULL"
            if props.get("primary_key", False):
                if primary_key_column is not None:
                    logger.error(f"Multiple primary key columns detected: {primary_key_column} and {col}")
                    raise ValueError("Only one primary key column is allowed")
                primary_key_column = col
                col_def += " PRIMARY KEY"
            columns.append(col_def)
        
        if not primary_key_column:
            logger.warning("No primary key column defined in the target schema")
        
        try:
            created = hook.create_table_if_not_exists(
                table_name=table_name,
                columns=columns,
                schema=schema_name
            )
            logger.info(f"Table {schema_name}.{table_name} {'created' if created else 'verified'}")
        except Exception as e:
            logger.error(f"Failed to create table {schema_name}.{table_name}: {str(e)}")
            raise
        
        try:
            existing_columns = hook.get_table_columns(schema=schema_name, table_name=table_name)
            existing_column_names = {col["column_name"].lower() for col in existing_columns}
            expected_columns = {col.lower(): props for col, props in target_config["columns"].items()}
            
            missing_columns = set(expected_columns.keys()) - existing_column_names
            if missing_columns:
                logger.info(f"Found missing columns in {schema_name}.{table_name}: {missing_columns}")
                for missing_col in missing_columns:
                    props = expected_columns[missing_col]
                    hook.add_column(
                        schema=schema_name,
                        table_name=table_name,
                        column_name=missing_col,
                        column_type=props["type"],
                        is_nullable=not props.get("nullable", True),
                        is_primary_key=props.get("primary_key", False)
                    )
                    logger.info(f"Added column {missing_col} to {schema_name}.{table_name}")
        except Exception as e:
            logger.error(f"Failed to update table schema {schema_name}.{table_name}: {str(e)}")
            raise

        return {"table_name": table_name, "schema_name": schema_name}

    def _fetch_and_sync_to_postgres(self, config, mysql_table_info, table_info):
        logger.info("Fetching and syncing data from MySQL to PostgreSQL")
        mysql_hook = MySqlHook(
            conn_id=self.source_config['connection_id'],
            connect_timeout=10
        )
        postgres_hook = PostgresHook(
            conn_id=self.target_config['connection_id']
        )
        
        # Build source to target column mapping
        source_to_target = {}
        source_columns = []
        
        for source_col, props in config["source"]["columns"].items():
            if props.get("active", True):
                target_col = props.get("target", source_col)
                source_to_target[source_col] = target_col
                source_columns.append(source_col)
        
        # Filter source columns to those available in MySQL
        available_source_columns = {c.lower() for c in mysql_table_info["available_columns"]}
        valid_source_columns = [col for col in source_columns if col.lower() in available_source_columns]
        
        if not valid_source_columns:
            logger.error(f"No valid source columns found for {config['table']}")
            raise ValueError("No valid source columns found")
        
        logger.debug(f"Valid source columns for query: {valid_source_columns}")
        
        # Build the SELECT query with source column names
        columns_str = ", ".join([f"`{col}`" for col in valid_source_columns])
        
        # Use incremental_column from SYNC_CONFIGS (this should be the source column name)
        incremental_col = self.source_config.get('incremental_column', 'updatedAt')
        
        # Get the target name for the incremental column for variable tracking
        target_incremental_col = source_to_target.get(incremental_col, incremental_col.lower())
        
        last_updated_at_str = Variable.get(f"{self.sync_key}_last_updated_at_postgres", default_var="1970-01-01 00:00:00")
        try:
            last_updated_at = datetime.strptime(last_updated_at_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            logger.warning(f"Invalid last_updated_at format: {last_updated_at_str}. Using default.")
            last_updated_at = datetime(1970, 1, 1)
        
        logger.info(f"Fetching records with {incremental_col} > {last_updated_at}")
        query = f"SELECT {columns_str} FROM {config['table']} WHERE {incremental_col} > %s ORDER BY {incremental_col}"
        logger.debug(f"Executing query: {query} with params: {last_updated_at}")
        params = (last_updated_at,)
        
        batch_size = self.source_config.get('batch_size', 500)
        logger.info(f"Using batch size: {batch_size}")
        
        total_rows = 0
        max_updated_at = last_updated_at
        
        for batch in mysql_hook.execute_query(query, params, fetch_batch=True, batch_size=batch_size):
            if not batch:
                break
            
            mapped_batch = []
            for row in batch:
                logger.debug(f"Raw row from MySQL: {dict(row)}")
                mapped_row = {}
                
                # Map each source column to its target column name
                for source_col in valid_source_columns:
                    if source_col in row:
                        target_col = source_to_target[source_col]
                        value = row[source_col]
                        mapped_row[target_col] = value
                        
                        if value is None:
                            logger.debug(f"Source column {source_col} -> target {target_col} is None")
                    else:
                        logger.warning(f"Source column {source_col} not found in MySQL row")
                        target_col = source_to_target[source_col]
                        mapped_row[target_col] = None
                
                # Type conversion for integers based on target schema
                for target_col, props in config["target"]["columns"].items():
                    if target_col in mapped_row and mapped_row[target_col] is not None:
                        if props.get("type") == "integer" or props.get("type") == "int":
                            try:
                                mapped_row[target_col] = int(mapped_row[target_col])
                            except (ValueError, TypeError):
                                logger.warning(f"Could not convert {target_col} value {mapped_row[target_col]} to integer")
                                mapped_row[target_col] = None
                        elif props.get("type") == "smallint":
                            try:
                                mapped_row[target_col] = int(mapped_row[target_col])
                            except (ValueError, TypeError):
                                logger.warning(f"Could not convert {target_col} value {mapped_row[target_col]} to smallint")
                                mapped_row[target_col] = None
                
                mapped_batch.append(mapped_row)
            
            logger.debug(f"Mapped batch sample: {mapped_batch[0] if mapped_batch else 'No rows'}")
            
            # Add sync_time to each row
            add_sync_time(mapped_batch, config["target"])
            
            try:
                upsert_conditions = self.target_config.get("upsert_conditions", ["id"])
                rows_affected = postgres_hook.upsert_rows(
                    table_name=table_info['table_name'],
                    rows=mapped_batch,
                    schema=table_info['schema_name'],
                    upsert_conditions=upsert_conditions,
                    update_condition=None
                )
                total_rows += rows_affected
                logger.info(f"Upserted {rows_affected} rows into {table_info['schema_name']}.{table_info['table_name']} (Total: {total_rows})")
                
                # Update the max timestamp using the target column name
                updated_at_values = [row[target_incremental_col] for row in mapped_batch if row.get(target_incremental_col) is not None]
                if updated_at_values:
                    batch_max_updated_at = max(updated_at_values)
                    max_updated_at = max(max_updated_at, batch_max_updated_at)
                else:
                    logger.warning(f"No valid {target_incremental_col} values in batch, skipping max update")
            except Exception as e:
                logger.error(f"Failed to upsert batch: {str(e)}")
                raise
            
        if total_rows > 0:
            max_updated_at_str = max_updated_at.strftime("%Y-%m-%d %H:%M:%S")
            Variable.set(f"{self.sync_key}_last_updated_at_postgres", max_updated_at_str)
            logger.info(f"Updated {self.sync_key}_last_updated_at_postgres to {max_updated_at_str}")
        
        logger.info(f"Completed sync of {total_rows} rows to {table_info['schema_name']}.{table_info['table_name']}")