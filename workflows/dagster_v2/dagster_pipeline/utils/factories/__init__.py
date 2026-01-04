# dagster_pipeline/factories/__init__.py
"""
ETL factories for creating Dagster assets
"""

from .etl_base_factory import BaseETLFactory
from .etl_mysql_to_clickhouse_factory import (
    MySQLToClickHouseFactory,
    create_mysql_to_clickhouse_asset
)

from .etl_postgres_to_clickhouse_factory import (
    PostgresToClickHouseFactory,
    create_postgres_to_clickhouse_asset
)

from .optimize_clickhouse_factory import (
    OptimizeClickHouseFactory,
    create_clickhouse_optimize_asset
)

__all__ = [
    "BaseETLFactory",
    
    # MySQL to ClickHouse
    "MySQLToClickHouseFactory",
    "create_mysql_to_clickhouse_asset",
    
    # Postgres to ClickHouse
    "PostgresToClickHouseFactory",
    "create_postgres_to_clickhouse_asset",
    
    # ClickHouse Cleanup
    "OptimizeClickHouseFactory",
    "create_clickhouse_optimize_asset",
]