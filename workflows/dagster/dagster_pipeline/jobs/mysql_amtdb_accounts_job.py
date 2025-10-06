from dagster import job
from dagster_pipeline.assets.etl.mysql_to_clickhouse.amtdb.accounts_asset import sync_accounts

@job
def mysql_amtdb_accounts_job():
    sync_accounts()