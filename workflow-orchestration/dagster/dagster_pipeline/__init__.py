# dagster_pipeline/__init__.py
from dagster import Definitions
from . import assets
from .jobs import customers_daily_sync_job, customers_daily_schedule
from .resources import resources

# Debug: Print what resources are loaded
print("DEBUG: Available resources:", list(resources.keys()))
print("DEBUG: Resource types:", {k: type(v).__name__ for k, v in resources.items()})

# Create the main Definitions object
defs = Definitions(
    assets=assets.assets,  # Now correctly accessing the assets list
    jobs=[customers_daily_sync_job],
    schedules=[customers_daily_schedule],
    resources=resources
)