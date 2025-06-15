import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import os
import hashlib
import json
from datetime import datetime

# Configure module-level logger
logger = logging.getLogger(__name__)

class LoadYamlSchema:
    """
    Utility class to load YAML schema or sync config files from the filesystem.
    Supports .yml and .yaml extensions. Schema paths are specified in sync configs
    under 'schemas.source.filesystem' as relative or absolute paths.
    """
    # Configuration
    DEFAULT_CONFIGS_DIR = Path(__file__).parent.parent.parent.parent.parent.parent / "configs" / "sync_configs"
    CONFIGS_DIR = Path(os.getenv("CONFIGS_DIR", DEFAULT_CONFIGS_DIR))
    VALID_EXTENSIONS = {".yml", ".yaml"}

    @classmethod
    def _log_schema_summary(cls, schema: Dict[str, Any], schema_path: str) -> None:
        """Log a concise summary of the schema instead of the full content."""
        try:
            meta = schema.get('_meta', {})
            source_info = schema.get('source', {})
            targets_info = schema.get('targets', {})
            
            # Count columns in source and targets
            source_cols = 0
            target_cols = 0
            
            if 'postgres' in source_info:
                source_cols = len(source_info['postgres'].get('columns', {}))
            
            if 'postgres' in targets_info:
                target_cols = len(targets_info['postgres'].get('columns', {}))
            
            # Create structured log entry
            summary = {
                "event": "schema_loaded",
                "schema_path": str(schema_path),
                "version": meta.get('version', 'unknown'),
                "created": meta.get('created', 'unknown'),
                "owner": meta.get('owner', 'unknown'),
                "source_columns": source_cols,
                "target_columns": target_cols,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Schema summary: {json.dumps(summary)}")
            
        except Exception as e:
            logger.warning(f"Could not generate schema summary: {e}")
            logger.info(f"Schema loaded from: {schema_path}")

    @classmethod
    def _get_schema_hash(cls, schema: Dict[str, Any]) -> str:
        """Generate a hash of the schema for change detection."""
        return hashlib.md5(str(sorted(schema.items())).encode()).hexdigest()

    @classmethod
    def load_sync_config_file(cls, sync_config_path: str) -> Dict[str, Any]:
        """
        Load a sync configuration YAML file from the filesystem.

        Args:
            sync_config_path: Path to the config file (e.g., 'pg_sunculture_ep_to_pg_reporting_service/premises').

        Returns:
            Dictionary containing the parsed config.

        Raises:
            FileNotFoundError: If the config file is not found.
            ValueError: If the YAML is invalid, empty, or missing required fields.
        """
        config_path = None
        for ext in cls.VALID_EXTENSIONS:
            candidate_path = cls.CONFIGS_DIR / f"{sync_config_path}{ext}"
            if candidate_path.exists():
                config_path = candidate_path
                break

        if config_path is None:
            possible_paths = [cls.CONFIGS_DIR / f"{sync_config_path}{ext}" for ext in cls.VALID_EXTENSIONS]
            logger.error(f"Config file not found for {sync_config_path}: tried {possible_paths}")
            raise FileNotFoundError(f"Config file not found for {sync_config_path}")

        logger.info(f"Loading sync configs from: {config_path}")
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            if config is None:
                raise ValueError(f"Config file {config_path} is empty")
            if not config.get("job_id") or not config.get("schemas", {}).get("source", {}).get("filesystem"):
                raise ValueError(f"Invalid sync config at {config_path}: missing job_id or schemas.source.filesystem")
            
            logger.info(f"Successfully loaded config for job_id: {config.get('job_id')}")
            return config
            
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in config {config_path}: {e}")
            raise ValueError(f"Invalid YAML in config {config_path}: {e}")

    @classmethod
    def load_yaml_schema(cls, schema_path: str, config_path: Path, 
                        log_full_schema: bool = False,
                        previous_schema_hash: Optional[str] = None) -> Dict[str, Any]:
        """
        Load schema from a YAML file specified by a filesystem path, relative to the config file.

        Args:
            schema_path: Filesystem path (e.g., '../../schemas/yaml/postgres/sunculture_ep/premises/v1/premises.yml').
            config_path: Path to the sync job config file for relative path resolution.
            log_full_schema: If True, logs the complete schema (use sparingly).
            previous_schema_hash: Hash of previous schema to detect changes.

        Returns:
            Dictionary containing the parsed schema.

        Raises:
            ValueError: If the path is invalid or the YAML is invalid.
            FileNotFoundError: If the schema file is not found.
        """
        # Resolve relative path
        resolved_path = (config_path.parent / schema_path).resolve()
        
        # Validate extension
        if resolved_path.suffix not in cls.VALID_EXTENSIONS:
            logger.error(f"Invalid schema file extension for {resolved_path}: must be .yml or .yaml")
            raise ValueError(f"Invalid schema file extension: {resolved_path.suffix}. Must be .yml or .yaml")

        # Check file existence
        if not resolved_path.exists():
            logger.error(f"Schema file not found at: {resolved_path}")
            raise FileNotFoundError(f"Schema file not found at: {resolved_path}")

        logger.info(f"Loading schema from: {resolved_path}")
        
        try:
            with open(resolved_path, 'r') as f:
                schema = yaml.safe_load(f)
                
            if schema is None:
                raise ValueError(f"Schema file {resolved_path} is empty")
            
            # Generate current schema hash
            current_hash = cls._get_schema_hash(schema)
            
            # Check if schema has changed
            if previous_schema_hash and current_hash == previous_schema_hash:
                logger.info(f"Schema unchanged (hash: {current_hash[:8]}...)")
            else:
                if previous_schema_hash:
                    logger.info(f"Schema changed (new hash: {current_hash[:8]}...)")
                
                # Log schema summary by default
                cls._log_schema_summary(schema, resolved_path)
            
            # Only log full schema if explicitly requested or in debug mode
            if log_full_schema or logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Full schema content: {schema}")
            
            # Add hash to schema for downstream use
            schema['_internal_hash'] = current_hash
            
            return schema
            
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {resolved_path}: {e}")
            raise ValueError(f"Invalid YAML in {resolved_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading schema {resolved_path}: {e}")
            raise