import json
import re
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class SchemaLoader:
    SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"
    API_SOURCE_TYPES = {"jira", "ccs", "github", "slack"}  # Extendable list of API sources
    
    @classmethod
    def load_source_schema(cls, source_type: str, source_subpath: str, table_name: str) -> Dict[str, Any]:
        """
        Load source table schema definition.
        
        :param source_type: Source type (e.g., 'jira', 'postgres', 'mysql')
        :param source_subpath: Subpath for source ('' for APIs, 'db_name' for databases)
        :param table_name: Source schema name (e.g., 'issues' for jira, 'table_name' for databases)
        :return: Source schema configuration
        """
        if source_type in cls.API_SOURCE_TYPES:
            schema_path = cls.SCHEMAS_DIR / "sources" / "apis" / source_type / f"{table_name}.json"
        else:
            schema_path = cls.SCHEMAS_DIR / "sources" / source_type / (source_subpath or "") / f"{table_name}.json"
        
        if not schema_path.exists():
            logger.error(f"Source schema file not found: {schema_path}")
            raise FileNotFoundError(f"Source schema file not found: {schema_path}")
        
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        if "table" not in schema or "columns" not in schema:
            logger.error(f"Invalid source schema: 'table' and 'columns' are required in {schema_path}")
            raise ValueError(f"Invalid source schema in {schema_path}")
        
        return schema
    
    @classmethod
    def load_target_schema(cls, target_type: str, table_name: str, target_subpath: str = "") -> Dict[str, Any]:
        """
        Load target table schema definition.
        
        :param target_type: Target database type (e.g., 'postgres')
        :param table_name: Target table name (e.g., 'jira_issues')
        :param target_subpath: Subpath for target (e.g., 'reporting_service')
        :return: Target schema configuration
        """
        schema_path = cls.SCHEMAS_DIR / "targets" / target_type / (target_subpath or "") / f"{table_name}.json"
        
        if not schema_path.exists():
            logger.error(f"Target schema file not found: {schema_path}")
            raise FileNotFoundError(f"Target schema file not found: {schema_path}")
        
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        if "table" not in schema or "column_mappings" not in schema:
            logger.error(f"Invalid target schema: 'table' and 'column_mappings' are required in {schema_path}")
            raise ValueError(f"Invalid target schema in {schema_path}")
        
        return schema
    
    @classmethod
    def get_combined_schema(cls, source_type: str, source_subpath: str, target_type: str, table_name: str, source_table_name: str = None, target_subpath: str = "") -> Dict[str, Any]:
        """
        Combine source and target schemas with validation.
        
        :param source_type: Source type (e.g., 'jira', 'postgres', 'mysql')
        :param source_subpath: Subpath for source ('' for APIs, 'db_name' for databases)
        :param target_type: Target database type (e.g., 'postgres')
        :param table_name: Target table name (e.g., 'jira_issues')
        :param source_table_name: Source schema name if different from target (e.g., 'issues' for jira)
        :param target_subpath: Subpath for target (e.g., 'reporting_service')
        :return: Combined schema with source, target, and mappings
        """
        source = cls.load_source_schema(source_type, source_subpath, source_table_name or table_name)
        target = cls.load_target_schema(target_type, table_name, target_subpath)
        
        cls._validate_schemas(source, target, table_name)
        
        return {
            "source": source,
            "target": target,
            "mappings": cls._build_column_mappings(source, target)
        }
    
    @classmethod
    def _build_column_mappings(cls, source: Dict[str, Any], target: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build column mappings with support for:
        - Field name transformations (createdAt → created_at)
        - Generated columns (like sync_time)
        - Backward compatibility with existing DB-to-DB pipelines
        - Explicit source-to-target field mapping
        
        :param source: Source schema
        :param target: Target schema
        :return: List of mappings with source and target details
        """
        mappings = []
        source_columns = source.get("columns", {})
        target_mappings = target.get("column_mappings", {})
        
        for target_col, target_config in target_mappings.items():
            # Initialize mapping with target info
            mapping = {
                "target": target_col,
                "target_type": target_config["type"],
                "target_nullable": "Nullable(" in target_config["type"],
                "generated": target_config.get("generated", False)
            }
            
            if mapping["generated"]:
                mapping.update({
                    "source": None,
                    "source_path": None,
                    "source_type": None,
                    "source_nullable": True,
                    "source_primary_key": False,
                    "source_incremental": False
                })
                mappings.append(mapping)
                continue
            
            # Find source column
            source_col = None
            source_info = None
            
            # Option 1: Explicit target reference in source column
            for src_col, src_info in source_columns.items():
                if src_info.get("target") == target_col:
                    source_col = src_col
                    source_info = src_info
                    break
            
            # Option 2: Direct name match (backward compatible)
            if source_col is None and target_col in source_columns:
                source_col = target_col
                source_info = source_columns[target_col]
            
            # Option 3: CamelCase to snake_case conversion
            if source_col is None:
                potential_source = re.sub(r'(?<!^)(?=[A-Z])', '_', target_col).lower()
                if potential_source in source_columns:
                    source_col = potential_source
                    source_info = source_columns[potential_source]
            
            if source_col is None:
                logger.error(f"No matching source column found for target column '{target_col}'")
                raise ValueError(f"Missing source mapping for target column '{target_col}'")
            
            # Build the complete mapping
            mapping.update({
                "source": source_col,
                "source_path": source_info.get("source", source_col),  # For API sources
                "source_type": source_info["type"],
                "source_nullable": source_info.get("nullable", True),
                "source_primary_key": source_info.get("primary_key", False),
                "source_incremental": source_info.get("incremental", False)
            })
            mappings.append(mapping)
        
        return mappings
    
    @classmethod
    def _validate_schemas(cls, source: Dict[str, Any], target: Dict[str, Any], table_name: str) -> None:
        """
        Validate compatibility between source and target schemas.
        
        :param source: Source schema
        :param target: Target schema
        :param table_name: Target table name
        :raises ValueError: If schemas are incompatible
        """
        source_columns = source.get("columns", {})
        target_mappings = target.get("column_mappings", {})
        
        for target_col, target_config in target_mappings.items():
            if target_config.get("generated", False):
                continue
            
            # Find source column
            source_col = None
            for src_col, src_info in source_columns.items():
                if src_info.get("target") == target_col:
                    source_col = src_col
                    break
            if source_col is None and target_col in source_columns:
                source_col = target_col
            if source_col is None:
                potential_source = re.sub(r'(?<!^)(?=[A-Z])', '_', target_col).lower()
                if potential_source in source_columns:
                    source_col = potential_source
            
            if source_col is None:
                logger.error(f"No matching source column found for target column '{target_col}' in table '{table_name}'")
                raise ValueError(f"No matching source column found for target column '{target_col}'")
        
        incremental_col = source.get("incremental_column")
        if incremental_col and incremental_col not in source_columns:
            logger.error(f"Incremental column '{incremental_col}' not found in source schema for table '{table_name}'")
            raise ValueError(f"Incremental column '{incremental_col}' not found")
        
        for col, info in source_columns.items():
            if info.get("primary_key") and not any(target_config.get("target") == col for target_config in target_mappings.values()):
                logger.warning(f"Primary key column '{col}' not included in target mappings for table '{table_name}'")
        
        logger.info(f"Schema validation passed for {source['table']} -> {target['table']}")