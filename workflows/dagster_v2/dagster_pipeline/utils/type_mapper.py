"""
Type mapper for converting source database types to destination types
Supports MySQL, Postgres → ClickHouse, BigQuery, Snowflake
"""

from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import re
import csv
from io import StringIO

# Use centralized logging
from dagster_pipeline.utils.logging_config import get_logger

# Get module-level logger
logger = get_logger(__name__)


class DataType(Enum):
    """Normalized internal data types"""
    INTEGER = "integer"
    BIGINT = "bigint"
    DECIMAL = "decimal"
    FLOAT = "float"
    STRING = "string"
    TEXT = "text"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIMESTAMP = "timestamp"
    JSON = "json"
    ARRAY = "array"
    ENUM = "enum"
    UUID = "uuid"


class TypeMapper:
    """
    Intelligent type mapper with smart defaults and robust parsing
    
    Usage:
        # Convert single column
        column = {"name": "id", "type": "bigint", "nullable": False}
        result = TypeMapper.convert_column(column, "mysql", "clickhouse")
        
        # Convert entire schema
        columns = TypeMapper.convert_schema(schema, "clickhouse")
    """
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    @staticmethod
    def _parse_type_with_params(type_str: str) -> Tuple[str, Optional[str]]:
        """
        Extract base type and parameters from type string
        
        FIXED: Now handles types without parentheses correctly
        
        Returns: (base_type, params_str)
        Examples:
            "varchar(255)" → ("varchar", "255")
            "decimal(18,2)" → ("decimal", "18,2")
            "uuid" → ("uuid", None)  # FIXED: was "u", "uid"
            "timestamp" → ("timestamp", None)  # FIXED: was "t", "imestamp"
            "timestamp without time zone" → ("timestamp without time zone", None)
            "character varying" → ("character varying", None)
        """
        type_str = type_str.strip()
        
        # Check if there are parentheses
        if '(' in type_str:
            # Type with parameters: base_type(params) optional_suffix
            # Match: word characters until '(', params inside '()', optional suffix after ')'
            match = re.match(r'^([^(]+)\((.*?)\)(.*)$', type_str)
            
            if match:
                base_type = match.group(1).strip()
                params_str = match.group(2).strip()
                suffix = match.group(3).strip()
                
                # Append suffix if it exists (e.g., "without time zone")
                if suffix:
                    base_type = f"{base_type} {suffix}"
                
                return base_type, params_str if params_str else None
            else:
                # Malformed type with parentheses
                logger.warning(
                    "type_parse_failed_malformed",
                    type_str=type_str
                )
                return type_str, None
        else:
            # No parentheses - just return the whole string as base_type
            # This fixes the "uuid" → "u" bug!
            return type_str, None
    
    @staticmethod
    def _parse_mysql_unsigned(type_str: str) -> Tuple[str, bool]:
        """
        Check if MySQL type has UNSIGNED modifier
        Returns: (type_without_unsigned, is_unsigned)
        """
        type_lower = type_str.lower()
        is_unsigned = 'unsigned' in type_lower
        
        if is_unsigned:
            # Remove unsigned keyword
            type_clean = re.sub(r'\s*unsigned\s*', '', type_lower, flags=re.IGNORECASE)
            return type_clean.strip(), True
        
        return type_str, False
    
    @staticmethod
    def _parse_enum_values(params_str: str) -> List[str]:
        """
        Safely parse ENUM values handling embedded quotes and commas
        
        Examples:
            "'active','inactive'" → ["active", "inactive"]
            "'O''Reilly','Smith, Jr.'" → ["O'Reilly", "Smith, Jr."]
        """
        try:
            # Use CSV reader with single quote as quote char
            reader = csv.reader(StringIO(params_str), quotechar="'")
            values = next(reader)
            return [v.strip() for v in values]
        except Exception as e:
            # Fallback to simple split
            logger.warning(
                "enum_parse_fallback",
                params_str=params_str,
                error=str(e)
            )
            return [v.strip().strip("'\"") for v in params_str.split(",")]
    
    # ========================================================================
    # MYSQL TYPE PARSER
    # ========================================================================
    
    @staticmethod
    def parse_mysql_type(type_str: str, nullable: bool = True) -> Dict[str, Any]:
        """
        Parse MySQL type into normalized form
        
        Examples:
            "varchar(255)" → {normalized_type: STRING, length: 255}
            "decimal(18,2)" → {normalized_type: DECIMAL, precision: 18, scale: 2}
            "enum('active','inactive')" → {normalized_type: ENUM, values: ['active','inactive']}
            "int(11) unsigned" → {normalized_type: INTEGER, unsigned: True}
        """
        type_str = type_str.lower().strip()
        
        # Check for UNSIGNED modifier (MySQL-specific)
        type_str, is_unsigned = TypeMapper._parse_mysql_unsigned(type_str)
        
        # Parse base type and parameters
        base_type, params_str = TypeMapper._parse_type_with_params(type_str)
        
        # Parse parameters
        params = {}
        if params_str:
            if base_type in ("enum", "set"):
                params["enum_values"] = TypeMapper._parse_enum_values(params_str)
            else:
                # Parse numeric parameters: 18,2 or 255
                param_list = [p.strip() for p in params_str.split(",")]
                params["params"] = param_list
        
        # Map MySQL type to normalized type
        type_mapping = {
            # Integer types
            "tinyint": DataType.INTEGER,
            "smallint": DataType.INTEGER,
            "mediumint": DataType.INTEGER,
            "int": DataType.INTEGER,
            "integer": DataType.INTEGER,
            "bigint": DataType.BIGINT,
            
            # Decimal types
            "decimal": DataType.DECIMAL,
            "numeric": DataType.DECIMAL,
            "float": DataType.FLOAT,
            "double": DataType.FLOAT,
            "real": DataType.FLOAT,
            
            # String types
            "char": DataType.STRING,
            "varchar": DataType.STRING,
            "tinytext": DataType.TEXT,
            "text": DataType.TEXT,
            "mediumtext": DataType.TEXT,
            "longtext": DataType.TEXT,
            "binary": DataType.STRING,
            "varbinary": DataType.STRING,
            
            # Date/Time types
            "date": DataType.DATE,
            "datetime": DataType.DATETIME,
            "timestamp": DataType.TIMESTAMP,
            "time": DataType.STRING,
            "year": DataType.INTEGER,
            
            # Other types
            "boolean": DataType.BOOLEAN,
            "bool": DataType.BOOLEAN,
            "json": DataType.JSON,
            "enum": DataType.ENUM,
            "set": DataType.ARRAY,
        }
        
        normalized_type = type_mapping.get(base_type)
        
        if normalized_type is None:
            logger.warning(
                "unknown_mysql_type",
                base_type=base_type,
                full_type=type_str,
                defaulting_to="STRING"
            )
            normalized_type = DataType.STRING
        
        result = {
            "normalized_type": normalized_type,
            "nullable": nullable,
            "source_type": type_str,
            "unsigned": is_unsigned,
        }
        
        # Add type-specific parameters
        if normalized_type == DataType.STRING and "params" in params:
            try:
                result["length"] = int(params["params"][0])
            except (ValueError, IndexError):
                logger.warning("invalid_length", params=params["params"])
        elif normalized_type == DataType.DECIMAL and "params" in params:
            try:
                result["precision"] = int(params["params"][0])
                result["scale"] = int(params["params"][1]) if len(params["params"]) > 1 else 0
            except (ValueError, IndexError) as e:
                logger.warning("invalid_decimal_params", params=params["params"], error=str(e))
                result["precision"] = 18
                result["scale"] = 2
        elif normalized_type == DataType.ENUM:
            result["enum_values"] = params.get("enum_values", [])
        elif normalized_type == DataType.DATETIME and "params" in params:
            # MySQL datetime(6) - fractional seconds precision
            try:
                result["precision"] = int(params["params"][0])
            except (ValueError, IndexError):
                result["precision"] = 0
        
        return result
    
    @staticmethod
    def parse_postgres_type(type_str: str, nullable: bool = True) -> Dict[str, Any]:
        """
        Parse PostgreSQL type into normalized form
        
        Examples:
            "integer" → {normalized_type: INTEGER}
            "varchar(255)" → {normalized_type: STRING, length: 255}
            "integer[]" → {normalized_type: ARRAY, element_type: INTEGER}
            "uuid" → {normalized_type: UUID}
            "decimal(18,2)[]" → {normalized_type: ARRAY, element_type: DECIMAL, element_precision: 18, element_scale: 2}
        """
        type_str = type_str.lower().strip()
        
        # Handle array types with underscore prefix: _int4, _uuid, etc.
        is_array_underscore = type_str.startswith("_")
        if is_array_underscore:
            element_type_str = type_str[1:]  # Remove the underscore
            # Parse the element type recursively
            element_info = TypeMapper.parse_postgres_type(element_type_str, nullable=False)
            result = {
                "normalized_type": DataType.ARRAY,
                "nullable": nullable,
                "source_type": type_str,
                "is_array": True,
                "element_info": element_info  # Store full element info
            }
            return result
        
        # Handle array types with [] suffix: integer[]
        is_array_suffix = type_str.endswith("[]")
        if is_array_suffix:
            element_type_str = type_str[:-2]
            # Parse the element type recursively
            element_info = TypeMapper.parse_postgres_type(element_type_str, nullable=False)
            result = {
                "normalized_type": DataType.ARRAY,
                "nullable": nullable,
                "source_type": type_str,
                "is_array": True,
                "element_info": element_info  # Store full element info
            }
            return result
        
        # Parse base type and parameters
        base_type, params_str = TypeMapper._parse_type_with_params(type_str)
        
        type_mapping = {
            # Integer types
            "smallint": DataType.INTEGER,
            "integer": DataType.INTEGER,
            "int": DataType.INTEGER,
            "int2": DataType.INTEGER,
            "int4": DataType.INTEGER,
            "bigint": DataType.BIGINT,
            "int8": DataType.BIGINT,
            "serial": DataType.INTEGER,
            "bigserial": DataType.BIGINT,
            
            # Decimal types
            "decimal": DataType.DECIMAL,
            "numeric": DataType.DECIMAL,
            "real": DataType.FLOAT,
            "float4": DataType.FLOAT,
            "double precision": DataType.FLOAT,
            "float8": DataType.FLOAT,
            
            # String types
            "char": DataType.STRING,
            "character": DataType.STRING,
            "varchar": DataType.STRING,
            "character varying": DataType.STRING,
            "text": DataType.TEXT,
            "uuid": DataType.UUID,
            
            # Date/Time types
            "date": DataType.DATE,
            "time": DataType.STRING,
            "time without time zone": DataType.STRING,
            "timetz": DataType.STRING,
            "time with time zone": DataType.STRING,
            "timestamp": DataType.TIMESTAMP,
            "timestamp without time zone": DataType.TIMESTAMP,
            "timestamptz": DataType.TIMESTAMP,
            "timestamp with time zone": DataType.TIMESTAMP,
            "interval": DataType.STRING,
            
            # Boolean
            "boolean": DataType.BOOLEAN,
            "bool": DataType.BOOLEAN,
            
            # JSON/JSONB
            "json": DataType.JSON,
            "jsonb": DataType.JSON,
            
            # Binary/BLOB
            "bytea": DataType.STRING,
            
            # Network/Other
            "inet": DataType.STRING,
            "cidr": DataType.STRING,
            "macaddr": DataType.STRING,
            "point": DataType.STRING,
            "line": DataType.STRING,
            "lseg": DataType.STRING,
            "box": DataType.STRING,
            "path": DataType.STRING,
            "polygon": DataType.STRING,
            "circle": DataType.STRING,
            "bit": DataType.STRING,
            "bit varying": DataType.STRING,
            "varbit": DataType.STRING,
            "tsvector": DataType.STRING,
            "tsquery": DataType.STRING,
            "xml": DataType.STRING,
            "int4range": DataType.STRING,
            "int8range": DataType.STRING,
            "numrange": DataType.STRING,
            "tsrange": DataType.STRING,
            "tstzrange": DataType.STRING,
            "daterange": DataType.STRING,
            "oid": DataType.BIGINT,
            "regproc": DataType.STRING,
            "regprocedure": DataType.STRING,
            "regoper": DataType.STRING,
            "regoperator": DataType.STRING,
            "regclass": DataType.STRING,
            "regtype": DataType.STRING,
            "regrole": DataType.STRING,
            "regnamespace": DataType.STRING,
            "regconfig": DataType.STRING,
            "regdictionary": DataType.STRING,
        }
        
        normalized_type = type_mapping.get(base_type)
        
        if normalized_type is None:
            logger.warning(
                "unknown_postgres_type",
                base_type=base_type,
                full_type=type_str,
                defaulting_to="STRING"
            )
            normalized_type = DataType.STRING
        
        result = {
            "normalized_type": normalized_type,
            "nullable": nullable,
            "source_type": type_str,
        }
        
        # Add parameters for specific types
        if params_str:
            params = [p.strip() for p in params_str.split(",")]
            
            if normalized_type == DataType.STRING:
                try:
                    if params and params[0].replace('.','',1).isdigit():
                        result["length"] = int(float(params[0]))
                except (ValueError, IndexError):
                    logger.warning("invalid_string_length", params=params)
                    
            elif normalized_type == DataType.DECIMAL:
                try:
                    if len(params) >= 1:
                        result["precision"] = int(params[0])
                    if len(params) >= 2:
                        result["scale"] = int(params[1])
                    else:
                        result["scale"] = 0
                except (ValueError, IndexError):
                    logger.warning("invalid_decimal_params", params=params)
                    result["precision"] = 18
                    result["scale"] = 2
                    
            elif normalized_type == DataType.TIMESTAMP:
                # timestamp(6) - fractional seconds precision
                try:
                    if params and params[0].isdigit():
                        result["precision"] = min(int(params[0]), 6)
                except (ValueError, IndexError):
                    result["precision"] = 6
        
        return result
    
    # ========================================================================
    # CLICKHOUSE MAPPER
    # ========================================================================
    
    @staticmethod
    def to_clickhouse_type(
        normalized_info: Dict[str, Any],
        optimization: str = "balanced"
    ) -> str:
        """
        Map to ClickHouse type with performance optimizations
        
        Args:
            normalized_info: Normalized type info from parse_*_type()
            optimization: "speed", "balanced", "storage"
        
        Returns:
            ClickHouse type string (e.g., "String", "Nullable(Int64)")
        """
        normalized_type = normalized_info["normalized_type"]
        nullable = normalized_info.get("nullable", True)
        is_unsigned = normalized_info.get("unsigned", False)

        # Handle arrays
        if normalized_type == DataType.ARRAY:
            element_info = normalized_info.get("element_info", {})
            if element_info:
                # Recursively convert element type
                element_ch_type = TypeMapper.to_clickhouse_type(element_info, optimization)
                # Remove Nullable wrapper from element type (arrays handle nulls differently)
                if element_ch_type.startswith("Nullable("):
                    element_ch_type = element_ch_type[9:-1]  # Strip Nullable()
                base_type = f"Array({element_ch_type})"
            else:
                base_type = "Array(String)"
            
            # Arrays themselves can't be Nullable in ClickHouse
            return base_type
        
        # Handle UUID - ALWAYS FixedString(36) or UUID type
        if normalized_type == DataType.UUID:
            if optimization == "storage":
                base_type = "UUID"
            else:
                base_type = "FixedString(36)"
            
            if nullable:
                return f"Nullable({base_type})"
            return base_type
        
        # Handle INTEGER with UNSIGNED modifier
        if normalized_type == DataType.INTEGER:
            if is_unsigned:
                base_type = "UInt32"
            else:
                base_type = "Int32"
        elif normalized_type == DataType.BIGINT:
            if is_unsigned:
                base_type = "UInt64"
            else:
                base_type = "Int64"
        else:
            # Base type mapping for non-integer types
            type_map = {
                DataType.FLOAT: "Float64",
                DataType.STRING: "String",
                DataType.TEXT: "String",
                DataType.BOOLEAN: "UInt8",
                DataType.DATE: "Date32",
                DataType.DATETIME: "DateTime",
                DataType.TIMESTAMP: "DateTime",
                DataType.JSON: "String",
            }
            base_type = type_map.get(normalized_type, "String")
        
        # Apply optimizations (but NOT for UUIDs)
        if optimization == "speed":
            if normalized_type == DataType.ENUM:
                base_type = "LowCardinality(String)"
            elif normalized_type == DataType.TIMESTAMP:
                precision = normalized_info.get("precision", 3)
                base_type = f"DateTime64({min(precision, 9)})"  # Max 9 for ClickHouse
        elif optimization == "balanced":
            if normalized_type == DataType.ENUM:
                enum_values = normalized_info.get("enum_values", [])
                if len(enum_values) < 100:
                    base_type = "LowCardinality(String)"
                else:
                    base_type = "String"
        
        # Handle DECIMAL with validation
        if normalized_type == DataType.DECIMAL:
            precision = normalized_info.get("precision", 18)
            scale = normalized_info.get("scale", 2)
            
            # ClickHouse Decimal limits
            if precision > 76:
                logger.warning(
                    "decimal_precision_exceeded",
                    requested=precision,
                    clamped_to=76
                )
                precision = 76
            
            base_type = f"Decimal({precision}, {scale})"
        
        # Handle LowCardinality wrapping
        if base_type.startswith("LowCardinality("):
            # Extract the inner type: LowCardinality(String) → String
            inner_type = base_type[15:-1]  # Remove "LowCardinality(" and ")"
            
            if nullable:
                # Wrap inner type with Nullable first, then LowCardinality
                return f"LowCardinality(Nullable({inner_type}))"
            else:
                # Keep as is
                return base_type
        # For all other types, wrap with Nullable if needed
        if nullable:
            return f"Nullable({base_type})"

        
        return base_type
    
    # ========================================================================
    # BIGQUERY MAPPER
    # ========================================================================
    # Add BigQuery mapping methods here if needed
    
    # ========================================================================
    # API Mapper METHODS
    # ========================================================================
    # Add App Level Methods Here
    
    # ========================================================================
    # Convert Column Method 
    # ========================================================================
    @classmethod
    def convert_column(
        cls,
        column_def: Dict[str, Any],
        source_db_type: str,
        destination_db_type: str,
        optimization: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Convert column definition from source to destination
        
        Args:
            column_def: Column from schema YAML
                {"name": "id", "type": "bigint", "nullable": False}
            source_db_type: "mysql" or "postgres"
            destination_db_type: "clickhouse", "bigquery", "snowflake"
            optimization: "speed", "balanced", "storage"
        
        Returns:
            {
                "name": "id",
                "source_type": "bigint",
                "destination_type": "Int64",
                "nullable": False,
                "normalized_type": "bigint",
                "primary_key": True
            }
        """
        # Parse source type
        if source_db_type == "mysql":
            normalized = cls.parse_mysql_type(
                column_def["type"],
                column_def.get("nullable", True)
            )
        elif source_db_type == "postgres":
            normalized = cls.parse_postgres_type(
                column_def["type"],
                column_def.get("nullable", True)
            )
        else:
            raise ValueError(f"Unsupported source DB type: {source_db_type}")
        
        # Map to destination
        if destination_db_type == "clickhouse":
            dest_type = cls.to_clickhouse_type(normalized, optimization)
        elif destination_db_type == "bigquery":
            dest_type = cls.to_bigquery_type(normalized)
        else:
            raise ValueError(f"Unsupported destination DB type: {destination_db_type}")
        
        return {
            "name": column_def["name"],
            "source_type": column_def["type"],
            "destination_type": dest_type,
            "nullable": normalized["nullable"],
            "normalized_type": normalized["normalized_type"].value,
            "primary_key": column_def.get("primary_key", False),
            "indexed": column_def.get("indexed", False),
            "unique": column_def.get("unique", False),
            "description": column_def.get("description", ""),
        }
    
    # ========================================================================
    # Convert Schema Method 
    # ========================================================================
    @classmethod
    def convert_schema(
        cls,
        schema: Dict[str, Any],
        destination_db_type: str,
        optimization: str = "balanced"
    ) -> List[Dict[str, Any]]:
        """
        Convert entire schema for a destination
        
        Args:
            schema: Loaded YAML schema
            destination_db_type: "clickhouse", "bigquery", etc.
            optimization: Performance optimization level
        
        Returns:
            List of converted columns
        """
        source_db_type = schema["source"]["type"]
        total_columns = len(schema["source"]["columns"])
        
        # Log schema conversion start (summary only)
        logger.debug(
            "schema_conversion_started",
            source_type=source_db_type,
            destination_type=destination_db_type,
            total_columns=total_columns,
            optimization=optimization
        )
        
        converted_columns = []
        failed_columns = []
        
        for column in schema["source"]["columns"]:
            try:
                converted = cls.convert_column(
                    column,
                    source_db_type,
                    destination_db_type,
                    optimization
                )
                converted_columns.append(converted)
            except Exception as e:
                column_name = column.get("name", "unknown")
                failed_columns.append({
                    "name": column_name,
                    "type": column.get("type"),
                    "error": str(e)
                })
                logger.error(
                    "column_conversion_failed",
                    column_name=column_name,
                    column_type=column.get("type"),
                    error=str(e),
                    error_type=type(e).__name__
                )
                # Continue processing other columns
                continue
        
        # Log summary (not individual columns!)
        logger.info(
            "schema_conversion_completed",
            source_type=source_db_type,
            destination_type=destination_db_type,
            columns_converted=len(converted_columns),
            columns_failed=len(failed_columns),
            success_rate=f"{(len(converted_columns)/total_columns*100):.1f}%"
        )
        
        # Only log failed columns if there are any
        if failed_columns:
            logger.warning(
                "schema_conversion_had_failures",
                failed_columns=failed_columns
            )
        
        return converted_columns