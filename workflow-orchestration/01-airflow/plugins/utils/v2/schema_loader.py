import json
import yaml
from pathlib import Path
from typing import Dict, Any
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

class SchemaLoader:
    SCHEMAS_DIR = Path(__file__).parent.parent.parent / "schemas"

    @classmethod
    #@lru_cache(maxsize=32)
    def load_schema(cls, source_type: str, source_subpath: str, table_name: str, target_type: str) -> Dict[str, Any]:
        """
        Load unified schema for a table, supporting both JSON and YAML.
        Uses table_name parameter instead of requiring 'table' in schema file.

        :param source_type: Source type (e.g., 'mysql', 'kafka', 'apis')
        :param source_subpath: Context identifier (e.g., 'amt', 'kafka_cluster', 'jira', 'weathermap')
        :param table_name: Table or entity name (e.g., 'customers', 'topic_name', 'issues', 'weather')
        :param target_type: Target database type (e.g., 'clickhouse', 'postgres')
        :return: Schema with table, source, target, and mappings
        """
        # Uniform path: schemas/source_type/source_subpath/table_name.yml
        schema_path = cls.SCHEMAS_DIR / source_type / (source_subpath or "") / f"{table_name}.yml"
        
        # Try alternate extensions
        if not schema_path.exists():
            schema_path = schema_path.with_suffix('.yaml')
        if not schema_path.exists():
            schema_path = schema_path.with_suffix('.json')
        
        if not schema_path.exists():
            logger.error(f"Schema file not found: {schema_path}")
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        logger.debug(f"Loading schema from {schema_path}")
        with open(schema_path, 'r') as f:
            if schema_path.suffix in ('.yml', '.yaml'):
                schema = yaml.safe_load(f)
            else:
                schema = json.load(f)
        
        if not schema or 'source' not in schema or 'targets' not in schema:
            logger.error(f"Invalid schema: 'source' and 'targets' are required in {schema_path}")
            raise ValueError(f"Invalid schema in {schema_path}")
        
        if 'columns' not in schema['source']:
            logger.error(f"Invalid schema: 'source.columns' is required in {schema_path}")
            raise ValueError(f"Invalid schema in {schema_path}")
        
        if target_type not in schema['targets'] or 'columns' not in schema['targets'][target_type]:
            logger.error(f"Invalid schema: 'targets.{target_type}.columns' is required in {schema_path}")
            raise ValueError(f"Invalid schema in {schema_path}")
        
        # Use table_name parameter, fallback to schema['table'] if present
        schema_table = schema.get('table', table_name)
        cls._validate_schema(schema, schema_table, target_type)
        
        return {
            "table": schema_table,
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
                    "source_incremental": False
                })
            else:
                # Find source column
                source_col = None
                source_info = None
                for src_col, src_info in source_columns.items():
                    if src_info.get('target') == target_col:
                        source_col = src_col
                        source_info = src_info
                        break
                    if src_col == target_col:
                        source_col = src_col
                        source_info = src_info
                
                if source_col is None:
                    logger.error(f"No matching source column found for target column '{target_col}'")
                    raise ValueError(f"No matching source column for target column '{target_col}'")
                
                mapping.update({
                    "source": source_col,
                    "source_type": source_info['type'],
                    "source_nullable": source_info.get('nullable', True),
                    "source_primary_key": source_info.get('primary_key', False),
                    "source_incremental": source_info.get('incremental', False),
                    "source_active": source_info.get('active', True)
                })
            
            mappings.append(mapping)
        
        return mappings

    @classmethod
    def _validate_schema(cls, schema: Dict[str, Any], table_name: str, target_type: str) -> None:
        """
        Validate schema compatibility, including:
        - Target columns must map to source columns (even if inactive), unless auto-generated
        - Warn about inactive source columns mapped to targets
        - Ensure only one active incremental column exists
        - Log unused active source columns (debugging aid)

        :raises ValueError: If schema is invalid
        """
        source_columns = schema['source']['columns']
        target_columns = schema['targets'][target_type]['columns']

        # --- 1. Validate target columns ---
        for target_col, target_info in target_columns.items():
            if target_info.get('auto_generated', False):
                continue  # Skip source mapping validation for auto-generated columns

            # Find matching source column (by name or 'target' mapping)
            source_col = None
            for src_col, src_info in source_columns.items():
                if src_info.get('target') == target_col or src_col == target_col:
                    source_col = src_col
                    break

            # Rule 1: Target columns must map to a source column
            if source_col is None:
                error_msg = f"Target column '{target_col}' has no matching source column in table '{table_name}'"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Rule 2: Warn if target column maps to an inactive source column
            if not source_columns[source_col].get('active', True):  # Default active=True
                logger.warning(
                    f"Target column '{target_col}' maps to inactive source column '{source_col}'. "
                    "This will result in NULL values in the target."
                )

        # --- 2. Validate incremental columns ---
        active_incremental_cols = [
            col for col, config in source_columns.items() 
            if config.get('incremental') and config.get('active', True)
        ]
        if len(active_incremental_cols) > 1:
            error_msg = f"Multiple active incremental columns found: {active_incremental_cols}. Only one allowed."
            logger.error(error_msg)
            raise ValueError(error_msg)

        # --- 3. Log unused active columns (optional but helpful) ---
        unused_active_cols = [
            col for col, config in source_columns.items()
            if config.get('active', True) and
            col not in target_columns and
            config.get('target') not in target_columns
        ]
        if unused_active_cols:
            logger.info(
                f"Active source columns not synced to target in '{table_name}': {unused_active_cols}. "
                "They will be ignored during sync."
            )

        logger.info(f"Schema validation passed for {table_name} -> {target_type}")