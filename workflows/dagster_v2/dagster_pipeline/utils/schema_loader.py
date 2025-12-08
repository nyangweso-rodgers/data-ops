# dagster_pipeline/utils/schema_loader.py
"""
Schema loader for reading and validating YAML schemas
Loads schemas from dagster_pipeline/schemas/
"""
from utils.type_mapper import TypeMapper

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class SourceType(Enum):
    """Supported source database types"""
    MYSQL = "mysql"
    POSTGRES = "postgres"
    S3 = "s3"
    API = "api"
    CLICKHOUSE = "clickhouse"


@dataclass
class ColumnDefinition:
    """
    Definition of a single column
    
    Attributes:
        name: Column name
        type: Data type (e.g., "bigint", "varchar(255)")
        nullable: Whether column can be NULL
        primary_key: Whether this is a primary key
        indexed: Whether column is indexed
        unique: Whether column values must be unique
        description: Human-readable description
        default: Default value
        source_name: Original column name in source (if renamed)
    """
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    indexed: bool = False
    unique: bool = False
    description: Optional[str] = None
    default: Optional[Any] = None
    source_name: Optional[str] = None
    
    def __post_init__(self):
        """Set source_name to name if not specified"""
        if self.source_name is None:
            self.source_name = self.name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for YAML serialization)"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class TableSchema:
    """
    Complete schema definition for a table
    
    Attributes:
        source_type: Type of source database
        database: Database name
        table: Table name
        columns: List of column definitions
        incremental_key: Column to use for incremental syncs
        metadata: Additional metadata (version, author, etc.)
    """
    source_type: SourceType
    database: str
    table: str
    columns: List[ColumnDefinition]
    incremental_key: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_column(self, column_name: str) -> Optional[ColumnDefinition]:
        """Get column definition by name"""
        for col in self.columns:
            if col.name == column_name or col.source_name == column_name:
                return col
        return None
    
    def get_primary_keys(self) -> List[ColumnDefinition]:
        """Get all primary key columns"""
        return [col for col in self.columns if col.primary_key]
    
    def get_column_names(self, use_source_names: bool = False) -> List[str]:
        """
        Get list of column names
        
        Args:
            use_source_names: If True, return source names instead of destination names
        """
        if use_source_names:
            return [col.source_name for col in self.columns]
        return [col.name for col in self.columns]
    
    def has_column(self, column_name: str) -> bool:
        """Check if column exists"""
        return self.get_column(column_name) is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for YAML serialization)"""
        return {
            "metadata": self.metadata,
            "source": {
                "type": self.source_type.value,
                "database": self.database,
                "table": self.table,
                "columns": [col.to_dict() for col in self.columns]
            },
            "incremental_key": self.incremental_key
        }

class SchemaLoader:
    """
    Advanced schema loader with caching, validation, and type mapping
    
    Features:
    - Eager loading with caching for performance
    - Type-safe dataclass models
    - Comprehensive validation
    - Integration with TypeMapper
    - Programmatic schema creation
    - Schema serialization back to YAML
    
    Usage:
        loader = SchemaLoader()
        schema = loader.get_schema("mysql", "amt", "accounts")
        
        # Type-safe access
        pk_columns = schema.get_primary_keys()
        customer_col = schema.get_column("customerId")
    """
    
    def __init__(self, schemas_dir: Optional[str] = None):
        """
        Initialize schema loader
        
        Args:
            schemas_dir: Path to schemas directory. If None, auto-detects.
        """
        if schemas_dir is None:
            # Auto-detect from module location
            current_file = Path(__file__).resolve()
            dagster_pipeline_dir = current_file.parent.parent
            self.schemas_dir = dagster_pipeline_dir / "schemas"
        else:
            self.schemas_dir = Path(schemas_dir)
        
        if not self.schemas_dir.exists():
            logger.warning(
                "schemas_directory_not_found",
                path=str(self.schemas_dir),
                message="Creating schemas directory"
            )
            self.schemas_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache: key -> TableSchema
        self._schemas_cache: Dict[str, TableSchema] = {}
        
        # Load all schemas on initialization
        self._load_all_schemas()
        
        logger.info(
            "schema_loader_initialized",
            schemas_dir=str(self.schemas_dir),
            schemas_loaded=len(self._schemas_cache)
        )
    
    def _load_all_schemas(self):
        """Load all schemas from directory into cache"""
        for schema_file in self.schemas_dir.rglob("*.yml"):
            # Skip templates
            if "template" in schema_file.stem.lower():
                continue
            
            relative_path = schema_file.relative_to(self.schemas_dir)
            schema_key = self._path_to_key(relative_path)
            
            try:
                schema = self._load_single_schema(schema_file)
                self._schemas_cache[schema_key] = schema
                logger.debug(
                    "schema_loaded",
                    key=schema_key,
                    columns=len(schema.columns)
                )
            except Exception as e:
                logger.error(
                    "schema_load_failed",
                    file=str(schema_file),
                    error=str(e)
                )
    
    def _path_to_key(self, path: Path) -> str:
        """Convert file path to cache key: mysql/amt/accounts.yml -> mysql:amt:accounts"""
        return str(path).replace('/', ':').replace('\\', ':').replace('.yml', '')
    
    def _key_to_path(self, key: str) -> Path:
        """Convert cache key to file path: mysql:amt:accounts -> mysql/amt/accounts.yml"""
        return self.schemas_dir / f"{key.replace(':', '/')}.yml"
    
    def _load_single_schema(self, file_path: Path) -> TableSchema:
        """Load and parse a single schema file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Validate required fields
        if 'source' not in data:
            raise ValueError(f"Missing 'source' section in {file_path}")
        
        source = data['source']
        required_fields = ['type', 'database', 'table', 'columns']
        for field in required_fields:
            if field not in source:
                raise ValueError(f"Missing '{field}' in source section: {file_path}")
        
        # Parse source type
        try:
            source_type = SourceType(source['type'].lower())
        except ValueError:
            raise ValueError(
                f"Invalid source type '{source['type']}' in {file_path}. "
                f"Valid types: {[t.value for t in SourceType]}"
            )
        
        # Parse columns
        columns = []
        for col_data in source['columns']:
            if 'name' not in col_data or 'type' not in col_data:
                raise ValueError(f"Column missing 'name' or 'type' in {file_path}")
            
            column = ColumnDefinition(
                name=col_data['name'],
                type=col_data['type'],
                nullable=col_data.get('nullable', True),
                primary_key=col_data.get('primary_key', False),
                indexed=col_data.get('indexed', False),
                unique=col_data.get('unique', False),
                description=col_data.get('description'),
                default=col_data.get('default'),
                source_name=col_data.get('source_name', col_data['name'])
            )
            columns.append(column)
        
        # Create TableSchema
        schema = TableSchema(
            source_type=source_type,
            database=source['database'],
            table=source['table'],
            columns=columns,
            incremental_key=data.get('incremental_key'),
            metadata=data.get('metadata', {})
        )
        
        return schema
    
    def get_schema(
        self,
        source_type: str,
        database: str,
        table: str
    ) -> Optional[TableSchema]:
        """
        Get schema from cache
        
        Args:
            source_type: "mysql", "postgres", etc.
            database: Database name
            table: Table name
        
        Returns:
            TableSchema or None if not found
        
        Example:
            >>> loader = SchemaLoader()
            >>> schema = loader.get_schema("mysql", "amt", "accounts")
            >>> print(schema.get_primary_keys())
            [ColumnDefinition(name='id', type='bigint', ...)]
        """
        key = f"{source_type.lower()}:{database}:{table}"
        schema = self._schemas_cache.get(key)
        
        if schema is None:
            logger.warning(
                "schema_not_found",
                source_type=source_type,
                database=database,
                table=table
            )
        
        return schema
    
    def get_schema_with_type_mapping(
        self,
        source_type: str,
        database: str,
        table: str,
        destination_type: str = "clickhouse",
        optimization: str = "balanced"
    ) -> Optional[TableSchema]:
        """
        Get schema with types converted for destination
        
        Returns:
            TableSchema with additional 'converted_columns' attribute
        """
        
        schema = self.get_schema(source_type, database, table)
        if schema is None:
            return None
        
        # Convert to dict for TypeMapper
        schema_dict = schema.to_dict()
        
        # Apply type mapping
        converted_columns = TypeMapper.convert_schema(
            schema_dict,
            destination_type,
            optimization
        )
        
        # Add converted columns to schema (as extra attribute)
        schema.converted_columns = converted_columns  # type: ignore
        schema.destination_type = destination_type  # type: ignore
        
        return schema
    
    def list_all_schemas(self) -> List[Dict[str, Any]]:
        """List all loaded schemas with summary info"""
        return [
            {
                "key": key,
                "source_type": schema.source_type.value,
                "database": schema.database,
                "table": schema.table,
                "columns": len(schema.columns),
                "primary_keys": len(schema.get_primary_keys()),
                "has_incremental_key": schema.incremental_key is not None,
                "incremental_key": schema.incremental_key
            }
            for key, schema in self._schemas_cache.items()
        ]
    
    def get_schemas_by_source(self, source_type: str) -> List[TableSchema]:
        """Get all schemas for a source type"""
        return [
            schema
            for key, schema in self._schemas_cache.items()
            if key.startswith(f"{source_type.lower()}:")
        ]
    
    def get_schemas_by_database(
        self,
        source_type: str,
        database: str
    ) -> List[TableSchema]:
        """Get all schemas for a specific database"""
        return [
            schema
            for key, schema in self._schemas_cache.items()
            if key.startswith(f"{source_type.lower()}:{database}:")
        ]
    
    def create_schema(
        self,
        source_type: str,
        database: str,
        table: str,
        columns: List[Dict[str, Any]],
        incremental_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TableSchema:
        """
        Create a new schema programmatically
        
        Example:
            >>> schema = loader.create_schema(
            ...     source_type="mysql",
            ...     database="amt",
            ...     table="new_table",
            ...     columns=[
            ...         {"name": "id", "type": "bigint", "primary_key": True},
            ...         {"name": "name", "type": "varchar(255)"}
            ...     ]
            ... )
        """
        column_defs = [
            ColumnDefinition(**{k: v for k, v in col.items() if k in ColumnDefinition.__annotations__})
            for col in columns
        ]
        
        schema = TableSchema(
            source_type=SourceType(source_type.lower()),
            database=database,
            table=table,
            columns=column_defs,
            incremental_key=incremental_key,
            metadata=metadata or {}
        )
        
        # Add to cache
        key = f"{source_type.lower()}:{database}:{table}"
        self._schemas_cache[key] = schema
        
        logger.info(
            "schema_created",
            source_type=source_type,
            database=database,
            table=table,
            columns=len(column_defs)
        )
        
        return schema
    
    def save_schema(self, schema: TableSchema, overwrite: bool = False):
        """
        Save schema to YAML file
        
        Args:
            schema: TableSchema to save
            overwrite: Whether to overwrite existing file
        """
        file_path = self._key_to_path(
            f"{schema.source_type.value}:{schema.database}:{schema.table}"
        )
        
        if file_path.exists() and not overwrite:
            raise FileExistsError(f"Schema file already exists: {file_path}")
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to YAML
        yaml_data = schema.to_dict()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                yaml_data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True
            )
        
        # Update cache
        key = f"{schema.source_type.value}:{schema.database}:{schema.table}"
        self._schemas_cache[key] = schema
        
        logger.info(
            "schema_saved",
            path=str(file_path),
            source_type=schema.source_type.value,
            database=schema.database,
            table=schema.table
        )
    
    def validate_schema(self, schema: TableSchema) -> List[str]:
        """
        Validate schema for common issues
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check duplicate column names
        column_names = schema.get_column_names()
        if len(column_names) != len(set(column_names)):
            duplicates = [name for name in column_names if column_names.count(name) > 1]
            errors.append(f"Duplicate column names: {set(duplicates)}")
        
        # Check incremental key exists
        if schema.incremental_key and not schema.has_column(schema.incremental_key):
            errors.append(
                f"Incremental key '{schema.incremental_key}' not found in columns"
            )
        
        # Check primary keys
        if not schema.get_primary_keys():
            errors.append("No primary key defined")
        
        # Check column types (basic validation)
        valid_type_patterns = {
            SourceType.MYSQL: ['bigint', 'int', 'varchar', 'text', 'decimal',
                              'timestamp', 'datetime', 'date', 'enum', 'json', 'boolean', 'char'],
            SourceType.POSTGRES: ['bigint', 'integer', 'text', 'varchar', 'numeric',
                                 'timestamp', 'date', 'jsonb', 'json', 'boolean', 'char'],
        }
        
        patterns = valid_type_patterns.get(schema.source_type, [])
        for col in schema.columns:
            if patterns and not any(pattern in col.type.lower() for pattern in patterns):
                errors.append(
                    f"Column '{col.name}' has potentially invalid type '{col.type}' "
                    f"for {schema.source_type.value}"
                )
        
        return errors
    
    def reload_schemas(self):
        """Reload all schemas from disk (useful after schema changes)"""
        logger.info("reloading_schemas")
        self._schemas_cache.clear()
        self._load_all_schemas()
        logger.info("schemas_reloaded", count=len(self._schemas_cache))