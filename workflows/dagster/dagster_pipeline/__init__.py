# dagster_pipeline/__init__.py
from dagster import Definitions, ScheduleDefinition
from . import assets
from .jobs import mysql_amtdb_accounts_job
from .resources import resources

# Define schedule (attach to job)
accounts_schedule = ScheduleDefinition(
    job=mysql_amtdb_accounts_job,
    cron_schedule="*/15 6-21 * * *",
    execution_timezone="UTC"
)

# Create the main Definitions object
defs = Definitions(
    assets=assets.assets,
    jobs=[mysql_amtdb_accounts_job],
    schedules=[accounts_schedule],  
    resources=resources
)