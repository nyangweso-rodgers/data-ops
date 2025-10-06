# dagster_pipeline/assets/__init__.py
from .etl.mysql_to_clickhouse.amtdb.accounts_asset import sync_accounts

assets = [sync_accounts]