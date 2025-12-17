"""
Schema loader for reading and validating YAML schemas
Loads schemas from dagster_pipeline/schemas/

DESIGN PRINCIPLES:
- Lazy loading ONLY - load schemas on-demand
- Fail fast - any schema error raises exception immediately
- Thread-safe for Dagster's multiprocess executor
- Minimal memory footprint
- No unnecessary logging
"""
from .type_mapper import TypeMapper

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import structlog
import threading

logger = structlog.get_logger(__name__)


class SourceType(Enum):
    """Supported source database types"""
    MYSQL = "mysql"
    POSTGRES = "postgres"
    S3 = "s3"
    API = "api"
    CLICKHOUSE = "clickhouse"


class SchemaNotFoundError(Exception):
    """Raised when a schema file cannot be found"""
    pass


class SchemaValidationError(Exception):
    """Raised when schema validation fails"""
    pass


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
        
        # Validate name
        if not self.name or not isinstance(self.name, str):
            raise ValueError(f"Invalid column name: {self.name}")
        if not self.type or not isinstance(self.type, str):
            raise ValueError(f"Invalid column type for {self.name}: {self.type}")
    
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
        schema_version: Version of this schema (for tracking changes)
    """
    source_type: SourceType
    database: str
    table: str
    columns: List[ColumnDefinition]
    incremental_key: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    schema_version: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization validation"""
        if not self.columns:
            raise SchemaValidationError(
                f"Schema {self.database}.{self.table} has no columns"
            )
    
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
        result = {
            "metadata": self.metadata,
            "source": {
                "type": self.source_type.value,
                "database": self.database,
                "table": self.table,
                "columns": [col.to_dict() for col in self.columns]
            },
            "incremental_key": self.incremental_key
        }
        
        if self.schema_version:
            result["schema_version"] = self.schema_version
        
        return result
    
    @property
    def full_name(self) -> str:
        """Get fully qualified table name"""
        return f"{self.source_type.value}.{self.database}.{self.table}"


