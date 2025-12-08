"""
Type mapper for converting source database types to destination types
Supports MySQL, Postgres → ClickHouse, BigQuery, Snowflake
"""

from typing import Dict, Any, Optional, List
from enum import Enum
import re


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


class TypeMapper:
    """
    Intelligent type mapper with smart defaults
    
    Usage:
        # Convert single column
        column = {"name": "id", "type": "bigint", "nullable": False}
        result = TypeMapper.convert_column(column, "mysql", "clickhouse")
        
        # Convert entire schema
        columns = TypeMapper.convert_schema(schema, "clickhouse")
    """
    
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
        """
        type_str = type_str.lower().strip()
        
        # Extract base type and parameters using regex
        match = re.match(r"(\w+)(?:\((.*?)\))?", type_str)
        if not match:
            raise ValueError(f"Cannot parse MySQL type: {type_str}")
        
        base_type = match.group(1)
        params_str = match.group(2) or ""
        
        # Parse parameters
        params = {}
        if params_str:
            if base_type == "enum" or base_type == "set":
                # Parse enum/set values: 'active','inactive','suspended'
                enum_values = [v.strip().strip("'\"") for v in params_str.split(",")]
                params["enum_values"] = enum_values
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
        
        normalized_type = type_mapping.get(base_type, DataType.STRING)
        
        result = {
            "normalized_type": normalized_type,
            "nullable": nullable,
            "source_type": type_str,
        }
        
        # Add type-specific parameters
        if normalized_type == DataType.STRING and "params" in params:
            result["length"] = int(params["params"][0])
        elif normalized_type == DataType.DECIMAL and "params" in params:
            result["precision"] = int(params["params"][0])
            result["scale"] = int(params["params"][1]) if len(params["params"]) > 1 else 0
        elif normalized_type == DataType.ENUM:
            result["enum_values"] = params.get("enum_values", [])
        
        return result
    
    @staticmethod
    def parse_postgres_type(type_str: str, nullable: bool = True) -> Dict[str, Any]:
        """
        Parse PostgreSQL type into normalized form
        
        Examples:
            "integer" → {normalized_type: INTEGER}
            "varchar(255)" → {normalized_type: STRING, length: 255}
            "integer[]" → {normalized_type: ARRAY}
        """
        type_str = type_str.lower().strip()
        
        # Handle array types: integer[]
        is_array = type_str.endswith("[]")
        if is_array:
            type_str = type_str[:-2]
        
        # Extract base type and parameters
        match = re.match(r"(\w+(?:\s+\w+)?)(?:\((.*?)\))?", type_str)
        if not match:
            raise ValueError(f"Cannot parse Postgres type: {type_str}")
        
        base_type = match.group(1)
        params_str = match.group(2) or ""
        
        type_mapping = {
            "smallint": DataType.INTEGER,
            "integer": DataType.INTEGER,
            "int": DataType.INTEGER,
            "int4": DataType.INTEGER,
            "bigint": DataType.BIGINT,
            "int8": DataType.BIGINT,
            "decimal": DataType.DECIMAL,
            "numeric": DataType.DECIMAL,
            "real": DataType.FLOAT,
            "float4": DataType.FLOAT,
            "double precision": DataType.FLOAT,
            "float8": DataType.FLOAT,
            "char": DataType.STRING,
            "varchar": DataType.STRING,
            "character varying": DataType.STRING,
            "text": DataType.TEXT,
            "date": DataType.DATE,
            "timestamp": DataType.TIMESTAMP,
            "timestamp without time zone": DataType.TIMESTAMP,
            "timestamptz": DataType.TIMESTAMP,
            "timestamp with time zone": DataType.TIMESTAMP,
            "boolean": DataType.BOOLEAN,
            "bool": DataType.BOOLEAN,
            "json": DataType.JSON,
            "jsonb": DataType.JSON,
            "uuid": DataType.STRING,
        }
        
        normalized_type = type_mapping.get(base_type, DataType.STRING)
        
        if is_array:
            normalized_type = DataType.ARRAY
        
        result = {
            "normalized_type": normalized_type,
            "nullable": nullable,
            "source_type": type_str + ("[]" if is_array else ""),
        }
        
        # Add parameters
        if params_str:
            params = [p.strip() for p in params_str.split(",")]
            if normalized_type == DataType.STRING:
                result["length"] = int(params[0])
            elif normalized_type == DataType.DECIMAL:
                result["precision"] = int(params[0])
                result["scale"] = int(params[1]) if len(params) > 1 else 0
        
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
        
        # Base type mapping
        type_map = {
            DataType.INTEGER: "Int32",
            DataType.BIGINT: "Int64",
            DataType.FLOAT: "Float64",
            DataType.STRING: "String",
            DataType.TEXT: "String",
            DataType.BOOLEAN: "UInt8",
            DataType.DATE: "Date",
            DataType.DATETIME: "DateTime",
            DataType.TIMESTAMP: "DateTime",
            DataType.JSON: "String",
            DataType.ARRAY: "Array(String)",
        }
        
        base_type = type_map.get(normalized_type, "String")
        
        # Apply optimizations
        if optimization == "speed":
            if normalized_type == DataType.ENUM:
                base_type = "LowCardinality(String)"
            elif normalized_type == DataType.TIMESTAMP:
                base_type = "DateTime64(3)"  # Millisecond precision
        elif optimization == "balanced":
            if normalized_type == DataType.ENUM:
                enum_values = normalized_info.get("enum_values", [])
                if len(enum_values) < 100:
                    base_type = "LowCardinality(String)"
                else:
                    base_type = "String"
        
        # Handle DECIMAL
        if normalized_type == DataType.DECIMAL:
            precision = normalized_info.get("precision", 18)
            scale = normalized_info.get("scale", 2)
            base_type = f"Decimal({min(precision, 76)}, {scale})"
        
        # Wrap with Nullable if needed
        if nullable and normalized_type not in [DataType.STRING, DataType.TEXT]:
            return f"Nullable({base_type})"
        
        return base_type
    
    # ========================================================================
    # BIGQUERY MAPPER
    # ========================================================================
    
    @staticmethod
    def to_bigquery_type(normalized_info: Dict[str, Any]) -> str:
        """Map to BigQuery type"""
        normalized_type = normalized_info["normalized_type"]
        
        type_map = {
            DataType.INTEGER: "INT64",
            DataType.BIGINT: "INT64",
            DataType.FLOAT: "FLOAT64",
            DataType.DECIMAL: "NUMERIC",
            DataType.STRING: "STRING",
            DataType.TEXT: "STRING",
            DataType.BOOLEAN: "BOOL",
            DataType.DATE: "DATE",
            DataType.DATETIME: "DATETIME",
            DataType.TIMESTAMP: "TIMESTAMP",
            DataType.JSON: "JSON",
            DataType.ARRAY: "ARRAY<STRING>",
            DataType.ENUM: "STRING",
        }
        
        return type_map.get(normalized_type, "STRING")
    
    # ========================================================================
    # HIGH-LEVEL API
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
        
        converted_columns = []
        for column in schema["source"]["columns"]:
            converted = cls.convert_column(
                column,
                source_db_type,
                destination_db_type,
                optimization
            )
            converted_columns.append(converted)
        
        return converted_columns