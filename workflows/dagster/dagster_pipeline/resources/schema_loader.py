# resources/schema_loader.py
from dagster import ConfigurableResource
from typing import Dict, Any, List, Optional
import yaml
import os
from pathlib import Path

class SchemaLoader(ConfigurableResource):
    """Loads and manages table schema configurations from YAML files"""
    
    config_base_path: str = "dagster_pipeline/config"
    
    def _get_schema_path(self, source_type: str, database: str, table_name: str) -> Path:
        """Get the full path to a schema file"""
        return Path(self.config_base_path) / "schemas" / source_type / database / f"{table_name}.yaml"
    
    def load_table_schema(self, source_type: str, database: str, table_name: str) -> Dict[str, Any]:
        """Load schema configuration for a specific table"""
        schema_path = self._get_schema_path(source_type, database, table_name)
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        # Validate required fields
        self._validate_schema(schema, source_type, database, table_name)
        
        return schema
    
    def _validate_schema(self, schema: Dict[str, Any], source_type: str, database: str, table_name: str):
        """Validate that the schema has all required fields"""
        required_fields = ['table_name', 'source', 'target', 'columns']
        
        for field in required_fields:
            if field not in schema:
                raise ValueError(f"Missing required field '{field}' in schema for {source_type}.{database}.{table_name}")
        
        # Validate source section
        if 'database' not in schema['source'] or 'table' not in schema['source']:
            raise ValueError(f"Source must contain 'database' and 'table' in schema for {source_type}.{database}.{table_name}")
        
        # Validate target section  
        if 'database' not in schema['target'] or 'table' not in schema['target']:
            raise ValueError(f"Target must contain 'database' and 'table' in schema for {source_type}.{database}.{table_name}")
        
        # Validate columns
        if not schema['columns']:
            raise ValueError(f"Columns cannot be empty in schema for {source_type}.{database}.{table_name}")
        
        for i, col in enumerate(schema['columns']):
            if 'name' not in col or 'target_name' not in col:
                raise ValueError(f"Column {i} must have 'name' and 'target_name' in schema for {source_type}.{database}.{table_name}")
    
    def get_all_table_schemas(self, source_type: str, database: str) -> Dict[str, Dict[str, Any]]:
        """Load all table schemas for a source database"""
        schema_dir = Path(self.config_base_path) / "schemas" / source_type / database
        
        if not schema_dir.exists():
            return {}
        
        schemas = {}
        for schema_file in schema_dir.glob("*.yaml"):
            table_name = schema_file.stem
            try:
                schemas[table_name] = self.load_table_schema(source_type, database, table_name)
            except Exception as e:
                print(f"Warning: Failed to load schema for {table_name}: {e}")
                continue
        
        return schemas
    
    def get_available_sources(self) -> List[Dict[str, str]]:
        """Get all available source databases and tables"""
        sources = []
        schemas_dir = Path(self.config_base_path) / "schemas"
        
        if not schemas_dir.exists():
            return sources
        
        for source_type in schemas_dir.iterdir():
            if source_type.is_dir():
                for database in source_type.iterdir():
                    if database.is_dir():
                        for schema_file in database.glob("*.yaml"):
                            sources.append({
                                'source_type': source_type.name,
                                'database': database.name,
                                'table': schema_file.stem
                            })
        
        return sources
    
    def schema_exists(self, source_type: str, database: str, table_name: str) -> bool:
        """Check if a schema file exists"""
        schema_path = self._get_schema_path(source_type, database, table_name)
        return schema_path.exists()