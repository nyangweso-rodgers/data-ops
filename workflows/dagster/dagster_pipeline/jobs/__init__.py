# dagster-pipeline/jobs/__init__.py
from .customers_jobs import customers_daily_sync_job, customers_daily_schedule

__all__ = [
    'customers_daily_sync_job',
    'customers_daily_schedule',
]