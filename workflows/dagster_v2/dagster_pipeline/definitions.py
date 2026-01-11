# definitions.py
"""
Main Dagster definitions file.
"""

from dagster import Definitions
from dagster import define_asset_job
from dagster import ScheduleDefinition

# Import ALL resources from the central registry
from dagster_pipeline.resources.registry import (
    # MySQL
    mysql_amt,
    mysql_sales_service_dev,
    mysql_sales_service,
    
    # ClickHouse
    clickhouse_resource,
    
    # PostgreSQL
    dagster_postgres_resource,
    postgres_fma,
    
)

# Import assets 
from dagster_pipeline.assets.etl.mysql_to_clickhouse_asset import assets as mysql_assets
from dagster_pipeline.assets.etl.postgres_to_clickhouse_asset import assets as postgres_assets
from dagster_pipeline.assets.maintenance.optimize_clickhouse_asset import assets as optimize_clickhouse_asset

# Import SchemaLoader class
from dagster_pipeline.utils.schema_loader import SchemaLoader

# ═════════════════════════════════════════════════════════════════════════════
# ETL JOBS
# ═════════════════════════════════════════════════════════════════════════════

# MySQL Sales Service Job
mysql_sales_service_to_clickhouse_job = define_asset_job(
    name="mysql_sales_service_to_clickhouse_job",
    selection=[
        "mysql_sales_service_leadsources_to_clickhouse",
        "mysql_sales_service_leads_to_clickhouse",
        "mysql_sales_service_lead_channels_to_clickhouse",
        "mysql_sales_service_cds_to_clickhouse",
        "mysql_sales_service_form_answers_to_clickhouse",
        "mysql_sales_service_kyc_requests_to_clickhouse",
        "mysql_sales_service_forms_to_clickhouse"
    ],
)

# MySQL AMT Job
mysql_amt_to_clickhouse_job = define_asset_job(
    name="mysql_amt_to_clickhouse_job",
    selection=[
        "mysql_amt_accounts_to_clickhouse",
    ],
)

# PostgreSQL FMA Job
postgres_fma_to_clickhouse_job = define_asset_job(
    name="postgres_fma_to_clickhouse_job",
    selection=[
        "postgres_fma_premises_to_clickhouse",
        "postgres_fma_premise_details_to_clickhouse",
    ],
)
# ═════════════════════════════════════════════════════════════════════════════
# SNAPSHOT JOBS (Point-in-Time Capture)
# ═════════════════════════════════════════════════════════════════════════════
# Monthly Snapshots (end of month)

# ═════════════════════════════════════════════════════════════════════════════
# MAINTENANCE JOBS
# ═════════════════════════════════════════════════════════════════════════════

# ClickHouse Cleanup Job
clickhouse_cleanup_job = define_asset_job(
    name="clickhouse_cleanup_job",
    selection=[
        "cleanup_sales_service_leads",
    ],
    description="Deduplicate ClickHouse tables to remove duplicate records",
)

# ═════════════════════════════════════════════════════════════════════════════
# ETL SCHEDULES
# ═════════════════════════════════════════════════════════════════════════════

# MySQL Sales Service Schedule (Every 20 minutes, 6 AM - 8 PM)
mysql_sales_service_to_clickhouse_schedule = ScheduleDefinition(
    job=mysql_sales_service_to_clickhouse_job,
    cron_schedule="*/20 6-20 * * *",
    name="mysql_sales_service_to_clickhouse_schedule",
)

# MySQL AMT Schedule (Every 20 minutes, 6 AM - 8 PM)
mysql_amt_to_clickhouse_schedule = ScheduleDefinition(
    job=mysql_amt_to_clickhouse_job,
    cron_schedule="*/20 6-20 * * *",
    name="mysql_amt_to_clickhouse_schedule",
)

# PostgreSQL FMA Schedule (Every 30 minutes, 6 AM - 8 PM)
postgres_fma_to_clickhouse_schedule = ScheduleDefinition(
    job=postgres_fma_to_clickhouse_job,
    cron_schedule="*/30 6-20 * * *",
    name="postgres_fma_to_clickhouse_schedule",
)

# ═════════════════════════════════════════════════════════════════════════════
# MAINTENANCE SCHEDULES
# ═════════════════════════════════════════════════════════════════════════════

# ClickHouse Cleanup Schedule (Daily at midnight, Sunday-Friday)
clickhouse_cleanup_schedule = ScheduleDefinition(
    job=clickhouse_cleanup_job,
    cron_schedule="0 0 * * 0-5",  # 0 0 * * 0-5 = midnight Sun-Fri
    name="clickhouse_cleanup_schedule",
    description="Run ClickHouse deduplication daily at midnight (Sun-Fri)",
)

# ═════════════════════════════════════════════════════════════════════════════
# SNAPSHOT SCHEDULES
# ═════════════════════════════════════════════════════════════════════════════

# Monthly Snapshots: Run on 1st-5th of month at 1 AM

# ═════════════════════════════════════════════════════════════════════════════
# DAGSTER DEFINITIONS
# ═════════════════════════════════════════════════════════════════════════════

defs = Definitions(
    assets=[
        # ETL assets (continuous sync)
        *mysql_assets,
        *postgres_assets,
        
        # Maintenance assets (cleanup/optimization)
        *optimize_clickhouse_asset,
    ],
    resources={
        # MySQL
        "mysql_amt": mysql_amt,
        "mysql_sales_service_dev": mysql_sales_service_dev,
        "mysql_sales_service": mysql_sales_service,
        
        # PostgreSQL
        "postgres_fma": postgres_fma,
        
        # ClickHouse
        "clickhouse_resource": clickhouse_resource,
        
        # Infrastructure
        "dagster_postgres_resource": dagster_postgres_resource,
        
        # Utilities
        "schema_loader": SchemaLoader(),
    },
    jobs=[
        # ETL Jobs
        mysql_sales_service_to_clickhouse_job,
        mysql_amt_to_clickhouse_job,
        postgres_fma_to_clickhouse_job,
        
        # Maintenance Jobs
        clickhouse_cleanup_job, 
        
        # Snapshot Jobs
        
        # Data Quality Jobs
    ],
    schedules=[
        # ETL Schedules
        mysql_sales_service_to_clickhouse_schedule,
        mysql_amt_to_clickhouse_schedule,
        postgres_fma_to_clickhouse_schedule,
        
        # Maintenance Schedules
        clickhouse_cleanup_schedule, 
        
        # Snapshot Schedules
        
        # Data Quality Schedules
    ], 
)