class SchemaLoader:
    """
    Lazy-loading schema loader for Dagster pipelines
    
    Design:
    - NO eager loading - schemas loaded only when requested
    - Thread-safe caching for multiprocess executor
    - Fail-fast validation - raises exceptions on any error
    - Minimal memory footprint - only caches what's used
    
    Usage:
        # In Dagster resource
        loader = SchemaLoader()
        
        # In asset - only loads THIS schema
        schema = loader.get_schema("mysql", "amtdb", "accounts")
        
        # Schema is cached for subsequent calls in same process
        schema2 = loader.get_schema("mysql", "amtdb", "accounts")  # From cache
    """
    
    def __init__(
        self,
        schemas_dir: Optional[str] = None,
        enable_cache: bool = True,
        validate_on_load: bool = True
    ):
        """
        Initialize schema loader
        
        Args:
            schemas_dir: Path to schemas directory. If None, auto-detects.
            enable_cache: Whether to cache loaded schemas (disable for testing)
            validate_on_load: Whether to validate schemas on load (should always be True)
        """
        if schemas_dir is None:
            current_file = Path(__file__).resolve()
            dagster_pipeline_dir = current_file.parent.parent
            self.schemas_dir = dagster_pipeline_dir / "schemas"
        else:
            self.schemas_dir = Path(schemas_dir)
        
        if not self.schemas_dir.exists():
            raise SchemaNotFoundError(
                f"Schemas directory not found: {self.schemas_dir}"
            )
        
        self.enable_cache = enable_cache
        self.validate_on_load = validate_on_load
        
        # Thread-safe cache - only stores schemas that have been requested
        self._schemas_cache: Dict[str, TableSchema] = {}
        self._cache_lock = threading.RLock()
        
        # Minimal logging on init
        logger.info(
            "schema_loader_initialized",
            schemas_dir=str(self.schemas_dir),
            cache_enabled=enable_cache
        )
    
    def _key_to_path(self, key: str) -> Path:
        """Convert cache key to file path: mysql:amtdb:accounts -> mysql/amtdb/accounts.yml"""
        return self.schemas_dir / f"{key.replace(':', '/')}.yml"
    
    def _load_and_validate_schema(self, file_path: Path, key: str) -> TableSchema:
        """
        Load and validate a single schema file
        Raises exceptions on any error - fail fast!
        """
        # Check file exists
        if not file_path.exists():
            raise SchemaNotFoundError(
                f"Schema file not found: {file_path} (key: {key})"
            )
        
        # Load YAML
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise SchemaValidationError(
                f"Invalid YAML in {file_path}: {e}"
            )
        except Exception as e:
            raise SchemaNotFoundError(
                f"Cannot read schema file {file_path}: {e}"
            )
        
        if not data:
            raise SchemaValidationError(f"Empty schema file: {file_path}")
        
        # Validate structure
        if 'source' not in data:
            raise SchemaValidationError(
                f"Missing 'source' section in {file_path}"
            )
        
        source = data['source']
        required_fields = ['type', 'database', 'table', 'columns']
        for field in required_fields:
            if field not in source:
                raise SchemaValidationError(
                    f"Missing '{field}' in source section: {file_path}"
                )
        
        # Parse source type
        try:
            source_type = SourceType(source['type'].lower())
        except ValueError:
            raise SchemaValidationError(
                f"Invalid source type '{source['type']}' in {file_path}. "
                f"Valid types: {[t.value for t in SourceType]}"
            )
        
        # Parse columns
        columns = []
        for idx, col_data in enumerate(source['columns']):
            if 'name' not in col_data or 'type' not in col_data:
                raise SchemaValidationError(
                    f"Column {idx} missing 'name' or 'type' in {file_path}"
                )
            
            try:
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
            except Exception as e:
                raise SchemaValidationError(
                    f"Failed to parse column '{col_data.get('name', idx)}' "
                    f"in {file_path}: {e}"
                )
        
        # Create TableSchema
        try:
            schema = TableSchema(
                source_type=source_type,
                database=source['database'],
                table=source['table'],
                columns=columns,
                incremental_key=data.get('incremental_key'),
                metadata=data.get('metadata', {}),
                schema_version=data.get('schema_version')
            )
        except Exception as e:
            raise SchemaValidationError(
                f"Failed to create schema from {file_path}: {e}"
            )
        
        # Validate schema
        if self.validate_on_load:
            validation_errors = self.validate_schema(schema)
            if validation_errors:
                raise SchemaValidationError(
                    f"Schema validation failed for {file_path}:\n" +
                    "\n".join(f"  - {err}" for err in validation_errors)
                )
        
        return schema
    
    def get_schema(
        self,
        source_type: str,
        database: str,
        table: str
    ) -> TableSchema:
        """
        Get schema - loads on first request, caches for subsequent calls
        
        Args:
            source_type: "mysql", "postgres", etc.
            database: Database name
            table: Table name
        
        Returns:
            TableSchema
        
        Raises:
            SchemaNotFoundError: If schema file doesn't exist
            SchemaValidationError: If schema is invalid
        
        Example:
            >>> loader = SchemaLoader()
            >>> schema = loader.get_schema("mysql", "amtdb", "accounts")
            >>> # Only accounts schema is loaded, nothing else
        """
        key = f"{source_type.lower()}:{database}:{table}"
        
        # Check cache first (thread-safe)
        if self.enable_cache:
            with self._cache_lock:
                if key in self._schemas_cache:
                    return self._schemas_cache[key]
        
        # Load schema (not in cache)
        file_path = self._key_to_path(key)
        
        # Log only when actually loading (not from cache)
        logger.info(
            "loading_schema",
            source_type=source_type,
            database=database,
            table=table,
            file=str(file_path)
        )
        
        schema = self._load_and_validate_schema(file_path, key)
        
        # Cache if enabled
        if self.enable_cache:
            with self._cache_lock:
                self._schemas_cache[key] = schema
        
        logger.info(
            "schema_loaded",
            key=key,
            columns=len(schema.columns),
            has_incremental_key=schema.incremental_key is not None
        )
        
        return schema
    
    def get_schema_with_type_mapping(
        self,
        source_type: str,
        database: str,
        table: str,
        destination_type: str = "clickhouse",
        optimization: str = "balanced"
    ) -> TableSchema:
        """
        Get schema with types converted for destination
        
        Returns:
            TableSchema with additional 'converted_columns' attribute
        """
        schema = self.get_schema(source_type, database, table)
        
        schema_dict = schema.to_dict()
        
        converted_columns = TypeMapper.convert_schema(
            schema_dict,
            destination_type,
            optimization
        )
        
        # Add converted columns as dynamic attributes
        schema.converted_columns = converted_columns  # type: ignore
        schema.destination_type = destination_type  # type: ignore
        
        return schema
    
    def validate_schema(self, schema: TableSchema) -> List[str]:
        """
        Validate schema for common issues
        
        Args:
            schema: TableSchema to validate
        
        Returns:
            List of validation errors (empty if valid)
            
        Example:
            >>> schema = loader.get_schema("postgres", "sunculture_ep", "premise_details")
            >>> errors = loader.validate_schema(schema)
            >>> if errors:
            ...     print(f"Validation failed: {errors}")
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
        
        # Validate column types with exact matching
        if schema.source_type == SourceType.MYSQL:
            valid_base_types = {
                'bigint', 'int', 'tinyint', 'smallint', 'mediumint',
                'varchar', 'char', 'text', 'mediumtext', 'longtext',
                'decimal', 'numeric', 'float', 'double',
                'timestamp', 'datetime', 'date', 'time',
                'enum', 'set', 'json', 'boolean', 'bool',
                'binary', 'varbinary', 'blob', 'bit'
            }
        elif schema.source_type == SourceType.POSTGRES:
            valid_base_types = {
                'bigint', 'integer', 'int', 'int2', 'int4', 'int8',
                'smallint', 'serial', 'bigserial',
                'decimal', 'numeric', 'real', 'float4',
                'double precision', 'float8',
                'text', 'varchar', 'character varying', 'char',
                'character', 'uuid',
                'timestamp', 'timestamptz', 'date', 'time',
                'timetz', 'interval',
                'jsonb', 'json', 'boolean', 'bool',
                'bytea', 'inet', 'cidr', 'macaddr', 'hstore'
            }
        else:
            # Skip validation for other source types
            return errors
        
        for col in schema.columns:
            col_type_lower = col.type.lower()
            
            # Extract base type (before parentheses or brackets)
            base_type = col_type_lower.split('(')[0].split('[')[0].strip()
            
            # Handle array types
            if base_type.startswith('_'):
                base_type = base_type[1:]  # Remove underscore prefix
            
            # Validate base type
            if base_type not in valid_base_types:
                errors.append(
                    f"Column '{col.name}' has invalid type '{col.type}' "
                    f"(base type: '{base_type}') for {schema.source_type.value}"
                )
        
        return errors
    
    def create_schema(
        self,
        source_type: str,
        database: str,
        table: str,
        columns: List[Dict[str, Any]],
        incremental_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        schema_version: Optional[str] = None
    ) -> TableSchema:
        """
        Create a new schema programmatically
        
        Validates immediately and raises exception if invalid
        """
        column_defs = [
            ColumnDefinition(**{
                k: v for k, v in col.items() 
                if k in ColumnDefinition.__annotations__
            })
            for col in columns
        ]
        
        schema = TableSchema(
            source_type=SourceType(source_type.lower()),
            database=database,
            table=table,
            columns=column_defs,
            incremental_key=incremental_key,
            metadata=metadata or {},
            schema_version=schema_version
        )
        
        # Validate before accepting
        validation_errors = self.validate_schema(schema)
        if validation_errors:
            raise SchemaValidationError(
                f"Schema validation failed:\n" +
                "\n".join(f"  - {err}" for err in validation_errors)
            )
        
        # Add to cache
        if self.enable_cache:
            key = f"{source_type.lower()}:{database}:{table}"
            with self._cache_lock:
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
        
        Raises:
            FileExistsError: If file exists and overwrite=False
        """
        file_path = self._key_to_path(
            f"{schema.source_type.value}:{schema.database}:{schema.table}"
        )
        
        if file_path.exists() and not overwrite:
            raise FileExistsError(
                f"Schema file already exists: {file_path}. "
                f"Use overwrite=True to replace it."
            )
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        yaml_data = schema.to_dict()
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    yaml_data,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True
                )
        except Exception as e:
            raise IOError(f"Failed to save schema to {file_path}: {e}")
        
        # Update cache
        if self.enable_cache:
            key = f"{schema.source_type.value}:{schema.database}:{schema.table}"
            with self._cache_lock:
                self._schemas_cache[key] = schema
        
        logger.info(
            "schema_saved",
            path=str(file_path),
            full_name=schema.full_name
        )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics (useful for debugging)"""
        with self._cache_lock:
            return {
                "cache_enabled": self.enable_cache,
                "schemas_cached": len(self._schemas_cache),
                "cached_schemas": list(self._schemas_cache.keys())
            }
    
    def clear_cache(self):
        """Clear the schema cache (useful for testing or hot-reloading)"""
        with self._cache_lock:
            count = len(self._schemas_cache)
            self._schemas_cache.clear()
        
        logger.info("schema_cache_cleared", schemas_cleared=count)
    
    # Utility methods for schema discovery (optional, not used in normal flow)
    
    def list_available_schemas(self) -> List[str]:
        """
        List all available schema files (for discovery/debugging)
        
        Note: This scans the filesystem. Use sparingly.
        """
        available = []
        for schema_file in self.schemas_dir.rglob("*.yml"):
            if "template" in schema_file.stem.lower():
                continue
            
            relative_path = schema_file.relative_to(self.schemas_dir)
            key = str(relative_path).replace('/', ':').replace('\\', ':').replace('.yml', '')
            available.append(key)
        
        return sorted(available)
    
    def preload_schemas(self, schema_keys: List[str]):
        """
        Preload specific schemas into cache
        
        Useful if you know you'll need multiple schemas and want to load them
        upfront (e.g., in a batch job processing multiple tables)
        
        Args:
            schema_keys: List of schema keys like ["mysql:amtdb:accounts", "mysql:amtdb:users"]
        """
        for key in schema_keys:
            parts = key.split(':')
            if len(parts) != 3:
                logger.warning(f"Invalid schema key format: {key}")
                continue
            
            source_type, database, table = parts
            try:
                self.get_schema(source_type, database, table)
            except Exception as e:
                # Re-raise - fail fast
                raise SchemaNotFoundError(
                    f"Failed to preload schema {key}: {e}"
                )