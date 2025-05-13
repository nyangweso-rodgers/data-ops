import json
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class SchemaLoader:
    SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"
    
    @classmethod
    def load_source_schema(cls, source_type: str, source_subpath: str, table_name: str) -> Dict[str, Any]:
        """
        Load source table schema definition.
        
        :param source_type: Source database type (e.g., 'mysql')
        :param source_subpath: Subpath for source (e.g., 'amt' for mysql/amt)
        :param table_name: Table name (e.g., 'customers')
        :return: Source schema configuration
        """
        schema_path = cls.SCHEMAS_DIR / "sources" / source_type / source_subpath / f"{table_name}.json"
        if not schema_path.exists():
            logger.error(f"Source schema file not found: {schema_path}")
            raise FileNotFoundError(f"Source schema file not found: {schema_path}")
        
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Validate source schema
        if "table" not in schema or "columns" not in schema:
            logger.error(f"Invalid source schema: 'table' and 'columns' are required in {schema_path}")
            raise ValueError(f"Invalid source schema in {schema_path}")
        
        return schema
    
    @classmethod
    def load_target_schema(cls, target_type: str, table_name: str) -> Dict[str, Any]:
        """
        Load target table schema definition.
        
        :param target_type: Target database type (e.g., 'clickhouse', 'postgres')
        :param table_name: Table name (e.g., 'customers')
        :return: Target schema configuration
        """
        schema_path = cls.SCHEMAS_DIR / "targets" / target_type / f"{table_name}.json"
        if not schema_path.exists():
            logger.error(f"Target schema file not found: {schema_path}")
            raise FileNotFoundError(f"Target schema file not found: {schema_path}")
        
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Validate target schema
        if "table" not in schema or "column_mappings" not in schema:
            logger.error(f"Invalid target schema: 'table' and 'column_mappings' are required in {schema_path}")
            raise ValueError(f"Invalid target schema in {schema_path}")
        
        return schema
    
    @classmethod
    def get_combined_schema(cls, source_type: str, source_subpath: str, target_type: str, table_name: str) -> Dict[str, Any]:
        """
        Combine source and target schemas with validation.
        
        :param source_type: Source database type (e.g., 'mysql')
        :param source_subpath: Subpath for source (e.g., 'amt')
        :param target_type: Target database type (e.g., 'clickhouse', 'postgres')
        :param table_name: Table name (e.g., 'customers')
        :return: Combined schema with source, target, and mappings
        """
        source = cls.load_source_schema(source_type, source_subpath, table_name)
        target = cls.load_target_schema(target_type, table_name)
        
        # Validate source-target compatibility
        cls._validate_schemas(source, target, table_name)
        
        return {
            "source": source,
            "target": target,
            "mappings": cls._build_column_mappings(source, target)
        }
    
    @classmethod
    def _build_column_mappings(cls, source: Dict[str, Any], target: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build complete column mappings with type and nullability information.
        
        :param source: Source schema
        :param target: Target schema
        :return: List of mappings with source and target details
        """
        mappings = []
        source_columns = source.get("columns", {})
        target_mappings = target.get("column_mappings", {})
        
        for source_col, target_config in target_mappings.items():
            if source_col not in source_columns:
                logger.error(f"Source column '{source_col}' not found in source schema for table '{source['table']}'")
                raise ValueError(f"Source column '{source_col}' not found in source schema")
            
            source_info = source_columns[source_col]
            mappings.append({
                "source": source_col,
                "source_type": source_info["type"],
                "source_nullable": source_info.get("nullable", True),  # Assume nullable if not specified
                "source_primary_key": source_info.get("primary_key", False),
                "source_incremental": source_info.get("incremental", False),
                "target": target_config["target"],
                "target_type": target_config["type"],
                #"target_nullable": not target_config["type"].startswith("Nullable(") if "Nullable(" in target_config["type"] else True
                "target_nullable": "Nullable(" in target_config["type"]
            })
        
        return mappings
    
    @classmethod
    def _validate_schemas(cls, source: Dict[str, Any], target: Dict[str, Any], table_name: str) -> None:
        """
        Validate compatibility between source and target schemas.
        
        :param source: Source schema
        :param target: Target schema
        :param table_name: Table name
        :raises ValueError: If schemas are incompatible
        """
        source_columns = source.get("columns", {})
        target_mappings = target.get("column_mappings", {})
        
        # Check that all target columns have a corresponding source column
        for source_col in target_mappings:
            if source_col not in source_columns:
                logger.error(f"Target column mapping for '{source_col}' not found in source schema for table '{table_name}'")
                raise ValueError(f"Target column mapping for '{source_col}' not found in source schema")
        
        # Validate incremental column
        incremental_col = source.get("incremental_column")
        if incremental_col and incremental_col not in source_columns:
            logger.error(f"Incremental column '{incremental_col}' not found in source schema for table '{table_name}'")
            raise ValueError(f"Incremental column '{incremental_col}' not found")
        
        # Validate primary key (if specified)
        for col, info in source_columns.items():
            if info.get("primary_key") and col not in target_mappings:
                logger.warning(f"Primary key column '{col}' not included in target mappings for table '{table_name}'")
        
        logger.info(f"Schema validation passed for {source['table']} -> {target['table']}")