# dagster-pipeline/resources/__init__.py
from dagster import ConfigurableResource
from .mysql import MySQLResource
from .postgres import PostgresResource
import yaml
import os
from typing import Dict, Any

def expand_env_vars(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively expand environment variables in configuration"""
    if isinstance(config_dict, dict):
        return {k: expand_env_vars(v) for k, v in config_dict.items()}
    elif isinstance(config_dict, list):
        return [expand_env_vars(item) for item in config_dict]
    elif isinstance(config_dict, str):
        return os.path.expandvars(config_dict)
    else:
        return config_dict

def create_resources_from_config(config: Dict[str, Any]) -> Dict[str, ConfigurableResource]:
    """Create resource instances from configuration"""
    resources = {}
    
    print(f"DEBUG: Raw config resources: {config.get('resources', {}).keys()}")
    
    for resource_name, resource_config in config.get('resources', {}).items():
        print(f"DEBUG: Processing resource '{resource_name}' of type '{resource_config['type']}'")
        
        resource_type = resource_config['type']
        resource_params = expand_env_vars(resource_config['config'])
        
        print(f"DEBUG: Resource params for {resource_name}: {resource_params}")
        
        # Convert string ports to integers
        if 'port' in resource_params and isinstance(resource_params['port'], str):
            try:
                resource_params['port'] = int(resource_params['port'])
            except ValueError:
                # Set default port based on resource type
                if resource_type == 'postgres':
                    resource_params['port'] = 5432
                elif resource_type == 'mysql':
                    resource_params['port'] = 3306
                else:
                    resource_params['port'] = 5432
        
        if resource_type == 'mysql':
            resources[resource_name] = MySQLResource(**resource_params)
            print(f"DEBUG: Created MySQL resource '{resource_name}'")
        elif resource_type == 'postgres':
            resources[resource_name] = PostgresResource(**resource_params)
            print(f"DEBUG: Created Postgres resource '{resource_name}'")
        elif resource_type == 'clickhouse':
            # TODO: Implement ClickHouse resource
            print(f"DEBUG: Skipping ClickHouse resource '{resource_name}' (not implemented)")
            pass
        else:
            raise ValueError(f"Unknown resource type: {resource_type}")
    
    print(f"DEBUG: Final resources created: {list(resources.keys())}")
    return resources

# Load config and create resources
config_path = os.path.join(os.path.dirname(__file__), '../config/local.yaml')
print(f"DEBUG: Loading config from: {config_path}")

try:
    with open(config_path, 'r') as f:
        config_content = f.read()
        # Expand environment variables in the YAML content
        expanded_content = os.path.expandvars(config_content)
        config = yaml.safe_load(expanded_content)
    
    print(f"DEBUG: Config loaded successfully")
    resources = create_resources_from_config(config)
    print(f"DEBUG: Resources initialization complete")
    
except Exception as e:
    print(f"ERROR: Failed to load resources: {e}")
    resources = {}

# Export resources for easy access
__all__ = ['create_resources_from_config', 'resources', 'MySQLResource', 'PostgresResource']