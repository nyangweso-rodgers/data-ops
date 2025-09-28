# dagster_pipeline/jobs/customers_jobs.py
from dagster import define_asset_job, AssetSelection, RunRequest, schedule
from ..assets.sync_customers import sync_customers
from datetime import datetime, timedelta

# Daily customer sync job - simplified without config
customers_daily_sync_job = define_asset_job(
    name="customers_daily_sync",
    description="Daily incremental sync of customer data",
    selection=AssetSelection.assets(sync_customers)
    # No config here - the asset handles its own configuration
)

@schedule(
    job=customers_daily_sync_job,
    cron_schedule="30 2 * * *",  # Daily at 2:30 AM
    description="Daily customer sync at 2:30 AM"
)
def customers_daily_schedule(context):
    """Daily customer data sync schedule"""
    execution_date = context.scheduled_execution_time.strftime('%Y-%m-%d')
    return RunRequest(
        run_key=f"customers_daily_{execution_date}",
        tags={
            "schedule": "customers_daily",
            "table": "customers",
            "sync_type": "incremental",
            "date": execution_date
        },
        partition_key=execution_date
    )