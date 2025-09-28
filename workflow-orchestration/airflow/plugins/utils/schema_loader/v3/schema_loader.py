import yaml
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class SchemaLoader:
    SCHEMAS_DIR = Path("/opt/airflow/plugins/schemas")

    @classmethod
    def load_schema(cls, source_type: str, source_subpath: str, table_name: str, target_type: str) -> Dict[str, Any]:
        """
        Load unified schema from a YAML file for a table.
        Table name is taken from table_name parameter.

        :param source_type: Source type (e.g., 'mysql', 'kafka', 'apis')
        :param source_subpath: Context identifier (e.g., 'amt', 'kafka_cluster', 'jira', 'weathermap')
        :param table_name: Table or entity name (e.g., 'customers', 'sprints', 'issues', 'weather')
        :param target_type: Target database type (e.g., 'clickhouse', 'postgres')
        :return: Schema with table, source, target, and mappings
        """
        # Path: schemas/source_type/source_subpath/table_name.yml
        schema_path = cls.SCHEMAS_DIR / source_type / (source_subpath or "") / f"{table_name}.yml"
        
        logger.debug(f"Attempting to load schema file: {schema_path}")
        if not schema_path.exists():
            logger.error(f"Schema file not found: {schema_path}")
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        logger.info(f"Loading schema from {schema_path}")
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        if not schema or 'source' not in schema or 'targets' not in schema:
            logger.error(f"Invalid schema: 'source' and 'targets' are required in {schema_path}")
            raise ValueError(f"Invalid schema in {schema_path}")
        
        if 'columns' not in schema['source']:
            logger.error(f"Invalid schema: 'source.columns' is required in {schema_path}")
            raise ValueError(f"Invalid schema in {schema_path}")
        
        if target_type not in schema['targets'] or 'columns' not in schema['targets'][target_type]:
            logger.error(f"Invalid schema: 'targets.{target_type}.columns' is required in {schema_path}")
            raise ValueError(f"Invalid schema in {schema_path}")
        
        cls._validate_schema(schema, table_name, target_type)
        
        return {
            "table": table_name,
            "source": schema['source'],
            "target": schema['targets'][target_type],
            "mappings": cls._build_mappings(schema['source']['columns'], schema['targets'][target_type]['columns'])
        }

    @classmethod
    def _build_mappings(cls, source_columns: Dict[str, Any], target_columns: Dict[str, Any]) -> list[Dict[str, Any]]:
        """
        Build column mappings from source to target, supporting auto-generated columns.

        :param source_columns: Source column definitions
        :param target_columns: Target column definitions
        :return: List of mappings with source and target details
        """
        mappings = []
        
        for target_col, target_info in target_columns.items():
            mapping = {
                "target": target_col,
                "target_type": target_info['type'],
                "target_nullable": target_info.get('nullable', True),
                "auto_generated": target_info.get('auto_generated', False)
            }
            
            if mapping["auto_generated"]:
                # Auto-generated columns have no source
                mapping.update({
                    "source": None,
                    "source_type": None,
                    "source_nullable": None,
                    "source_primary_key": False,
                    "source_active": False
                })
            else:
                # Find source column by 'target' field
                source_col = None
                source_info = None
                for src_col, src_info in source_columns.items():
                    if src_info.get('target') == target_col:
                        source_col = src_col
                        source_info = src_info
                        break
                
                if source_col is None:
                    logger.error(f"No source column with target '{target_col}' found")
                    raise ValueError(f"No source column with target '{target_col}' found")
                
                mapping.update({
                    "source": source_info.get('source_path', source_col),
                    "source_type": source_info['type'],
                    "source_nullable": source_info.get('nullable', True),
                    "source_primary_key": source_info.get('primary_key', False),
                    "source_active": source_info.get('active', True)
                })
            
            mappings.append(mapping)
        
        return mappings

    @classmethod
    def _validate_schema(cls, schema: Dict[str, Any], table_name: str, target_type: str) -> None:
        """
        Validate schema compatibility, including:
        - Each source column must have a 'target' field
        - Target columns must map to source columns (even if inactive), unless auto-generated
        - Warn about inactive source columns mapped to targets
        - Log unused active source columns (debugging aid)

        :raises ValueError: If schema is invalid
        """
        source_columns = schema['source']['columns']
        target_columns = schema['targets'][target_type]['columns']

        # --- 1. Validate each source column has a 'target' ---
        for src_col, src_info in source_columns.items():
            if 'target' not in src_info or not src_info['target']:
                error_msg = f"Missing or empty 'target' for source column '{src_col}' in table '{table_name}'"
                logger.error(error_msg)
                raise ValueError(error_msg)

        # --- 2. Validate target columns ---
        for target_col, target_info in target_columns.items():
            if target_info.get('auto_generated', False):
                continue  # Skip source mapping validation for auto-generated columns

            # Find matching source column by 'target' field
            source_col = None
            for src_col, src_info in source_columns.items():
                if src_info.get('target') == target_col:
                    source_col = src_col
                    break

            if source_col is None:
                error_msg = f"Target column '{target_col}' has no matching source column in table '{table_name}'"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Warn if target column maps to an inactive source column
            if not source_columns[source_col].get('active', True):
                logger.warning(
                    f"Target column '{target_col}' maps to inactive source column '{source_col}'."
                    "This will result in NULL values in the target."
                )

        # --- 3. Log unused active columns ---
        unused_active_cols = [
            col for col, config in source_columns.items()
            if config.get('active', True)
            and config.get('target') not in target_columns
        ]
        if unused_active_cols:
            logger.info(
                f"Active source columns not synced to target in '{table_name}': {unused_active_cols}. "
                "They will be ignored during sync."
            )

        logger.info(f"Schema validation passed for {table_name} -> {target_type}")