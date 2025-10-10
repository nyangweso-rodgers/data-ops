# resources/schema_loader.py
from dagster import ConfigurableResource
from typing import Dict, Any, List, Optional, Tuple
import yaml
from pathlib import Path

class SchemaLoader(ConfigurableResource):
    """Loads and manages table schema configurations from YAML files with version support"""
    
    config_base_path: str = "dagster_pipeline/config"
    default_version: str = "v1"  # Default version to use
    
    def _get_schema_path(self, source_type: str, database: str, table_name: str, version: Optional[str] = None) -> Path:
        """Get the full path to a schema file with version support"""
        if version:
            # New versioned path: schemas/mysql/amtdb/accounts/v1/accounts.yaml
            return Path(self.config_base_path) / "schemas" / source_type / database / table_name / version / f"{table_name}.yaml"
        else:
            # Try default version first, then fallback to old structure for compatibility
            default_path = Path(self.config_base_path) / "schemas" / source_type / database / table_name / self.default_version / f"{table_name}.yaml"
            if default_path.exists():
                return default_path
            else:
                # Fallback to old structure: schemas/mysql/amtdb/accounts.yaml
                return Path(self.config_base_path) / "schemas" / source_type / database / f"{table_name}.yaml"
    
    def load_table_schema(self, source_type: str, database: str, table_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Load schema configuration for a specific table and version"""
        schema_path = self._get_schema_path(source_type, database, table_name, version)
        
        if not schema_path.exists():
            # Try to find available versions
            available_versions = self.get_available_versions(source_type, database, table_name)
            if available_versions:
                raise FileNotFoundError(
                    f"Schema file not found: {schema_path}\n"
                    f"Available versions for {source_type}.{database}.{table_name}: {available_versions}"
                )
            else:
                raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        # Validate required fields
        self._validate_schema(schema, source_type, database, table_name)
        
        # Add version information to schema
        if version:
            schema['version'] = version
        else:
            # Extract version from path
            schema['version'] = schema_path.parent.name if schema_path.parent.name.startswith('v') else 'legacy'
        
        return schema
    
    def get_available_versions(self, source_type: str, database: str, table_name: str) -> List[str]:
        """Get all available versions for a table"""
        table_dir = Path(self.config_base_path) / "schemas" / source_type / database / table_name
        
        if not table_dir.exists():
            return []
        
        versions = []
        for item in table_dir.iterdir():
            if item.is_dir() and item.name.startswith('v'):
                schema_file = item / f"{table_name}.yaml"
                if schema_file.exists():
                    versions.append(item.name)
        
        return sorted(versions)  # Returns ['v1', 'v2', ...]
    
    def get_latest_version(self, source_type: str, database: str, table_name: str) -> Optional[str]:
        """Get the latest version available for a table"""
        versions = self.get_available_versions(source_type, database, table_name)
        return versions[-1] if versions else None
    
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
    
    def get_all_table_schemas(self, source_type: str, database: str, version: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Load all table schemas for a source database with optional version"""
        # Try new versioned structure first
        schema_dir = Path(self.config_base_path) / "schemas" / source_type / database
        
        if not schema_dir.exists():
            return {}
        
        schemas = {}
        
        # Look for table directories (new structure)
        for table_dir in schema_dir.iterdir():
            if table_dir.is_dir():
                table_name = table_dir.name
                try:
                    schema = self.load_table_schema(source_type, database, table_name, version)
                    schemas[table_name] = schema
                except Exception as e:
                    print(f"Warning: Failed to load schema for {table_name}: {e}")
                    continue
        
        # If no versioned schemas found, try old structure for backward compatibility
        if not schemas:
            for schema_file in schema_dir.glob("*.yaml"):
                table_name = schema_file.stem
                try:
                    schema = self.load_table_schema(source_type, database, table_name)
                    schemas[table_name] = schema
                except Exception as e:
                    print(f"Warning: Failed to load schema for {table_name}: {e}")
                    continue
        
        return schemas
    
    def get_available_sources(self) -> List[Dict[str, str]]:
        """Get all available source databases and tables with version info"""
        sources = []
        schemas_dir = Path(self.config_base_path) / "schemas"
        
        if not schemas_dir.exists():
            return sources
        
        for source_type in schemas_dir.iterdir():
            if source_type.is_dir():
                for database in source_type.iterdir():
                    if database.is_dir():
                        # Check if this is a table directory (new structure)
                        for table_dir in database.iterdir():
                            if table_dir.is_dir():
                                table_name = table_dir.name
                                versions = self.get_available_versions(source_type.name, database.name, table_name)
                                for version in versions:
                                    sources.append({
                                        'source_type': source_type.name,
                                        'database': database.name,
                                        'table': table_name,
                                        'version': version
                                    })
                            else:
                                # Old structure file
                                if table_dir.suffix == '.yaml':
                                    sources.append({
                                        'source_type': source_type.name,
                                        'database': database.name,
                                        'table': table_dir.stem,
                                        'version': 'legacy'
                                    })
        
        return sources
    
    def schema_exists(self, source_type: str, database: str, table_name: str, version: Optional[str] = None) -> bool:
        """Check if a schema file exists"""
        schema_path = self._get_schema_path(source_type, database, table_name, version)
        return schema_path.exists()
    
    def copy_schema_version(self, source_type: str, database: str, table_name: str, from_version: str, to_version: str) -> bool:
        """Copy a schema from one version to another"""
        source_path = self._get_schema_path(source_type, database, table_name, from_version)
        target_path = self._get_schema_path(source_type, database, table_name, to_version)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source schema not found: {source_path}")
        
        # Create target directory if it doesn't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the file
        import shutil
        shutil.copy2(source_path, target_path)
        
        return target_path.exists()