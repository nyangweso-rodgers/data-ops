from dagster import job
from dagster_pipeline.assets.etl.mysql_to_clickhouse.amtdb.accounts.v1.accounts_asset import sync_accounts_to_clickhouse

@job
def mysql_amtdb_accounts_job():
    sync_accounts_to_clickhouse()