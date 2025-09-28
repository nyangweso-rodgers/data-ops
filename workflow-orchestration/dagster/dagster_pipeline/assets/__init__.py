# dagster_pipeline/assets/__init__.py
from dagster import load_assets_from_modules
from . import sync_customers

# Load assets from the sync_customers module
assets = load_assets_from_modules([sync_customers])

# Export the assets and modules
__all__ = ['assets', 'sync_customers']