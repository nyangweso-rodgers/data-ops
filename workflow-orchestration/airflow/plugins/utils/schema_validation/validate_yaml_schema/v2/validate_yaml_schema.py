import logging
from typing import Dict, Any
import json
from datetime import datetime

# Configure module-level logger
logger = logging.getLogger(__name__)

class ValidateYamlSchema:
    """
    Utility class to validate YAML schema files for sync jobs.
    Ensures schema meets specific rules for source and target columns.
    Supports multiple source/target types (e.g., postgres, mysql) for scalability.
    """
    VALID_SQL_TYPES = {
        "uuid", "int4", "_int", "varchar", "varchar(255)", "timestamp", "boolean"
    }
    VALID_SOURCE_TYPES = {"postgres", "mysql", "clickhouse", "api"}  # Extend as needed
    VALID_TARGET_TYPES = {"postgres", "mysql", "clickhouse"}  # Extend as needed

    @classmethod
    def _log_validation_summary(cls, schema: Dict[str, Any], source_type: str, target_type: str) -> None:
        """Log a concise summary of the validation results."""
        try:
            meta = schema.get('_meta', {})
            source_columns = schema.get("source", {}).get(source_type, {}).get("columns", {})
            target_columns = schema.get("targets", {}).get(target_type, {}).get("columns", {})
            
            # Count active vs inactive source columns
            active_source_cols = sum(1 for col in source_columns.values() if col.get("active", False))
            inactive_source_cols = len(source_columns) - active_source_cols
            
            # Count primary keys and auto-generated columns
            primary_keys = [col_name for col_name, col_config in target_columns.items() 
                          if col_config.get("primary_key")]
            auto_generated_cols = [col_name for col_name, col_config in target_columns.items() 
                                 if col_config.get("auto_generated")]
            
            validation_summary = {
                "event": "schema_validated",
                "schema_version": meta.get('version', 'unknown'),
                "source_type": source_type,
                "target_type": target_type,
                "source_columns_total": len(source_columns),
                "source_columns_active": active_source_cols,
                "source_columns_inactive": inactive_source_cols,
                "target_columns_total": len(target_columns),
                "primary_keys": primary_keys,
                "auto_generated_columns": auto_generated_cols,
                "validation_status": "success",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Validation summary: {json.dumps(validation_summary)}")
            
        except Exception as e:
            logger.warning(f"Could not generate validation summary: {e}")
            logger.info("Schema validation completed successfully")

    @classmethod
    def validate_schema(cls, schema: Dict[str, Any]) -> None:
        """
        Validate a loaded schema dictionary against specific rules.

        Args:
            schema: Parsed schema dictionary from LoadYamlSchema.

        Raises:
            ValueError: If the schema fails any validation rule.
        """
        logger.info("Starting schema validation")
        logger.debug(f"Schema content: {schema}")

        try:
            # 1. Check _meta presence
            if "_meta" not in schema:
                raise ValueError("Schema missing required '_meta' section")
            meta = schema["_meta"]
            for field in ["version", "created", "description"]:
                if field not in meta:
                    raise ValueError(f"Schema _meta missing required field: {field}")

            logger.debug(f"_meta validation passed for version: {meta.get('version')}")

            # 2. Check source and targets presence
            if "source" not in schema or "targets" not in schema:
                raise ValueError("Schema missing 'source' or 'targets' section")

            # Validate source type
            source_types = [key for key in schema["source"] if key in cls.VALID_SOURCE_TYPES]
            if len(source_types) != 1:
                raise ValueError(f"Schema 'source' must have exactly one valid type from {cls.VALID_SOURCE_TYPES}, found: {source_types}")
            source_type = source_types[0]

            # Validate target type
            target_types = [key for key in schema["targets"] if key in cls.VALID_TARGET_TYPES]
            if len(target_types) != 1:
                raise ValueError(f"Schema 'targets' must have exactly one valid type from {cls.VALID_TARGET_TYPES}, found: {target_types}")
            target_type = target_types[0]

            logger.debug(f"Source type: {source_type}, Target type: {target_type}")

            # 3. Check columns presence
            source_columns = schema["source"][source_type].get("columns", {})
            target_columns = schema["targets"][target_type].get("columns", {})
            if not source_columns or not target_columns:
                raise ValueError("Source or target columns are empty")

            logger.debug(f"Found {len(source_columns)} source columns and {len(target_columns)} target columns")

            # 4. Validate source-to-target mapping
            mapping_errors = []
            for col_name, col_config in source_columns.items():
                if "target" not in col_config:
                    mapping_errors.append(f"Source column '{col_name}' missing 'target' field")
                    continue
                target_name = col_config["target"]
                if target_name not in target_columns:
                    mapping_errors.append(f"Source column '{col_name}' maps to non-existent target column '{target_name}'")
            
            if mapping_errors:
                raise ValueError(f"Column mapping errors: {'; '.join(mapping_errors)}")

            logger.debug("Source-to-target column mapping validation passed")

            # 5. Validate target column types
            type_errors = []
            for col_name, col_config in target_columns.items():
                if "type" not in col_config:
                    type_errors.append(f"Target column '{col_name}' missing 'type' field")
                    continue
                col_type = col_config["type"]
                if not any(col_type.startswith(valid_type) for valid_type in cls.VALID_SQL_TYPES):
                    type_errors.append(f"Target column '{col_name}' has invalid type: {col_type}")
            
            if type_errors:
                raise ValueError(f"Column type errors: {'; '.join(type_errors)}")

            logger.debug("Target column type validation passed")

            # 6. Validate auto-generated sync_time
            if "sync_time" not in target_columns:
                raise ValueError("Target columns missing required 'sync_time' column")
            sync_time = target_columns["sync_time"]
            sync_time_errors = []
            if not sync_time.get("auto_generated", False):
                sync_time_errors.append("Missing 'auto_generated: True'")
            if sync_time.get("type") != "timestamp":
                sync_time_errors.append("Must have type 'timestamp'")
            if not sync_time.get("nullable", True):
                sync_time_errors.append("Must be nullable")
            
            if sync_time_errors:
                raise ValueError(f"sync_time column errors: {'; '.join(sync_time_errors)}")

            logger.debug("sync_time column validation passed")

            # 7. Validate exactly one primary key in target
            primary_keys = [col_name for col_name, col_config in target_columns.items() 
                          if col_config.get("primary_key")]
            if len(primary_keys) != 1:
                raise ValueError(f"Target must have exactly one primary key, found {len(primary_keys)}: {primary_keys}")

            logger.debug(f"Primary key validation passed: {primary_keys[0]}")

            # 8. Validate source column active boolean
            active_errors = []
            for col_name, col_config in source_columns.items():
                if "active" not in col_config:
                    active_errors.append(f"Source column '{col_name}' missing 'active' field")
                elif not isinstance(col_config["active"], bool):
                    active_errors.append(f"Source column '{col_name}' 'active' must be boolean, got {type(col_config['active'])}")
            
            if active_errors:
                raise ValueError(f"Active field errors: {'; '.join(active_errors)}")

            logger.debug("Source column 'active' field validation passed")

            # Log validation summary
            cls._log_validation_summary(schema, source_type, target_type)

        except ValueError as e:
            logger.error(f"Schema validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during schema validation: {str(e)}")
            raise ValueError(f"Schema validation failed due to unexpected error: {str(e)}")