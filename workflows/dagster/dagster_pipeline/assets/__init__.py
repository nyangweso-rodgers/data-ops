# workflows/dagster/dagster_pipeline/assets/__init__.py
from .etl.mysql_to_clickhouse.amtdb.accounts.v1.accounts_asset import sync_accounts_to_clickhouse

assets = [sync_accounts_to_clickhouse]