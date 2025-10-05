# dagster_pipeline/jobs/accounts_jobs.py
from dagster import define_asset_job, AssetSelection, RunRequest, schedule
from ..assets.sync_accounts import sync_accounts, AccountsSyncConfig
from datetime import datetime, timedelta


# Daily account reconciliation job
accounts_daily_reconciliation_job = define_asset_job(
    name="accounts_daily_reconciliation", 
    description="Daily account data reconciliation",
    selection=AssetSelection.assets(sync_accounts),
    config={
        "ops": {
            "sync_accounts": AccountsSyncConfig(
                sync_mode="incremental",
                batch_size=15000,
                destination_schema="public"
            )
        }
    }
)

# End-of-day account snapshot job
accounts_eod_snapshot_job = define_asset_job(
    name="accounts_eod_snapshot",
    description="End-of-day account snapshot",
    selection=AssetSelection.assets(sync_accounts),
    config={
        "ops": {
            "sync_accounts": AccountsSyncConfig(
                sync_mode="full",  # Full snapshot at end of day
                batch_size=20000,
                destination_schema="snapshots",  # Different schema for snapshots
                table_name="accounts_daily_snapshot"
            )
        }
    }
)


@schedule(
    job=accounts_daily_reconciliation_job,
    cron_schedule="45 2 * * *",  # Daily at 2:45 AM (after customers sync)
    description="Daily account reconciliation at 2:45 AM"
)
def accounts_daily_schedule(context):
    """Daily account reconciliation schedule"""
    return RunRequest(
        run_key=f"accounts_daily_{context.scheduled_execution_time.strftime('%Y%m%d')}",
        tags={
            "schedule": "accounts_daily",
            "table": "accounts",
            "sync_type": "reconciliation",
            "date": context.scheduled_execution_time.strftime('%Y-%m-%d')
        }
    )


@schedule(
    job=accounts_eod_snapshot_job,
    cron_schedule="0 23 * * 1-5",  # End of business day at 11 PM, Mon-Fri
    description="End-of-day account snapshot"
)
def accounts_eod_schedule(context):
    """End-of-day account snapshot schedule"""
    return RunRequest(
        run_key=f"accounts_eod_{context.scheduled_execution_time.strftime('%Y%m%d')}",
        tags={
            "schedule": "accounts_eod",
            "table": "accounts",
            "sync_type": "snapshot",
            "date": context.scheduled_execution_time.strftime('%Y-%m-%d'),
            "snapshot": "end_of_day"
        }
    )